# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Lê Duy Anh
**Vai trò trong nhóm:** Worker Owner

**Ngày nộp:** 14/04/2026 
**Độ dài yêu cầu:** 500–800 từ

---

> **Lưu ý quan trọng:**
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
- File chính: `workers/retrieval.py`
- Functions tôi implement: `_get_embedding_fn(), _get_collection(), retrieve_dense(), run()`

**Cách công việc của tôi kết nối với phần của thành viên khác:**
Tôi đóng vai trò cung cấp "bộ não/ngữ cảnh" cho toàn bộ hệ thống. Khi người dùng đặt câu hỏi (qua node Supervisor), request sẽ được route đến Worker của tôi. Tôi nhận task từ AgentState, thực hiện vector search trên ChromaDB để lấy ra các đoạn tài liệu liên quan nhất (retrieved_chunks) và tên file nguồn (retrieved_sources). Sau đó, tôi cập nhật các giá trị này trở lại AgentState cùng với worker_io_logs để các node phía sau (như Generator LLM) có context chính xác nhằm trả lời câu hỏi mà không bị hallucinate.
_________________

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
commit a35a1f35898563aec7cc4274841bc420a96b406e
Author: AnhLD2809 <leduyanh2k3@gmail.com>
Date:   Tue Apr 14 17:26:53 2026 +0700

    update worker_contracts for retrieval worker

commit 0a803c6381715ce4c0599f06732a997f41fb1c12
Author: AnhLD2809 <leduyanh2k3@gmail.com>
Date:   Tue Apr 14 17:02:15 2026 +0700

    fix retrieval

commit 3b6b631f27964bead5f2aea0ec68bc1451a67863
Author: AnhLD2809 <leduyanh2k3@gmail.com>
Date:   Tue Apr 14 16:55:54 2026 +0700

    fix retrieval

commit 14b8d33503f64d4ef67b50d38707cd580c8a33a2
Author: AnhLD2809 <leduyanh2k3@gmail.com>
Date:   Tue Apr 14 16:36:58 2026 +0700

    refactor retrieval workers
_________________

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

**Quyết định:** Thiết kế hệ thống Fallback 3 cấp độ cho Embedding Function kết hợp với Global Caching (Singleton pattern).

**Lý do:**
Ban đầu, nhóm có thể chỉ dùng SentenceTransformer chạy local, nhưng việc này sẽ gây chậm máy (nếu không có GPU) hoặc thiếu thư viện. Nếu chỉ dùng OpenAI, hệ thống sẽ sập nếu hết quota hoặc mất internet.
_________________

**Trade-off đã chấp nhận:**
Sử dụng global cache trong môi trường multi-threading thực tế có thể gây rủi ro về thread-safety, nhưng trong phạm vi lab và Graph này (thực thi tuần tự), nó tối ưu hóa triệt để latency khởi tạo.
_________________

**Bằng chứng từ trace/code:**

```
def _get_embedding_fn() -> Callable[[str], List[float]]:
    """
    Khởi tạo và cache embedding function.
    Ưu tiên: Sentence Transformers (Local) → OpenAI → Random (test).
    """
    global _EMBED_FN
    if _EMBED_FN is not None:
        return _EMBED_FN

    # 1. ƯU TIÊN 1: OpenAI (Nếu có API Key)

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=openai_key)
            print("🔄 Using OpenAI for embeddings...")
            
            def embed_oai(text: str) -> List[float]:
                resp = client.embeddings.create(input=text, model="text-embedding-3-small")
                return resp.data[0].embedding
                
            _EMBED_FN = embed_oai
            return _EMBED_FN
        except ImportError:
            print("⚠️ Có OPENAI_API_KEY nhưng chưa cài thư viện `openai`. Chuyển qua Option 2...")
            pass
    else:print("ℹ️ Không tìm thấy OPENAI_API_KEY trong .env. Chuyển qua Option 2...")

    # 2. ƯU TIÊN 2: Sentence Transformers (Offline Local)
    try:
        from sentence_transformers import SentenceTransformer
        print(f"🔄 Loading SentenceTransformer model: {EMBED_MODEL_NAME}...")
        model = SentenceTransformer(EMBED_MODEL_NAME)
        
        def embed_st(text: str) -> List[float]:
            return model.encode([text])[0].tolist()
            
        _EMBED_FN = embed_st
        return _EMBED_FN
    except ImportError:
        pass


    # 3. FALLBACK: Random (Chỉ dùng cho testing khi thiếu thư viện)
    import random
    print("⚠️ WARNING: Using random embeddings (test only). Please install openai or sentence-transformers.")
    
    def embed_random(text: str) -> List[float]:
        return [random.random() for _ in range(384)]  # Trùng dimension với MiniLM hoặc có thể sửa tùy ý
        
    _EMBED_FN = embed_random
    return _EMBED_FN
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Hệ thống không lấy được dữ liệu khi chạy Retrieval Worker — Standalone Test do lệch mô hình Embedding giữa lúc Index và lúc Query.

**Symptom (pipeline làm gì sai?):**
Khi chạy test thử bằng lệnh `python workers/retrieval.py`, kết quả trả về luôn là `retrieved: 0 chunks`.
_________________

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Sự cố nằm ở cơ chế ưu tiên của hàm `_get_embedding_fn()`. Database (`day09_docs`) ban đầu được nhóm nhúng (embed) và lưu bằng mô hình Local (`all-MiniLM-L6-v2` với vector 384 chiều). Tuy nhiên, máy tôi lại đang set sẵn `OPENAI_API_KEY` trong file `.env`. Do đó, Worker tự động ưu tiên dùng mô hình `text-embedding-3-small` (1536 chiều) của OpenAI để chuyển hóa câu hỏi tìm kiếm. Việc so sánh vector 1536 chiều với database 384 chiều khiến ChromaDB không thể tính toán khoảng cách (Cosine Similarity).
_________________

**Cách sửa:**
Tôi đã xử lý bằng cách đổi Index cũng embed bằng text embbeding model của OpenAI.
_________________

**Bằng chứng trước/sau:**
Output trước khi sửa:
==================================================
Retrieval Worker — Standalone Test
==================================================

▶ Query: SLA ticket P1 là bao lâu?
🔄 Using OpenAI for embeddings...
🔄 Connecting to ChromaDB at ./chroma_db...
⚠️ Collection 'day09_docs' created but is empty. Please run index script.
  Retrieved: 0 chunks
  Sources: []

▶ Query: Điều kiện được hoàn tiền là gì?
  Retrieved: 0 chunks
  Sources: []

▶ Query: Ai phê duyệt cấp quyền Level 3?
  Retrieved: 0 chunks
  Sources: []

✅ retrieval_worker test done.

Output sau khi sửa:
==================================================
Retrieval Worker — Standalone Test
==================================================

▶ Query: SLA ticket P1 là bao lâu?
🔄 Using OpenAI for embeddings...
🔄 Connecting to ChromaDB at D:\lab9_C401_F1\lab\chroma_db...
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
_________________

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**
Tôi đã xây dựng được một module có độ bền bỉ (robustness) cao. Việc xử lý biệt lệ (Exception handling) trong hàm run() đảm bảo rằng dù quá trình retrieval gặp lỗi kỹ thuật, hệ thống vẫn ghi log vào worker_io_logs và tiếp tục chạy thay vì làm gián đoạn toàn bộ quy trình của nhóm.
_________________

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Hệ thống hiện tại mới chỉ hỗ trợ Dense Retrieval (truy vấn ngữ nghĩa). Tôi chưa tích hợp Keyword Search (BM25), dẫn đến việc tìm kiếm các từ khóa cụ thể hoặc mã số ticket đôi khi chưa đạt độ chính xác tối ưu.
_________________

**Nhóm phụ thuộc vào tôi ở đâu?** 
Nếu module Retrieval không hoạt động, Agent sẽ mất đi khả năng truy xuất kiến thức nội bộ, dẫn đến việc trả lời sai lệch hoặc hallucinate về các thông tin dự án.

_________________

**Phần tôi phụ thuộc vào thành viên khác:** 
Tôi cần dữ liệu ChomaDB từ thành viên thực hiện phần `graph.py`.

_________________

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

Tôi sẽ nâng cấp module bằng kỹ thuật **Query Decomposition (Phân rã truy vấn)** trước khi gọi ChromaDB. 

*Lý do:* Theo đối chiếu trace log và barem ở câu `gq09` (câu hỏi ghép về cả SLA P1 lẫn Level 2 Access), hệ thống đã trả lời sai điều kiện cấp quyền thành "Tech Lead phê duyệt" thay vì "Line Manager + IT Admin". Nguyên nhân do vector embedding của câu hỏi ghép bị loãng ngữ nghĩa, cộng với `top_k` nhỏ khiến ChromaDB không fetch đủ chunk từ 2 tài liệu khác nhau. Tôi sẽ dùng LLM nhỏ (như gpt-4o-mini) tách `task` gốc thành mảng `sub_queries`, retrieve độc lập từng query rồi gộp kết quả lại để loại bỏ hoàn toàn góc chết thông tin này.

_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
