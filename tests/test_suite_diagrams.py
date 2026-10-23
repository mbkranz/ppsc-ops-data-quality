"""Diagram parts preserve Ibis structure and group nodes by their owning entities."""

import xml.etree.ElementTree as ET

import ibis
import ibis.expr.operations as ops
import pytest
from ibis.expr.visualize import to_graph

from ppsc_ops_data_quality.account_to_survey_results.schemas import (
    FLOW_ACCOUNT_COMPARISON,
    ROLLUP_ACCOUNT_COMPARISON,
)
from scripts import generate_suite_diagrams as diagrams


def test_parts_stop_at_named_inputs_and_preserve_schemas():
    parts = diagrams.illustrative_parts()
    expected_inputs = {
        "flow": {
            "Account_Before": {"Account_History"},
            "Contact_At_Execution": {"Contact_History"},
            "Survey_Results_At_Execution": {"Survey_Result__c_History"},
            "Trigger_Survey_Result": {"Survey_Results_At_Execution"},
            "Joined_Record": {"Trigger_Survey_Result", "Contact_At_Execution", "Account_Before"},
            "Record_With_Primary_Consent": {
                "Joined_Record",
                "Survey_Results_At_Execution",
            },
            "Record_With_EHR_Consent": {
                "Record_With_Primary_Consent",
                "Survey_Results_At_Execution",
            },
            "Record_With_Physical_Measurement": {
                "Record_With_EHR_Consent",
                "Survey_Results_At_Execution",
            },
            "Record_With_Pediatric_Permission": {
                "Record_With_Physical_Measurement",
                "Survey_Results_At_Execution",
            },
            "Flow_Context": {"Record_With_Pediatric_Permission"},
            "Expected_Account": {"Flow_Context"},
            "Account_After": {"Account_History"},
            "Account_After_By_Survey_Event": {"Account_After"},
            "Flow_Comparison": {"Flow_Context", "Account_After_By_Survey_Event"},
        },
        "rollups": {
            "Account_Snapshot": {"Account_History"},
            "Survey_Result_Snapshot": {"Survey_Result__c_History"},
            "Expected_Rollups": {"Account_Snapshot", "Survey_Result_Snapshot"},
            "Rollup_Comparison": {"Account_Snapshot", "Survey_Result_Snapshot"},
        },
    }
    for suite, stages in parts.items():
        assert [part.name for part in stages] == list(expected_inputs[suite])
        schemas = {}
        for part in stages:
            inputs = part.expression.op().find(ops.UnboundTable)
            assert {node.name for node in inputs} == expected_inputs[suite][part.name]
            for node in inputs:
                if node.name in schemas:
                    assert node.schema == schemas[node.name]
            schemas[part.name] = part.expression.schema()
    assert parts["flow"][-1].expression.schema() == FLOW_ACCOUNT_COMPARISON
    assert parts["rollups"][-1].expression.schema() == ROLLUP_ACCOUNT_COMPARISON


def _svg_elements(root, kind):
    namespace = "{http://www.w3.org/2000/svg}"
    return {
        group.find(namespace + "title").text: tuple(
            text.text for text in group.iter(namespace + "text")
        )
        for group in root.iter(namespace + "g")
        if group.attrib.get("class") == kind
    }


def test_parent_ownership_survives_boundaries():
    flow_parent = "Flow: Survey_Result_Survey_Completion_Updates"
    object_parent = "Salesforce object: Account"
    outputs_by_suite = {}
    case_parents = set()
    for suite, parts in diagrams.illustrative_parts().items():
        inputs = {}
        for part in parts:
            parents, outputs = diagrams.node_parents(part.expression, inputs)
            inputs[part.name] = outputs
            if part.name == "Flow_Context":
                assert {
                    parent for node, parent in parents.items() if isinstance(node, ops.Floor)
                } == {flow_parent}
                for node, parent in parents.items():
                    if isinstance(node, ops.Field) and node.name == "Participant__r.Birthdate":
                        assert parent == "Salesforce object: Contact"
            case_parents.update(
                parent for node, parent in parents.items() if isinstance(node, ops.SearchedCase)
            )
        outputs_by_suite[suite] = inputs
    flow = outputs_by_suite["flow"]
    assert flow["Joined_Record"]["Participant__r.Account.Id"] == object_parent
    assert flow["Joined_Record"]["Participant__r.AccountId"] == "Salesforce object: Contact"
    assert flow["Joined_Record"]["Participant__r.Birthdate"] == "Salesforce object: Contact"
    assert flow["Joined_Record"]["Id"] == "Salesforce object: Survey_Result__c"
    for name in (
        "FlowFormula_Age_At_Execution",
        "FlowRecordLookup.Pediatric_Permission_For_Assent.match_count",
    ):
        assert flow["Flow_Context"][name] == flow_parent
    assert flow["Expected_Account"]["Basics_Date_Time__c"] == object_parent
    for role in ("expected", "observed"):
        assert flow["Flow_Comparison"][f"{role}__Basics_Date_Time__c"] == object_parent
    assert object_parent in case_parents
    assert set(outputs_by_suite["rollups"]["Rollup_Comparison"].values()) == {object_parent}


def test_identical_field_names_use_their_source_object_and_shared_expressions_are_neutral():
    account = ibis.table({"Id": "string"}, name="Account_History")
    contact = ibis.table({"Id": "string"}, name="Contact_History")
    query = account.join(contact, account.Id == contact.Id).select(
        account.Id.name("account"), contact.Id.name("contact")
    )
    parents, outputs = diagrams.node_parents(query, {})
    assert outputs == {
        "account": "Salesforce object: Account",
        "contact": "Salesforce object: Contact",
    }
    for node, parent in parents.items():
        if isinstance(node, ops.Equals):
            assert parent == diagrams.SHARED_PARENT
    assert parents[query.op()] == diagrams.SHARED_PARENT
    unknown = ibis.table({"a": "string"}, name="Unmapped")
    _, outputs = diagrams.node_parents(unknown, {})
    assert outputs == {"a": diagrams.SHARED_PARENT}


def test_default_exports_separate_parent_grouped_native_graphs(tmp_path, monkeypatch):
    parts = diagrams.illustrative_parts()
    monkeypatch.setattr(diagrams, "illustrative_parts", lambda: parts)
    assert diagrams.main(["--output", str(tmp_path)]) == 0
    assert len(list(tmp_path.iterdir())) == sum(2 * len(stages) + 1 for stages in parts.values())
    for suite, stages in parts.items():
        slug = f"account_to_survey_results_{suite}"
        markdown = (tmp_path / f"{slug}.md").read_text()
        assert "diagram-only boundaries, not materialized runtime tables" in markdown
        assert "no data was queried" in markdown
        assert "Parent entity" in markdown
        assert "Shared expressions" in markdown
        assert not (tmp_path / f"{slug}.svg").exists()
        inputs = {}
        for part in stages:
            stem = f"{slug}_{part.name}"
            parents, outputs = diagrams.node_parents(part.expression, inputs)
            inputs[part.name] = outputs
            grouped = (tmp_path / f"{stem}.dot").read_text()
            assert grouped == diagrams.build_parent_graph(part.expression, parents).source
            assert "expectation_0" not in grouped
            native_svg = ET.fromstring(to_graph(part.expression).pipe(format="svg"))
            grouped_svg = ET.parse(tmp_path / f"{stem}.svg").getroot()
            assert _svg_elements(native_svg, "node") == _svg_elements(grouped_svg, "node")
            assert _svg_elements(native_svg, "edge") == _svg_elements(grouped_svg, "edge")
            clusters = _svg_elements(grouped_svg, "cluster")
            assert {text for labels in clusters.values() for text in labels} == set(
                parents.values()
            )
            for parent in set(parents.values()):
                assert f'fillcolor="{diagrams.PARENT_COLORS[parent]}"' in grouped
            assert f"[SVG]({stem}.svg) | [DOT]({stem}.dot)" in markdown
            assert f"`{part.builder}()`" in markdown
            assert f"## {part.name}" in markdown


@pytest.mark.parametrize("suite", ["flow", "rollups"])
def test_suite_selection_exports_only_selected_parts(tmp_path, monkeypatch, suite):
    table = ibis.table({"a": "int64"}, name="source")
    part = diagrams.DiagramPart("Example", "example", table)
    monkeypatch.setattr(diagrams, "illustrative_parts", lambda: {"flow": [part], "rollups": [part]})
    assert diagrams.main(["--suite", suite, "--output", str(tmp_path)]) == 0
    slug = f"account_to_survey_results_{suite}"
    assert {path.name for path in tmp_path.iterdir()} == {
        f"{slug}.md",
        f"{slug}_Example.svg",
        f"{slug}_Example.dot",
    }


def test_missing_boundary_fails_explicitly():
    source = ibis.table({"a": "int64"}, name="source")
    other = ibis.table(source.schema(), name="other")
    with pytest.raises(ValueError, match="boundary must occur"):
        diagrams._cut_input(source, other, other)


def test_missing_graphviz_fails_explicitly(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(diagrams.shutil, "which", lambda _: None)
    with pytest.raises(SystemExit) as error:
        diagrams.main(["--output", str(tmp_path)])
    assert error.value.code == 2
    assert "Install Graphviz's 'dot' executable" in capsys.readouterr().err
    assert not list(tmp_path.iterdir())
