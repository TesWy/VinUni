# Ngày 5 — Tài liệu tham khảo

**Chương trình:** VinUni A20 — AI Thực Chiến
**Chủ đề:** Thiết kế sản phẩm AI cho xác suất
**Mục đích:** Tra cứu trong và sau buổi học. Mỗi mục có link gốc, tóm tắt ngắn, và giải thích liên quan đến nội dung bài giảng.

---

## 1. Frameworks & models

### 1.1 Frameworks dạy trong buổi học

| Framework | Mô tả | Nguồn |
|-----------|--------|-------|
| AI = Probabilistic | AI output là xác suất kèm sai số, không phải kết quả chính xác. Dùng khi đặt kỳ vọng cho product: "thiết kế cho uncertainty." | Bài giảng Ngày 5 |
| Automation vs Augmentation | 2 cách deploy AI: làm thay user (automation) vs gợi ý để user quyết (augmentation). Chọn sai → cascade xuống mọi quyết định sau. | Bài giảng Ngày 5 |
| Agency Progression (V1→V3) | Bắt đầu augmentation, tăng dần automation: V1 routing → V2 copilot → V3 tự động. Mỗi version thu data để quyết định lên tiếp. | Bài giảng Ngày 5 |
| 3 trụ (Requirement · UX · Eval) | AI product thay đổi cả 3: requirement = threshold + failure modes, UX = thiết kế cho lúc sai, eval = đo phân bố chất lượng. | Bài giảng Ngày 5 |
| Failure Mode Library | Thay vì list features, list cách product có thể fail: Trigger / Hậu quả / Mitigation. | Bài giảng Ngày 5 |
| Precision vs Recall | PM chọn precision (ít sai nhầm) hay recall (ít bỏ sót) — phụ thuộc cost of error của product, không phải kỹ thuật. | Bài giảng Ngày 5 |
| 4 paths UX cho AI | 4 câu hỏi UX cho mỗi AI feature: khi đúng → value moment, khi low-confidence → escalate, khi sai → correction path, khi mất tin → explain + opt-out. | Bài giảng Ngày 5 |
| Graceful Failure + Trust | Thiết kế UX cho lúc AI sai: show confidence, explain why, cho user sửa, cho opt-out. | Bài giảng Ngày 5 |
| AI Product Canvas | Canvas 3 cột (Value / Trust / Feasibility) + Learning Signal row. Gộp requirement, UX, eval vào 1 artifact. | Bài giảng Ngày 5 |
| Feedback Loop | AI product = organism, không phải artifact. Loop 4 bước: Ingest → Digest → Output → Repeat. KPI = tốc độ loop. | Bài giảng Ngày 5 |
| Data Flywheel | Có user → thu data → AI tốt hơn → hút thêm user. AI capabilities commodity hoá → data riêng = lợi thế thật. | Bài giảng Ngày 5 |
| Qualitative > Quantitative | AI phương sai cao — "87% accuracy" che lấp chất lượng thật. Qualitative cho biết WHERE + WHY, quantitative chỉ HOW MUCH. | Bài giảng Ngày 5 |
| Cost-Capability-Speed | Mọi AI product chọn 1 ưu tiên, trade-off 2 còn lại. Copilot = speed, Harvey = capability, Grammarly = cost. | Bài giảng Ngày 5 |
| ROI 3 kịch bản | Best / Expected / Worst case + kill criteria. Kiểm tra "có đáng build không" trước khi code. | Bài giảng Ngày 5 |

### 1.2 Frameworks bên ngoài

**Reforge — AI Product Management course**
Khoá học chuyên sâu về AI product strategy, nguồn gốc nhiều framework trong bài giảng: "Four Critical AI Product Strategy Mistakes" (1.1), "Learning vs Computational Problems" (1.2), "AI Feature Map" (1.3), "Cost-Capability-Speed" (2.2). Nếu muốn hiểu sâu logic đằng sau bài giảng, đây là nguồn chính.
- [reforge.com](https://www.reforge.com/) (có paywall)

**Zwee Dao — AI Product Design series**
Bộ slides về automation vs augmentation, precision/recall, ML errors & graceful failure, explainability & trust. Nguồn cho nhiều framework UX — đặc biệt phần 4 paths và trust patterns.
- Nguồn nội bộ (slides series #2, #3, #5, #6)

Xem thêm: Tài liệu tham khảo Ngày 2 — Google PAIR Guidebook, Microsoft HAX Toolkit, NIST AI RMF.

---

## 2. Case studies

### Google AI Overview vs Perplexity — cùng tech, khác product strategy

Google "rắc AI fairy dust" lên search — trả lời sai, ăn keo dán pizza. Perplexity dùng cùng LLM nhưng build product khác — thành công. Bài học: "sprinkling AI" lên product có sẵn ≠ product strategy. Liên quan trực tiếp đến thesis bài giảng: vấn đề không phải AI yếu, mà cách build product sai.
- Nguồn: Reforge 1.1 "Four Critical AI Product Strategy Mistakes"

### Chegg — incumbent bị disrupt không phải vì tech yếu

EdTech mất 90% giá trị cổ phiếu sau ChatGPT. Chegg có data, có relationship với trường — nhưng không biến thành AI product advantage. Quizlet cùng bị disrupt nhưng pivot tốt hơn vì xây product mới xung quanh AI.
- Nguồn: Reforge 2.7

### GitHub Copilot — 30% accuracy vẫn 20 triệu user

Accuracy chỉ 30%, nhưng ghost text UX khiến cost of reject = 0 (nhấn Tab hoặc tiếp tục gõ). Minh hoạ: augmentation không cần accuracy cao nếu UX đúng. Speed-first ROI positioning ($19/user/month, scale nhanh).
- Xem thêm: Tài liệu tham khảo Ngày 2

### Harvey — legal AI, sai = mất vụ kiện

Invest accuracy trước, ship chậm. $500+/user/month nhưng client chấp nhận vì precision cao + value cao. Capability-first ROI positioning — ngược hoàn toàn với Copilot.
- Nguồn: Reforge 2.2

### Microsoft Tay — không có failure design, thành racist bot

Chatbot không có graceful failure hay content moderation → bị troll thành racist. Ví dụ kinh điển cho tầm quan trọng của path 3 (khi sai) và path 4 (khi mất tin) trong 4 paths UX.
- Nguồn: Bài giảng Ngày 5

### Descript — gắn AI quality vào pricing tier

Tier Basic accuracy thấp hơn, Pro tốt hơn. Minh hoạ: AI requirement khác traditional software — quality là spectrum, không phải binary.
- Nguồn: Reforge 1.3

### Microsoft Dragon — data flywheel cho y tế

AI ghi chép cho bác sĩ. Từ synthetic data (acceptance 30–60%) → 600K ca thực tế + chuyên gia đánh giá (75%) → continuous loop (83%). Bài học: dữ liệu thật + chuyên gia hiệu quả gấp nhiều lần synthetic.
- Nguồn: Lenny's Podcast — Asha Sharma interview

### Customer Support Agent V1→V3 — agency progression thực tế

V1 chỉ routing ticket → V2 gợi ý draft trả lời → V3 tự xử lý. Team nhảy thẳng V3 phải shutdown vì lỗi quá nhiều. Minh hoạ: bắt đầu augmentation, tăng dần automation khi có data.
- Nguồn: Lenny's Podcast — Reganti & Badam interview

Xem thêm: Tài liệu tham khảo Ngày 2 — Google Photos, Stripe AI, Gmail Smart Compose, Grammarly.

---

## 3. Sách & bài viết chuyên sâu

### AI product strategy

**Hamel Husain — "Your AI Product Needs Evals" (2024)**
Hướng dẫn thực tiễn cách viết eval cho AI products: bắt đầu từ 50–100 outputs → phân loại lỗi → viết eval từ error patterns. Được dạy trực tiếp trong bài giảng. Đọc nếu muốn biết cách bắt đầu viết eval.
- [hamel.dev/blog/posts/evals](https://hamel.dev/blog/posts/evals/)

### Expert interviews (Lenny's Podcast)

Các cuộc phỏng vấn dưới đây là nguồn gốc cho nhiều expert insights trong bài giảng. Nghe/đọc nếu muốn hiểu context đầy đủ hơn.

**Aparna Chennapragada (CPO Microsoft, ex-Google Lens)**
2 thời đại AI product: 2012–2020 interface quá tham vọng + AI chưa giỏi (Siri, Alexa), 2023+ AI cực giỏi + interface vẫn chỉ chat box. "Chatbot = modem quay số AOL." Học được: tại sao UX phải match với intelligence level.
- [lennysnewsletter.com/p/microsoft-cpo-on-ai](https://www.lennysnewsletter.com/p/microsoft-cpo-on-ai)

**Ash Reganti & Vikram Badam (50+ AI deployments, OpenAI/Google/Amazon)**
AI product có 3 lớp bất định: input, output, process — cả 3 đều uncertainty. Case customer support V1→V3 trong bài giảng lấy từ đây. Học được: tại sao AI product phải thiết kế khác từ gốc.
- [lennysnewsletter.com/p/what-openai-and-google-engineers-learned](https://www.lennysnewsletter.com/p/what-openai-and-google-engineers-learned)

**Kevin Weil (CPO OpenAI)**
60% accuracy = copilot, 95% = semi-auto, 99.5% = autopilot. "Model bạn dùng hôm nay là model tệ nhất bạn sẽ dùng trong đời." Eval sẽ trở thành core skill cho PM. Học được: accuracy quyết định UX pattern.
- [lennysnewsletter.com/p/kevin-weil-open-ai](https://www.lennysnewsletter.com/p/kevin-weil-open-ai)
- [lennysnewsletter.com/p/openais-cpo-on-evals](https://www.lennysnewsletter.com/p/openais-cpo-on-evals)

**Asha Sharma (CVP Microsoft AI Platform)**
Quản lý 80.000 công ty build AI. AI product = organism, không phải artifact. KPI mới = "metabolism" — tốc độ loop. Case Dragon (AI ghi chép bác sĩ). Học được: feedback loop là product, là IP.
- [lennysnewsletter.com/p/how-80000-companies-build-with-ai-asha-sharma](https://www.lennysnewsletter.com/p/how-80000-companies-build-with-ai-asha-sharma)

**Mike Krieger (CPO Anthropic, co-founder Instagram)**
Model Intelligence × Context × UI = Utility. Phép nhân — 1 cái = 0 thì tất cả = 0. "Overhang": AI làm được nhiều hơn user thực tế dùng. Học được: UX phải thu hẹp gap giữa capability và adoption.
- [lennysnewsletter.com/p/anthropics-cpo-heres-what-comes-next](https://www.lennysnewsletter.com/p/anthropics-cpo-heres-what-comes-next)

Xem thêm: Tài liệu tham khảo Ngày 2 — Chip Huyen, Sculley et al., a16z LLM architectures, Emmanuel Ameisen.

---

## 4. UX & design cho AI

**Google PAIR — People + AI Guidebook**
Bộ hướng dẫn thiết kế AI product từ Google, tổ chức theo câu hỏi thực tế (đặt kỳ vọng, xử lý lỗi, xây mental model). Đọc nếu muốn áp dụng 4 paths UX vào product thật — guidebook có ví dụ cụ thể cho từng pattern.
- [pair.withgoogle.com/guidebook](https://pair.withgoogle.com/guidebook/)

**Alexa Effect — vòng xoáy đi xuống**
Chất lượng kém → user ngừng dùng → mất data → AI càng kém. Amazon Alexa là ví dụ kinh điển. Ngăn bằng: launch scope nhỏ + augmentation thay vì automation. Liên quan trực tiếp đến phần feedback loop trong bài giảng.
- Nguồn: Bài giảng Ngày 5

Xem thêm: Tài liệu tham khảo Ngày 2 — Microsoft HAX Toolkit (18 nguyên tắc tương tác người-AI), NN/g Customer Journey Mapping.

---

## 5. Nguyên tắc cốt lõi (quick reference)

| # | Nguyên tắc | Giải thích ngắn | Nguồn |
|---|-----------|----------------|-------|
| 1 | "Vấn đề không phải AI yếu. Vấn đề là ta đang đối xử AI như phần mềm thường." | Thesis bài giảng: requirement, UX, eval đều phải khác | Bài giảng Ngày 5 |
| 2 | "Nếu sản phẩm dùng AI, bạn đang thiết kế cho uncertainty." | AI = xác suất → product phải handle sai số | Bài giảng Ngày 5 |
| 3 | "Cùng AI, khác cách deploy → kết quả hoàn toàn ngược." | Copilot (aug, 30%) vs Spam filter (auto, 99%+) | Bài giảng Ngày 5 |
| 4 | "0→80% = 1 tuần, 80→95% = 4x effort." | Demo khác product. 20% cuối quyết định có ai dùng | Reforge 1.1 |
| 5 | "Thay vì list features, list cách product có thể fail." | Failure mode library > feature list cho AI product | Reforge 2.5 |
| 6 | "Sai mà user KHÔNG BIẾT → precision. Sai mà user THẤY NGAY → recall ok." | Cách chọn metric phụ thuộc user visibility | Bài giảng Ngày 5 |
| 7 | "AI capabilities commodity hoá → data riêng + cách dùng riêng = lợi thế thật." | Model ai cũng dùng được, data riêng mới khác biệt | Reforge 1.6 |
| 8 | "Model bạn dùng hôm nay là model tệ nhất bạn sẽ dùng trong đời." | Đừng over-engineer cho limitations hiện tại | Kevin Weil, CPO OpenAI |
| 9 | "The loop IS the product, IS the IP." | Feedback loop không phải feature phụ, là core product | Asha Sharma, CVP Microsoft |
| 10 | "Intelligence × Context × UI = Utility. Phép nhân." | 1 cái = 0 thì tất cả = 0. UX quan trọng ngang model | Mike Krieger, CPO Anthropic |
| 11 | "Qualitative > Quantitative. 87% accuracy nhưng 13% sai ở đâu?" | Metric đơn giản che lấp vấn đề thật ở early stage | Bài giảng Ngày 5 |

---

## 6. Đọc thêm — nghiên cứu bổ sung

Các nguồn dưới đây không có trong bài giảng nhưng bổ sung trực tiếp cho từng chủ đề. Tất cả miễn phí hoặc có bản free.

### AI product management

**Lenny Rachitsky — "Counterintuitive Advice for Building AI Products" (2024)**
Phỏng vấn 20+ người build AI product thành công, chia sẻ bài học không hiển nhiên. Đọc nếu muốn nghe nhiều góc nhìn thực tế từ practitioners — bổ sung cho phần "demo ≠ product" trong bài giảng.
- [lennysnewsletter.com/p/counterintuitive-advice-for-building](https://www.lennysnewsletter.com/p/counterintuitive-advice-for-building)

**a16z — "16 Changes to the Way Enterprises Are Building and Buying Generative AI" (2024)**
Khảo sát 70+ doanh nghiệp Fortune 500 về cách họ quyết định AI: model selection, use-case prioritization, resourcing. Đọc nếu muốn hiểu bức tranh lớn hơn — các công ty thật đang build AI thế nào.
- [a16z.com/generative-ai-enterprise-2024](https://a16z.com/generative-ai-enterprise-2024/)

### Precision, recall & eval metrics

**Evidently AI — "Accuracy vs. Precision vs. Recall in ML"**
Giải thích rõ ràng precision, recall với ví dụ trực quan, khi nào chọn metric nào dựa trên cost of error. Đọc nếu phần precision/recall trong bài giảng chưa rõ — bài này giải thích bằng hình, không cần nền statistics.
- [evidentlyai.com/classification-metrics/accuracy-precision-recall](https://www.evidentlyai.com/classification-metrics/accuracy-precision-recall)

**Google ML Crash Course — "Classification: Accuracy, Precision, Recall"**
Module miễn phí từ Google, có interactive examples và visualizations cho confusion matrix. Tự học với ví dụ tương tác, tốt hơn đọc definition.
- [developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall)

### UX cho AI products

**The Shape of AI — AI UX Pattern Library**
Thư viện 24+ patterns UX cho AI (refine output, prompt presets, explainability layers, error recovery) với 50+ ví dụ từ sản phẩm thật. Dùng khi thiết kế 4 paths — tra cứu pattern nào phù hợp product của mình.
- [shapeof.ai](https://www.shapeof.ai/)

**Smashing Magazine — "Designing for Agentic AI: UX Patterns for Control, Consent, and Accountability" (2026)**
Patterns UX cho AI agent (hệ thống tự hành động thay user): control flows, consent checkpoints, accountability. Đọc nếu project là agent/automation — bài này cover đúng vấn đề trust trong cột Trust của Canvas.
- [smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns](https://www.smashingmagazine.com/2026/02/designing-agentic-ai-practical-ux-patterns/)

### AI Product Canvas & PRD

**Miqdad Jaffer (Product Lead @ OpenAI) — "A Proven AI PRD Template" (2025)**
PRD template thực tế từ OpenAI product lead, có case study Shopify "Auto Write." Dùng khi viết Mini AI spec — template này có sections cho model selection, evaluation criteria, non-functional requirements.
- [productcompass.pm/p/ai-prd-template](https://www.productcompass.pm/p/ai-prd-template)

### Feedback loops & data flywheel

**Shreya Shankar (UC Berkeley) — "Data Flywheels for LLM Applications"**
Cách thiết kế data flywheel cho ứng dụng LLM: biến user interactions thành systematic model improvement. Đọc nếu muốn hiểu sâu hơn phần Learning Signal trong Canvas — bài này chỉ cách thu và dùng feedback cụ thể.
- [sh-reya.com/blog/ai-engineering-flywheel](https://www.sh-reya.com/blog/ai-engineering-flywheel/)

**MIT Sloan — "Why It's Time for Data-Centric Artificial Intelligence"**
Andrew Ng's data-centric AI framework: cải thiện data quality iteratively quan trọng hơn scale model, đặc biệt cho team nhỏ. Liên quan đến nguyên tắc "qualitative > quantitative" trong bài giảng.
- [mitsloan.mit.edu/ideas-made-to-matter/why-its-time-data-centric-artificial-intelligence](https://mitsloan.mit.edu/ideas-made-to-matter/why-its-time-data-centric-artificial-intelligence)

### ROI cho AI products

**Larridin — "The AI ROI Measurement Framework" (2025)**
Framework đo ROI cho AI: 5-link chain (Spend → Adoption → Proficiency → Productivity → Business Outcome). Dùng khi viết ROI 3 kịch bản — bài này chỉ cách đo beyond vanity metrics.
- [larridin.com/blog/ai-roi-measurement](https://larridin.com/blog/ai-roi-measurement)

### Automation vs augmentation

**Stanford HAI — "Humans in the Loop: The Design of Interactive AI Systems"**
Reframe automation thành HCI design problem: "không phải how do we build a smarter system mà how do we incorporate meaningful human interaction?" Bổ sung cho framework auto vs aug trong bài giảng — đặc biệt phần augmentation design.
- [hai.stanford.edu/news/humans-loop-design-interactive-ai-systems](https://hai.stanford.edu/news/humans-loop-design-interactive-ai-systems)

### Prototyping AI products

**Lenny's Newsletter — "A Guide to AI Prototyping for Product Managers"**
Framework prototyping cho PM: bắt đầu từ one-pager + prompts, dùng AI builders tạo variations nhanh, test với 5-8 users. Đọc trước hackathon nếu chưa biết bắt đầu từ đâu — bài này chỉ khi nào dùng tool nào (Cursor, v0, Bolt, Replit).
- [lennysnewsletter.com/p/a-guide-to-ai-prototyping-for-product](https://www.lennysnewsletter.com/p/a-guide-to-ai-prototyping-for-product)

---

## Cách sử dụng tài liệu này

- **Trong bài giảng:** tra cứu Section 1 (frameworks) khi giảng viên nhắc đến framework nào
- **Sau bài giảng:** đọc Section 2 (case studies) và Section 3 (expert interviews) để hiểu sâu hơn
- **Trước hackathon:** đọc Section 6 (đọc thêm) theo chủ đề quan tâm
- **Trong hackathon:** dùng hackathon toolkit (templates, tools, cheatsheet) — không phải file này

---

*Tài liệu tham khảo — Ngày 5: Thiết kế sản phẩm AI cho xác suất*
*VinUni A20 — AI Thực Chiến*
