# Ngày 5 — Thiết kế sản phẩm AI cho sự không chắc chắn

> AI chạy được chưa phải product. Hôm nay học cách thiết kế cho uncertainty — khi AI có thể sai, UI phải xử lý thế nào?

---

## Tổng quan buổi học

```text
SÁNG — Lecture + Workshop                   CHIỀU — Lecture + Hackathon kickoff
┌──────────────────────────────┐            ┌──────────────────────────────┐
│ AI = probabilistic            │            │ Feedback loop + Data flywheel│
│ 3 trụ: Requirement · Eval · UX│     →      │ ROI 3 kịch bản               │
│ UX workshop (cá nhân)         │            │ Hackathon briefing           │
│ Canvas practice (nhóm)        │            │ Draft SPEC                   │
└──────────────────────────────┘            └──────────────────────────────┘
```

**Lecture** dạy framework: AI product khác phần mềm thường vì luôn có sai số. 3 trụ thiết kế: Requirement (precision/recall), Eval (metric + threshold), UX (4 paths khi AI đúng/sai/không chắc/user sửa). Canvas gộp tất cả vào 1 trang.

**Workshop + Practice** cho bạn thực hành trên sản phẩm AI thật (UX exercise) và bắt đầu thiết kế product AI của nhóm (Canvas practice + SPEC draft).

---

## Agenda

| Giờ | Hoạt động | Hình thức | Deliverable |
|-----|-----------|-----------|-------------|
| 9:00 | Opening — 3 cases thất bại + thesis "AI ≠ phần mềm thường" | Lecture | |
| 9:15 | Block 1: AI = probabilistic + Automation vs Augmentation | Lecture | |
| 9:45 | Block 2: 3 trụ — Requirement · Eval · UX | Mixed | |
| | — Requirement: lecture + Discord "tìm lỗi spec" | Discord (cá nhân, ~3 phút) | |
| | — Eval: lecture + Discord "precision hay recall?" | Discord (cá nhân, ~3 phút) | |
| | — **UX workshop:** phân tích sản phẩm AI thật | **Cá nhân** (40 phút) | **Sketch giấy + ghi chú 4 paths** |
| | — Debrief: kết nối 3 trụ | Lecture | |
| 11:10 | Break | | |
| 11:25 | Block 3: Canvas — Value / Trust / Feasibility + learning signal | Lecture | |
| 12:00 | Canvas practice — sketch Canvas cho project của nhóm + peer peek | Nhóm (25 phút) | |
| 13:00 | Nghỉ trưa | | |
| 14:00 | Block 4: Feedback loop + Data flywheel + Qual>Quant | Lecture | |
| 14:30 | Block 5: ROI 3 kịch bản | Lecture | |
| 15:00 | Q&A + Buffer | | |
| 15:30 | Break | | |
| 16:00 | **Hackathon briefing** + chia nhóm + chọn track + bắt đầu draft SPEC | Nhóm (3–5 người) | |
| **23h59** | **Deadline 08/04** | Nhóm | **Submit topic + SPEC draft** |

---

## Hoạt động chính

### 1. UX workshop — phân tích sản phẩm AI thật (40 phút, cá nhân)

Chọn 1 sản phẩm AI thật (MoMo / Vietnam Airlines / V-App), dùng thử, phân tích theo 4 paths, sketch cải thiện.

**Xem chi tiết:** [`01-ux-exercise.md`](01-ux-exercise.md)

**Output:** mỗi người nộp sketch giấy + ghi chú phân tích 4 paths. Đây là điểm cá nhân.

### 2. Canvas practice (25 phút, nhóm)

Sketch Canvas cho project của nhóm lên giấy A3 hoặc whiteboard. Peer peek: đi xem Canvas nhóm khác, ghi 1 feedback.

**Xem template:** [`02-canvas-template.md`](02-canvas-template.md)

### 3. SPEC draft (từ 16:00 + tối, nhóm)

Bắt đầu viết SPEC cho hackathon. Deadline: 23h59 08/04 Day 5.

SPEC gồm 6 phần: Canvas, User Stories 4 paths, Eval metrics, Failure modes, ROI, Mini AI spec.

**Template SPEC sẽ có trong repo hackathon:** [Day06-AI-Product-Hackathon](https://github.com/VinUni-AI20k/Day06-AI-Product-Hackathon)

---

## Deliverables

| # | Deliverable | Loại | Deadline | Ghi chú |
|---|-------------|------|----------|---------|
| 1 | **Bài tập UX** — sketch giấy (as-is + to-be) + ghi chú phân tích 4 paths | Cá nhân | Cuối UX workshop | Nộp tại lớp |
| 2 | **SPEC draft** — topic + Canvas + hướng đi chính | Nhóm | 23h59 08/04/2026 | Submit kịp = pass. Chất lượng chấm ở SPEC final Day 6 |

---

## Cách tính điểm

Day 5 + Day 6 chấm chung = **100 điểm**.

| Hạng mục | Điểm | Loại | Khi nào |
|----------|------|------|---------|
| SPEC milestone | 25 | Nhóm + cá nhân | Draft 23h59 08/04 D5, final 23h59 09/04 |
| Prototype milestone | 15 | Nhóm + cá nhân | 23h59 09/04 |
| Demo Day | 25 | Nhóm | Present 16:00, nộp file 23h59 09/04 |
| **Bài tập UX** | **10** | **Cá nhân + bonus** | **UX workshop sáng D5** |
| Individual reflection | 25 | Cá nhân | 23h59 09/04 |
| **Tổng** | **100** | | |

### Bài tập UX (10 điểm + bonus)

| Tiêu chí | Điểm |
|----------|------|
| Phân tích 4 paths đủ + nhận xét path yếu nhất | 4 |
| Sketch as-is + to-be rõ ràng | 4 |
| Nhận xét gap marketing vs thực tế | 2 |
| **Bonus:** nhóm vote sketch hay nhất | +bonus |

---

## 4 hackathon tracks

| Track | Lĩnh vực | Gợi ý bài toán |
|-------|----------|----------------|
| **A** | VinFast | AI chatbot hỗ trợ mua xe/bảo dưỡng, phân tích review |
| **B** | Vinmec | AI triage, hỏi triệu chứng → gợi ý chuyên khoa |
| **C** | VinUni/VinSchool | AI tutor, trợ lý học tập, Q&A nội bộ |
| **D** | Tự chọn | Tự chọn domain, phải justify |

Nhóm 3–5 người, chia zone (~5 team/zone).

---

## Tài liệu trong repo này

| File | Mô tả |
|------|-------|
| [`01-ux-exercise.md`](01-ux-exercise.md) | Đề bài UX workshop — hướng dẫn từng phần, tiêu chí nộp bài |
| [`02-canvas-template.md`](02-canvas-template.md) | Template AI Product Canvas — dùng cho Canvas practice |
| [`03-day5-cheatsheet.md`](03-day5-cheatsheet.md) | Tóm tắt 1 trang các framework từ lecture — tra cứu nhanh |

---

## Nộp bài Day 5

**Deadline:** 23h59 08/04/2026 | **Nộp lên:** LMS | **Mỗi người nộp 1 zip riêng**

```
MaHocVien-HoTen-Day05.zip
│
├── canhan/
│   └── ux-exercise/               ← Ảnh chụp/scan sketch + ghi chú phân tích 4 paths
│       ├── sketch.jpg/pdf         ← Sketch giấy (as-is + to-be)
│       └── analysis.md            ← Ghi chú phân tích 4 paths + gap marketing vs thực tế
│
└── NhomXX-Room/                   ← VD: Nhom01-403
    └── spec-draft.md              ← SPEC draft (file nhóm, mỗi người nộp giống nhau)
```

---

## Rời lớp Day 5, mỗi nhóm phải có

1. Track đã chọn (VinFast / Vinmec / VinUni-VinSchool / Open)
2. Problem statement 1 câu: "Ai gặp vấn đề gì, hiện giải thế nào, AI giúp được gì"
3. Phân công ai làm phần nào trong Canvas
4. SPEC draft submit trước 23h59 08/04

---

*Ngày 5 — VinUni A20 — AI Thực Chiến · 2026*
