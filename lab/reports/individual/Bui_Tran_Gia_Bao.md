# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Bùi Trần Gia Bảo
**Vai trò trong nhóm:** MCP Owner
**Ngày nộp:** 14/04/2026
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
>
> - Viết ở ngôi **"tôi"**, gắn với chi tiết thật của phần bạn làm
> - Phải có **bằng chứng cụ thể**: tên file, đoạn code, kết quả trace, hoặc commit
> - Nội dung phân tích phải khác hoàn toàn với các thành viên trong nhóm
> - Deadline: Được commit **sau 18:00** (xem SCORING.md)
> - Lưu file với tên: `reports/individual/[ten_ban].md` (VD: `nguyen_van_a.md`)

---

## 1. Tôi phụ trách phần nào? (100–150 từ)

> Mô tả cụ thể module, worker, contract, hoặc phần trace bạn trực tiếp làm.
> Không chỉ nói "tôi làm Sprint X" — nói rõ file nào, function nào, quyết định nào.

**Module/file tôi chịu trách nhiệm:**

- File chính: `mcp_server.py`
- Functions tôi implement: `search_kb`, `get_ticket_info`, `check_access_permission`, `create_ticket`(`@mcp.tool()`), bổ sung FastMCP, mode chạy `--serve` / `--serve-http`, và phần HITL liên quan trong `graph.py` gồm `human_review_node()` cùng logic resume trong `run_graph()`

**Cách công việc của tôi kết nối với phần của thành viên khác:** Phần tôi làm nằm ởgiữa orchestration và tool layer. `policy_tool_worker` gọi `_call_mcp_tool()` rồi dùng `dispatch_tool` từ `mcp_server.py`, nên nếu lớp MCP chưa chạy ổn thì worker policy chỉ có thể test bằng dữ liệu tự tạo. Ở `graph.py`, phần HITL tôi thêm có thể tạm dừng workflow ở `human_review`, sau đó mới tiếp tục retrieval và synthesis cho các câu có rủi ro cao. Vì tôi xong sprint của mình khá sớm, tôi còn dùng pipeline đã chạy được để hỗ trợ chạy evaluation và giúp nhóm viết tài liệu cuối giờ.

---

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

> 7450a940d7067a175fa0c6729e735a0cf879b8bb, 7043d98831f82fb9cc45e3f473c5d57dd983bee1, 03d98a3a6c026fd8c64c8f4ea9f17588aece24b4, a82bd4ca38fed5e66a7c4d9edf401ae343985142, 7f351231d32292f75363f44d6dc817d5c9328c3c, fb0c9d5321d994c3d42745da98b36d712de62dc0 và các commit khác đã bị thành `merge branch 'main' of ...`

> Một số commit khác của tôi đã được gộp vào các merge commit (merge branch 'main') do workflow của nhóm, nên không show dưới dạng commit riêng lẻ.

---

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
>
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Tôi chọn giữ MCP theo hướng mock-friendly nhưng vẫn để có thể update sang real MCP và bổ sung HITL ở graph thay vì để hệ thống chạy một mạch cho mọi câu hỏi.

**Ví dụ:**

> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
> Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
> Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**

> Phần tool business logic cơ bản đã có sẵn từ đầu, nên việc tôi làm chỉ là cho nó gần hơn với mô hình MCP thật: thêm FastMCP, thêm các wrapper @mcp.tool(), tận dụng FastMCP có sẵn để chạy ở hai chế độ --serve và --serve-http, đồng thời sửa tool_search_kb() theo hướng trả lỗi có cấu trúc thay vì trả mock chunk khi fail. Tôi cũng thêm debug log trong dispatch_tool() để lúc trace dễ biết tool nào đã được gọi. Ở graph.py tôi thêm human_review_node() và đoạn resume trong run_graph() để các câu bị route vào human_review không dừng chết giữa chừng mà có thể được duyệt rồi chạy tiếp. Tôi chọn cách này vì lab chỉ có ít giờ. Nếu ép tất cả phải là MCP thật ngay từ đầu thì rất tốn thời gian setup, còn nếu bỏ HITL thì workflow risk cao mà lại lại thiếu an toàn.

---

**Trade-off đã chấp nhận:**

> Cách này thực dụng hơn là “thuần MCP” hoàn toàn. `policy_tool_worker` vẫn gọi `dispatch_tool()` trong process, nên hệ thống chưa tách client-server hoàn toàn. HITL cũng làm graph phức tạp hơn, nhưng đổi lại giúp xử lý được các route có rủi ro cao.

---

**Bằng chứng từ trace/code:**

```python
@mcp.tool()
def search_kb(query: str, top_k: int = 3) -> dict:
    return tool_search_kb(query=query, top_k=top_k)
```

```python
if "--serve" in sys.argv:
  print("Starting real MCP server over stdio...")
  mcp.run()
elif "--serve-http" in sys.argv:
  print("Starting real MCP server over Streamable HTTP...")
  mcp.run(transport="streamable-http")
```

```python
def human_review_node(state: AgentState) -> AgentState:
    state["hitl_triggered"] = True
    state["history"].append("[human_review] HITL triggered — awaiting human input")
    state["workers_called"].append("human_review")
    state["supervisor_route"] = "retrieval_worker"
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Khi retrieval luôn trả về 0 chunks và không có evidence.

**Symptom (pipeline làm gì sai?):**

> Index build thành công nhưng khi chạy workers/retrieval.py thì worker không lấy được chunk nào mà không trả về lỗi gì và pipeline phía sau không có evidence để tổng hợp câu trả lời. Trong log trước khi sửa, cả ba query test đều trả về

```
Retrieved: 0 chunks và Sources: [].
```

---

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

> Lỗi nằm ở bước indexing và embedding consistency. Index trước đó được build bằng Sentence Transformer, nhưng lúc retrieve thì worker lại dùng OpenAI embedding text-embedding-3-small. Vì collection đang expect vector dimension 384 nhưng query lại dùng vector 1536 nên ChromaDB không thể trả kết quả. Đây không phải lỗi routing hay synthesis mà là lỗi không đồng nhất embedding giữa lúc build index và lúc query.

---

**Cách sửa:**

> Tôi đồng bộ lại embedding giữa index và retrieval, rồi test lại trực tiếp bằng standalone retrieval worker. Sau khi sửa, cùng các query cũ, retrieval đã trả được 2 chunks cho mỗi câu và có source rõ ràng như support/sla-p1-2026.pdf, policy/refund-v4.pdf, và it/access-control-sop.md. Việc này rất quan trọng vì nếu retrieval không có evidence thì các worker sau vẫn chạy nhưng câu trả lời sẽ yếu hoặc dễ abstain sai.

---

**Bằng chứng trước/sau:**

> Trước khi sửa:

```
$ python workers/retrieval.py
==================================================
Retrieval Worker — Standalone Test
==================================================

▶ Query: SLA ticket P1 là bao lâu?
🔄 Using OpenAI for embeddings...
🔄 Connecting to ChromaDB at ./chroma_db...
⚠️ ChromaDB query failed: Collection expecting embedding with dimension of 384, got 1536
  Retrieved: 0 chunks
  Sources: []

▶ Query: Điều kiện được hoàn tiền là gì?
⚠️ ChromaDB query failed: Collection expecting embedding with dimension of 384, got 1536
  Retrieved: 0 chunks
  Sources: []

▶ Query: Ai phê duyệt cấp quyền Level 3?
⚠️ ChromaDB query failed: Collection expecting embedding with dimension of 384, got 1536
  Retrieved: 0 chunks
  Sources: []

✅ retrieval_worker test done.
```

> Sau Khi sửa:

```
$ python workers/retrieval.py
==================================================
Retrieval Worker — Standalone Test
==================================================

▶ Query: SLA ticket P1 là bao lâu?
🔄 Using OpenAI for embeddings...
🔄 Connecting to ChromaDB at ./chroma_db...
  Retrieved: 2 chunks
    1. [0.704] support/sla-p1-2026.pdf: === Phần 2: SLA theo mức độ ưu tiên ===   Ticket P1: - Phản hồi ban đầu (first r...
    2. [0.570] support/sla-p1-2026.pdf: === Phần 3: Quy trình xử lý sự cố P1 ===   Bước 1: Tiếp nhận On-call engineer nh...
  Sources: ['support/sla-p1-2026.pdf']

▶ Query: Điều kiện được hoàn tiền là gì?
  Retrieved: 2 chunks
    1. [0.629] policy/refund-v4.pdf: === Điều 2: Điều kiện được hoàn tiền ===  Khách hàng được quyền yêu cầu hoàn tiề...
    2. [0.542] policy/refund-v4.pdf: === Điều 5: Hình thức hoàn tiền ===  - Hoàn tiền qua phương thức thanh toán gốc:...
  Sources: ['policy/refund-v4.pdf']

▶ Query: Ai phê duyệt cấp quyền Level 3?
  Retrieved: 2 chunks
    1. [0.535] it/access-control-sop.md: === Section 2: Phân cấp quyền truy cập ===   Level 1 - Read Only: Áp dụng cho: T...
    2. [0.510] it/access-control-sop.md: === Section 3: Quy trình yêu cầu cấp quyền ===   Bước 1: Nhân viên tạo Access Re...
  Sources: ['it/access-control-sop.md']

✅ retrieval_worker test done.
```

---

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

> Tôi đã hoàn thành phần của mình khá sớm nên ngoài MCP và HITL, tôi còn có thời gian hỗ trợ nhóm test lại flow chạy và debug ở những phần khác.

---

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

> Tôi không phụ trách phần policy logic, nên có lúc phần MCP của tôi phải tự test riêng thay vì gắn được ngay vào workflow chung.

---

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

> Ở cuối giờ, khi cần chạy evaluation và hoàn thiện tài liệu, nhóm cần phần tôi để workflow có thể chạy qua tool layer và có thêm dữ liệu thực tế để đối chiếu.

---

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

> Tôi phụ thuộc vào phần policy_tool.py để dùng MCP vào đúng flow thật, và cũng phải đợi evaluation chạy xong để test lại toàn bộ workflow thay vì chỉ test riêng từng phần.

---

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nếu có thêm 2 giờ, tôi sẽ nối check_access_permission vào policy_tool_worker thay vì chỉ để tool tồn tại ở mcp_server.py. Lý do là hiện tool này đã có schema và logic emergency access khá rõ, nhưng policy_tool_worker chủ yếu mới gọi search_kb và get_ticket_info. Với các câu multi-hop về access như gq03 hoặc gq09, việc dùng trực tiếp tool này sẽ giúp policy worker bớt phụ thuộc vào LLM và trả lời nhất quán hơn.
