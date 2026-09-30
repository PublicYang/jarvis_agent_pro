"""
Jarvis Agent Pro - 人工审查与中断节点 (Human Approval Node)

提供人机协同 (Human-in-the-Loop, HITL) 拦截原语：
针对高危或敏感工具调用发起无状态执行挂起 (Interrupt)，并在外部指令唤醒 (Resume) 后
根据人工核准或驳回结果安全路由下游流程。
"""

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage
from langgraph.types import interrupt

from nodes.base import NodeFunction, with_error_boundary
from state.agent_state import AgentState

# 默认高危敏感工具集合
DEFAULT_SENSITIVE_TOOLS = frozenset({"execute_shell", "delete_file", "drop_db", "rm_rf"})


def create_human_approval_node(
    sensitive_tools: Sequence[str] | frozenset[str] | None = None,
) -> NodeFunction:
    """
    创建人工审批节点 (Human Approval Node)

    Args:
        sensitive_tools: 触发人工审批的高危工具名称集合

    Returns:
        NodeFunction: 遵循图节点契约的可调用函数
    """
    protected_tools = frozenset(sensitive_tools) if sensitive_tools else DEFAULT_SENSITIVE_TOOLS

    @with_error_boundary("human_approval")
    def human_approval_node(state: AgentState) -> dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {"approval_status": "approved"}

        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            return {"approval_status": "approved"}

        tool_calls = getattr(last_message, "tool_calls", None) or []
        sensitive_calls = [tc for tc in tool_calls if tc.get("name") in protected_tools]

        # 若无敏感操作，直接放行
        if not sensitive_calls:
            return {"approval_status": "approved"}

        # 构造中断请求载荷并调用 LangGraph 原生 interrupt 原语挂起图执行
        interrupt_payload = {
            "type": "human_approval_required",
            "task_goal": state.get("task_goal", ""),
            "sensitive_tool_calls": sensitive_calls,
        }

        # 框架挂起执行，直到外部通过 Command(resume=...) 注入恢复输入
        resume_data: Any = interrupt(interrupt_payload)

        # 解析人工审批结果
        is_approved = False
        reason = "操作被用户驳回"

        if isinstance(resume_data, dict):
            is_approved = bool(resume_data.get("approved", False))
            reason = str(resume_data.get("reason", reason if not is_approved else "人工核准"))
        elif isinstance(resume_data, bool):
            is_approved = resume_data
            reason = "人工核准" if is_approved else "用户直接拒绝"

        if is_approved:
            return {
                "approval_status": "approved",
                "scratchpad": [f"人工审批通过: {len(sensitive_calls)} 项敏感操作已核准"],
            }

        # 若审批驳回：为每个敏感工具调用构造拒绝 ToolMessage，交由模型自适应调整计划
        rejection_messages = [
            ToolMessage(
                content=f"操作被人工驳回: {reason}",
                tool_call_id=call.get("id", ""),
                name=call.get("name", ""),
            )
            for call in sensitive_calls
        ]

        return {
            "messages": rejection_messages,
            "approval_status": "rejected",
            "scratchpad": [f"人工审批驳回: {reason}"],
        }

    return human_approval_node
