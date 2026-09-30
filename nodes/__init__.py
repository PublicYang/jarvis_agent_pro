"""
Jarvis Agent Pro - 节点计算层 (Nodes Layer)

无状态的原子计算单元 (Callable)。接收不可变状态快照输入，
产出部分增量更新字典 (Partial State Update)。
核心节点包括：Planner Node、Tool Node、Approval Node、Aggregator Node。
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
