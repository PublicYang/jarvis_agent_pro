"""
Jarvis Agent Pro - 条件路由与分支决策器 (Conditional Router)

根据当前状态快照推导后续执行路径，解耦“业务决策数据生产”与“拓扑流转方向”。
"""

from typing import Final, Literal

from langchain_core.messages import AIMessage

from state.agent_state import AgentState

# 路由目标常量
ROUTER_ACTION_TOOLS: Final = "tool_executor"
ROUTER_ACTION_END: Final = "end"

RouteDecision = Literal["tool_executor", "end"]


def route_planner_decision(state: AgentState) -> RouteDecision:
    """
    评估 Planner 最新输出，决定分支走向

    - 若最新 AIMessage 包含 tool_calls，流向工具执行节点 (tool_executor)
    - 若不包含 tool_calls 或已产出最终答复，流向终止节点 (end -> END)
    """
    messages = state.get("messages", [])
    if not messages:
        return ROUTER_ACTION_END

    last_message = messages[-1]
    if not isinstance(last_message, AIMessage):
        return ROUTER_ACTION_END

    tool_calls = getattr(last_message, "tool_calls", None)
    if tool_calls and len(tool_calls) > 0:
        return ROUTER_ACTION_TOOLS

    return ROUTER_ACTION_END
