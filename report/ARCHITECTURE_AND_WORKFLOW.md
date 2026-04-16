# Defense-in-Depth Pipeline Architecture & Workflow

Tài liệu này giải thích chi tiết cấu trúc, cách triển khai và cơ chế hoạt động của hệ thống Phòng thủ AI Đa Lớp (Defense-in-Depth Pipeline) áp dụng cho trợ lý AI ngành ngân hàng.

## 1. Tổng quan Kiến trúc (Architecture)

Hệ thống được thiết kế theo "Mô hình Phễu Lọc" (Pipeline Pattern) bằng **Python Bất đồng bộ (Asyncio)**. Dữ liệu từ người dùng sẽ đi qua 7 lớp bảo mật độc lập trước và sau khi chạm đến LLM Agent. Kiến trúc này triệt tiêu hoàn toàn Single Point of Failure (Điểm lỗi duy nhất).

Cấu trúc thư mục (Tối giản, chuyên dụng):
```
Day-11-Guardrails/
├── src/
│   ├── core/
│   │   ├── audit.py        (Lớp Audit Log & Monitor Board tự động)
│   │   └── config.py       (System Config, PII Regex Patterns, Whitelists)
│   ├── layers/
│   │   ├── anomaly_detector.py (Option)
│   │   ├── cost_guard.py   (Lớp quản lý chi phí & Token)
│   │   ├── input_guardrails.py (Lớp tiền xử lý: Length, Stealth chars, Regex)
│   │   ├── output_guardrails.py (Lớp hậu xử lý: PII Filter & LLM Judge)
│   │   ├── rate_limiter.py (Chống DoS/Spam)
│   │   └── toxicity_classifier.py (Phân loại độc hại bằng OpenAI Moderation)
│   ├── agent/
│   │   └── chatbot.py      (Mô hình gpt-4o-mini với Vulnerable System Prompt)
│   ├── pipeline.py         (Orchestrator định tuyến bất đồng bộ 7 layers)
│   └── main.py             (Test Suite Evaluator)
└── security_audit.json     (Bằng chứng hệ thống xuất ra sau quá trình Test)
```

## 2. Quy trình Xử lý Dữ liệu (Data Workflow)

Mỗi Request (Của cả người dùng tốt và Red Team) được đưa vào `pipeline.process()` và phải trải qua quy trình khắc nghiệt sau:

### Phase 1: Pre-flight Defense (Trước khi LLM tạo phản hồi)
1.  **Rate Limiter**: Kiểm tra Window Sliding (10 requests/60s). Vượt ngưỡng ➔ **Trả về lỗi, Block**. Giúp chống lại DDoS cục bộ.
2.  **Cost Guard**: Kiểm tra tổng số `tokens_used` của tiến trình `user_id` hiện tại. Quá ngân sách 5,000 tokens ➔ **Chặn đứng** để bảo vệ ngân sách (Chống DoW - Denial of Wallet).
3.  **Input Guardrails (Fast)**:
    *   Giới hạn ký tự khắt khe (Max 500 chars) tránh tràn viền Token LLM.
    *   Tẩy xóa mã ẩn (Zero-width chars, `\u200b`).
    *   Tính tỉ lệ ký tự đặc biệt, phát hiện thẻ `<script>` chống XSS/Code Execution.
    *   Dò Regex để bẫy Prompt Injection, Jailbreak, tiếng lóng (Vietnamese Jailbreaks) và Block Off-topic (Không thuộc Whitelist Ngân hàng).
4.  **Toxicity Classifier**: Gọi độc lập lên OpenAI `v1/moderations` hoàn toàn miễn phí. Nếu chứa câu từ bạo lực, xúc phạm, gợi dục ➔ **Block**.

### Phase 2: Generation (Sinh văn bản)
5.  **Async LLM Agent**: Dữ liệu sống sót qua Phase 1 sẽ được bọc kèm `System Prompt` (Cố tình gài mật khẩu và ID thật) sau đó đưa lên OpenAI lấy phản hồi thông qua kiến trúc Bất đồng bộ (`async / await`) giúp Pipeline không bị tắc nghẽn. Trả về Response + `Usage Tokens`.

### Phase 3: Post-flight Defense (Sau khi LLM tạo phản hồi)
6.  **Output Guardrails (PII Filter)**: LLM có thể bị lừa tiết lộ mã `admin123`. Engine này rà soát phản hồi, ghi đè toàn bộ thông tin nhạy cảm thành `[REDACTED]`. Khách hàng chỉ thấy thẻ "*Mật khẩu là [REDACTED]*".
7.  **LLM-as-Judge Evaluator**: Lấy phản hồi đã sạch PII, gửi lại lần nữa lên OpenAI với Prompt yêu cầu rà soát theo 4 thông số `SAFETY`, `RELEVANCE`, `ACCURACY`, `TONE` (Từ 1-5). Nếu trung bình < 3.5 điểm hoặc Verdict trả về FAIL ➔ Ghi đè Response bằng dòng chữ "Yêu cầu bị từ chối do vi phạm tiêu chuẩn". Thu thập phí mảng Judge này nạp lại cho Cost Guard.

### Phase 4: Tracing & Auditing (Ghi vết rủi ro)
8.  **Audit Logger**: Bắt đầu tính giờ từ Phase 1, đến lúc này lưu toàn bộ `Latency`, `Tokens expended`, `Block Layer`, `Block Reason` vào `security_audit.json`. Cuối chu kỳ sẽ nổ Alert cảnh báo hệ thống nếu tỷ lệ Red Team tàn phá > 40%.

## 3. Lý do Kiến trúc này Mạnh Mẽ

1.  **Bất đồng bộ (Asyncio/Aiohttp)**: Toàn bộ quá trình gọi Judge và gọi Agent được làm trên tập lệnh Async/Await. 15 luồng rate-limit hoạt động trơn tru trong chưa tới 3 giây mà không làm sụp hệ thống.
2.  **Defense-in-Depth Chính Cống**: Các layer bổ trợ cho sự thất bại của nhau. Injection lọt qua Regex sẽ vướng Moderation. Moderation mù mờ sẽ bị LLM-Judge túm lổ ở ngõ ra. Sự rò rỉ bộ nhớ (Token) được kìm kẹp bởi Cost Guard từ hai chiều.
3.  **Tự động cập nhật ngân sách (Token Auto-budgeting)**: Hệ thống duy nhất tự đếm token của bot để ép budget của End-user, triệt phá tận gốc các hành vi phá hoại tài nguyên.
