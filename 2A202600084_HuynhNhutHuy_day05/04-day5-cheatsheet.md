# Day 5 cheatsheet — 1 trang recap

Tra cứu nhanh trong lúc làm hackathon.

## Domino chain

```
AI = probabilistic (luôn có sai số)
  → Automation hay augmentation?
    → 3 trụ: Requirement / UX / Eval
      → Canvas (gộp 3 trụ vào 1 trang)
        → Feedback loop + Data flywheel
          → ROI 3 kịch bản
```

---

## Automation vs augmentation

| | Automation | Augmentation |
|---|---|---|
| AI làm gì | Làm thay user | Gợi ý, user quyết |
| Khi AI sai | Thiệt hại đã xảy ra — user không kịp can thiệp | User bỏ qua, không thiệt hại |
| Accuracy cần | Rất cao (99%+) | Chấp nhận thấp hơn (Copilot: 30%) |
| UX cần | Monitoring, alert, undo | Suggestion UI — accept/reject |
| Trust risk | Over-trust (không verify) | Under-trust (bỏ qua hết) |

Thực tế: bắt đầu aug → tăng dần auto khi data đủ (V1 routing → V2 copilot → V3 tự động).

---

## Precision vs recall

- **Precision:** AI nói "có" → đúng bao nhiêu? Ưu tiên khi sai nhầm = thiệt hại lớn
- **Recall:** trong số đúng thật → AI tìm được bao nhiêu? Ưu tiên khi bỏ sót = thiệt hại lớn
- User THẤY & sửa được → recall ok. User KHÔNG thấy → precision cao
- PM chọn precision/recall = product decision, không phải technical decision

---

## 4 paths — khi AI output xong, chuyện gì xảy ra?

| Path | Câu hỏi thiết kế |
|------|-------------------|
| Happy — AI đúng | User thấy gì? Flow kết thúc ra sao? |
| Low-confidence — AI không chắc | System báo bằng cách nào? User quyết thế nào? |
| Failure — AI sai | User biết sai bằng cách nào? Recover ra sao? |
| Correction — user sửa | User sửa bằng cách nào? Data đó đi vào đâu? |

---

## AI Product Canvas — 3 cột

| Value | Trust | Feasibility |
|-------|-------|-------------|
| User nào? Pain gì? AI giải gì? | Khi AI sai → user bị gì? Sửa thế nào? | Cost? Latency? Risk chính? |

+ Auto/aug? + Learning signal (implicit / explicit / correction)

---

## Feedback loop — 3 loại signal

| Loại | Mô tả | Ví dụ |
|------|-------|-------|
| Implicit | User behavior, không biết đang cho feedback | Click, skip, dwell time |
| Explicit | User chủ động | Thumbs up/down, rating, report |
| Correction | User sửa output AI | Kéo email sang nhãn đúng, edit text AI viết |

Qualitative > quantitative: "accuracy 87%" không nói sai ở đâu — cần nhìn output bằng mắt.

---

## ROI 3 kịch bản

| | Conservative | Realistic | Optimistic |
|---|---|---|---|
| Assumption | Ít user, adoption thấp | Trung bình | Nhiều user, adoption cao |
| Cost | Inference + maintain | | |
| Benefit | Tiết kiệm thời gian/tiền | | |
| Net | | | |

Kill criteria: khi nào nên dừng? (VD: cost > benefit 2 tháng liên tục)

---

*Day 5 cheatsheet — VinUni A20 — AI Thực Chiến · 2026*
