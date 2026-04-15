# TravelBuddy Lab 4

## Tong quan

Đây là bài lab xây dựng trợ lý du lịch bằng LangGrpah cho TravelBuddy
Project hiện tại hỗ trợ Gemini và OpenAI:
- switch provider giua Gemini va OpenAI
- chat CLI va giao dien Streamlit
- Có chat CLI và giao diện Streamlit
- Có logging và traces để quan sát
- eval 5 test case để kiểm tra hành vi của agent

Agent hiện có 5 tools:
- `search_flights`
- `search_hotels`
- `calculate_budget`
- `get_weather` :Bonus tool
- `convert_currency` :Bonus tool


- `get_weather` Chỉ nên được gọi trực tiếp khi user hỏi về thời tiết
- `response_utils.py` dùng để làm sạch format

## Trang thai hien tai

Bản hiện tại có các file chính:
- `agent.py`: CLI agent bang LangGraph
- `app_streamlit.py`: demo UI + observability
- `tools.py`: 5 tools cho bai toan du lich
- `observability.py`: ghi log va traces
- `eval_agent.py`: bo test danh gia hanh vi agent
- `system_prompt.txt`: prompt dieu huong cach chon tool
- `test_api.py`: test ket noi model

Ket qua eval moi nhat:
- `logs/evals/eval_latest.md`
- Pass `5/5`

## Cau truc thu muc

```text
lab4_agent/
|-- agent.py
|-- app_streamlit.py
|-- eval_agent.py
|-- observability.py
|-- response_utils.py
|-- system_prompt.txt
|-- test_api.py
|-- tools.py
|-- requirements.txt
|-- .env
`-- logs/
    |-- travelbuddy.log
    |-- traces.jsonl
    |-- chat_sessions.json
    `-- evals/
```

## Mo ta file chinh

### `agent.py`
- Khởi tạo model theo `LLM_PROVIDER`
- Bind tools vao LangGraph
- Chay chat loop trong terminal
- Ghi traces cho moi turn va tool call

### `tools.py`
Chua 5 tools:

1. `search_flights(origin, destination)`
- Trả danh sách chuyến bay hiện có giữa 2 thành phố

2. `search_hotels(city, max_price_per_night=99999999)`
- Tìm khách sạn theo thành phố
- Có thể lọc theo giá

3. `calculate_budget(total_budget, expenses)`
- Dùng tính tổng chi phí và ngân sách còn lại

4. `get_weather(city)`
- Lấy thời tiết hiện tại theo thành phố

5. `convert_currency(amount, from_currency, to_currency)`
- Quy đổi tiền tệ qua API Frankfurter

### `app_streamlit.py`
- Giao diện phong cách TravelBuddy
- Hộ trợ `Single` va `Compare` :Trong trường hợp muốn so sánh Gemma-4-31b-it và GPT
- Co workspace `Travel Chat` va `Observability`
- Lưu lịch sử chat vào `logs/chat_sessions.json`

### `observability.py`
- Tao `travelbuddy.log`
- Tao `traces.jsonl`
- Gan `turn_id` cho moi luot chat

### `response_utils.py`
- Chuyen structured content cua model thanh text de doc
- Lam sach cac ky hieu formatting nhu LaTeX/markdown math

### `eval_agent.py`
- Chay cac test case danh gia hanh vi agent
- Log ro input, tool da goi, tool output, final answer, check pass/fail
- Xuat report ra `logs/evals/`

## Cài đặt

### 1. Tạo môi trường và cài thư viện

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Cau hinh `.env`

Vi du:

```env
LLM_PROVIDER=gemini
GEMINI_MODEL=gemma-4-31b-it
OPENAI_MODEL=gpt-4o-mini
GOOGLE_API_KEY=your_google_key
OPENAI_API_KEY=your_openai_key
```

Ghi chu:
- Neu dung Gemini: can `GOOGLE_API_KEY` hoac bien tuong duong ma SDK chap nhan.
- Neu dung OpenAI: can `OPENAI_API_KEY`.
- `LLM_PROVIDER` nhan `gemini` hoac `openai`.

## Cach chay

### Test model API

```powershell
python test_api.py
```

### Chay CLI agent

```powershell
python agent.py
```

### Chay giao dien Streamlit

```powershell
streamlit run app_streamlit.py
```

### Chay eval

```powershell
python eval_agent.py
```

Report moi nhat se nam o:
- `logs/evals/eval_latest.md`
- `logs/evals/eval_latest.json`

## Logging va traces

Project se tu dong sinh cac file sau trong `logs/`:
- `travelbuddy.log`: log text de doc nhanh
- `traces.jsonl`: traces theo tung event va `turn_id`
- `chat_sessions.json`: session chat cua Streamlit
- `evals/`: ket qua chay danh gia

## Hanh vi tool chinh

### Flight planning
- Agent chi dung `search_flights` cho bai toan flight.
- Tu danh sach chuyen bay tra ve, agent tu tong hop:
  - ve re nhat
  - ve bay som nhat
  - phuong an cao cap hon
  - phuong an hop budget

### Trip planning co budget
Neu user dua du diem di, diem den, budget va nhu cau khach san, luong mong muon la:
1. `search_flights`
2. `search_hotels`
3. `calculate_budget`
4. Tong hop thanh cau tra loi cuoi cung

### Weather va currency
- `get_weather` chi dung khi user hoi thoi tiet
- `convert_currency` chi dung khi user muon doi tien

## Eval hien tai

Bộ eval mặc định trong `eval_agent.py` gồm 5 case:
- direct answer khong can tool
- single tool call cho flight lookup
- multi-step tool chaining
- missing info / clarification
- guardrail / refusal

Trang thai moi nhat:
- `5/5` pass theo `logs/evals/eval_latest.md`
