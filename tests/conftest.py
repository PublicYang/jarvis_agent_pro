"""
Jarvis Agent Pro - 全局测试固件与基础设施 (conftest.py)

提供可复用的消息构造、线程配置生成器与模拟组件，
为全图生命周期与各层单测提供标准测试基底。
"""

from collections.abc import Callable
from typing import Any

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig


@pytest.fixture
def make_human_message() -> Callable[[str], HumanMessage]:
    """生成标准用户消息的工厂固件"""

    def _factory(content: str = "执行目标任务") -> HumanMessage:
        return HumanMessage(content=content)

    return _factory


@pytest.fixture
def make_ai_tool_call_message() -> Callable[[str, dict[str, Any], str], AIMessage]:
    """生成带有工具调用请求的 AI 消息工厂固件"""

    def _factory(
        tool_name: str = "search_code",
        tool_args: dict[str, Any] | None = None,
        call_id: str = "call_mock_001",
    ) -> AIMessage:
        args = tool_args or {"query": "StateGraph"}
        return AIMessage(
            content="",
            tool_calls=[
                {
                    "name": tool_name,
                    "args": args,
                    "id": call_id,
                    "type": "tool_call",
                }
            ],
        )

    return _factory


@pytest.fixture
def make_tool_message() -> Callable[[str, str], ToolMessage]:
    """生成工具执行结果观察消息的工厂固件"""

    def _factory(content: str = "执行成功", call_id: str = "call_mock_001") -> ToolMessage:
        return ToolMessage(content=content, tool_call_id=call_id)

    return _factory


@pytest.fixture
def make_thread_config() -> Callable[[str, str | None], RunnableConfig]:
    """生成 LangGraph 标准 RunnableConfig 运行配置的工厂固件"""

    def _factory(
        thread_id: str = "test-session-001", checkpoint_id: str | None = None
    ) -> RunnableConfig:
        configurable: dict[str, Any] = {"thread_id": thread_id}
        if checkpoint_id:
            configurable["checkpoint_id"] = checkpoint_id
        return {"configurable": configurable}

    return _factory
