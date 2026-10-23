# Kiến trúc Assistant Core — bản tích hợp member 6

## Trách nhiệm module

| Module | Trách nhiệm |
|---|---|
| config | Settings, đọc environment/.env; không để service đọc biến môi trường trực tiếp. |
| models / errors | Message, Response, Source, Intent; domain exceptions dùng chung. |
| knowledge | Office, Rule, KnowledgeBase, load_knowledge; exception thực tế là KnowledgeError. |
| router / tools | Nhận diện intent; parse tín chỉ và tính học phí deterministic. |
| responder | Protocol Responder.explain, StubLLMResponder và TemplateResponder. |
| logging_setup | JSON logs, whitelist metadata, mặc định stderr, không nhân handler. |
| service | Nối các dependency, điều phối và fallback; không tự đọc CLI. |
| __main__ | Parse argument, validate message, startup, output văn bản hoặc --json và exit code. |

Luồng phụ thuộc: CLI → service → router/knowledge/tools/responder; các model dùng chung không import service.
Import module không tự load file hay khởi tạo provider.

## Service contract

```python
AssistantService(settings: Settings, knowledge: KnowledgeBase, responder: Responder)
AssistantService.handle(msg: Message) -> Response
create_service(settings: Settings) -> AssistantService
```

- Message.text được chuẩn hóa khoảng trắng biên và giới hạn 1–2000 ký tự bởi models.
- Factory gọi load_knowledge một lần lúc startup. Chỉ llm_provider=stub được hỗ trợ; các tên khác báo ConfigError.
- Routing: greeting → fee → office → rule. Service truyền tên office dạng casefold theo yêu cầu router.
- Fee dùng cấu hình, không gọi LLM. InvalidRequest trở thành trả lời hướng dẫn, intent fee.
- Rule có source id/title. ProviderError dùng TemplateResponder, giữ source và đặt degraded=True.
- Không tìm thấy dữ liệu phù hợp trả intent unknown, sources rỗng, degraded=False, không gọi provider.
- KnowledgeError chưa kế thừa AssistantError trong module của nhóm; CLI bắt đúng exception thực tế thay vì giả định DataError.
- Unexpected exception không bị catch rộng.

## CLI

Chạy từ assistant_core_lab sau khi cài requirements.txt và `pip install -e .`:

```console
python -m assistant_core "hi"
python -m assistant_core "where is the library"
python -m assistant_core "tuition for 18 credits and 2 retake"
python -m assistant_core --json "thesis registration credits"
```

stdout: answer và sources hoặc một Response JSON. stderr: log và lỗi startup/validation.
Exit 0 cho request đã xử lý (kể cả unknown hoặc tín chỉ không hợp lệ), 1 cho lỗi cấu hình/dữ liệu startup, 2 cho argument/message sai.
ASSISTANT_DATA_DIR mặc định data, tương đối với thư mục đang chạy; dùng đường dẫn tuyệt đối khi chạy từ nơi khác.
Không có interactive REPL. History/stats/save của monolith không được triển khai trong phạm vi service này.

## Quyết định và giới hạn

1. Dependency injection giúp thay responder/test fallback không cần mạng.
2. Học phí đi qua tools.tuition của member 4; member 6 không đổi thuật toán hay tự thêm Decimal. Công thức mặc định 18*450000 + 2*450000*1.5 = 9450000 VND.
3. Fail fast khi file CSV/JSON thiếu hoặc hỏng; không dựng service với knowledge tải dở.
4. Log message cố định với intent, latency_ms, session, degraded; không log provider exception hoặc câu hỏi. session_id phải là mã không nhạy cảm do caller cấp.
5. --json serialize model Response thay vì tạo schema thứ hai; default text giữ tương thích.
6. Settings hiện tại chủ yếu kiểm tra kiểu; chưa đảm bảo mọi giới hạn số dương hoặc multiplier hữu hạn. Không ghi nhận các validation chưa tồn tại là đã có.
7. Không sửa workflow để bỏ lint/test. Bản sửa thích nghi API knowledge thực của nhóm và giữ các module đồng đội.

## Kiểm chứng 23/10/2026

Python 3.12.14, pytest 8.3.3, Ruff 0.6.9, Pydantic 2.9.2. Full suite 121 passed; Ruff toàn package pass. Đây là kết quả Windows local, không thay thế một GitHub Actions run trên commit mới.
