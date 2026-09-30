"""
Jarvis Agent Pro - 规划与决策节点 (Planner Node)

负责理解当前任务目标与历史上下文，调用大语言模型进行推理规划，
生成思考决策并决定是否发起工具调用 (Tool Call) 或输出最终答复。
"""

from collections.abc import Sequence
from typing import Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    SystemMessage,
)

from nodes.base import NodeFunction, with_error_boundary
from state.agent_state import AgentState


def create_planner_node(
    model: Any,
    system_prompt: str | None = None,
) -> NodeFunction:
    """
    创建 Planner 节点纯函数 (支持依赖注入)

    Args:
        model: 实现了 .invoke(messages) 的模型适配器或 Mock 对象
        system_prompt: 可选的系统级指令提示词

    Returns:
        NodeFunction: 遵循图节点契约的可调用函数
    """

    @with_error_boundary("planner")
    def planner_node(state: AgentState) -> dict[str, Any]:
        history: Sequence[BaseMessage] = state.get("messages", [])
        prompt_messages: list[BaseMessage] = []

        # 注入系统提示词 (若未存在)
        if system_prompt and (not history or not isinstance(history[0], SystemMessage)):
            prompt_messages.append(SystemMessage(content=system_prompt))

        prompt_messages.extend(history)

        # 调用模型推导下一步
        response = model.invoke(prompt_messages)

        # 确保输出封装为 AIMessage 实例
        if isinstance(response, str):
            ai_message = AIMessage(content=response)
        elif isinstance(response, AIMessage):
            ai_message = response
        else:
            ai_message = AIMessage(content=str(response))

        tool_calls = getattr(ai_message, "tool_calls", [])
        has_tools = bool(tool_calls)

        scratch_entry = (
            f"Planner 决策: 生成 {len(tool_calls)} 个工具调用"
            if has_tools
            else "Planner 决策: 生成最终答复"
        )

        return {
            "messages": [ai_message],
            "scratchpad": [scratch_entry],
        }

    return planner_node
