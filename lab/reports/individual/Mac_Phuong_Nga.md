# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Mạc Phương Nga
**Vai trò trong nhóm:** Worker Owner
**Ngày nộp:** 14/04/2026
**Độ dài yêu cầu:** 500–800 từ


## 1. Tôi phụ trách phần nào? (100–150 từ)

Tôi phụ trách module `workers/policy_tool.py`, một worker chính trong hệ thống multi-agent orchestration. Module này xử lý việc kiểm tra và phân tích chính sách doanh nghiệp dựa trên context được cung cấp từ retrieval worker, và có khả năng gọi MCP tools khi cần thiết để lấy thêm thông tin.

**Module/file tôi chịu trách nhiệm:**
- File chính: `workers/policy_tool.py`
- Functions tôi implement: `analyze_policy()` (phân tích policy bằng LLM hoặc rule-based fallback, `_call_mcp_tool()` (gọi MCP tools như search_kb và get_ticket_info), `run()` (entry point của worker), và `_rule_based_fallback()` (logic backup khi LLM không khả dụng).

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Module của tôi nhận `retrieved_chunks` từ `retrieval_worker` để phân tích policy, và output `policy_result` cùng `mcp_tools_used` để `synthesis_worker` tổng hợp câu trả lời cuối cùng. Nếu cần tool, tôi gọi MCP server để lấy dữ liệu bổ sung, kết nối với phần MCP implementation của nhóm.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
File `workers/policy_tool.py` có comment "# workers/policy_tool.py — Policy & Tool Worker" và tên worker là "policy_tool_worker". Trong test standalone, có 3 test cases với output policy_applies và exceptions. Trace `run_20260414_172352.json` cho thấy worker được gọi và policy_result được set đúng.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:** Tôi chọn sử dụng LLM (GPT-4o-mini) để phân tích policy với fallback sang rule-based khi không có API key hoặc lỗi LLM.

**Ví dụ:**
> "Tôi chọn dùng LLM cho policy analysis thay vì chỉ rule-based vì độ chính xác cao hơn, nhưng thêm fallback để đảm bảo reliability."

**Lý do:**
Tôi quyết định dùng LLM vì nó có thể hiểu ngữ cảnh phức tạp và ngoại lệ trong policy, như "Flash Sale không hoàn tiền" hoặc "sản phẩm kỹ thuật số không hoàn tiền", dựa trên prompt chi tiết. Lựa chọn thay thế là chỉ dùng rule-based (keyword matching), nhưng nó kém chính xác với câu hỏi mơ hồ. LLM cho kết quả JSON chuẩn với exceptions_found, dễ tích hợp. Fallback đảm bảo hệ thống không fail khi API key thiếu.

**Trade-off đã chấp nhận:**
LLM chậm hơn (~800ms vs ~5ms rule-based), nhưng chính xác hơn. Rule-based nhanh nhưng miss ngoại lệ phức tạp. Tôi chấp nhận latency tăng để có accuracy cao.

**Bằng chứng từ trace/code:**
 
``` python
def analyze_policy(task: str, chunks: list) -> dict:
    """
    Phân tích policy bằng LLM. Trả về format chuẩn để Synthesis dễ dàng đọc.
    """
    sources = list({c.get("source", "unknown") for c in chunks if c})
    context_text = "\n".join([f"[{c.get('source', 'unknown')}] {c.get('text', '')}" for c in chunks])

    api_key = os.getenv("OPENAI_API_KEY")
    
    # NẾU KHÔNG CÓ API KEY HOẶC LỖI -> FALLBACK VỀ RULE-BASED CŨ CỦA BẠN
    if not api_key:
        return _rule_based_fallback(task, chunks, sources)

    client = OpenAI(api_key=api_key)

    system_prompt = """Bạn là một Chuyên gia phân tích Chính sách Doanh nghiệp.
        Nhiệm vụ của bạn là đối chiếu 'Task' (yêu cầu của khách hàng/nhân viên) với 'Context' (quy định công ty) để xem yêu cầu có được chấp thuận hay không.

        HÃY CHÚ Ý ĐẶC BIỆT CÁC NGOẠI LỆ:
        1. Đơn hàng "Flash Sale" -> KHÔNG hoàn tiền.
        2. Sản phẩm kỹ thuật số (license key, subscription) -> KHÔNG hoàn tiền.
        3. Sản phẩm đã kích hoạt/đăng ký -> KHÔNG hoàn tiền.
        4. Chú ý mốc thời gian: Nếu Task nhắc đến ngày trước 01/02/2026, ghi chú là "Áp dụng chính sách v3 (ngoài tài liệu hiện tại)".

        Trích xuất thông tin và CHỈ trả về định dạng JSON sau (không markdown, không giải thích thêm):
        {
            "policy_applies": true/false,
            "policy_name": "Tên chính sách đang xét (ví dụ: Chính sách hoàn tiền v4)",
            "exceptions_found": [
                {"type": "tên_ngoại_lệ", "rule": "quy định bị vi phạm", "source": "tên file nguồn"}
            ],
            "policy_version_note": "Ghi chú về version nếu có, nếu không để rỗng",
            "explanation": "Giải thích ngắn gọn tại sao"
        }
        """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", # Dùng model mini cho rẻ và nhanh
            response_format={"type": "json_object"}, # Bắt buộc trả JSON
            temperature=0.1, # Nhiệt độ thấp để trả lời mang tính logic, không sáng tạo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Task: {task}\n\nContext:\n{context_text}"}
            ]
        )
        
        # Parse JSON từ LLM
        result = json.loads(response.choices[0].message.content)
        result["source"] = sources # Gắn đính kèm danh sách file nguồn
        
        # Đảm bảo policy_applies là boolean chuẩn xác (nếu có exceptions thì ko apply)
        if result.get("exceptions_found") and len(result["exceptions_found"]) > 0:
            result["policy_applies"] = False
            
        return result

    except Exception as e:
        print(f"[Policy Worker] LLM Analysis Error: {e}. Falling back to Rule-based.")
        return _rule_based_fallback(task, chunks, sources)
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

**Lỗi:** Chạy retrieval với các test cases luôn trả về số lượng Retrieved Chunks = 0.

**Symptom (pipeline làm gì sai?):**
Nhóm sử dụng `index.py` như trong hướng dẫn README (sử dụng embedding model `all-MiniLM-L6-v2` để index tài liệu), nhưng trong `retrieval_worker.py`, embedding model được set là `text-embedding-3-small`. Do đó, khi retrieval worker gọi embedding với model `text-embedding-3-small`, nó không tìm thấy vector nào trong index được tạo bằng `all-MiniLM-L6-v2`, dẫn đến kết quả trả về luôn là 0 chunks.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Vấn đề nằm ở việc indexing và retrieval sử dụng embedding model khác nhau, số chiều khác nhau -> dẫn đến mismatch vector và không trả về kết quả nào.

**Cách sửa:**
Tôi sửa bằng cách đồng bộ embedding model trong `index.py` và `retrieval_worker.py` về cùng một model `text-embedding-3-small`.

**Bằng chứng trước/sau:**

> Trước khi sửa:

```log
▶ Query: SLA ticket P1 là bao lâu?
🔄 Using OpenAI for embeddings...
🔄 Connecting to ChromaDB at ./chroma_db...
  Retrieved: 0 chunks
  Sources: []

▶ Query: Điều kiện được hoàn tiền là gì?
  Retrieved: 0 chunks
  Sources: []

▶ Query: Ai phê duyệt cấp quyền Level 3?
  Retrieved: 0 chunks
  Sources: []

✅ retrieval_worker test done.
```

> Sau khi sửa:

```log
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
```

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

**Tôi làm tốt nhất ở điểm nào?**
Tôi implement logic policy analysis linh hoạt với LLM và fallback, đảm bảo hệ thống robust khi API fail. Code có test standalone với 3 cases, output đúng policy_applies và exceptions.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Logic fallback còn đơn giản, chỉ keyword, không handle context phức tạp.

**Nhóm phụ thuộc vào tôi ở đâu?**
Policy check là core cho questions về refund/policy. Nếu tôi chưa xong, synthesis_worker thiếu policy_result, dẫn đến answer sai hoặc incomplete.

**Phần tôi phụ thuộc vào thành viên khác:**
Tôi cần retrieved_chunks từ retrieval_worker để analyze. Nếu retrieval fail, tôi phải call MCP search_kb, phụ thuộc vào MCP server implementation.
---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ implement real MCP client thay vì import trực tiếp mcp_server, vì trace `run_20260414_172352.json` cho mcp_tools_used với "Simulated success" message, nghĩa là chưa real call. Dùng HTTP requests để call MCP server, giảm coupling và cho phép deploy riêng. Điều này fix "MCP Server not found" error trong _call_mcp_tool().

---

