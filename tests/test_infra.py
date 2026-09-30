"""
Phase 2 测试: 验证工程基础设施、测试固件与核心依赖交互
"""

from collections.abc import Callable
from typing import Annotated, Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class MinimalState(TypedDict):
    """用于测试基础设施的最小状态模型"""

    messages: Annotated[list[Any], add_messages]
    flag: bool


def test_fixture_human_message(make_human_message: Callable[[str], HumanMessage]) -> None:
    """验证 HumanMessage 固件工厂行为"""
    msg = make_human_message("测试输入指令")
    assert isinstance(msg, HumanMessage)
    assert msg.content == "测试输入指令"


def test_fixture_ai_tool_call_message(
    make_ai_tool_call_message: Callable[[str, dict[str, Any], str], AIMessage],
) -> None:
    """验证带有工具调用意图的 AIMessage 固件工厂"""
    msg = make_ai_tool_call_message(
        "read_file",
        {"path": "main.py"},
        "call_123",
    )
    assert isinstance(msg, AIMessage)
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0]["name"] == "read_file"
    assert msg.tool_calls[0]["args"] == {"path": "main.py"}
    assert msg.tool_calls[0]["id"] == "call_123"


def test_fixture_tool_message(make_tool_message: Callable[[str, str], ToolMessage]) -> None:
    """验证工具返回观察结果的 ToolMessage 固件工厂"""
    msg = make_tool_message("文件读取完毕: 200 行", "call_123")
    assert isinstance(msg, ToolMessage)
    assert msg.content == "文件读取完毕: 200 行"
    assert msg.tool_call_id == "call_123"


def test_fixture_thread_config(make_thread_config: Callable[..., Any]) -> None:
    """验证 LangGraph 标准 RunnableConfig 固件"""
    config_simple = make_thread_config(thread_id="session-42")
    assert config_simple == {"configurable": {"thread_id": "session-42"}}

    config_with_cp = make_thread_config(thread_id="session-42", checkpoint_id="cp-007")
    assert config_with_cp == {
        "configurable": {
            "thread_id": "session-42",
            "checkpoint_id": "cp-007",
        }
    }


def test_langgraph_dependency_import() -> None:
    """验证 LangGraph 核心图与状态机原语可正常从底层加载"""
    from langgraph.checkpoint.base import BaseCheckpointSaver
    from langgraph.graph import END, START, StateGraph

    assert START == "__start__"
    assert END == "__end__"
    assert StateGraph is not None
    assert BaseCheckpointSaver is not None


def test_minimal_state_schema_introspection() -> None:
    """验证 TypedDict 状态模式的字段自省与类型注解正确性"""
    annotations = MinimalState.__annotations__
    assert "messages" in annotations
    assert "flag" in annotations
