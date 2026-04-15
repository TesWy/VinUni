# Morning Mini-Lab: Data Cleaning Sprint

Chào mừng các bạn đến với bài Lab về **Data Sanitization**. Trong bài thực hành này, chúng ta sẽ học cách xử lý dữ liệu thô (toxic data) để đảm bảo tính an toàn (Privacy) và độ tin cậy (Reliability) trước khi đưa vào hệ thống AI.

## 1. Cấu trúc thư mục
- `toxic_sample.json`: Dữ liệu thô chứa lỗi (PII, duplicates, outliers).
- `mini-lab-data-cleaning.md`: Hướng dẫn chi tiết các bước thực hiện.
- `cleaning.py`: File code mẫu với các `TODO` để học viên hoàn thiện.
- `cleaning_solution.py`: File lời giải tham khảo.

## 2. Chuẩn bị môi trường
Bài Lab này chỉ yêu cầu **Python 3.x** cơ bản và thư viện `json` (đã có sẵn trong Python Standard Library). 

Để đảm bảo môi trường sạch, bạn nên khởi tạo môi trường ảo (virtual environment):

**Trên Windows:**
```bash
# Khởi tạo venv
python -m venv venv
# Kích hoạt venv
.\venv\Scripts\activate
```

**Trên macOS/Linux:**
```bash
# Khởi tạo venv
python3 -m venv venv
# Kích hoạt venv
source venv/bin/activate
```

Sau khi kích hoạt, bạn có thể kiểm tra phiên bản Python:
```bash
python --version
```

## 3. Hướng dẫn thực hiện
Học viên thực hiện theo các bước sau:

1.  **Đọc yêu cầu**: Mở file `mini-lab-data-cleaning.md` để hiểu các quy tắc cần làm sạch dữ liệu.
2.  **Lập trình**: Mở file `cleaning.py` và hoàn thiện các phần được đánh dấu `# TODO`.
3.  **Chạy thử nghiệm**: Chạy script để kiểm tra kết quả:
    ```bash
    python cleaning.py
    ```
4.  **Kiểm tra kết quả**: Sau khi chạy thành công, file `sanitized_sample.json` sẽ được tạo ra. Hãy kiểm tra xem:
    - Trường `name` đã bị xóa chưa?
    - `email` đã được che (mask) chưa?
    - Các bản ghi trùng lặp và giá trị lỗi (giá > $5000 hoặc < 0) đã được loại bỏ chưa?

## 4. Giải thích thuật ngữ
- **PII (Personally Identifiable Information)**: Thông tin định danh cá nhân cần được bảo vệ.
- **Sanitization**: Quá trình làm sạch dữ liệu.
- **Outlier**: Giá trị bất thường trong tập dữ liệu.

---
*Chúc các bạn hoàn thành bài Lab xuất sắc!*
