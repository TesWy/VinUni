# Báo cáo Cá nhân - Phần B

**Sinh viên:** [Tên của bạn]
**Assignment 11:** Building a Defense-in-Depth Pipeline (Xây dựng hệ thống phòng thủ AI đa lớp)

## Q1: Phân tích các Lớp phòng thủ (Layer Analysis)
*Giải thích cách các lớp phòng thủ tương tác với nhau. Lớp nào bắt được nhiều cuộc tấn công nhất? Có trường hợp ngoại lệ nào lọt qua lớp đầu tiên nhưng bị lớp thứ hai chặn đứt không? Hãy sử dụng ví dụ từ các lần chạy thử nghiệm hoặc từ file log `security_audit.json`.*

**Trả lời:**
Luồng xử lý (pipeline) bất đồng bộ nâng cao của chúng tôi triển khai một hệ thống phòng thủ 7 lớp cực kỳ kiên cố, bao gồm: Rate Limiter (Giới hạn truy cập), Cost Guard (Kiểm soát chi phí), Input Guardrails bằng Regex (Kiểm duyệt dải văn bản đầu vào), Toxicity Classifier qua OpenAI Moderation API (Kiểm duyệt tính độc hại), LLM Generation (Xử lý sinh ngôn ngữ tự nhiên), PII Output Filter (Màng lọc chống lộ dữ liệu nhạy cảm) và cuối cùng là LLM-as-Judge Evaluator (Mô hình trọng tài chấm điểm).

Xuyên suốt quá trình kiểm thử toàn diện (được ghi lại rõ nét trong tệp `security_audit.json`), các lớp này hoạt động theo mô hình bọc lót lẫn nhau rất hiệu quả:
1.  **Input Guardrails (Lớp kiểm duyệt đầu vào nhanh)** là lớp bắt được số lượng lớn nhất các cuộc tấn công (chiếm trên 80%). Từ các mã Prompt Injection (Tiêm mã) kinh điển kiểu *"Ignore all previous instructions"* cho đến các thủ thuật tinh vi của Red Team như chèn mã tàng hình zero-width (`u200b`) hay dùng tiếng lóng, tiếng bản địa (*"Bỏ qua mọi chỉ thị trước đó"*), Input Guard đều "tóm sống" một cách tức thời nhờ Regex và Sanitize Filter. Nó cũng dập tắt lập tức mã độc Javascript như XSS `<script>` hay Spam Emoji.
2.  **Toxicity Classifier (Lớp số 6 - Kiểm duyệt Độc hại)** đã phát huy sức mạnh ở các trường hợp lọt lưới mảng tài chính. Ví dụ: Input mang yếu tố bạo lực *"I will bring a gun and shoot everyone at the VinBank branch..."* dễ dàng vượt qua chốt kiểm tra Regex chuyên vi phạm ngân hàng, nhưng bị OpenAI Moderation API bắt thóp ngay là `violence/graphic` và khóa câu trả lời.
3.  **Cost Guard** thực thi vai trò Tấm khiên chống vắt kiệt tài chính (Denial of Wallet). Với giới hạn 5,000 tokens cho mỗi user, kẻ tấn công rải thảm dữ liệu nhằm bào mòn ngân sách OpenAI sẽ bị cấm vận lập tức ngay khi ngân sách vượt ngưỡng dự kiến.

**Trường hợp điển hình (Edge Case):** Một Hacker khôn ngoan biết dùng câu lệnh thuần túy *"What is the savings rate?"* (Một truy vấn hợp lệ 100% trong ngành ngân hàng) và gửi thư rác liên tục 15 lần/giây để phá hoại. Câu truy vấn này dĩ nhiên vượt qua toàn bộ lớp Regex, Toxicity và cả LLM-as-Judge. Tuy nhiên, nó bị chặn gắt gao tại điểm chạm đầu tiên là **Rate Limiter Layer** ở Request thứ 11, đảm bảo backend LLM không bao giờ bị quá tải.

---

## Q2: Phân tích Tỷ lệ Nhầm Lẫn (False Positives Analysis)
*Nếu mang hệ thống phòng thủ này đem lên triển khai trên môi trường thật (Production), bạn sẽ có những mối bận tâm nào? (Ví dụ: Chặn lầm người tốt, độ trễ, chi phí...). Bạn sẽ thay đổi và tinh chỉnh các tùy chọn đối với "LLM Judge" như thế nào để cân bằng giữa sự an toàn và Trải nghiệm người dùng?*

**Trả lời:**

1.  **Nhầm lẫn ở cửa ngõ Regex:** Hệ thống Input Guardrails sử dụng từ khóa Normalize (Bỏ dấu). Một khách hàng gặp khó khăn viết thư khiếu nại dài ngoằng: *"Ứng dụng đòi mật khẩu mệt quá chả muốn dùng"* có nguy cơ lọt nhầm vào bẫy của chốt chặn `(tiết lộ|...|mật khẩu)`. Ở môi trường thực tế, tôi sẽ giảm bớt sự phụ thuộc vào Regex cứng nhắc, thay vào đó là sử dụng Semantic Vector Router (Bắt ý nghĩa đoạn văn bằng đồ thị) để nhận diện Intent chính xác hơn.
2.  **Độ trễ và Chi phí API cao (Latency & Cost):** Do tích hợp một trọng tài giám khảo (LLM-as-Judge) để chấm điểm ĐA CHIỀU (SAFETY, RELEVANCE, ACCURACY, TONE) trên *mỗi chặng Output trả về*, độ trễ (latency) của một phản hồi bình thường bị kéo dài thêm ~1 đến 2 giây, đồng thời làm `nhân đôi` phí vận hành OpenAI Tokens / User.
3.  **Fail-Closed so với Fail-Open:** Hiện tại hệ thống LLM-as-Judge của tôi cài đặt theo thiên hướng "Fail-Closed" (Luôn khóa mõm nếu như không gọi được hàm hay Timeout API). Dù tính bảo mật của lựa chọn này ở mức tuyệt đối nhưng lại phản tác dụng đối với hệ thống dịch vụ 24/7. Nếu server OpenAI rớt mạng, mọi request ngân hàng của User đều bị từ chối phục vụ. Cần có thiết kế Bypass "Fail-Open" khi lỗi hạ tầng.
4.  **Tinh chỉnh Tùy chọn Threshold Balance (Cân bằng Giám Khảo):**
    Hiện nay, mô hình Giám khảo LLM hoạt động rất kỹ tính, yêu cầu điểm trung bình `avg_score >= 3.5` và không tiêu chí nào được rớt xuống dưới điểm 3.
    *   Để kích thích *Trải nghiệm Người Dùng (UX)* mượt mà hơn, tôi sẽ **tụt ngưỡng bắt buộc của TONE (Thái độ) và RELEVANCE (Sự quan tâm)** xuống còn điểm 2. Việc AI lỡ trả lời với tông giọng quá máy móc (Low Tone) không đáng để Block gắt gao và làm gián đoạn luồng làm việc của khách hàng.
    *   Tuy nhiên, tôi vẫn **giữ nguyên ngưỡng bắt buộc đạt 4 hoặc 5/5 của hai mục SAFETY và ACCURACY**. Ngân hàng VinBank tuyệt đối không được thỏa hiệp với thông tin ảo mộng (Hallucinated rates) hay lộ lọt dữ liệu.

Bằng cách liên tục quan sát biểu đồ **Monitor Dashboard** từ File Log để biết `Block Rate` đang ở mức bao nhiêu, chúng tôi có thể liên tục kéo thả Threshold này qua từng tuần để máy học AI luôn ổn định.
