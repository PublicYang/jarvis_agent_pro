"""
Phase 5 测试: 验证静态边 (Static Edges)、START/END 拓扑连通、顺序执行流与 Mermaid 图导出
"""

from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langgraph.graph import END, START

from graph.builder import create_agent_graph_builder
from graph.edges import (
    build_linear_agent_graph,
    connect_sequence,
    export_mermaid_diagram,
)
from nodes.planner import create_planner_node
from nodes.tool_executor import create_tool_node
from state.agent_state import AgentState


def test_connect_sequence_builds_edges() -> None:
    """验证 connect_sequence 正确将多个节点按序连线"""
    builder = create_agent_graph_builder(AgentState)

    builder.add_node("step_a", lambda s: {"scratchpad": ["a"]})
    builder.add_node("step_b", lambda s: {"scratchpad": ["b"]})
    connect_sequence(builder, [START, "step_a", "step_b", END])

    compiled = builder.compile()
    graph_repr = compiled.get_graph()

    # 验证节点存在
    assert "step_a" in graph_repr.nodes
    assert "step_b" in graph_repr.nodes

    # 验证边连接关系
    edge_pairs = {(e.source, e.target) for e in graph_repr.edges}
    assert (START, "step_a") in edge_pairs
    assert ("step_a", "step_b") in edge_pairs
    assert ("step_b", END) in edge_pairs


def test_connect_sequence_invalid_length_raises() -> None:
    """验证节点序列不足 2 个时抛出 ValueError"""
    builder = create_agent_graph_builder(AgentState)
    with pytest.raises(ValueError, match="节点序列至少需要包含 2 个节点"):
        connect_sequence(builder, ["single_node"])


def test_build_linear_agent_graph_execution() -> None:
    """验证包含 Planner 与 Tool Executor 的标准线性流端到端静态流转"""
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(
        content="准备查询系统负载",
        tool_calls=[{"name": "get_load", "args": {}, "id": "call_load_1", "type": "tool_call"}],
    )
    planner = create_planner_node(model=mock_model)

    def get_load() -> str:
        return "CPU: 12%, Memory: 45%"

    tool_node = create_tool_node(tools={"get_load": get_load})

    # 装配标准线性图: START -> planner -> tool_executor -> END
    compiled = build_linear_agent_graph(planner_node=planner, tool_node=tool_node)

    initial_state: AgentState = {
        "messages": [HumanMessage(content="查询当前系统状态")],
        "task_goal": "系统状态自检",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    result = compiled.invoke(initial_state)

    # 验证消息流顺序推进：HumanMessage -> AIMessage -> ToolMessage
    messages = result["messages"]
    assert len(messages) == 3
    assert isinstance(messages[0], HumanMessage)
    assert isinstance(messages[1], AIMessage)
    assert isinstance(messages[2], ToolMessage)
    assert "CPU: 12%" in messages[2].content

    # 验证 Scratchpad 顺序累加
    assert len(result["scratchpad"]) == 2
    assert "Planner 决策" in result["scratchpad"][0]
    assert "Tool [get_load] 执行成功" in result["scratchpad"][1]


def test_build_linear_agent_graph_without_tools() -> None:
    """验证无工具时的简易线性流: START -> planner -> END"""
    mock_model = MagicMock()
    mock_model.invoke.return_value = AIMessage(content="直接答复内容")
    planner = create_planner_node(model=mock_model)

    compiled = build_linear_agent_graph(planner_node=planner, tool_node=None)

    initial_state: AgentState = {
        "messages": [HumanMessage(content="打个招呼")],
        "task_goal": "问答",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    result = compiled.invoke(initial_state)
    assert len(result["messages"]) == 2
    assert result["messages"][1].content == "直接答复内容"


def test_export_mermaid_diagram() -> None:
    """验证 Mermaid 流程图文本导出与节点拓扑完整性"""
    builder = create_agent_graph_builder(AgentState)
    builder.add_node("planner", lambda s: {})
    builder.add_node("tool_executor", lambda s: {})
    connect_sequence(builder, [START, "planner", "tool_executor", END])

    compiled = builder.compile()
    mermaid_str = export_mermaid_diagram(compiled)

    assert isinstance(mermaid_str, str)
    assert len(mermaid_str) > 0
    # 验证包含核心节点标记
    assert "planner" in mermaid_str
    assert "tool_executor" in mermaid_str


def test_invalid_edge_connectivity_rejected() -> None:
    """验证向不存在的节点声明静态边时，编译期抛出拓扑异常"""
    builder = create_agent_graph_builder(AgentState)
    builder.add_node("existing_node", lambda s: {})

    # 连接到未注册的幽灵节点
    builder.add_edge("existing_node", "ghost_node")

    with pytest.raises(ValueError):
        builder.compile()
