# Before / After — Hùng (member 6, dmh612)

Ngày kiểm tra: 23/10/2026. Phạm vi: service, CLI và điều phối kiến trúc.
Tài liệu do Codex hỗ trợ soạn từ mã nguồn và kết quả chạy thực tế. Hùng cần đọc lại trước khi nộp.

## So sánh theo 10 câu hỏi worksheet

| Câu hỏi | Trước: monolith | Sau: package tích hợp |
|---|---|---|
| Đổi đơn giá tín chỉ ở đâu, mấy chỗ? | Một hằng `RATE` trong script; logic dùng trực tiếp global. | Một cấu hình `CREDIT_RATE_VND`, được load vào Settings rồi truyền cho tuition; không sửa service. |
| Test không internet/API key? | Không có suite pytest độc lập; hàm test chạy tay, provider có sleep và lỗi ngẫu nhiên. | 121 test pass offline với stub và fixture; không cần API key. Cài dependency lần đầu cần nguồn package. |
| Thiếu handbook.json? | Bare except chỉ in lỗi, vẫn chạy với dữ liệu trống. | KnowledgeError khi khởi tạo; CLI trả mã 1, thông báo stderr, không traceback. |
| Có in/log secret? | Có debug in API key và một phần prompt. | Service chỉ log thông báo cố định và metadata; test canary kiểm tra key/câu hỏi không xuất hiện. Session ID phải không nhạy cảm. |
| Thành viên mới tìm logic học phí? | Đọc nhánh fee trong handle dài 56 dòng. | Tìm tuition trong tools.py, _fee trong service.py; thời gian đọc chưa đo bằng người thật. |
| Số biến/hằng cấp module? | 9, gồm cả dữ liệu mutable history/offices/handbook. | 5 trên toàn bộ src/assistant_core; gồm hằng router/config/logging và logger; không có global history. |
| Số bare except? | 3. | 0. |
| Hàm dài nhất? | handle: 56 dòng. | main: 29 dòng. |
| Ruff? | 8 vấn đề khi lint riêng monolith bằng E,F,I,B,UP,BLE, line-length 120, isolated. | Ruff 0.6.9 check toàn package: 0 vấn đề theo cấu hình CI. Hai phép đo khác phạm vi, không xem là điểm chất lượng tuyệt đối. |
| Đổi LLM có sửa service? | llm gắn trực tiếp trong handle. | Inject đối tượng theo Responder.explain; không đổi handle. Factory chỉ hỗ trợ stub, adapter thực cần được bổ sung rõ ràng. |

Phương pháp đo: AST đếm Assign/AnnAssign trực tiếp ở module, bao gồm hằng; độ dài hàm tính từ def đến end_lineno, gồm khoảng trắng/comment. Không tính tests vào số đo after.

## Ba câu kết luận

Cải thiện lớn nhất là service có đầu vào/đầu ra có kiểu, nối các module riêng và giữ nguồn khi provider lỗi.
Điều phức tạp hơn là phải đồng bộ hợp đồng giữa các thành viên, ví dụ KnowledgeBase khác API của prototype cũ.
Bước tiếp theo nên thống nhất domain exception và validation cấu hình với người phụ trách, rồi xác nhận GitHub CI trên commit được push.
