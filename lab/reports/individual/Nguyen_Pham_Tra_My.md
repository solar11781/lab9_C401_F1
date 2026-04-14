# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Nguyễn Phạm Trà My 
**Vai trò trong nhóm:** Worker Owner and Docs Owner  
**Ngày nộp:** 14/4/2026 
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

**Module/file tôi chịu trách nhiệm: Trong bài lab này, tôi phụ trách xây dựng synthesis worker, được implement trong file workers/synthesis.py. Đây là thành phần chịu trách nhiệm tổng hợp câu trả lời cuối cùng dựa trên dữ liệu đã được xử lý từ các worker trước đó.**
- File chính: `synthesis.py và single_vs_multi_comparison.md`
- Functions tôi implement: `_build_context(): xây dựng context từ chunks và policy
_call_llm(): gọi LLM (OpenAI hoặc Gemini)
_estimate_confidence(): tính toán độ tin cậy
synthesize(): tổng hợp answer, sources và confidence
run(): entry point của worker trong graph`

**Cách công việc của tôi kết nối với phần của thành viên khác: Worker của tôi đóng vai trò là bước cuối trong pipeline. Sau khi nhận dữ liệu từ các worker trước, tôi build context, gọi LLM để sinh câu trả lời và trả về final_answer, sources, và confidence vào state để hiển thị cho người dùng.**

_________________

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**
e3f496a update synthesis
_________________

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:**  
Tôi quyết định chuẩn hóa cách quản lý API key và cơ chế gọi LLM trong `synthesis_worker` bằng cách sử dụng biến môi trường (`dotenv`) kết hợp với cơ chế fallback giữa nhiều LLM provider (OpenAI → Gemini).

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

---

**Lý do:**

Trong quá trình làm việc với `synthesis.py`, tôi nhận thấy phần gọi LLM là điểm nhạy cảm nhất của worker vì:
- phụ thuộc trực tiếp vào API key
- nếu lỗi sẽ ảnh hưởng toàn bộ pipeline (không có answer)

Do đó, tôi không chỉ dừng ở việc import `dotenv`, mà còn kiểm soát toàn bộ flow gọi LLM theo hướng **an toàn và fail-safe**:

1. API key được lấy từ environment thay vì hard-code → tránh lộ key khi commit  
2. Nếu OpenAI fail (thiếu key / lỗi runtime) → fallback sang Gemini  
3. Nếu cả hai đều fail → trả về message lỗi rõ ràng thay vì hallucinate  

Một lựa chọn đơn giản hơn là chỉ dùng 1 provider (OpenAI), tuy nhiên cách này khiến hệ thống dễ bị “single point of failure”.



**Trade-off đã chấp nhận:**
- Code phức tạp hơn do phải xử lý nhiều nhánh `try/except`  
- Output có thể không hoàn toàn consistent giữa các model  
- Không kiểm soát được chất lượng giữa các provider (OpenAI vs Gemini)  

Tuy nhiên, tôi ưu tiên **độ ổn định của hệ thống** hơn là sự đơn giản trong code.
_________________

**Bằng chứng từ trace/code:**

```
from dotenv import load_dotenv
load_dotenv()
def _call_llm(messages: list) -> str:
    """
    Gọi LLM để tổng hợp câu trả lời.
    TODO Sprint 2: Implement với OpenAI hoặc Gemini.
    """
    # Option A: OpenAI
    try:
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.1,  # Low temperature để grounded
            max_tokens=500,
        )
        return response.choices[0].message.content
    except Exception:
        pass

    # Option B: Gemini
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        model = genai.GenerativeModel("gemini-1.5-flash")
        combined = "\n".join([m["content"] for m in messages])
        response = model.generate_content(combined)
        return response.text
    except Exception:
        pass

    # Fallback: trả về message báo lỗi (không hallucinate)
    return "[SYNTHESIS ERROR] Không thể gọi LLM. Kiểm tra API key trong .env."
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** 
Lỗi đọc file trace trong `eval_trace.py` gây crash chương trình với `UnicodeDecodeError`.

---

**Symptom (pipeline làm gì sai?):**

Sau khi chạy thành công toàn bộ 15 câu hỏi, chương trình bị crash ở bước phân tích trace mặc dù pipeline chính (retrieval, policy, synthesis) đều hoạt động bình thường và trả về kết quả, nhưng hệ thống không thể hoàn tất bước `analyze_traces()`.

_________________

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**
Nguyên nhân nằm ở việc đọc file trace bằng encoding mặc định của Windows (`cp1252`), trong khi nội dung file trace chứa các ký tự UTF-8 (có thể đến từ response của LLM).
_________________

**Cách sửa:**
Cụ thể, trong `eval_trace.py`, đoạn code đọc file:

```python
traces.append(json.load(f))
_________________

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.
Trước: 
✅ Done. 15 / 15 succeeded.
Traceback (most recent call last):
  File "C:\Users\2tmy\Desktop\AI_Thuc_Chien\lab9_C401_F1\lab\eval_trace.py", line 355, in <module>
    metrics = analyze_traces()
  File "C:\Users\2tmy\Desktop\AI_Thuc_Chien\lab9_C401_F1\lab\eval_trace.py", line 193, in analyze_traces
    traces.append(json.load(f))
                  ~~~~~~~~~^^^
  File "C:\Users\2tmy\AppData\Local\Python\pythoncore-3.14-64\Lib\json\__init__.py", line 298, in load
    return loads(fp.read(),
                 ~~~~~~~^^
  File "C:\Users\2tmy\AppData\Local\Python\pythoncore-3.14-64\Lib\encodings\cp1252.py", line 23, in decode
    return codecs.charmap_decode(input,self.errors,decoding_table)[0]
           ~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d in position 443: character maps to <undefined>

Sau:
✅ Done. 15 / 15 succeeded.

📊 Trace Analysis:
  total_traces: 60
  routing_distribution:
    retrieval_worker: 28/60 (46%)
    policy_tool_worker: 28/60 (46%)
    human_review: 4/60 (6%)
  avg_confidence: 0.525
  avg_latency_ms: 0
  mcp_usage_rate: 28/60 (46%)
  hitl_rate: 0/60 (0%)
  top_sources:
    • ('support/sla-p1-2026.pdf', 16)
    • ('it/access-control-sop.md', 8)
    • ('hr/leave-policy-2026.pdf', 8)
    • ('support/helpdesk-faq.md', 4)

📄 Eval report → artifacts/eval_report.json

✅ Sprint 4 complete!
   Next: Điền docs/ templates và viết reports/                                              

_________________

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**
Tôi cho rằng điểm mạnh nhất của mình là đảm bảo synthesis worker hoạt động đúng vai trò “grounded generation”. Tôi đã thiết kế prompt và logic xử lý để hệ thống chỉ trả lời dựa trên context, từ đó giảm nguy cơ hallucination. Ngoài ra, tôi cũng đảm bảo worker trả về đầy đủ các trường cần thiết trong state như final_answer, sources, confidence, và worker_io_logs, giúp việc debug dễ dàng hơn.
_________________

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**
Tuy nhiên, phần còn hạn chế là cách tính confidence hiện tại vẫn còn đơn giản. Hàm _estimate_confidence() chủ yếu dựa vào average score của chunks và penalty từ policy exception, chưa phản ánh đầy đủ chất lượng của câu trả lời.
_________________

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_
Nhóm phụ thuộc vào tôi ở bước cuối cùng của pipeline. Nếu synthesis worker sai, toàn bộ kết quả trả về cho user sẽ không chính xác dù các bước trước đã đúng.
_________________

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_
Ngược lại, tôi phụ thuộc vào retrieval worker để cung cấp đúng dữ liệu và policy worker để xác định các ngoại lệ.
_________________

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*
Nếu có thêm thời gian, tôi sẽ cải thiện phần confidence scoring.

Hiện tại, hàm _estimate_confidence() chỉ dựa trên:

average score của chunks
penalty từ policy exception

Tôi sẽ mở rộng bằng cách:

kiểm tra xem answer có citation hay không
đánh giá độ đầy đủ của câu trả lời
hoặc sử dụng LLM để đánh giá answer dựa trên context

Điều này sẽ giúp confidence phản ánh chính xác hơn chất lượng thực tế của hệ thống.
_________________

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
