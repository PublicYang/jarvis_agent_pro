"""
Jarvis Agent Pro - 节点契约与错误边界 (Node Contracts & Error Boundary)

规范节点纯函数契约 (Callable)，提供统一的异常防护与状态安全降级机制。
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

from langchain_core.messages import AIMessage
from langgraph.errors import GraphInterrupt

from state.agent_state import AgentState

logger = logging.getLogger(__name__)

# 节点纯函数类型定义：接收只读 AgentState 快照，输出局部状态增量字典 (Partial State)
NodeFunction = Callable[[AgentState], dict[str, Any]]


def with_error_boundary(node_name: str) -> Callable[[NodeFunction], NodeFunction]:
    """
    节点异常隔离边界装饰器 (Node Error Boundary)

    捕获节点内部未预期的运行时异常，阻止整个图调度进程崩溃。
    注意：LangGraph 控制流异常 (如 GraphInterrupt) 必须原样抛出，供引擎挂起。
    """

    def decorator(func: NodeFunction) -> NodeFunction:
        @functools.wraps(func)
        def wrapper(state: AgentState) -> dict[str, Any]:
            try:
                return func(state)
            except GraphInterrupt:
                # 重新抛出 GraphInterrupt，确保人机协同 (HITL) 挂起原语生效
                raise
            except Exception as exc:
                logger.exception("Node [%s] execution failed with error: %s", node_name, exc)
                error_msg = f"节点 [{node_name}] 执行异常: {exc!s}"
                return {
                    "messages": [AIMessage(content=error_msg)],
                    "scratchpad": [f"ERROR in {node_name}: {exc!s}"],
                    "metadata": {"last_node_error": str(exc), "failed_node": node_name},
                }

        return wrapper

    return decorator
