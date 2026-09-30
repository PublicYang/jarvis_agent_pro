"""
Phase 6 测试: 验证条件边 (Conditional Edge)、Router 决策分发、ReAct 动态反馈闭环与递归深度熔断
"""

from typing import Any
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.errors import GraphRecursionError

from graph.react_graph import build_react_agent_graph
from graph.router import (
    ROUTER_ACTION_END,
    ROUTER_ACTION_TOOLS,
    route_planner_decision,
)
from nodes.planner import create_planner_node
from nodes.tool_executor import create_tool_node
from state.agent_state import AgentState


def test_route_planner_decision_branches() -> None:
    """验证 Router 路由函数在各种状态下的分支推导正确性"""
    # 1. 状态为空消息 -> 路由至 END
    assert route_planner_decision({"messages": []}) == ROUTER_ACTION_END  # type: ignore[typeddict-item]

    # 2. 状态末尾为用户消息 -> 路由至 END
    assert (
        route_planner_decision({"messages": [HumanMessage(content="test")]})  # type: ignore[typeddict-item]
        == ROUTER_ACTION_END
    )

    # 3. 状态末尾为无工具调用的普通 AIMessage -> 路由至 END
    assert (
        route_planner_decision({"messages": [AIMessage(content="Final Answer")]})  # type: ignore[typeddict-item]
        == ROUTER_ACTION_END
    )

    # 4. 状态末尾包含结构化 tool_calls -> 路由至 tool_executor
    msg_with_tool = AIMessage(
        content="",
        tool_calls=[{"name": "search", "args": {}, "id": "c1", "type": "tool_call"}],
    )
    assert (
        route_planner_decision({"messages": [msg_with_tool]})  # type: ignore[typeddict-item]
        == ROUTER_ACTION_TOOLS
    )


def test_react_loop_end_to_end_trajectory() -> None:
    """验证完整的 ReAct 闭环多超步推演 (Thought -> Action -> Observation -> Final Answer)"""
    call_count = 0

    def mock_model_invoke(messages: list[Any]) -> AIMessage:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # 第一次思考：决定调用查询工具
            return AIMessage(
                content="查询股价中...",
                tool_calls=[
                    {
                        "name": "get_stock_price",
                        "args": {"symbol": "AAPL"},
                        "id": "call_aapl_001",
                        "type": "tool_call",
                    }
                ],
            )
        # 第二次思考：收到工具观察结果，输出最终答复
        return AIMessage(content="苹果公司当前股价为 225 美元。")

    mock_model = MagicMock()
    mock_model.invoke.side_effect = mock_model_invoke
    planner = create_planner_node(model=mock_model)

    def get_stock_price(symbol: str) -> str:
        return f"{symbol}: 225 USD"

    tool_node = create_tool_node(tools={"get_stock_price": get_stock_price})

    # 装配 ReAct 闭环图
    app = build_react_agent_graph(planner_node=planner, tool_node=tool_node)

    initial_state: AgentState = {
        "messages": [HumanMessage(content="请帮我查一下苹果股价")],
        "task_goal": "查询股价",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    final_state = app.invoke(initial_state)

    # 验证消息轨迹完整闭环
    messages = final_state["messages"]
    assert len(messages) == 4
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[1], AIMessage) and bool(messages[1].tool_calls)
    assert isinstance(messages[2], ToolMessage) and "AAPL: 225 USD" in messages[2].content
    assert isinstance(messages[3], AIMessage) and "225 美元" in messages[3].content

    # 验证 Planner 被调用了两次（循环产生生效）
    assert call_count == 2


def test_react_direct_answer_skips_tool_executor() -> None:
    """验证当模型认为无需工具时直接流向 END，工具节点绝不触发"""
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(content="你好，很高兴为你服务！")
    planner = create_planner_node(model=mock_model)

    mock_tool = MagicMock()
    tool_node = create_tool_node(tools={"mock_tool": mock_tool})

    app = build_react_agent_graph(planner_node=planner, tool_node=tool_node)

    initial_state: AgentState = {
        "messages": [HumanMessage(content="你好")],
        "task_goal": "日常闲聊",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    final_state = app.invoke(initial_state)

    # 验证工具未被调用
    mock_tool.assert_not_called()
    assert len(final_state["messages"]) == 2
    assert final_state["messages"][1].content == "你好，很高兴为你服务！"


def test_recursion_limit_guard_prevents_infinite_loop() -> None:
    """验证死循环防御：当节点持续互相调用时触发 GraphRecursionError 熔断"""
    # 模拟永不停止的死循环 Planner (每次调用产生新的工具调用请求)
    infinite_planner_model = MagicMock()
    infinite_planner_model.invoke.side_effect = lambda msgs: AIMessage(
        content="继续执行下一个工具",
        tool_calls=[{"name": "ping", "args": {}, "id": f"loop_{len(msgs)}", "type": "tool_call"}],
    )
    planner = create_planner_node(model=infinite_planner_model)
    tool_node = create_tool_node(tools={"ping": lambda: "pong"})

    app = build_react_agent_graph(planner_node=planner, tool_node=tool_node)

    initial_state: AgentState = {
        "messages": [HumanMessage(content="进入死循环")],
        "task_goal": "测试死循环",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    # 设置 recursion_limit=5，验证安全熔断
    with pytest.raises(GraphRecursionError):
        app.invoke(initial_state, config={"recursion_limit": 5})
