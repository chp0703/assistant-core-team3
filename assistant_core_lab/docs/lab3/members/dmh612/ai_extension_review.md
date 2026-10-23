# H1 — AI Extension Review — Hùng (member 6, dmh612)

## Một tính năng mở rộng: CLI --json

Mục tiêu: cho phép dùng kết quả trợ lý trong chương trình khác, giữ nguyên chế độ trả lời văn bản mặc định.
Thực hiện ngày 23/10/2026 bằng OpenAI Codex. Không thêm dependency.

## Prompt và nguồn gốc

Yêu cầu gốc của Hùng: kiểm tra lỗi CI, chạy test, tạo tài liệu member 6 theo ảnh hướng dẫn.
Để hoàn thành H1, Codex chọn tính năng --json trong phạm vi CLI. Đây là chỉ dẫn triển khai được Codex diễn giải từ yêu cầu, không phải trích nguyên văn một prompt riêng Hùng đã gửi:

> Thêm cờ --json cho python -m assistant_core. Xuất đúng Response gồm answer, intent, sources, degraded. Giữ output văn bản mặc định; log và lỗi ở stderr; không xuất Settings, secret hoặc câu hỏi. Thêm test subprocess cho schema, nguồn, đầu vào lỗi, Unicode và bảo mật.

## Review kỹ thuật và ít nhất ba tinh chỉnh

Bảng này ghi nhận các quyết định triển khai/review của Codex ở lần làm hiện tại; không khẳng định Hùng đã tự review hoặc từng thực hiện chúng trước đây.

| # | Cách làm ban đầu / điểm cần review | Vấn đề | Điều chỉnh đã thực hiện | Lý do |
|---|---|---|---|---|
| 1 | CLI cũ chỉ in answer rồi source riêng. | Không thể parse thành một JSON document. | Dùng Response.model_dump_json() và return ngay trong nhánh --json. | Tái sử dụng schema chuẩn, không trộn source văn bản vào JSON. |
| 2 | Xuất toàn object/cấu hình sẽ dễ hơn việc xác định contract. | Có nguy cơ lộ API key hoặc dữ liệu không thuộc Response. | Chỉ serialize Response; test exact keys và secret/question canary. | Giới hạn dữ liệu xuất, giữ contract hiện có. |
| 3 | Chỉ test JSON với greeting là chưa đủ. | Không kiểm tra nguồn handbook, lỗi input hoặc tiếng Việt. | Thêm 7 trường hợp H1: 4 intent, invalid input, canary, Vietnamese. | Bảo vệ tính năng ở subprocess thực, bao gồm streams và exit code. |
| 4 | Test cũ trông chờ log propagate qua caplog; CLI chưa xử lý KnowledgeError và LOG_LEVEL không hợp lệ. | Logger của nhóm tắt propagation; lỗi startup có thể tạo traceback. | Capture stream JSON thật, bắt KnowledgeError và đổi riêng ValueError của setup_logging thành ConfigError. | Test đúng contract logging, xử lý lỗi có chủ đích, không nuốt lỗi lập trình rộng. |

## Kiểm tra và giới hạn

- Interface service vẫn là handle(Message) -> Response; thay đổi H1 nằm ở adapter CLI.
- Không có network/provider thực, không thêm dependency hay lưu lịch sử người dùng.
- Đã kiểm tra: full pytest **121 passed**, Ruff toàn package pass, format bốn file member 6 pass.
- `--json` giữ source và degraded nhờ serialize model; fallback được test tại service.
- Đây là review kỹ thuật do AI hỗ trợ. Hùng cần mở diff, chạy thử và xác nhận nhận xét trước khi nộp dưới tên mình.
- Tính năng --json được bổ sung trong lần hỗ trợ này, không được ghi nhận là công việc đã làm trước đó.

Ví dụ từ assistant_core_lab sau cài đặt:

```console
python -m assistant_core --json "tuition for 18 credits and 2 retake"
```

Kết quả stdout có answer "Your tuition is 9,450,000 VND.", intent "fee", sources [] và degraded false. Log JSON ở stderr.
