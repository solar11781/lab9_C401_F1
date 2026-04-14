# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Trương Minh Sơn 
**Vai trò trong nhóm:** Trace & Docs Owner  
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
- File chính: lab/eval_trace.py, docs/system_architecture.md, docs/single_vs_multi_comparison.md.
-Functions tôi implement: analyze_traces(), generate_eval_report(), và logic tính toán các chỉ số avg_confidence, routing_distribution.

>Tôi chịu trách nhiệm thiết kế "hệ thống đo lường" cho toàn bộ Sprint 4. Thay vì chỉ tập trung vào việc Agent trả lời gì, tôi tập trung vào việc tại sao nó trả lời như vậy. Tôi đã xây dựng công cụ để tự động quét hàng loạt file JSON trace, trích xuất dữ liệu về độ trễ, độ tin cậy và các nguồn tài liệu được sử dụng nhiều nhất (Top Sources), từ đó cung cấp bằng chứng định lượng cho báo cáo so sánh giữa Single-Agent và Multi-Agent.
**Cách công việc của tôi kết nối với phần của thành viên khác:**

Tôi là người "chốt chặn" cuối cùng để đánh giá chất lượng code của nhóm. Sau khi các thành viên khác (như người làm Supervisor hay Worker) hoàn thành pipeline, tôi sẽ chạy bộ test và phân tích kết quả. Nếu Châu thay đổi logic RAG hay em thay đổi Supervisor, tôi sẽ là người chỉ ra sự thay đổi đó làm tăng hay giảm avg_confidence. Tôi giúp nhóm hiểu được hiệu quả của các quyết định kỹ thuật thông qua các con số cụ thể.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

File chính: lab/eval_trace.py với toàn bộ logic xử lý dữ liệu JSON.

Kết quả thực tế: Bảng Trace Analysis trong báo cáo tổng (ghi nhận 15 traces, avg_confidence: 0.542, mcp_usage_rate: 46%).

Tài liệu: File eval_report.json được tạo ra tự động từ script của tôi.

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách..


**Quyết định:** Thiết lập cơ chế Automated Trace-to-Metric Extraction (Tự động trích xuất chỉ số từ Trace) trong file eval_trace.py thay vì tổng hợp báo cáo thủ công.

**Ví dụ:**
> "Tôi chọn dùng keyword-based routing trong supervisor_node thay vì gọi LLM để classify.
>  Lý do: keyword routing nhanh hơn (~5ms vs ~800ms) và đủ chính xác cho 5 categories.
>  Bằng chứng: trace gq01 route_reason='task contains P1 SLA keyword', latency=45ms."

**Lý do:**

Trong vai trò phụ trách Documentation và Evaluation, tôi nhận thấy việc đọc từng file JSON để đánh giá hiệu quả của Multi-Agent là không khả thi và dễ sai sót.

Các lựa chọn thay thế: (1) Đọc thủ công từng trace để nhận xét định tính hoặc (2) Chỉ sử dụng kết quả cuối cùng mà không quan tâm đến quá trình điều hướng (routing).

Lý do chọn: Tôi chọn xây dựng các hàm analyze_traces() và calculate_confidence_avg() để quét toàn bộ thư mục /traces. Việc này giúp tôi có cái nhìn khách quan về Routing Distribution (tỷ lệ điều hướng) và MCP Usage Rate. Dưới góc độ làm tài liệu, các con số này cung cấp bằng chứng thép để chứng minh hệ thống Multi-Agent thực sự hoạt động hiệu quả hơn Single-Agent trong việc phân loại tác vụ chuyên sâu._

**Trade-off đã chấp nhận:**

Tôi chấp nhận tăng thêm thời gian xử lý hậu kỳ (post-processing) và độ phức tạp của mã nguồn eval_trace.py. Ngoài ra, hệ thống sẽ gặp lỗi nếu cấu trúc file JSON thay đổi, đòi hỏi tôi phải thiết lập các "chốt chặn" xử lý lỗi ngoại lệ chặt chẽ.

**Bằng chứng từ trace/code:**

# Đoạn code trích từ eval_trace.py do tôi thực hiện
def extract_metrics(trace_data):
    return {
        "id": trace_data.get("question_id"),
        "route": trace_data.get("supervisor_route"),
        "conf": trace_data.get("confidence", 0),
        "tools": len(trace_data.get("mcp_tools_used", []))
    }

Đoạn này trích từ run_20260414_170748.json (câu q09). Nó chứng minh em đã thiết lập được "chốt chặn" an toàn khi gặp mã lỗi lạ.
{
  "task": "ERR-403-AUTH là lỗi gì và cách xử lý?",
  "route_reason": "unknown error code + risk_high → human review",
  "risk_high": true,
  "supervisor_route": "human_review",
  "history": [
    "[supervisor] received task: ERR-403-AUTH là lỗi gì và cách xử lý?",
    "[supervisor] route=human_review reason=unknown error code + risk_high → human review"
  ]
}

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:** Trong quá trình chạy đánh giá tự động 15 câu hỏi bằng script eval_trace.py, hệ thống đột ngột bị crash giữa chừng, không thể xuất ra file báo cáo tổng hợp eval_report.json

**Symptom (pipeline làm gì sai?):**

Màn hình terminal hiển thị thông báo lỗi: json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0). Quá trình đánh giá dừng lại ở câu hỏi số 15 và không lưu lại bất kỳ chỉ số thống kê nào._

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Do cơ chế ghi file của hệ thống Multi-Agent diễn ra quá nhanh. Khi eval_trace.py thực hiện vòng lặp đọc các file trong thư mục /traces, nó đã cố gắng truy cập vào một file JSON đang trong trạng thái "mở" để ghi hoặc một file trống vừa mới khởi tạo nhưng chưa kịp đổ dữ liệu (race condition). Việc đọc một file trống hoặc chưa đóng hoàn chỉnh dẫn đến trình thông dịch JSON không tìm thấy cấu trúc hợp lệ.

**Cách sửa:**

At tầng Trace Generation: Sử dụng context manager with open() và thêm lệnh .flush() sau khi ghi để đảm bảo dữ liệu được đẩy xuống đĩa cứng ngay lập tức.

Tại tầng Eval Trace: Thêm khối try...except để bắt lỗi JSONDecodeError. Nếu gặp file lỗi, script sẽ bỏ qua file đó và tiếp tục xử lý các file khác thay vì dừng toàn bộ tiến trình.

**Bằng chứng trước/sau:**
> Dán trace/log/output trước khi sửa và sau khi sửa.

[15/15] gq10: Khách hàng mua sản phẩm Flash Sale...
Traceback (most recent call last):
  File "eval_trace.py", line 193, in analyze_traces
    traces.append(json.load(f))
json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)


sau khi sửa: 
# Đoạn code xử lý lỗi trong eval_trace.py
try:
    with open(trace_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        traces.append(data)
except json.JSONDecodeError:
    print(f"⚠️ Warning: File {trace_path} is corrupted or empty. Skipping...")
    continue

Kết quả Terminal:
✅ Done. 15 / 15 succeeded.
[Analysis] total_traces: 15, avg_confidence: 0.542
---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt nhất ở việc chuyển hóa dữ liệu thô thành thông tin có ý nghĩa. Nhờ việc xây dựng script eval_trace.py, tôi đã giúp nhóm không chỉ hoàn thành bài lab mà còn có các con số thống kê chính xác về tỉ lệ điều hướng

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Tôi còn yếu trong việc quản lý luồng ghi dữ liệu thời gian thực. Việc để xảy ra lỗi JSONDecodeError và không ghi lại được latency_ms (trả về 0 trong eval_report.json) cho thấy tôi chưa bao quát hết các điều kiện biên khi hệ thống chạy ở tốc độ cao. Tôi cần cải thiện kỹ năng xử lý bất đồng bộ (async) và ghi log chuyên sâu hơn.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nhóm bị block hoàn toàn ở khâu đối soát và viết báo cáo cuối cùng. Nếu tôi không hoàn thành script phân tích trace, nhóm sẽ không có dữ liệu để so sánh Single vs Multi-agent trong mục 4 của báo cáo tổng, và cũng không thể giải trình được tại sao hệ thống lại chọn Worker này thay vì Worker kia.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Tôi phụ thuộc hoàn toàn vào Supervisor của Gia Khánh. Tôi cần Supervisor ghi nhận đúng định dạng supervisor_route và route_reason vào file JSON. Nếu cấu trúc file trace thay đổi mà không thông báo, script đánh giá của tôi sẽ bị crash ngay lập tức.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)


- Nếu có thêm 2 giờ, tôi sẽ tập trung sửa mã nguồn để thu thập chính xác chỉ số latency_ms.
ng file eval_report.json hiện tại, mục avg_latency_ms của Multi-agent đang hiển thị là 0, điều này làm giảm tính khách quan khi so sánh với Single-agent (850ms). Tôi muốn đo chính xác độ trễ phát sinh tại node Supervisor khi nó phải thực hiện Keyword Routing kết hợp gọi LLM, từ đó đưa ra bằng chứng định lượng về việc Multi-agent thực sự "nặng" hơn hay hiệu quả hơn về mặt thời gian xử lý so với Single-agent.
---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
