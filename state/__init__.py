"""
Jarvis Agent Pro - 状态语义层 (State Layer)

整个图的单一可信数据源 (Single Source of Truth)。
定义强类型 TypedDict 契约以及字段级原子规约器 (Reducers)，
保障多分支并发写安全与增量更新一致性。
"""

from state.agent_state import (
    AgentState,
    append_reducer,
    merge_dict_reducer,
)

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "AgentState",
    "append_reducer",
    "merge_dict_reducer",
]
