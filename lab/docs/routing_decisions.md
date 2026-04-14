# Routing Decisions Log — Lab Day 09

**Nhóm:** C401_F1  
**Ngày:** 14/04/2026

> **Hướng dẫn:** Ghi lại ít nhất **3 quyết định routing** thực tế từ trace của nhóm.
> Không ghi giả định — phải từ trace thật (`artifacts/traces/`).
> 
> Mỗi entry phải có: task đầu vào → worker được chọn → route_reason → kết quả thực tế.

---

## Routing Decision #1

**Task đầu vào:**
> 'SLA xử lý ticket P1 là bao lâu?'

**Worker được chọn:** `retrieval_worker`  
**Route reason (từ trace):** `knowledge lookup (SLA / ticket / docs)`  
**MCP tools được gọi:** None  
**Workers called sequence:** `retrieval_worker` -> `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Phản hồi ban đầu: 15 phút; Xử lý và khắc phục: 4 giờ.
- confidence: 0.6
- Correct routing? Yes

**Nhận xét:** outing chính xác. Supervisor nhận diện đúng các từ khóa "SLA", "ticket" để định tuyến thẳng đến `retrieval_worker` nhằm tra cứu tài liệu kỹ thuật. Vì đây là câu hỏi tra cứu thông tin tĩnh, không cần gọi MCP hay kiểm tra ngoại lệ chính sách.

_________________

---

## Routing Decision #2

**Task đầu vào:**
> 'Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?'

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword`  
**MCP tools được gọi:** search_kb  
**Workers called sequence:** `policy_tool_worker` -> `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.
- confidence: 0.52
- Correct routing? Yes

**Nhận xét:** Routing chính xác dựa trên từ khóa "hoàn tiền". Đáng chú ý là Supervisor đã kích hoạt `needs_tool: true`. Do đó, `policy_tool_worker` đã sử dụng MCP tool `search_kb` để tìm kiếm dữ liệu thay vì dựa vào kết quả của `retrieval_worker` trước đó.

_________________

---

## Routing Decision #3

**Task đầu vào:**
> 'Ai phải phê duyệt để cấp quyền Level 3?' 

**Worker được chọn:** `policy_tool_worker`  
**Route reason (từ trace):** `task contains policy/access keyword`  
**MCP tools được gọi:** search_kb 
**Workers called sequence:** `policy_tool_worker` -> `synthesis_worker`

**Kết quả thực tế:**
- final_answer (ngắn): Cần phê duyệt của Line Manager, IT Admin và IT Security.
- confidence: 0.51
- Correct routing? Yes

**Nhận xét:** Đúng mục tiêu. Supervisor nhận diện yêu cầu cấp quyền (access) là một tác vụ liên quan đến quy trình/chính sách nên đã gửi đến `policy_tool_worker`. Worker này cũng đã gọi MCP `search_kb` để lấy context từ tài liệu `access-control-sop.md`.

_________________

---

## Routing Decision #4 (tuỳ chọn — bonus)

**Task đầu vào:**
> 

**Worker được chọn:**  
**Route reason:** 

**Nhận xét: Đây là trường hợp routing khó nhất trong lab. Tại sao?**

_________________

---

## Tổng kết

### Routing Distribution

| Worker | Số câu được route | % tổng |
|--------|------------------|--------|
| retrieval_worker | 7 | 46.67% |
| policy_tool_worker | 7 | 46.67% |
| human_review | 1 | 6.67% |

### Routing Accuracy

> Trong số X câu nhóm đã chạy, bao nhiêu câu supervisor route đúng?

- Câu route đúng: 15 / 15
- Câu route sai (đã sửa bằng cách nào?): 0
- Câu trigger HITL: 1 (đã route đến human_review) trong câu 'ERR-403-AUTH là lỗi gì và cách xử lý?'

### Lesson Learned về Routing

> Quyết định kỹ thuật quan trọng nhất nhóm đưa ra về routing logic là gì?  

1. Sử dụng keyword matching để định tuyến đến worker chuyên biệt (retrieval vs policy) giúp tăng độ chính xác và giảm chi phí so với việc dùng LLM classifier cho tất cả các câu hỏi.
2. Thêm Human in the Loop (HITL) cho các câu hỏi có keyword "ERR", "khẩn cấp", ... để đảm bảo không bỏ sót các tình huống cần can thiệp thủ công.

### Route Reason Quality

>
> Các route_reason như `task contains policy/access keyword` hoặc `knowledge lookup (SLA / ticket / docs)` đã cung cấp được tín hiệu phân loại cơ bản nhưng chưa đủ sâu để debug các trường hợp phức tạp
>
> Nhóm sẽ chuyển sang format Logic-based + Confidence. Việc bổ sung chỉ số tin cậy (Confidence) của chính Supervisor và liệt kê cụ thể các từ khóa "bắt" được sẽ giúp lập trình viên biết chính xác Supervisor đang bị nhầm lẫn ở đâu nếu định tuyến sai.

_________________
