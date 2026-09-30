"""
Jarvis Agent Pro - 工具执行节点 (Tool Executor Node)

负责接收并解析最新 AIMessage 中携带的结构化工具调用指令 (tool_calls)，
调度本地工具函数执行，并将结果封装为 ToolMessage 观察反馈回图状态。
"""

import inspect
from collections.abc import Callable, Sequence
from typing import Any

from langchain_core.messages import AIMessage, ToolMessage

from nodes.base import NodeFunction, with_error_boundary
from state.agent_state import AgentState


def create_tool_node(
    tools: Sequence[Callable[..., Any]] | dict[str, Callable[..., Any]] | None = None,
) -> NodeFunction:
    """
    创建 Tool Executor 节点纯函数 (支持工具注册依赖注入)

    Args:
        tools: 可调用的工具函数序列或字典映射表

    Returns:
        NodeFunction: 遵循图节点契约的可调用函数
    """
    tool_map: dict[str, Callable[..., Any]] = {}

    if isinstance(tools, dict):
        tool_map = dict(tools)
    elif tools:
        for t in tools:
            tool_name = str(getattr(t, "__name__", None) or getattr(t, "name", None) or str(t))
            tool_map[tool_name] = t

    @with_error_boundary("tool_executor")
    def tool_executor_node(state: AgentState) -> dict[str, Any]:
        messages = state.get("messages", [])
        if not messages:
            return {}

        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            return {}

        tool_calls = getattr(last_message, "tool_calls", None) or []
        if not tool_calls:
            return {}

        tool_messages: list[ToolMessage] = []
        scratch_logs: list[str] = []

        for call in tool_calls:
            tool_name = call.get("name", "")
            tool_args = call.get("args", {})
            call_id = call.get("id", "")

            if tool_name not in tool_map:
                error_obs = f"错误: 未注册工具 '{tool_name}'"
                tool_messages.append(
                    ToolMessage(content=error_obs, tool_call_id=call_id, name=tool_name)
                )
                scratch_logs.append(f"Tool [{tool_name}] 未找到")
                continue

            tool_func = tool_map[tool_name]
            try:
                if isinstance(tool_args, dict):
                    # 判断签名传参
                    sig = inspect.signature(tool_func)
                    if any(
                        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
                    ) or all(k in sig.parameters for k in tool_args):
                        res = tool_func(**tool_args)
                    else:
                        # 兼容无参或位置参数
                        res = tool_func(**tool_args)
                else:
                    res = tool_func(tool_args)

                obs_str = str(res)
                tool_messages.append(
                    ToolMessage(content=obs_str, tool_call_id=call_id, name=tool_name)
                )
                scratch_logs.append(f"Tool [{tool_name}] 执行成功 -> {obs_str[:60]}")
            except Exception as err:
                fail_obs = f"工具 [{tool_name}] 执行失败: {err!s}"
                tool_messages.append(
                    ToolMessage(content=fail_obs, tool_call_id=call_id, name=tool_name)
                )
                scratch_logs.append(f"Tool [{tool_name}] 抛出异常: {err!s}")

        return {
            "messages": tool_messages,
            "scratchpad": scratch_logs,
        }

    return tool_executor_node
