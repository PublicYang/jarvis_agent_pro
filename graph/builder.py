"""
Jarvis Agent Pro - 状态图构建器与编译封装 (StateGraph Builder & Compiler)

提供状态图初始化、通道注册与拓扑编译的标准入口，
严格坚持从原生 StateGraph 核心原语构建，避免使用黑盒预置封装。
"""

from collections.abc import Sequence
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from state.agent_state import AgentState


def create_agent_graph_builder(
    state_schema: type[Any] = AgentState,
) -> StateGraph:
    """
    初始化图构建器 (StateGraph Builder)

    基于强类型状态 Schema 声明图通道与规约器映射。
    """
    return StateGraph(state_schema=state_schema)


def compile_agent_graph(
    builder: StateGraph,
    checkpointer: BaseCheckpointSaver | None = None,
    interrupt_before: Sequence[str] | None = None,
    interrupt_after: Sequence[str] | None = None,
) -> CompiledStateGraph:
    """
    编译状态图 (Compile StateGraph)

    执行静态拓扑与可达性校验，生成不可变的运行期执行图。

    Args:
        builder: 已配置节点与边的 StateGraph 构建器
        checkpointer: 可选的检查点持久化存储实例
        interrupt_before: 在指定节点执行前挂起中断 (HITL)
        interrupt_after: 在指定节点执行后挂起中断 (HITL)

    Returns:
        CompiledStateGraph: 可执行的编译后状态图实例
    """
    return builder.compile(
        checkpointer=checkpointer,
        interrupt_before=list(interrupt_before) if interrupt_before else None,
        interrupt_after=list(interrupt_after) if interrupt_after else None,
    )
