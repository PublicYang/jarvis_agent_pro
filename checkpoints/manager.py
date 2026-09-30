"""
Jarvis Agent Pro - 检查点管理器与存储适配 (Checkpoint Manager & Savers)

提供内存 (MemorySaver) 与磁盘 SQLite (SqliteSaver) 检查点适配，
支持基于 thread_id 的会话隔离、时间旅行历史快照追溯与分支分叉 (Forking)。
"""

import sqlite3

from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import (
    BaseCheckpointSaver,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph.state import CompiledStateGraph
from langgraph.pregel.types import StateSnapshot


def create_memory_saver() -> MemorySaver:
    """创建纯内存检查点存储器 (适用于测试、无状态短会话)"""
    return MemorySaver()


def create_sqlite_saver(db_path: str = ":memory:") -> SqliteSaver:
    """
    创建基于 SQLite 的检查点持久化存储器

    Args:
        db_path: SQLite 数据库文件路径，默认为内存数据库 ':memory:'

    Returns:
        SqliteSaver: 初始化的 SQLite 检查点存储器实例
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    saver = SqliteSaver(conn)
    saver.setup()
    return saver


class CheckpointManager:
    """
    检查点与状态快照高级管理器

    统一封装多租户会话隔离、历史状态回溯 (Time Travel) 与分叉分支管理。
    """

    def __init__(self, saver: BaseCheckpointSaver | None = None) -> None:
        self.saver = saver or create_memory_saver()

    @staticmethod
    def get_session_history(
        graph: CompiledStateGraph,
        thread_id: str,
    ) -> list[StateSnapshot]:
        """
        获取指定会话 thread_id 的完整历史状态演进切片列表 (按最新到最旧倒序排列)
        """
        config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
        return list(graph.get_state_history(config))

    @staticmethod
    def get_state_at_checkpoint(
        graph: CompiledStateGraph,
        thread_id: str,
        checkpoint_id: str,
    ) -> StateSnapshot:
        """
        精准读取指定会话在历史某个时刻 (checkpoint_id) 的冻结状态快照
        """
        config: RunnableConfig = {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }
        return graph.get_state(config)

    @staticmethod
    def create_fork_config(
        thread_id: str,
        checkpoint_id: str,
    ) -> RunnableConfig:
        """
        生成指定历史时间点的分支调用配置，用于从该检查点开启时间旅行 (Time Travel)
        """
        return {
            "configurable": {
                "thread_id": thread_id,
                "checkpoint_id": checkpoint_id,
            }
        }
