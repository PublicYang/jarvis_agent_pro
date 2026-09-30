"""
Jarvis Agent Pro - 状态模型与规约器 (AgentState & Reducers)

定义图的核心状态模型 AgentState 以及声明式规约函数 (Reducers)，
确保图执行超步中的状态合并具备原子性、确定性与并发安全性。
"""

from collections.abc import Sequence
from typing import Annotated, Any, Literal

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


def append_reducer(existing: list[Any] | None, update: Any | list[Any] | None) -> list[Any]:
    """
    通用列表追加规约器 (Append Reducer)

    支持单元素追加、列表批量合并，并安全处理 None 初始值与空增量。
    """
    existing_list = list(existing) if existing else []
    if update is None:
        return existing_list
    if isinstance(update, list):
        return existing_list + update
    return existing_list + [update]


def merge_dict_reducer(
    existing: dict[str, Any] | None, update: dict[str, Any] | None
) -> dict[str, Any]:
    """
    字典合并规约器 (Merge Dict Reducer)

    合并键值对，若出现同名键则后写入者覆盖，并安全处理 None 初始值。
    """
    result = dict(existing) if existing else {}
    if update:
        result.update(update)
    return result


class AgentState(TypedDict):
    """
    Jarvis Agent Pro 核心图状态模型 (单一可信数据源)
    """

    # 1. 消息流历史：基于 LangGraph 官方 add_messages 规约
    # 支持追加新消息、相同 ID 原地更新 (Upsert) 及 RemoveMessage 物理删除
    messages: Annotated[Sequence[BaseMessage], add_messages]

    # 2. 任务总目标 (声明式稳定目标)
    task_goal: str

    # 3. 规划与拆解状态 (最新工作计划)
    plan: dict[str, Any] | None

    # 4. 待执行或待审批动作载荷
    pending_action: dict[str, Any] | None

    # 5. 人机协同审批标志
    approval_status: Literal["pending", "approved", "rejected"] | None

    # 6. 工作暂存草稿本 (支持多节点并发追加)
    scratchpad: Annotated[list[str], append_reducer]

    # 7. 并发分支结果汇聚区 (支持多分支字典合并)
    branch_results: Annotated[dict[str, Any], merge_dict_reducer]

    # 8. 运行时元数据控制 (会话、调试标记等)
    metadata: dict[str, Any]
