# H1 - AI Extension Review: Message Normalization

- Member: Hiển (`AIVIETNAM-AIO-TheHien`).
- Date: 2026-10-23.
- Feature: normalize message text at the public request boundary.
- Files: `src/assistant_core/models.py`, `tests/test_models.py` and related docs.
- Baseline: models/errors refactor from `1d7fc84`, locally merged into `main` at
  `2999d51`. The owner has authorized a local commit; the H1 changes are not yet published.

## 1. Feature and intended behavior

The original `Message` accepted whitespace-only text and checked raw length
before any normalization. The extension strips surrounding whitespace, then
requires the result to contain 1-2000 characters. Unicode content and internal
whitespace are preserved; `session_id`, `Source` and `Response` fields retain
their previous behavior.

| Input or contract | Before H1 | After H1 |
| --- | --- | --- |
| `Message(text="  hi  ").text` | `"  hi  "` | `"hi"` |
| Whitespace-only text, including tabs or Unicode spaces | Accepted if its raw length was in range | `ValidationError` on `text` |
| 2000 content characters plus surrounding whitespace | Rejected because the raw input exceeded 2000 | Accepted after stripping |
| 2001 content characters plus surrounding whitespace | Rejected | Still rejected |
| Internal double spaces and Vietnamese/emoji content | Preserved | Still preserved |
| Valid UTF-8 byte input | Pydantic decoded it without stripping | Pydantic decodes it, then strips and validates |
| Invalid types or invalid UTF-8 bytes | `ValidationError` | Still `ValidationError`, without an accidental `.strip()` exception |
| Spaces in a session ID, source title or response answer | Preserved | Still preserved |

This is an intentional extension to the tutorial's initial request contract,
not a claim that the original refactor was behavior-preserving for whitespace.
Callers that validate a blank request must handle Pydantic `ValidationError`.

## 2. Prompt and authorization

The owner's H1 authorization was:

> từ từ xin lỗi nhé mày làm H1 luôn add feature gì cũng được như cái meassage hồi nãy

The working brief below was formulated by the assistant from the approved
message feature; it is not a verbatim quotation of a separate user prompt:

> Extend `Message.text` to strip leading/trailing whitespace, reject blank
> results and enforce 1-2000 characters after normalization. Preserve Unicode,
> internal whitespace and all unrelated fields. Reuse existing Pydantic,
> add meaningful tests, document at least three review improvements and leave
> all changes uncommitted for Hiển to check before authorizing a commit.

## 3. Initial AI prototype and observed problems

The initial prototype was executed in a scratch Python session:

```python
class InitialDraft(BaseModel):
    text: str = Field(min_length=1, max_length=2000)

    @field_validator("text")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()
```

Observed: `"   "` became an accepted zero-length string, while a padded
2000-character message raised `ValidationError`. The default after-validator
ran too late relative to the field constraints.

A second scratch prototype changed the decorator to
`@field_validator("text", mode="before")` but still called `value.strip()`
unconditionally. It corrected those length cases, but integer and `None` input
raised `AttributeError` instead of the intended Pydantic `ValidationError`.
These are observed prototype results, not hypothetical failures attributed to
code that was never generated.

## 4. Three implemented review improvements

| # | Generated or existing code | Observed problem | Implemented change | Why it improves the result |
| --- | --- | --- | --- | --- |
| 1 | Initial after-validator stripped text after `Field` length checks. | Blank text passed after becoming empty; padded 2000-character content was rejected. | Moved normalization and length constraints into field-scoped `StringConstraints`, which strips before checking length. | The required order is enforced consistently at model validation. |
| 2 | Follow-up before-validator called `.strip()` directly on untrusted input. | Integer and `None` input escaped as `AttributeError`; hand-written string handling also needed to account for Pydantic's normal UTF-8 decoding. | Removed the custom validator and delegated decoding, stripping and validation to Pydantic's string constraints. | Invalid input remains a normal `ValidationError`, and valid bytes follow the same normalization contract. |
| 3 | The existing test expected surrounding whitespace to be retained; no H1 regression cases existed. | The new behavior could conflict with the old expectation or silently affect other fields. | Updated that expectation and added 15 cases covering blank/Unicode text, normalized boundaries, wrong types, bytes, JSON round trips and field isolation. | The tests detect the new feature and preserve unrelated contracts rather than merely checking a happy path. |

The final implementation is deliberately small:

```python
from typing import Annotated
from pydantic import BaseModel, StringConstraints

class Message(BaseModel):
    text: Annotated[
        str,
        StringConstraints(strip_whitespace=True, min_length=1, max_length=2000),
    ]
    session_id: str = "local"
```

The repository file uses the same constraint in a single-line annotation.
No global model setting is used, so normalization is limited to `Message.text`.

## 5. Tests and checks

The normalization tests were run against the old model first: **10 failed,
26 passed** in `tests/test_models.py`, demonstrating that the new behavior was
not already present. After the implementation:

| Check | Actual local result |
| --- | --- |
| Full `python -m pytest -q` | **50 passed**: 36 model, 4 exception and 10 configuration cases |
| Increase over the earlier 35-case refactor | **15 additional cases**, plus one changed expectation |
| `python -m ruff check .` from `assistant_core_lab` | **Passed, 0 issues** |
| Ruff format check on the four models/errors Python files | **Passed** |
| Pyright 1.1.414 on those four files with the root config and `.venv` | **0 errors, 0 warnings** |

The feature adds no dependency: `Annotated` comes from the standard library and
`StringConstraints` comes from the already pinned Pydantic 2.9.2. It adds no
provider calls, credentials, logging or persistence. The shared
`Message -> Response` contract and exception hierarchy remain in place.

## 6. Scope and review status

- The message feature and automated checks are complete locally.
- Other team service/router/provider modules remain placeholders in this
  snapshot; no complete CLI/service or fallback verification is claimed.
- `docs/ai-use-log.md` contains a separate Hiển entry without changing another
  member's record.
- Codex prepared the implementation and technical review evidence. Hiển still
  needs to personally inspect the diff and confirm the three review decisions
  before presenting this as an individual manual review.
- The owner has authorized a local commit in English. Push and submission remain pending.
