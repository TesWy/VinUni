HV: 2A202600084
Lab_5

# UX Exercise — Phân Tích Sản Phẩm AI Thực Chiến
**Bài tập:** Ngày 5 — VinUni A20 — AI Thực Chiến · 2026  
**Thời gian:** 40 phút | **Cá nhân**  
**Sản phẩm chọn:** Vietnam Airlines — Chatbot NEO  
**Kênh trải nghiệm:** vietnamairlines.com  
**Tình huống thử:** Tra cứu chuyến bay để đặt vé

---

## Phần 1 — Khám Phá

### 1.1 Marketing hứa gì?

| Điểm marketing | Nguồn |
|---|---|
| Hỗ trợ 24/7, phản hồi nhanh, chính xác, đa ngôn ngữ (10+ ngôn ngữ) | vietnamairlines.com, LinkedIn FPT AI |
| Tra cứu vé, chuyến bay, hành lý; **hỗ trợ đặt vé và thanh toán** | vietnamairlines.com/chatbot |
| Hiện diện đa kênh: Website, Zalo, App, Facebook | Spirit VNA blog |
| Powered by Generative AI (co-developed với FPT Software, 2026) | FPT AI LinkedIn |
| Đại diện thương hiệu chuyển đổi số "Vạn Dặm Nâng Niu" | Spirit VNA blog 12/2024 |

**Tóm lại:** Marketing định vị NEO là AI thông minh, đa năng, hiện đại — có thể đồng hành toàn bộ hành trình từ tra cứu → đặt vé → thanh toán.

---

### 1.2 Thực tế dùng thử

**Scenario:** Mở vietnamairlines.com → mở NEO chatbot → thử tra cứu chuyến bay để đặt vé.

#### Quan sát theo từng thao tác:

| Thao tác | Kết quả thực tế | Ghi chú |
|---|---|---|
| Hỏi tìm vé / đặt vé | ❌ Chưa hỗ trợ | Gap lớn so với marketing |
| Bug phát hiện | ❌ Duplicate câu trả lời (1 lần) | Lỗi hiển thị UI — render 2 lần |
| Tra mã vé | ❌ Không tra ra được | Không rõ lý do — thiếu thông báo lỗi rõ |
| Tra chuyến bay (cần số chính xác) | ✅ Hoạt động ổn | VN 6025 → ra kết quả |
| Hỏi thêm hành lý sau khi tra chuyến | ❌ Fail | Không giữ context từ câu trước |
| Hỏi tea break / dịch vụ trên máy bay | ❌ Fail | Ngoài scope hoặc không hiểu intent |
| NEO hỏi ngược: "Chuyến bay đó có tồn tại không?" | ⚠️ Weird behavior | Chatbot tự hỏi user về dữ liệu của chính nó |
| Tra VU787 | ❌ NEO nói không hợp lệ | Sai: thực tế chuyến này tồn tại |
| Tra VN 6025 | ✅ Ra kết quả | Đúng |
| Hỏi câu không liên quan | ✅ Từ chối phù hợp | Scope boundary được xử lý tốt |
| Yêu cầu gặp nhân viên | ✅ Hiện rõ, có SĐT đầy đủ | Nhưng spam vì xuất hiện quá nhiều lần |

---

## Phần 2 — Phân Tích 4 Paths

### Path 1 — Khi AI **đúng**

**Hoạt động được:**
- Tra cứu chuyến bay khi có **số chuyến chính xác** (VD: VN 6025)
- Trả lời thông tin hành lý cơ bản (câu hỏi độc lập, không sau hội thoại)
- Hướng dẫn thủ tục chung
- Chuyển hướng sang nhân viên tư vấn

**UI confirm thế nào:** Trả lời dạng text thuần, không có badge xác nhận, không có animation, không có cơ chế feedback "câu trả lời này có hữu ích không?".

**Nhận xét:** Path này ổn nhưng trải nghiệm khá thụ động — user không biết chắc mình có thể tin câu trả lời không.

---

### Path 2 — Khi AI **không chắc**

**Hành vi quan sát được:**
- Hỏi lại user để làm rõ
- Trả lời "không biết" / "không có thông tin"
- **Chưa** đưa ra phương án thay thế (alternative suggestions)
- Chưa gợi ý query cụ thể hơn để user retry

**Ví dụ thực tế:** Hỏi hành lý sau câu tra chuyến bay → NEO không giữ context → xử lý như câu hỏi mới → trả lời thất bại, không gợi ý "Bạn có thể hỏi: Hành lý ký gửi tối đa VN là bao nhiêu kg?"

**Nhận xét:** NEO dừng lại ở "không biết" mà không dẫn đường tiếp — đây là vùng cần cải thiện.

---

### Path 3 — Khi AI **sai**

**Trường hợp phát hiện:**
- **VU787** → NEO trả lời "không hợp lệ" nhưng thực tế chuyến bay tồn tại → **AI sai thông tin**
- Nhìn chung NEO **ít sai** vì scope trả lời bị hạn chế rất hẹp → từ chối nhiều hơn là trả lời sai

**User phát hiện bằng cách nào:** Tự kiểm tra bên ngoài (Google/website VNA) — không có cơ chế nào trong app giúp user cross-check.

**Sửa bằng cách nào:** Không có nút "Báo lỗi" hay "Thông tin này sai". User chỉ có thể thử lại câu khác hoặc thoát.

**Số bước để correct:** Không có flow sửa — dead end.

**Nhận xét:** NEO "không sai nhiều" nhưng đó là vì nó trả lời rất ít, không phải vì nó thông minh. Khi sai, không có cơ chế recovery nào cho user.

---

### Path 4 — Khi user **mất tin tưởng**

**Fallback có không:** ✅ Có — nút/link gặp nhân viên tư vấn, SĐT hiện đầy đủ.

**Dễ tìm không:** ✅ Rất dễ tìm — xuất hiện gần như sau mọi lần NEO không trả lời được.

**Điểm yếu của fallback:** Vì NEO thất bại quá nhiều → fallback xuất hiện **spam liên tục** → mất đi tính hữu ích, trở thành background noise. User bị "nhàm" với nó và có thể bỏ qua.

**Nhận xét:** Path 4 là path được xử lý tốt nhất về mặt kỹ thuật, nhưng lại bị kéo xuống bởi tần suất trigger quá cao.

---

### Tổng kết 4 Paths

| Path | Đánh giá | Lý do |
|---|---|---|
| 1 — AI đúng | ⭐⭐⭐ Trung bình | Đúng nhưng hẹp, thiếu confirm UX |
| 2 — AI không chắc | ⭐⭐ Yếu | Dừng ở "không biết", không dẫn đường |
| 3 — AI sai | ⭐⭐ Yếu-trung bình | Ít sai nhờ scope hẹp, nhưng khi sai thì không có recovery |
| 4 — Mất tin | ⭐⭐⭐⭐ Tốt nhất | Có fallback rõ ràng, dễ thấy — nhưng spam |

**Path tốt nhất:** Path 4 (mất tin → có người thật). Thiết kế rõ ràng, luôn hiện diện.

**Path yếu nhất: Path 2 (AI không chắc)**
> NEO không thông minh, không linh hoạt, không hiểu ý user. Đặc biệt: **quên context hoàn toàn giữa các câu** — câu trước câu sau là reset. Đây là vấn đề cốt lõi ảnh hưởng toàn bộ trải nghiệm hội thoại.

---

### Gap: Marketing vs. Thực Tế

| Marketing hứa | Thực tế | Gap |
|---|---|---|
| Đặt vé + thanh toán qua NEO | Chưa hỗ trợ | 🔴 Lớn |
| Generative AI thông minh | Scope cứng, stateless, không giữ context | 🔴 Lớn |
| Hỗ trợ chính xác 24/7 | VU787 sai, nhiều câu hỏi bị fail | 🟡 Trung bình |
| Đa ngôn ngữ, đa kênh | Không test hết, nhưng web hoạt động | 🟢 Không rõ |
| Fallback nhân viên | ✅ Hoạt động tốt | 🟢 Đúng |

**Nhận xét gap:** Khoảng cách lớn nhất nằm ở **conversation intelligence** — marketing định vị NEO như một AI thế hệ mới (GenAI), nhưng thực tế hành xử giống rule-based chatbot truyền thống: stateless, scope cứng, không suy luận ngữ cảnh.

---

## Phần 3 — Sketch "Làm Tốt Hơn"

**Path chọn để cải thiện:** Path 2 — Khi AI không chắc (yếu nhất)  
**Vấn đề cụ thể:** NEO quên context → câu hỏi follow-up fail hoàn toàn

---

### AS-IS (User Journey hiện tại)
[User] Tra chuyến VN 6025
↓
[NEO] Trả ra thông tin chuyến ✅
↓
[User] Hỏi thêm: "Hành lý ký gửi bao nhiêu kg?"
↓
[NEO] ❌ QUÊN context — xử lý như câu độc lập
↓
[NEO] Fail / trả lời chung chung / hỏi lại từ đầu
↓
[User] Confused — không biết phải làm gì
↓
[NEO] Show fallback "Gọi tổng đài" (lần thứ N)
↓
[User] Mất tin, thoát chatbot ❌

← Điểm gãy tại bước 3: mất context
← Điểm gãy tại bước 7: spam fallback

text

---

### TO-BE (User Journey đề xuất)
[User] Tra chuyến VN 6025
↓
[NEO] Trả ra thông tin chuyến ✅
+ Giữ context: {flight: VN6025, route: HAN-SGN, date: ...}
↓
[User] Hỏi thêm: "Hành lý ký gửi bao nhiêu kg?"
↓
[NEO] ✅ Hiểu "hành lý" = trong ngữ cảnh VN6025
→ "Với hạng vé Economy trên VN 6025,
hành lý ký gửi là 23kg (1 kiện). Với hạng vé Business hành lý ký gửi là ..."
↓
[User] Hỏi thêm: "Có suất ăn không?"
↓
[NEO] ✅ Vẫn giữ context → trả lời đúng
+ Gợi ý proactive: "Bạn có muốn tôi
hỗ trợ thêm về check-in hoặc đặt chỗ ngồi?"
↓
[User] Có thể tiếp tục → hoặc nhấn "Đặt vé" (CTA rõ)

+ Fallback chỉ xuất hiện khi user
chủ động hỏi "gặp nhân viên"
hoặc sau 2 lần fail liên tiếp

text

---

### Thêm / Bớt / Đổi

| | Nội dung |
|---|---|
| ➕ **Thêm** | Session context memory (giữ thông tin chuyến bay trong hội thoại) |
| ➕ **Thêm** | Proactive suggestions sau mỗi câu trả lời ("Bạn có muốn hỏi thêm về...?") | ➕ **Thêm** | Cơ chế streaming hoặc loading khi chatbot đang làm việc
| ➕ **Thêm** | Trigger fallback thông minh (chỉ sau N lần fail, không spam) |
| ➖ **Bớt** | Bớt số lần tự động hiển thị "Gọi tổng đài" |
| ➖ **Bớt** | Bớt độ dài và các tin nhắn vô nghĩa của chatbot
| 🔄 **Đổi** | Từ stateless chatbot → stateful conversation với flight context |
| 🔄 **Đổi** | Từ "không biết → im lặng" → "không biết → gợi ý câu hỏi khác" |

---

## Phần 4 — Trình Bày 30 Giây

> *"Tôi thử NEO của Vietnam Airlines với task tra chuyến bay để đặt vé. NEO tra được số chuyến chính xác, nhưng hỏi follow-up gì thêm — hành lý, suất ăn — là reset hoàn toàn. Chatbot quên context từng câu một. Tôi đề xuất thêm session memory: giữ thông tin chuyến trong hội thoại và gợi ý proactive, thay vì để user bị dead-end rồi spam tổng đài."*

---

*Bài tập UX — Ngày 5 — VinUni A20 — AI Thực Chiến · 2026*