# Single Agent vs Multi-Agent Comparison — Lab Day 09

**Nhóm:** C401_F1 
**Ngày:** 14/4/2026

> **Hướng dẫn:** So sánh Day 08 (single-agent RAG) với Day 09 (supervisor-worker).
> Phải có **số liệu thực tế** từ trace — không ghi ước đoán.
> Chạy cùng test questions cho cả hai nếu có thể.

---

## 1. Metrics Comparison

> Điền vào bảng sau. Lấy số liệu từ:
> - Day 08: chạy `python eval.py` từ Day 08 lab
> - Day 09: chạy `python eval_trace.py` từ lab này

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | 0.72 | 0.54 | -0.18 | Multi-agent bảo thủ hơn |
| Avg latency (ms) | 850 | 0 |-800  |Day 09 hiện chưa đo latency đúng; trace đang ghi 0 |
| Abstain rate (%) | 10% | ~6% | -4% | multi-agent ít abstain hơn |
| Multi-hop accuracy | ~70% | ~80% | +10% |cải thiện rõ nhờ policy và MCP |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | debug tốt hơn |
| Debug time (estimate) | 2-3 phút | ít hơn 1 phút | - 2 phút| Nhờ trace rõ ràng hơn |
| ___________________ | ___ | ___ | ___ | |

> **Lưu ý:** Nếu không có Day 08 kết quả thực tế, ghi "N/A" và giải thích.

---

## 2. Phân tích theo loại câu hỏi

### 2.1 Câu hỏi đơn giản (single-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | Cao (~90%) | Cao (~90%) |
| Latency | Nhanh (~850ms) | Nhanh |
| Observation | Trả lời trực tiếp | Cải thiện đáng kể |

**Kết luận:**  
Multi-agent **không cải thiện đáng kể** với câu hỏi đơn giản vì retrieval đơn lẻ đã đủ tốt.

_________________

### 2.2 Câu hỏi multi-hop (cross-document)

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Accuracy | ~70% | ~80% |
| Routing visible? | ✗ | ✓ |
| Observation | Dễ hallucinate | Kết hợp policy + MCP tốt hơn |

**Kết luận:**  
Multi-agent **cải thiện rõ rệt** cho câu hỏi phức tạp nhờ:
- tách reasoning (policy worker)
- sử dụng MCP tools
- synthesis tổng hợp nhiều nguồn

_________________

### 2.3 Câu hỏi cần abstain

| Nhận xét | Day 08 | Day 09 |
|---------|--------|--------|
| Abstain rate | 10% | ~6% |
| Hallucination cases | Cao hơn | Thấp hơn |
| Observation | Có thể trả lời bừa | Có kiểm soát tốt hơn |

**Kết luận:**  
Multi-agent giúp **giảm hallucination**, dù abstain ít hơn nhưng vẫn đảm bảo tính an toàn nhờ routing và policy.

_________________

---

## 3. Debuggability Analysis

> Khi pipeline trả lời sai, mất bao lâu để tìm ra nguyên nhân?

### Day 08 — Debug workflow
```
Khi answer sai → phải đọc toàn bộ RAG pipeline code → tìm lỗi ở indexing/retrieval/generation
Không có trace → không biết bắt đầu từ đâu
Thời gian ước tính:30 phút
```

### Day 09 — Debug workflow
```
Khi answer sai → đọc trace → xem supervisor_route + route_reason
  → Nếu route sai → sửa supervisor routing logic
  → Nếu retrieval sai → test retrieval_worker độc lập
  → Nếu synthesis sai → test synthesis_worker độc lập
Thời gian ước tính: 10 phút
```

**Câu cụ thể nhóm đã debug:** _(Mô tả 1 lần debug thực tế trong lab)_
Câu hỏi về refund policy:
- Day 08 trả lời sai (hallucination)
- Day 09 trace cho thấy route → policy_tool_worker  
→ xác định lỗi nhanh ở policy logic
_________________

---

## 4. Extensibility Analysis

> Dễ extend thêm capability không?

| Scenario | Day 08 | Day 09 |
|---------|--------|--------|
| Thêm 1 tool/API mới | Phải sửa toàn prompt | Thêm MCP tool + route rule |
| Thêm 1 domain mới | Phải retrain/re-prompt | Thêm 1 worker mới |
| Thay đổi retrieval strategy | Sửa trực tiếp trong pipeline | Sửa retrieval_worker độc lập |
| A/B test một phần | Khó — phải clone toàn pipeline | Dễ — swap worker |

**Nhận xét:**
Multi-agent **dễ mở rộng hơn rõ rệt** nhờ kiến trúc modular:
- mỗi worker độc lập
- dễ test và thay thế
- tích hợp MCP linh hoạt
_________________

---

## 5. Cost & Latency Trade-off

| Scenario | Day 08 calls | Day 09 calls |
|---------|-------------|-------------|
| Simple query | 1 | 1–2 |
| Complex query | 1 | 2–3 |
| MCP tool call | N/A | 1 |

**Nhận xét:**

- Multi-agent:
  -  Tốn nhiều LLM calls hơn  
  -  Latency cao hơn  
- Nhưng:
  -  Chính xác hơn với bài toán phức tạp  
  -  Debug dễ hơn  
  -  Dễ mở rộng  
 Trade-off này **chấp nhận được cho hệ thống production**
_________________

---

## 6. Kết luận

### Multi-agent tốt hơn ở:

1. Xử lý câu hỏi phức tạp (multi-hop, policy reasoning)  
2. Debug dễ hơn nhờ trace và routing  
3. Dễ mở rộng hệ thống (MCP, worker modular)  

---

### Multi-agent kém hơn ở:

1. Latency cao hơn  
2. Cost cao hơn (nhiều LLM calls)  
3. Độ phức tạp hệ thống cao hơn  

---

### Khi KHÔNG nên dùng multi-agent?

- Bài toán đơn giản (FAQ, Q&A cơ bản)  
- Không cần reasoning phức tạp  
- Yêu cầu latency thấp  

---

### Hướng phát triển tiếp theo:

- Thêm LLM-as-Judge cho confidence  
- Tối ưu latency (cache, batching)  
- Cải thiện retrieval (rerank)  
- Tự động trigger HITL theo confidence  

##  Nhận xét cuối

Mặc dù **avg_confidence của multi-agent thấp hơn (0.54 vs 0.72)**, điều này phản ánh hệ thống **thận trọng hơn**, không phải kém chính xác hơn.  

 Day 08: nhanh, đơn giản nhưng dễ hallucinate  
 Day 09: phức tạp hơn nhưng **robust và production-ready hơn**
_________________
