from mcp_server import dispatch_tool

res = dispatch_tool(
    "get_ticket_info",
    {"ticket_id": "P1-LATEST"}
)

print(res)