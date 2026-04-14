# Báo Cáo Nhóm — Lab Day 09: Multi-Agent Orchestration

**Tên nhóm:** C401_F1 
**Thành viên:**
**Tên nhóm:** C401_F1
**Thành viên:**
| Tên | Vai trò | Email |
|-----|---------|-------|
| Lê Duy Anh | Tech Lead | leduyanh2k3@gmail.com |
| Bùi Trần Gia Bảo | Retrieval Owner | billxd04@gmail.com |
| Lại Gia Khánh | Retrieval Owner | laigiakhanh1211@gmail.com |
| Trương Minh Sơn | Eval Owner | chokhon2004@gmail.com |
| Mạc Phương Nga | Tester | mpnga03@gmail.com |
| Nguyễn Phạm Trà My | Documentation Owner | ___ |

**Ngày nộp:** 14/04/2026
**Repo:** [(https://github.com/solar11781/lab8_C401_F1.git)](https://github.com/solar11781/lab9_C401_F1.git)
**Độ dài khuyến nghị:** 600–1000 từ

---

> **Hướng dẫn nộp group report:**
> 
> - File này nộp tại: `reports/group_report.md`
> - Deadline: Được phép commit **sau 18:00** (xem SCORING.md)
> - Tập trung vào **quyết định kỹ thuật cấp nhóm** — không trùng lặp với individual reports
> - Phải có **bằng chứng từ code/trace** — không mô tả chung chung
> - Mỗi mục phải có ít nhất 1 ví dụ cụ thể từ code hoặc trace thực tế của nhóm

---

## 1. Kiến trúc nhóm đã xây dựng (150–200 từ)

> Mô tả ngắn gọn hệ thống nhóm: bao nhiêu workers, routing logic hoạt động thế nào,
> MCP tools nào được tích hợp. Dùng kết quả từ `docs/system_architecture.md`.

**Hệ thống tổng quan:**
>> Hệ thống được xây dựng theo mô hình Multi-Agent Orchestration, tập trung vào khả năng chuyên môn hóa và tính minh bạch (observability). Trung tâm của hệ thống là Supervisor Agent, đóng vai trò bộ não điều phối các Workers chuyên biệt:
- Retrieval Worker: Chuyên trách truy xuất dữ liệu từ cơ sở dữ liệu vector (ChromaDB) cho các câu hỏi tra cứu thông tin chung (SLA, FAQ).
- Policy Tool Worker: Tập trung xử lý các tác vụ phức tạp liên quan đến chính sách hoàn tiền và kiểm soát truy cập, có khả năng ra quyết định dựa trên các quy tắc cứng.
- Synthesis Worker: Chịu trách nhiệm tổng hợp dữ liệu thô từ các workers khác, kiểm tra tính logic và tạo câu trả lời cuối cùng có kèm trích dẫn nguồn.
- Human Review Worker: Cung cấp lớp bảo mật HITL (Human-in-the-Loop), tự động kích hoạt khi hệ thống gặp rủi ro cao hoặc mã lỗi chưa xác định.
> Hệ thống tích hợp giao thức MCP (Model Context Protocol) với các công cụ như search_kb để truy vấn tri thức sâu và get_ticket_info để kết nối trực tiếp với dữ liệu ticket thực tế, giúp AI không chỉ trả lời mà còn "hành động" được trên dữ liệu.

**Routing logic cốt lõi:**
> Supervisor sử dụng cơ chế Keyword Routing để quyết định lộ trình (route) cho mỗi câu hỏi


_________________

**MCP tools đã tích hợp:**
> Liệt kê tools đã implement và 1 ví dụ trace có gọi MCP tool.

- search_kb: Công cụ tra cứu cơ sở tri thức (Knowledge Base) chuyên sâu. Công cụ này được policy_tool_worker sử dụng để truy vấn các đoạn văn bản cụ thể trong các tài liệu PDF/Markdown về chính sách hoàn tiền hoặc quy trình vận hành (SOP).
- get_ticket_info: Công cụ truy xuất thông tin chi tiết của một ticket cụ thể từ hệ thống quản lý sự cố. Nó giúp Worker lấy được trạng thái, thời gian tạo và mức độ ưu tiên thực tế của ticket để đối chiếu với SLA.
- human_review_handler: (Nằm trong luồng xử lý rủi ro) Công cụ gửi yêu cầu phê duyệt đến con người khi hệ thống phát hiện các mã lỗi không xác định hoặc các yêu cầu có độ nhạy cảm cao (High Risk).

Ví dụ: 
{
  "task": "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?",
  "history": [
    "[supervisor] received task: Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?",
    "[supervisor] route=policy_tool_worker reason=task contains policy/access keyword",
    "[policy_tool_worker] called",
    "[policy_tool_worker] called MCP tool: search_kb | input={'query': 'Refund time limit', 'top_k': 3}",
    "[policy_tool_worker] policy check complete: Found '7 ngày làm việc'",
    "[synthesis_worker] called",
    "[synthesis_worker] answer generated: '...trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng [1].'"
  ],
  "mcp_tools_used": ["search_kb"]
}

## 2. Quyết định kỹ thuật quan trọng nhất (200–250 từ)

> Chọn **1 quyết định thiết kế** mà nhóm thảo luận và đánh đổi nhiều nhất.
> Phải có: (a) vấn đề gặp phải, (b) các phương án cân nhắc, (c) lý do chọn phương án đã chọn.

**Quyết định:** Quyết định: Thiết lập cơ chếK Keyword Routing 

**Bối cảnh vấn đề:**
Trong quá trình phát triển Sprint 4, nhóm đối mặt với rủi ro "ảo giác" (hallucination) của LLM khi phân loại các yêu cầu nhạy cảm. Nếu chỉ dựa hoàn toàn vào việc Supervisor sử dụng ngôn ngữ tự nhiên để định tuyến, hệ thống có thể hiểu sai ý định khi gặp các mã lỗi kỹ thuật lạ hoặc các cụm từ gây nhiễu. Ví dụ, với lỗi ERR-403-AUTH, một Agent thuần LLM có thể cố gắng suy diễn nội dung từ bộ nhớ thay vì nhận diện đây là sự cố bảo mật cần quy trình nghiêm ngặt. Thách thức là làm sao đảm bảo tính chính xác 100% cho các tác vụ then chốt (hoàn tiền, bảo mật) mà không làm mất đi tính linh hoạt của AI.

**Các phương án đã cân nhắc:**

| Phương án | Ưu điểm | Nhược điểm |
|-----------|---------|-----------|
| Pure LLM Router | Cực kỳ linh hoạt, hiểu được mọi cách diễn đạt của người dùng. | Dễ bị đánh lừa bởi các câu hỏi mẹo (prompt injection) hoặc trả lời sai về bảo mật. |
| Rule-based Router | Tuyệt đối an toàn, tốc độ xử lý nhanh nhất. | Cứng nhắc, không hiểu được các câu hỏi có ngữ cảnh phức tạp hoặc đa ý định. |
| HKeyword-First Hybrid (Chọn) | Đảm bảo an toàn bằng từ khóa trước, sau đó mới dùng LLM cho các ca khó. |Cần duy trì và cập nhật danh sách từ khóa (Keyword Library) thường xuyên.|

**Phương án đã chọn và lý do:**

Nhóm quyết định chọn Keyword-First Hybrid Routing. Với vai trò Prompt Engineer, Solar đã thiết kế Supervisor thực hiện một bước kiểm tra từ khóa định danh (như "refund", "access", "ERR-") trước khi chuyển task cho LLM suy luận. Lý do chính là để bảo vệ tính toàn vẹn của hệ thống (System Integrity). Nếu phát hiện từ khóa rủi ro hoặc mã lỗi hệ thống, Supervisor sẽ lập tức "ép" luồng vào policy_tool_worker hoặc human_review. Điều này loại bỏ hoàn toàn rủi ro LLM đi sai hướng trong các tác vụ tuân thủ (Compliance), vốn là ưu tiên hàng đầu tại VinUni/VinAI.

**Bằng chứng từ trace/code:**
> Trong trace gq01 và q09, logic routing đã thực thi dựa trên từ khóa khớp lệnh thay vì chỉ dựa vào phân tích ngữ nghĩa:
```
[NHÓM ĐIỀN VÀO ĐÂY — ví dụ trace hoặc code snippet]
```
{
  "task": "Ticket P1 lúc 2am... emergency fix cho contractor...",
  "route_reason": "task contains policy/access keyword | risk_high flagged",
  "supervisor_route": "policy_tool_worker",
  "mcp_tools_used": ["search_kb", "get_ticket_info"]
}
---

## 3. Kết quả grading questions (150–200 từ)

> Sau khi chạy pipeline với grading_questions.json (public lúc 17:00):
> - Nhóm đạt bao nhiêu điểm raw? 
> - Câu nào pipeline xử lý tốt nhất? q 
> - Câu nào pipeline fail hoặc gặp khó khăn?

**Tổng điểm raw ước tính:** 90 / 96 (hệ thống trả lời đúng logic 9/10 câu, trừ một số lỗi nhỏ về định dạng latency)

**Câu pipeline xử lý tốt nhất:**
- ID: gd10 — Lý do tốt: Pipeline đã thể hiện khả năng suy luận đa điều kiện cực kỳ xuất sắc. Mặc dù sản phẩm bị lỗi và còn trong hạn 7 ngày, nhưng hệ thống đã nhận diện được "ngoại lệ" (Flash Sale) để từ chối hoàn tiền đúng theo chính sách, tránh thất thoát cho doanh nghiệp.

**Câu pipeline fail hoặc partial:**
- ID: gq09 (Partial) — Fail ở đâu: Phản hồi nội dung chính xác nhưng gặp lỗi latency_ms: null trong log. 
  Root cause: Hàm run_graph trong graph.py chưa cập nhật giá trị thời gian thực thi vào dictionary kết quả, dẫn đến thiếu metric quan trọng để đánh giá hiệu năng.

**Câu gq07 (abstain):** Nhóm xử lý thế nào?

Với các câu hỏi nằm ngoài phạm vi tri thức (out-of-scope), hệ thống được cấu hình để retrieval_worker trả về độ tin cậy thấp. Thay vì "bịa" ra câu trả lời, synthesis_worker sẽ đưa ra phản hồi trung lập, thông báo không tìm thấy thông tin trong tài liệu chính thống và hướng dẫn người dùng liên hệ bộ phận liên quan, giúp đảm bảo tính trung thực của AI.

**Câu gq09 (multi-hop khó nhất):** Trace ghi được 2 workers không? Kết quả thế nào?

1. Policy Tool Worker: Được gọi để kiểm tra quy trình cấp quyền Level 2 cho contractor.
2. Retrieval Worker (thông qua Supervisor): Được gọi để tra cứu SLA thông báo stakeholders.

> Kết quả: Trace ghi lại đầy đủ mcp_tools_used: ["search_kb", "get_ticket_info"]. Hệ thống đã trả về câu trả lời phức hợp: vừa nêu đúng quy trình phê duyệt khẩn cấp (Emergency Fix), vừa tính toán đúng thời gian thông báo theo SLA.

---

## 4. So sánh Day 08 vs Day 09 — Điều nhóm quan sát được (150–200 từ)

> Dựa vào `docs/single_vs_multi_comparison.md` — trích kết quả thực tế.

**Metric thay đổi rõ nhất (có số liệu):**

Sự thay đổi rõ rệt nhất nằm ở khả năng quan sát (Observability) và độ tin cậy (Confidence).

Trong khi Day 08 là một "hộp đen" với avg_confidence ảo ở mức 0.72, thì Day 09 cho con số thực tế hơn là 0.542.

Routing Distribution cho thấy sự phân hóa rõ rệt: 46% tác vụ được xử lý bởi policy_tool_worker thông qua các công cụ MCP chuyên biệt, điều mà Single-Agent chỉ có thể làm thông qua việc nhồi nhét prompt (Prompt Stuffing).

Đặc biệt, hệ thống đã ghi nhận 6% (1/15) yêu cầu được chuyển hướng tới human_review, giúp ngăn chặn hoàn toàn việc AI tự ý đưa ra quyết định sai lầm trong các tình huống rủi ro cao.

**Điều nhóm bất ngờ nhất khi chuyển từ single sang multi-agent:**

Nhóm bất ngờ về khả năng tự động lựa chọn công cụ (Tool Selection) của Supervisor. Với các câu hỏi phức tạp (Multi-hop) như gq09, hệ thống không còn trả lời chung chung mà biết tự gọi đồng thời cả search_kb và get_ticket_info. Việc tách rời các Worker giúp chúng tôi dễ dàng phát hiện ra lỗi nằm ở đâu (ví dụ: lỗi tại bước Retrieval hay bước Synthesis) mà không cần phải chạy lại toàn bộ pipeline, giúp tốc độ debug tăng lên đáng kể.

**Trường hợp multi-agent KHÔNG giúp ích hoặc làm chậm hệ thống:**

Multi-agent bộc lộ nhược điểm về độ trễ (Latency) và tính phức tạp đối với các câu hỏi đơn giản.

Với các câu hỏi FAQ ngắn (như q03), việc đi qua vòng lặp Supervisor -> Worker -> Synthesis làm tăng thời gian phản hồi so với Single-Agent.

---

## 5. Phân công và đánh giá nhóm (100–150 từ)

> Đánh giá trung thực về quá trình làm việc nhóm.

**Phân công thực tế:**

| Thành viên | Phần đã làm | Sprint |
|------------|-------------|--------|
| Lại Gia Khánh | graph.py | 1 |
| Lê Duy Anh | retrieval.py + system_architecture.md | 2 |
| Mạc Phương Nga | policy_tool.py + routing_decisions.md | 2 |
| Nguyễn Phạm Trà My | synthesis.py + single_vs_multi_comparision.md | 2 |
| Bùi Trần Gia Bảo | mcp_server.py | 3 |
| Trương Minh Sơn | eval_trace.py + group_report.md | 4 |

**Điều nhóm làm tốt:**

Thiết kế hệ thống có tính quan sát cao, xử lý Logic phức tạp: Hệ thống phân biệt tốt các trường hợp ngoại lệ (như Flash Sale) và tính toán chính xác deadline theo SLA, tích hợp MCP thực tế: Sử dụng thành công search_kb và get_ticket_info

**Điều nhóm làm chưa tốt hoặc gặp vấn đề về phối hợp:**

Thiếu sót trong đo lường Performance: Việc để sót giá trị latency_ms (trả về null) khiến nhóm thiếu dữ liệu định lượng để so sánh tốc độ xử lý giữa các phiên bản.

**Nếu làm lại, nhóm sẽ thay đổi gì trong cách tổ chức?**

Thiết lập Pipeline tự động: Tích hợp kiểm tra lỗi JSON và đo lường latency ngay trong quá trình chạy, tránh việc phải sửa thủ công khi đã sát deadline.

---

## 6. Nếu có thêm 1 ngày, nhóm sẽ làm gì? (50–100 từ)

> 1–2 cải tiến cụ thể với lý do có bằng chứng từ trace/scorecard.

Dựa trên bằng chứng từ eval_report.json (avg_confidence chỉ đạt 0.542), nếu có thêm 1 ngày, nhóm sẽ:

1. Refine Prompt cho Synthesis Worker: Tối ưu hóa cách tổng hợp để nâng cao confidence score lên mức >0.7 bằng cách cung cấp thêm các "few-shot examples" về cách trích dẫn nguồn.

2. Sửa lỗi Log Metric: Hoàn thiện code đo latency_ms và xử lý triệt để lỗi JSONDecodeError khi phân tích trace, từ đó có bảng so sánh hiệu năng (performance delta) chuẩn xác hơn giữa Single và Multi-Agent để thuyết phục các Coach.

---

*File này lưu tại: `reports/group_report.md`*  
*Commit sau 18:00 được phép theo SCORING.md*
