"""Load the provisional logical input contract; physical bindings stay explicit."""

from functools import cache
from importlib.resources import files
from pathlib import Path

from open_data_contract_standard.model import OpenDataContractStandard
from ppsc_metadata.contracts import load_contract


@cache
def validation_input_contract() -> OpenDataContractStandard:
    return load_contract(Path(str(files(__package__).joinpath("validation-inputs.odcs.yaml"))))
