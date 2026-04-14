"""
workers/policy_tool.py — Policy & Tool Worker
Sprint 2+3: Kiểm tra policy dựa vào context, gọi MCP tools khi cần.

Input (từ AgentState):
    - task: câu hỏi
    - retrieved_chunks: context từ retrieval_worker
    - needs_tool: True nếu supervisor quyết định cần tool call

Output (vào AgentState):
    - policy_result: {"policy_applies", "policy_name", "exceptions_found", "source", "rule"}
    - mcp_tools_used: list of tool calls đã thực hiện
    - worker_io_log: log

Gọi độc lập để test:
    python workers/policy_tool.py
"""

import os
import sys
from typing import Optional
from openai import OpenAI
import json

WORKER_NAME = "policy_tool_worker"


# ─────────────────────────────────────────────
# MCP Client — Sprint 3: Thay bằng real MCP call
# ─────────────────────────────────────────────

def _call_mcp_tool(tool_name: str, tool_input: dict) -> dict:
    """
    Gọi MCP tool.

    Sprint 3 TODO: Implement bằng cách import mcp_server hoặc gọi HTTP.

    Hiện tại: Import trực tiếp từ mcp_server.py (trong-process mock).
    """
    from datetime import datetime

    try:
        # TODO Sprint 3: Thay bằng real MCP client nếu dùng HTTP server
        from mcp_server import dispatch_tool
        result = dispatch_tool(tool_name, tool_input)
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": result,
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }
    except ImportError:
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": {"message": f"Simulated {tool_name} success. MCP Server not found."},
            "error": None,
            "timestamp": datetime.now().isoformat(),
        }
    except Exception as e:
        return {
            "tool": tool_name,
            "input": tool_input,
            "output": None,
            "error": {"code": "MCP_CALL_FAILED", "reason": str(e)},
            "timestamp": datetime.now().isoformat(),
        }


# ─────────────────────────────────────────────
# Policy Analysis Logic
# ─────────────────────────────────────────────

def analyze_policy(task: str, chunks: list) -> dict:
    """
    Phân tích policy bằng LLM. Trả về format chuẩn để Synthesis dễ dàng đọc.
    """
    # Lấy nguồn tài liệu từ chunks
    sources = list({c.get("source", "unknown") for c in chunks if c})
    context_text = "\n".join([f"[{c.get('source', 'unknown')}] {c.get('text', '')}" for c in chunks])

    # Khởi tạo OpenAI Client
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

def _rule_based_fallback(task: str, chunks: list, sources: list) -> dict:
    """Hàm backup rule-based cũ của bạn, chạy khi LLM lỗi hoặc không có Key"""
    task_lower = task.lower()
    context_text = " ".join([c.get("text", "") for c in chunks]).lower()
    exceptions_found = []

    if "flash sale" in task_lower or "flash sale" in context_text:
        exceptions_found.append({"type": "flash_sale", "rule": "Không hoàn tiền Flash Sale", "source": "policy_refund_v4.txt"})
    if any(kw in task_lower for kw in ["license", "subscription", "kỹ thuật số"]):
        exceptions_found.append({"type": "digital_product", "rule": "Không hoàn tiền hàng Digital", "source": "policy_refund_v4.txt"})
    if any(kw in task_lower for kw in ["đã kích", "đăng ký", "đã sử dụng"]):
        exceptions_found.append({"type": "activated", "rule": "Không hoàn tiền sản phẩm đã dùng", "source": "policy_refund_v4.txt"})

    policy_version_note = "Áp dụng v3" if any(k in task_lower for k in ["31/01", "30/01", "trước 01/02"]) else ""

    return {
        "policy_applies": len(exceptions_found) == 0,
        "policy_name": "refund_policy_v4",
        "exceptions_found": exceptions_found,
        "source": sources,
        "policy_version_note": policy_version_note,
        "explanation": "Analyzed via rule-based fallback.",
    }


# ─────────────────────────────────────────────
# Worker Entry Point
# ─────────────────────────────────────────────

def run(state: dict) -> dict:
    """
    Worker entry point — gọi từ graph.py.

    Args:
        state: AgentState dict

    Returns:
        Updated AgentState với policy_result và mcp_tools_used
    """
    task = state.get("task", "")
    chunks = state.get("retrieved_chunks", [])
    needs_tool = state.get("needs_tool", False)

    state.setdefault("workers_called", [])
    state.setdefault("history", [])
    state.setdefault("mcp_tools_used", [])

    state["workers_called"].append(WORKER_NAME)

    worker_io = {
        "worker": WORKER_NAME,
        "input": {
            "task": task,
            "chunks_count": len(chunks),
            "needs_tool": needs_tool,
        },
        "output": None,
        "error": None,
    }

    try:
        # Step 1: Nếu chưa có chunks, gọi MCP search_kb
        if not chunks and needs_tool:
            mcp_result = _call_mcp_tool("search_kb", {"query": task, "top_k": 3})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP search_kb")

            if mcp_result.get("output") and mcp_result["output"].get("chunks"):
                chunks = mcp_result["output"]["chunks"]
                state["retrieved_chunks"] = chunks

        # Step 2: Phân tích policy
        policy_result = analyze_policy(task, chunks)
        state["policy_result"] = policy_result

        # Step 3: Nếu cần thêm info từ MCP (e.g., ticket status), gọi get_ticket_info
        if needs_tool and any(kw in task.lower() for kw in ["ticket", "p1", "jira"]):
            mcp_result = _call_mcp_tool("get_ticket_info", {"ticket_id": "P1-LATEST"})
            state["mcp_tools_used"].append(mcp_result)
            state["history"].append(f"[{WORKER_NAME}] called MCP get_ticket_info")

        worker_io["output"] = {
            "policy_applies": policy_result["policy_applies"],
            "exceptions_count": len(policy_result.get("exceptions_found", [])),
            "mcp_calls": len(state["mcp_tools_used"]),
        }
        state["history"].append(
            f"[{WORKER_NAME}] policy_applies={policy_result['policy_applies']}, "
            f"exceptions={len(policy_result.get('exceptions_found', []))}"
        )

    except Exception as e:
        worker_io["error"] = {"code": "POLICY_CHECK_FAILED", "reason": str(e)}
        state["policy_result"] = {"error": str(e)}
        state["history"].append(f"[{WORKER_NAME}] ERROR: {e}")

    state.setdefault("worker_io_logs", []).append(worker_io)
    return state


# ─────────────────────────────────────────────
# Test độc lập
# ─────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 50)
    print("Policy Tool Worker — Standalone Test")
    print("=" * 50)

    test_cases = [
        {
            "task": "Khách hàng Flash Sale yêu cầu hoàn tiền vì sản phẩm lỗi — được không?",
            "retrieved_chunks": [
                {"text": "Ngoại lệ: Đơn hàng Flash Sale không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.9}
            ],
        },
        {
            "task": "Khách hàng muốn hoàn tiền license key đã kích hoạt.",
            "retrieved_chunks": [
                {"text": "Sản phẩm kỹ thuật số (license key, subscription) không được hoàn tiền.", "source": "policy_refund_v4.txt", "score": 0.88}
            ],
        },
        {
            "task": "Khách hàng yêu cầu hoàn tiền trong 5 ngày, sản phẩm lỗi, chưa kích hoạt.",
            "retrieved_chunks": [
                {"text": "Yêu cầu trong 7 ngày làm việc, sản phẩm lỗi nhà sản xuất, chưa dùng.", "source": "policy_refund_v4.txt", "score": 0.85}
            ],
        },
    ]

    for tc in test_cases:
        print(f"\n▶ Task: {tc['task'][:70]}...")
        result = run(tc.copy())
        pr = result.get("policy_result", {})
        print(f"  policy_applies: {pr.get('policy_applies')}")
        if pr.get("exceptions_found"):
            for ex in pr["exceptions_found"]:
                print(f"  exception: {ex['type']} — {ex['rule'][:60]}...")
        print(f"  MCP calls: {len(result.get('mcp_tools_used', []))}")

    print("\n✅ policy_tool_worker test done.")
