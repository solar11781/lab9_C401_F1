# Báo Cáo Cá Nhân — Lab Day 09: Multi-Agent Orchestration

**Họ và tên:** Lại Gia Khánh
**Vai trò trong nhóm:** Supervisor Owner
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
- File chính: `graph.py`
- Functions tôi implement: `supervisor_node(), build_graph()`

**Cách công việc của tôi kết nối với phần của thành viên khác:**

Phần tôi phụ trách đóng vai trò orchestrator trung tâm của toàn bộ hệ thống agent. Cụ thể, trong supervisor_node() tôi triển khai routing logic để phân tích task đầu vào và quyết định worker nào sẽ xử lý tiếp theo (retrieval, policy tool hoặc human review). Sau đó, trong build_graph() tôi thiết lập cấu trúc workflow bằng StateGraph, kết nối các node và định nghĩa conditional edges để chuyển trạng thái giữa các worker. Phần này liên kết trực tiếp với các worker do thành viên khác phát triển, như retrieval_worker, policy_tool_worker và synthesis_worker. Các worker đó xử lý nghiệp vụ cụ thể và trả kết quả về AgentState, sau đó graph tiếp tục chuyển sang bước tiếp theo.

**Bằng chứng (commit hash, file có comment tên bạn, v.v.):**

- https://github.com/solar11781/lab9_C401_F1/commit/2eeb12b48be7fb0199ed265df1c822779ec50516

---

## 2. Tôi đã ra một quyết định kỹ thuật gì? (150–200 từ)

> Chọn **1 quyết định** bạn trực tiếp đề xuất hoặc implement trong phần mình phụ trách.
> Giải thích:
> - Quyết định là gì?
> - Các lựa chọn thay thế là gì?
> - Tại sao bạn chọn cách này?
> - Bằng chứng từ code/trace cho thấy quyết định này có effect gì?

**Quyết định:**
Tôi quyết định triển khai keyword-based routing trong supervisor_node() để xác định worker phù hợp thay vì sử dụng LLM để phân loại yêu cầu của người dùng. Trong file graph.py, supervisor phân tích task đầu vào bằng cách kiểm tra các keyword như "refund", "hoàn tiền", "policy" để route sang policy_tool_worker, các keyword như "p1", "ticket", "escalation" để route sang retrieval_worker, và các pattern như "err-" để chuyển sang human_review. Logic này được thực hiện trực tiếp trong function supervisor_node() trước khi graph chuyển sang bước route_decision() và worker tương ứng.

**Lý do:**

Tôi chọn keyword routing vì nó nhanh, đơn giản và dễ kiểm soát trong giai đoạn prototype. Việc kiểm tra keyword chỉ mất vài mili-giây và không cần gọi API ngoài. Bằng chứng trong code là route_reason được ghi vào history và AgentState, ví dụ "task contains policy/access keyword" hoặc "knowledge lookup (SLA / ticket / docs)". Trong trace của graph, quyết định này giúp route được xác định ngay ở bước supervisor trước khi worker được gọi, giúp pipeline chạy nhanh và rõ ràng.

**Trade-off đã chấp nhận:**

Cách tiếp cận này kém linh hoạt hơn so với LLM classification vì nó phụ thuộc vào danh sách keyword cố định. Nếu người dùng diễn đạt câu hỏi theo cách khác hoặc dùng từ đồng nghĩa, supervisor có thể route sai worker. Tuy nhiên, trade-off này được chấp nhận vì mục tiêu của hệ thống hiện tại là xây dựng một workflow agent ổn định và dễ debug, trước khi mở rộng sang routing thông minh hơn bằng LLM trong các phiên bản sau.

**Bằng chứng từ trace/code:**

```
    policy_keywords = [
        "hoàn tiền", "refund", "policy", "flash sale", "license",
        "cấp quyền", "access", "access level", "level 3",
    ]    
    risk_keywords = ["emergency", "khẩn cấp", "2am", "không rõ", "err-"]
    retrieval_keywords = ["p1", "escalation", "sla", "ticket"]

    if any(kw in task for kw in retrieval_keywords):
        route = "retrieval_worker"
        route_reason = "knowledge lookup (SLA / ticket / docs)"

    elif any(kw in task for kw in policy_keywords):
        route = "policy_tool_worker"
        route_reason = f"task contains policy/access keyword"
        needs_tool = True
    
    if any(kw in task for kw in risk_keywords):
        risk_high = True
        route_reason += " | risk_high flagged"
```

---

## 3. Tôi đã sửa một lỗi gì? (150–200 từ)

> Mô tả 1 bug thực tế bạn gặp và sửa được trong lab hôm nay.
> Phải có: mô tả lỗi, symptom, root cause, cách sửa, và bằng chứng trước/sau.

**Lỗi:**
Routing trong supervisor_node() khiến một số query liên quan đến incident (P1) bị route sai sang policy_tool_worker.

**Symptom (pipeline làm gì sai?):**

Khi chạy query "Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?", pipeline trả về "Route: policy_tool_worker". Trong khi query này thực chất liên quan đến incident P1, nên hệ thống cần truy xuất tài liệu hướng dẫn xử lý sự cố. Vì vậy worker đúng phải là retrieval_worker.

**Root cause (lỗi nằm ở đâu — indexing, routing, contract, worker logic?):**

Lỗi nằm ở thứ tự kiểm tra keyword trong routing logic của supervisor_node(). Trong code ban đầu, hệ thống kiểm tra policy_keywords trước retrieval_keywords. Vì query chứa các keyword như "cấp quyền" và "level 3", điều kiện policy được match trước và route sang policy_tool_worker, dù trong câu hỏi cũng có "P1".

**Cách sửa:**

Tôi sửa bằng cách đổi thứ tự ưu tiên trong routing logic, kiểm tra retrieval_keywords trước policy_keywords. Điều này đảm bảo các query liên quan đến incident (p1, ticket, sla, escalation) luôn được route đến retrieval_worker trước khi xét policy.

**Bằng chứng trước/sau:**
- Trước khi sửa:
> Query: Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?
> Route   : policy_tool_worker

- Sau khi sửa
> Query: Cần cấp quyền Level 3 để khắc phục P1 khẩn cấp. Quy trình là gì?
> Route   : retrieval_worker

---

## 4. Tôi tự đánh giá đóng góp của mình (100–150 từ)

> Trả lời trung thực — không phải để khen ngợi bản thân.

**Tôi làm tốt nhất ở điểm nào?**

Tôi làm tốt nhất ở việc thiết kế và triển khai luồng điều phối (orchestration) của hệ thống agent trong file graph.py. Tôi đã xây dựng supervisor_node() để phân tích task và quyết định route sang worker phù hợp, đồng thời thiết lập build_graph() để kết nối các node bằng StateGraph và các conditional edges. Điều này giúp pipeline của hệ thống chạy theo đúng thứ tự: supervisor → worker → synthesis.

**Tôi làm chưa tốt hoặc còn yếu ở điểm nào?**

Phần routing hiện tại vẫn dựa chủ yếu vào keyword-based rules, nên có thể chưa đủ linh hoạt nếu câu hỏi được diễn đạt theo nhiều cách khác nhau. Tôi cũng chưa triển khai các phương pháp nâng cao hơn như LLM-based classification hoặc dynamic routing.

**Nhóm phụ thuộc vào tôi ở đâu?** _(Phần nào của hệ thống bị block nếu tôi chưa xong?)_

Nhóm phụ thuộc vào phần supervisor orchestration và graph structure mà tôi xây dựng. Nếu supervisor_node() hoặc build_graph() chưa hoàn thành, các worker của thành viên khác sẽ không thể được gọi đúng cách và toàn bộ pipeline agent sẽ không chạy được.

**Phần tôi phụ thuộc vào thành viên khác:** _(Tôi cần gì từ ai để tiếp tục được?)_

Phần của tôi phụ thuộc vào việc các worker khác được implement đúng, đặc biệt là retrieval_worker, policy_tool_worker, và synthesis_worker. Tôi cần các worker này trả về dữ liệu đúng format trong AgentState để graph có thể tiếp tục chuyển sang bước tiếp theo và tạo ra câu trả lời cuối cùng.

---

## 5. Nếu có thêm 2 giờ, tôi sẽ làm gì? (50–100 từ)

> Nêu **đúng 1 cải tiến** với lý do có bằng chứng từ trace hoặc scorecard.
> Không phải "làm tốt hơn chung chung" — phải là:
> *"Tôi sẽ thử X vì trace của câu gq___ cho thấy Y."*

Tôi sẽ cải tiến logic routing của supervisor để giảm over-trigger policy_tool_worker, vì trace cho thấy các câu như q02 và q07 có confidence khá thấp (~0.45–0.52) dù route đúng, cho thấy worker này đang bị gọi ngay cả khi chưa đủ context. Cụ thể, tôi sẽ thêm bước kiểm tra “có cần retrieval trước không” (dựa vào thiếu retrieved_chunks) trước khi quyết định needs_tool=True, nhằm tăng chất lượng input cho policy worker và cải thiện confidence tổng thể.

---

*Lưu file này với tên: `reports/individual/[ten_ban].md`*  
*Ví dụ: `reports/individual/nguyen_van_a.md`*
