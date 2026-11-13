# TEAM 3 — LAB 06 RAG INTEGRATION CONTRACT v1.0

**Project:** CSC10014 — Smart Virtual Assistant  
**Repository:** https://github.com/chp0703/assistant-core-team3  
**Project chính:** `assistant_core_lab/`  
**Phạm vi thầy giao:** Part C, D, E, F và H1  
**Kiến trúc:** Một Assistant Core thống nhất từ Lab 03 đến Lab 06  
**Trạng thái:** Đã chốt cho Team 3; Giai đoạn 0 (`chore/lab06-contract-foundation`) đã hoàn tất contract types & configuration.

## 1. QUYẾT ĐỊNH CHUNG

Team 3 thống nhất:

1. Giữ `assistant_core_lab/` làm project chính.
2. Giữ `create_service(settings)` là hàm khởi tạo duy nhất cho CLI và FastAPI.
3. Không copy đè `service.py`, `models.py`, `router.py` hoặc toàn bộ starter Lab 06.
4. Giữ nguyên hoạt động của Fee Calculator, Offices, Weather, Chat API, Feedback, SQLite và Rate Limiting.
5. RAG chỉ là một module mới được gắn vào `AssistantService`.
6. Giữ nguyên public `Response` và HTTP `ChatResponse` của Lab 03–05 trong giai đoạn tích hợp.
7. Dùng `RagResult` nội bộ để lưu thông tin RAG như `path`, `escalate`, `confidence`.
8. Mặc định sử dụng `StubLLM` offline, không bắt buộc API key.
9. Không xóa `public_materials/` trong Lab 06; thư mục này là nguồn tham chiếu của thầy.
10. Các thay đổi phải đi qua branch → PR → review → CI → merge.

## 2. CONTRACT #1 — KNOWLEDGE RETRIEVAL

**Owner:** Nguyễn Trần Minh Khang (`@kentlatoi`)

**Files:**

- `assistant_core_lab/src/assistant_core/rag/chunker.py`
- `assistant_core_lab/src/assistant_core/rag/index.py`
- `assistant_core_lab/data/kb/`

Định nghĩa giao tiếp:

```python
@dataclass(frozen=True)
class Chunk:
    id: str
    doc_id: str
    title: str
    text: str
    version: str
    owner: str


@dataclass(frozen=True)
class Hit:
    chunk: Chunk
    score: float


class Index(Protocol):
    def search(
        self,
        query: str,
        k: int = 3,
    ) -> list[Hit]: ...
```

**Quy tắc:**

- `chunker.py` đọc Markdown và metadata của tài liệu.
- ID nguồn phải ổn định, ví dụ `H26#5.3`.
- `index.py` triển khai BM25 theo starter của thầy.
- Kết quả được sắp xếp theo điểm liên quan giảm dần.
- Không tìm thấy tài liệu phù hợp thì trả `[]`.
- Không gọi LLM trong module tìm kiếm.
- Part C có thể hoàn thành và kiểm thử độc lập trước khi tích hợp service.

**Branch:** `feat/lab06-rag-knowledge-kent`

## 3. CONTRACT #2 — LLM + GROUNDING

**Owner:** Huỳnh Nguyễn Thế Hiển (`@AIVIETNAM-AIO-TheHien`)

**Files:**

- `assistant_core_lab/src/assistant_core/llm.py`
- `assistant_core_lab/src/assistant_core/prompts/answer_v1.txt`

Interface:

```python
class LLM(Protocol):
    name: str

    def complete(self, prompt: str) -> str: ...
```

Structured output:

```python
class AnswerDraft(BaseModel):
    answer: str
    source_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)
    abstain: bool = False
```

**A2 — Grounding rule:**

Nếu model không abstain thì:

- Phải có ít nhất một `source_id`.
- Mọi `source_id` phải thuộc `allowed_ids`, tức những chunk thật sự đã truy xuất.
- Nếu không hợp lệ, raise `ProviderError`.
- Không hiển thị câu trả lời có nguồn giả.

```python
if not draft.abstain and (
    not draft.source_ids
    or not set(draft.source_ids) <= allowed_ids
):
    raise ProviderError(
        "answer cites sources that were not retrieved"
    )
```

`parse_draft(raw, allowed_ids)` phải kiểm tra JSON, Pydantic schema và grounding.

**Branch:** `feat/lab06-grounding-a2`

## 4. CONTRACT #3 — RAG RESULT

**Owner:** Châu Hòa Phát (`@chp0703`)

Tạo file chia sẻ:

`assistant_core_lab/src/assistant_core/rag/types.py`

Thống nhất kiểu kết quả nội bộ như sau:

```python
from dataclasses import dataclass
from typing import Literal

from assistant_core.models import Intent, Source

RagPath = Literal[
    "retrieval",
    "llm",
    "abstain",
    "tool",
]


@dataclass(frozen=True)
class RagResult:
    answer: str
    intent: Intent
    sources: tuple[Source, ...] = ()
    path: RagPath = "retrieval"
    degraded: bool = False
    escalate: bool = False
    confidence: float | None = None
```

Đây là **contract do nhóm quyết định cho bản tích hợp**, không phải class đã có trong starter.

**Ý nghĩa:**

- `answer`: nội dung trả lời.
- `intent`: `RULE`, `UNKNOWN` hoặc `FEE` nếu có tool calling.
- `sources`: những nguồn đã được kiểm chứng.
- `path`: phương pháp thực sự tạo kết quả.
- `degraded`: có sử dụng fallback vì provider không hoạt động hoặc trả kết quả không hợp lệ.
- `escalate`: có cần hướng người dùng đến nhân viên hỗ trợ không.
- `confidence`: giá trị do model trả về; không coi là xác suất câu trả lời đúng.

Các thành viên phải dùng chung kiểu này, không tự tạo `RagResult` khác trong module riêng.

## 5. CONTRACT #4 — RAG ANSWERER + ABSTAIN

**Owner:** Đặng Minh Hùng (`@dmh612`)

**Files:**

- `assistant_core_lab/src/assistant_core/rag/answerer.py`
- `assistant_core_lab/src/assistant_core/guard.py`

Interface chính:

```python
class RagAnswerer:
    def answer(self, question: str) -> RagResult:
        ...
```

Thống nhất quy trình:

**Bước 1 — Retrieval**

Gọi `index.search(question, k)`.

**Bước 2 — A1 Abstain**

Nếu không có kết quả hoặc điểm cao nhất thấp hơn `min_score`:

- Trả `RagResult` với `intent=Intent.UNKNOWN`.
- `path="abstain"`.
- `escalate=True`.
- `confidence=0.0`.
- Không gọi LLM.
- Không bịa nguồn tài liệu.

**Bước 3 — Retrieval-only**

Nếu không cấu hình model, trả lời bằng đoạn tài liệu phù hợp nhất với `path="retrieval"`.

**Bước 4 — LLM**

Nếu có model:

- Xây dựng prompt từ các chunks tìm được.
- Gọi `LLM.complete()`.
- Gọi `parse_draft()` để kiểm tra JSON và citation.
- Trả `path="llm"` nếu kết quả hợp lệ.
- Nếu model abstain, trả `path="abstain"` và không cung cấp trích dẫn giả.

**Bước 5 — Fallback**

Nếu LLM lỗi hoặc xuất dữ liệu không hợp lệ:

- Thử lại một lần theo starter của thầy.
- Nếu vẫn lỗi, trả nguyên thông tin từ nguồn đã tìm được.
- `path="retrieval"`, `degraded=True`.

**Privacy guard:**

- Chặn các yêu cầu truy cập thông tin riêng tư của sinh viên khác.
- Privacy guard chạy trước retrieval và LLM.
- Không gửi dữ liệu riêng tư bị chặn vào prompt.
- Không ghi raw question hoặc session ID vào log.

Giữ khả năng sử dụng `tool_runner` theo starter nếu port bộ test tool-calling của thầy. Không cho model tự quyết định thực thi tool mà không qua kiểm tra tham số.

**Branch:** `feat/lab06-abstain-a1`

## 6. CONTRACT #5 — ASSISTANT SERVICE INTEGRATION

**Owner:** Châu Hòa Phát (`@chp0703`)

**Files:**

- `assistant_core_lab/src/assistant_core/service.py`
- `assistant_core_lab/src/assistant_core/config.py`
- `assistant_core_lab/src/assistant_core/rag/types.py`

Thống nhất:

```python
create_service(settings: Settings) -> AssistantService
```

Không đổi tên hàm này thành `build_service()`.

`AssistantService` được phép nhận thêm dependency:

```python
rag: RagAnswerer | None = None
```

Khi `rag is None`, giữ nguyên cách xử lý của Lab 03–05.

Khi RAG được bật:

- Greeting, Fee và Office vẫn xử lý bằng rules/tools cũ.
- Kiểm tra privacy trước các thao tác có nguy cơ truy xuất nội dung riêng tư.
- Câu hỏi về quy định chuyển qua `RagAnswerer.answer()`.
- Chuyển `RagResult` thành public `Response` hiện tại.

Không thêm các field `path`, `escalate`, `confidence` vào public `Response` trong giai đoạn này vì tests Lab 03 đang kiểm tra JSON contract cũ.

Evaluation được phép quan sát metadata từ `RagResult` nội bộ, không bắt buộc thay đổi HTTP API.

### Configuration

Phát bổ sung các tham số:

- `RAG_ENABLED` — mặc định `false` cho đến khi tích hợp và regression hoàn tất.
- `KB_DIR` — mặc định `data/kb`.
- `RETRIEVAL_KIND` — mặc định `bm25`.
- `RETRIEVAL_MIN_SCORE` — mặc định `2.0`, áp dụng cho BM25.
- `LLM_PROVIDER` — mặc định `stub`.
- `LLM_MODEL` — model được cấu hình nếu sử dụng Ollama.
- `LLM_BASE_URL`.
- `LLM_TIMEOUT_S`.
- `PROMPT_VERSION` — mặc định `answer_v1`.

Chỉ bật RAG trong demo và evaluation khi các module đã tích hợp đầy đủ. Khi bật RAG, phải kiểm tra cả CLI lẫn FastAPI sử dụng cùng cấu hình.

Không sử dụng mặc định của mô hình khác để tính điểm BM25 mà chưa hiệu chỉnh threshold.

**Branch foundation:** `chore/lab06-contract-foundation`  
**Branch integration:** `feat/lab06-unify-service`

## 7. CONTRACT #6 — EVALUATION PART F

**Owner:** Phạm Hùng Khôi (`@phkhoiit-1508`)

**Files:**

- `assistant_core_lab/eval/compare_paths.py`
- `assistant_core_lab/docs/lab6/path_comparison.md`
- Các integration tests Lab 06 được nhóm thống nhất.

Đánh giá đúng ba chế độ:

| Path | Quy tắc |
|---|---|
| Deterministic | Fee và Office dùng rules/tools; không dùng tìm kiếm RAG cho câu hỏi quy định |
| Retrieval | Sử dụng BM25; trích dẫn nguồn; không gọi LLM |
| LLM | Sử dụng cùng BM25 và StubLLM; structured output, grounding, fallback |

Mỗi phương pháp phải chạy trên cùng bộ câu hỏi.

Đo:

- Correct / total.
- Correct abstentions.
- Median latency (p50).
- Maximum latency.
- Danh sách các câu thất bại.

Không dùng số liệu mẫu trong PDF làm số liệu chạy thật.

Báo cáo phải có bảng comparison, ba câu nhận xét và phân tích lỗi.

**Branch:** `feat/lab06-path-evaluation`

## 8. CONTRACT #7 — HOMEWORK H1

**Owner:** Nguyễn Ngọc Thanh Hương (`@thanhhuong107`)

**File:** `assistant_core_lab/eval/cases.jsonl`

Thống nhất:

- Sao chép 20 test cases gốc từ starter.
- Bổ sung đúng 5 test cases H1.
- Trong năm câu mới: 3 normal có `expect_source`, 2 abstain có `expect_abstain=true`.
- Tổng theo PDF: **25 câu**.
- Giữ định dạng JSONL: mỗi dòng là một JSON object hợp lệ.
- Kiểm tra source ID tồn tại trong `data/kb/`.
- Không điều chỉnh nhãn kỳ vọng chỉ để làm kết quả có vẻ tốt.

README hiện có kế hoạch 25+5, nhưng yêu cầu H1 trong PDF là 20+5; nhóm sử dụng 25 câu chính thức, còn bộ câu mở rộng nếu có phải ghi riêng.

Sau khi H1 merge, Khôi chạy comparison trên 25 câu và cập nhật báo cáo thực tế.

**Branch:** `feat/lab06-h1-cases`

## 9. FILE OWNERSHIP — KHÔNG SỬA ĐÈ NHAU

| Thành viên | File chính được sở hữu |
|---|---|
| Phát | `service.py`, `config.py`, `rag/types.py`, tài liệu tích hợp |
| Hiển | `llm.py`, `prompts/answer_v1.txt` |
| Khôi | `eval/compare_paths.py`, `docs/lab6/path_comparison.md` |
| Khang | `rag/chunker.py`, `rag/index.py`, `data/kb/` |
| Hương | `eval/cases.jsonl` |
| Hùng | `rag/answerer.py`, `guard.py` |

Có thể bổ sung file test riêng theo từng module. Không sửa file khác người phụ trách nếu chưa thống nhất.

Tất cả file nằm trong `assistant_core_lab/` trừ tài liệu tham khảo tại `public_materials/`.

## 10. MERGE ORDER

Thứ tự đề xuất:

1. Phát — Contract foundation (`rag/types.py`, config, interface).
2. Khang — Part C Retrieval.
3. Hiển — Part D A2.
4. Hùng — Part E A1.
5. Phát — Service integration, CLI/API.
6. Hương — H1 evaluation cases.
7. Khôi — Part F evaluation/report.
8. Phát — Final review, full regression, release.

Hương có thể chuẩn bị H1 song song; Hiển và Hùng cũng có thể triển khai song song sau khi contract được chốt.

Từng người tạo branch mới từ `main` đã cập nhật và PR về `main`.

## 11. TESTING & ACCEPTANCE

**Part C**

- Chunks có ID và metadata.
- Truy vấn về khóa luận tìm đúng `H26#5.3`.
- BM25 trả về kết quả theo thứ tự phù hợp.

**Part D**

- Valid JSON được chấp nhận.
- Invalid JSON bị từ chối.
- Không có citation hoặc citation giả khi model không abstain phải bị từ chối.
- Provider lỗi thì không làm sập assistant.

**Part E**

- Không có hits → abstain.
- Best score dưới threshold → abstain.
- Không gọi LLM khi đã quyết định abstain.
- LLM lỗi → fallback retrieval.
- Privacy guard chặn yêu cầu nhạy cảm.

**Part F**

- Evaluation chạy được trên cùng bộ cases.
- Có số liệu thực, bảng kết quả và ba câu nhận xét.

**H1**

- Đủ 20+5 câu.
- 5 câu mới có expected outputs hợp lệ.
- Evaluation được chạy lại trên 25 câu.

**Full regression**

- Tests Lab 03 pass.
- Tests Lab 04 pass.
- Tests Lab 05 pass.
- Tests Lab 06 pass.
- Ruff pass.
- FastAPI vẫn lưu interaction và feedback.
- Fee vẫn được tính bằng code.
- CLI và HTTP dùng cùng `AssistantService`.

Chạy tại `assistant_core_lab/`:

```bash
python -m pytest -q
python -m ruff check .
python -m pytest -q tests/test_rag.py
python eval/compare_paths.py
```

Chỉ xác nhận PASS khi lệnh thực sự đã chạy thành công.

## 12. YÊU CẦU NỘP BÀI CỦA THẦY

Theo Lab 06 PDF trang 18, mỗi thành viên cần PR có A1–A2 và comparison table. Việc phân công owner ở trên là để tránh xung đột khi tích hợp **một codebase chung**, không tự động thay thế yêu cầu PR cá nhân.

Để bảo đảm bằng chứng, từng thành viên nên lưu kết quả kiểm thử A1–A2 và bảng comparison của mình trong:

`assistant_core_lab/docs/lab6/members/<github-username>/path_comparison.md`

Mỗi thành viên cần có PR cá nhân. Phát phải xác nhận với thầy liệu PR chứa bằng chứng kiểm thử trên implementation chung có được chấp nhận, hay thầy yêu cầu từng người tự triển khai A1–A2 trong branch của mình.

Team Lead sẽ merge bản triển khai thống nhất, giữ các deterministic/retrieval paths và tạo tag `v0.6-ai` theo thời hạn của giảng viên.

**Không tự nhận đã hoàn thành toàn bộ Lab 06 chỉ vì scaffold hoặc CI Lab 03–05 đã pass.**

## 13. DEFINITION OF DONE

Lab 06 hoàn thành khi:

- [ ] Part C chạy được từ package chính.
- [ ] A2 grounding pass tests.
- [ ] A1 abstain pass tests.
- [ ] RAG được tích hợp vào `AssistantService` chính.
- [ ] Fee, Offices, Weather, Feedback và SQLite vẫn hoạt động.
- [ ] Part F có kết quả comparison thật.
- [ ] H1 có đủ 5 câu mới và kết quả chạy lại.
- [ ] Full pytest + Ruff pass.
- [ ] PRs được review và merge đúng quy trình.
- [ ] Có bằng chứng PR cá nhân theo yêu cầu thầy.
- [ ] Tag `v0.6-ai` được tạo sau final merge.

**FINAL DECISION: ONE REPOSITORY — ONE ASSISTANT CORE — ONE SERVICE — ONE INTEGRATED RELEASE.**

---

## FIRST ACTION FOR TEAM LEAD

Phát nên làm **PR Contract Foundation** trước, chỉ bổ sung `rag/types.py` và các cấu hình cần thiết, chưa thay toàn bộ logic `service.py`. Sau khi PR này merge, Khang, Hiển và Hùng có thể dùng chung interface để phát triển song song.

Điều này giúp nhóm tránh ba lỗi lớn: mỗi người tự định nghĩa kết quả RAG khác nhau, phá public `Response` của Lab 03–05, hoặc tạo một Assistant Core độc lập.
