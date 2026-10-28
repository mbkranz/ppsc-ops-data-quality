# Skill source

Installed from the user-supplied `ppsc-agent-skills.bundle` Git bundle.
Source commit: `ce719a670a77efb142531a8ec29318d658f70557`.
Bundle SHA256: `7f67cac984a668a912c4003cb3340eedb7e4468ebb07e77a765c3a5569cf5056`.

The three upstream skill files are copied unchanged. Repository discovery uses
`.agents/skills/design-python-contracts/SKILL.md`; the examples are available
locally through its relative reference link. No upstream top-level repository
instructions, evaluation harness or application dependencies were installed.

| Upstream skill-relative file | SHA256 |
| --- | --- |
| `SKILL.md` | `5b45853c713da7b1d440628f72abf1d1699b39c1fda2d32ba77a17d9e09427a4` |
| `agents/openai.yaml` | `bc66d3c6049be7249ded464edaa09f7f2559377bccab2cbfb598aaa8aa08f819` |
| `references/ppsc-design-examples.md` | `a41641a6b20d83710b44667ef7c265beeaf376e3885b56572f7ba995cf5df488` |

To update, inspect a reviewed source revision, replace the same three files and
refresh this provenance. Apply the skill within Ops' existing `AGENTS.md`
constraints and the user's authorized task scope. A new agent session may be
needed for automatic skill discovery; the files can also be read directly.
