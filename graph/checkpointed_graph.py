"""
Jarvis Agent Pro - 状态图检查点装配助手 (Checkpointed Graph Helper)

为图实例无缝注入检查点持久化能力，支持多租户会话与历史回溯。
"""

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph

from checkpoints.manager import create_memory_saver
from graph.builder import compile_agent_graph


def compile_with_checkpointer(
    builder: StateGraph,
    checkpointer: BaseCheckpointSaver | None = None,
) -> CompiledStateGraph:
    """
    为 StateGraph 构建器注入检查点并编译

    Args:
        builder: 已声明节点与连线的图构建器
        checkpointer: 检查点持久化实例，默认为内存 MemorySaver

    Returns:
        CompiledStateGraph: 具备状态持久化能力的编译图
    """
    saver = checkpointer or create_memory_saver()
    return compile_agent_graph(builder=builder, checkpointer=saver)
