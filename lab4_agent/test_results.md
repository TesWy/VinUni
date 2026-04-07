## Báo cáo kết quả Chatbot hỗ trợ du lịch 
Mã HV: 2A202600084
Lab03 - 7/4/2026

Chi tiết console nằm trong file logs/evals/eval_20260407_154741.json
Chi tiết đánh giá 5 test case nằm trong file logs/evals/eval_latest.md

## Đối với bài làm em có thay đổi các thứ như sau.

1. Đầu tiên là sử dụng mô hình Gemma-4-31b-it của Google thay vì dùng OpenAI (để tiết kiệm chi phí)
2. Phát triển thêm 2 tools ngoài là trao đổi tiền tệ và lấy thông tin về thời tiết. Từ API https://api.open-meteo.com/v1/forecast, https://geocoding-api.open-meteo.com/v1/search và tiền tệ của https://api.frankfurter.dev/v2/rates https://api.frankfurter.dev/v1/latest .Dùng mỗi cái 2 cái để fallback trong trường hợp cái kia bị lỗi
3. Có thêm file response_utils.py để xử lý format
4. Có hỗ trợ UI thông qua streamlit