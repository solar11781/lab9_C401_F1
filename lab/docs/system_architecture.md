# System Architecture — Lab Day 09

**Nhóm:** C401-F1 
**Ngày:** 14/04/2026  
**Version:** 1.0

---

## 1. Tổng quan kiến trúc

> Mô tả ngắn hệ thống của nhóm: chọn pattern gì, gồm những thành phần nào.

**Pattern đã chọn:** Supervisor-Worker  
**Lý do chọn pattern này**

> Tránh quá tải & ảo giác: Không nhồi nhét toàn bộ context và tools vào một prompt duy nhất, giảm thiểu rủi ro kẹt vòng lặp ReAct.

>Dễ debug & nâng cấp: Mỗi worker đảm nhận một nhiệm vụ chuyên biệt (Separation of Concerns) với prompt riêng, dễ dàng test độc lập.

>Kiểm soát luồng rõ ràng: Dễ theo dõi lý do điều hướng (routing) và linh hoạt chặn các tác vụ rủi ro cao.

**Các thành phần chính**

>Supervisor: Phân tích request, đánh giá rủi ro (risk_high), xác định nhu cầu dùng tool (needs_tool) và quyết định điều hướng luồng.

>Retrieval Worker: Thực hiện RAG, truy xuất và trả về thông tin thô (evidence).

>Policy Tool Worker: Xử lý nghiệp vụ, kiểm tra rào cản chính sách và gọi external tool qua MCP.

>Synthesis Worker: Tổng hợp dữ liệu từ các worker trước, định dạng câu trả lời cuối và trích dẫn nguồn (cite).
_________________

---

## 2. Sơ đồ Pipeline

> Vẽ sơ đồ pipeline dưới dạng text, Mermaid diagram, hoặc ASCII art.
> Yêu cầu tối thiểu: thể hiện rõ luồng từ input → supervisor → workers → output.

**Ví dụ (ASCII art):**
```
User Request
     │
     ▼
┌──────────────┐
│  Supervisor  │  ← route_reason, risk_high, needs_tool
└──────┬───────┘
       │
   [route_decision]
       │
  ┌────┴────────────────────┐
  │                         │
  ▼                         ▼
Retrieval Worker     Policy Tool Worker
  (evidence)           (policy check + MCP)
  │                         │
  └─────────┬───────────────┘
            │
            ▼
      Synthesis Worker
        (answer + cite)
            │
            ▼
         Output
```

**Sơ đồ thực tế của nhóm:**

```
User Request
    |
    v
.------------.
| Supervisor |  <- route_reason, risk_high, needs_tool
'------------'
    |
 [route_decision]
    |
    |-----------------------|-----------------------|
    v                       v                       v
Retrieval Worker      Policy Tool Worker       Human review
  (evidence)        (policy check + MCP)          (HITL)
    |                       |                       |
    |<----------------------------------------------| (HITL feedback)
    |                       |
    |-----------------------|
                |
                v
        Synthesis Worker
         (answer + cite)
                |
                v
              Output
```

---

## 3. Vai trò từng thành phần

### Supervisor (`graph.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Route đến các worker, nhận output và state từ các worker để đi đến bước tiếp theo |
| **Input** | User query |
| **Output** | supervisor_route, route_reason, risk_high, needs_tool |
| **Routing logic** | Key word routing logic: Supervisor phân tích task và quyết định: 1. Route sang worker nào; 2. Có cần MCP tool không; 3. Có risk cao cần HITL không |
| **HITL condition** | risk_keywords = ["emergency", "khẩn cấp", "2am", "không rõ", "err-"] |

### Retrieval Worker (`workers/retrieval.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Implement retrieval từ ChromaDB, trả về chunks + sources. |
| **Embedding model** | Ưu tiên gọi API OpenAI, tự động lùi về Local Sentence Transformers (all-MiniLM-L6-v2) nếu thiếu API key, và dùng Random embedding làm môi trường test cuối cùng |
| **Top-k** | 3 |
| **Stateless?** | No |

### Policy Tool Worker (`workers/policy_tool.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **Nhiệm vụ** | Kiểm tra policy dựa vào context, gọi MCP tools khi cần. |
| **MCP tools gọi** | Đưa ra list các tools cần thực hiện |
| **Exception cases xử lý** | Đối chiếu yêu cầu với chính sách để xác định các ngoại lệ, iểm tra mốc thời gian hiệu lực |

### Synthesis Worker (`workers/synthesis.py`)

| Thuộc tính | Mô tả |
|-----------|-------|
| **LLM model** | Gpt-4o-mini |
| **Temperature** | 0.1 |
| **Grounding strategy** | Build context từ retrieved_chunks + policy_result, ép LLM chỉ trả lời dựa trên context qua system prompt |
| **Abstain condition** | Khi không có retrieved_chunks hoặc context không đủ → trả "Không đủ thông tin trong tài liệu nội bộ" |

### MCP Server (`mcp_server.py`)

| Tool | Input | Output |
|------|-------|--------|
| search_kb | query, top_k | chunks, sources, total_found |
| get_ticket_info | ticket_id | ticket_id, priority, status, assignee, created_at, sla_deadline |
| check_access_permission | access_level, requester_role, is_emergency | can_grant, required_approvers, emergency_override, notes, source |
| create_ticket | priority, title, description | ticket_id, priority, status, created_at, url |


---

## 4. Shared State Schema

> Liệt kê các fields trong AgentState và ý nghĩa của từng field.

| Field | Type | Mô tả | Ai đọc/ghi |
|-------|------|-------|-----------|
| task | str | Câu hỏi đầu vào | supervisor đọc |
| supervisor_route | str | Worker được chọn | supervisor ghi |
| route_reason | str | Lý do route | supervisor ghi |
| retrieved_chunks | list | Evidence từ retrieval | retrieval ghi, synthesis đọc |
| policy_result | dict | Kết quả kiểm tra policy | policy_tool ghi, synthesis đọc |
| mcp_tools_used | list | Tool calls đã thực hiện | policy_tool ghi |
| final_answer | str | Câu trả lời cuối | synthesis ghi |
| confidence | float | Mức tin cậy | synthesis ghi |
| risk_high | bool | Cần HITL hoặc human_review | supervisor ghi |
| needs_tool | bool | Cần gọi external tool qua MCP | supervisor đọc |
| hitl_triggered | bool | Đã pause cho human review | supervisor đọc |
| retrieved_sources | list | Danh sách nguồn tài liệu | retrieval ghi, synthesis đọc |
| sources | list | Sources được cite | synthesis ghi |
| history | list | Lịch sử các bước đã qua | system ghi |
| workers_called | list | Danh sách workers đã được gọi | worker ghi |
| latency_ms | Optional[int] | Thời gian xử lý (ms) | system ghi |
| run_id | str | ID của run này | system ghi |

---

## 5. Lý do chọn Supervisor-Worker so với Single Agent (Day 08)

| Tiêu chí | Single Agent (Day 08) | Supervisor-Worker (Day 09) |
|----------|----------------------|--------------------------|
| Debug khi sai | Khó — không rõ lỗi ở đâu | Dễ hơn — test từng worker độc lập |
| Thêm capability mới | Phải sửa toàn prompt | Thêm worker/MCP tool riêng |
| Routing visibility | Không có | Có route_reason trong trace |
| Quản lý Context & Token | Dễ quá tải vì nhồi nhét mọi tools và context vào 1 prompt. | Tối ưu hơn, mỗi worker chỉ nhận context/tools chuyên biệt. |

**Nhóm điền thêm quan sát từ thực tế lab:**
Vấn đề chuyển tiếp Sub-task: Khi sử dụng Single Agent với một system prompt nguyên khối (v1), hệ thống rất dễ bị "trượt" logic và thất bại trong việc xâu chuỗi các sub-task liên tục (ví dụ: không thể lên lịch trình chuyển tiếp ngày qua ngày một cách chi tiết). Việc chuyển sang Supervisor giúp chia nhỏ logic, đảm bảo output của worker này được định dạng chuẩn xác trước khi router quyết định bước tiếp theo (v2).

Đánh đổi về độ phức tạp cấu hình: Mặc dù Supervisor-Worker dễ debug logic hơn, nhưng quá trình config đồ thị (graph) lại nhạy cảm với lỗi cú pháp hơn rất nhiều. Thực tế triển khai cho thấy chỉ cần một sự sai lệch nhỏ trong việc định danh node (ví dụ: mismatch tên giữa hàm router_condition và node đích) là luồng sẽ lập tức văng lỗi traceback thay vì tự động bypass như Single Agent. Điều này đòi hỏi quy trình đặt tên và quản lý state phải cực kỳ chặt chẽ.
_________________

---

## 6. Giới hạn và điểm cần cải tiến

> Key word routing không được linh hoạt, phụ thuộc vào các list key word
