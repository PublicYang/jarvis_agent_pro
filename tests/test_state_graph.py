"""
Phase 3 测试: 验证 StateGraph 初始化、规约器 (Reducers) 行为与图生命周期编译
"""

from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, RemoveMessage
from langgraph.graph import END, START
from langgraph.graph.message import add_messages
from langgraph.graph.state import CompiledStateGraph

from graph.builder import compile_agent_graph, create_agent_graph_builder
from state.agent_state import (
    AgentState,
    append_reducer,
    merge_dict_reducer,
)


def test_append_reducer_behavior() -> None:
    """验证列表追加规约器的各项合并语义"""
    # 1. 初始为 None 时追加单元素
    assert append_reducer(None, "item1") == ["item1"]

    # 2. 已有列表追加单元素
    assert append_reducer(["a"], "b") == ["a", "b"]

    # 3. 已有列表批量合并列表
    assert append_reducer(["a"], ["b", "c"]) == ["a", "b", "c"]

    # 4. update 为 None 时安全保持不变
    assert append_reducer(["a", "b"], None) == ["a", "b"]


def test_merge_dict_reducer_behavior() -> None:
    """验证字典合并规约器的各项覆盖与保留语义"""
    # 1. 初始为 None 时合并新字典
    assert merge_dict_reducer(None, {"key1": "val1"}) == {"key1": "val1"}

    # 2. 合并无重叠键
    base = {"a": 1}
    assert merge_dict_reducer(base, {"b": 2}) == {"a": 1, "b": 2}

    # 3. 同名键后写入者覆盖
    assert merge_dict_reducer({"a": 1, "b": 2}, {"b": 99, "c": 3}) == {
        "a": 1,
        "b": 99,
        "c": 3,
    }

    # 4. update 为 None 时安全保持不变
    assert merge_dict_reducer({"a": 1}, None) == {"a": 1}


def test_agent_state_annotations_integrity() -> None:
    """验证 AgentState 核心字段声明的完整性"""
    annotations = AgentState.__annotations__
    required_fields = {
        "messages",
        "task_goal",
        "plan",
        "pending_action",
        "approval_status",
        "scratchpad",
        "branch_results",
        "metadata",
    }
    assert required_fields.issubset(annotations.keys())


def test_add_messages_reducer_semantics() -> None:
    """验证官方 add_messages 规约器在消息追加、相同 ID 更新与物理删除的行为"""
    msg1 = HumanMessage(content="Hello", id="msg_1")
    msg2 = AIMessage(content="Hi there", id="msg_2")

    # 1. 追加消息
    step1 = add_messages([], [msg1, msg2])  # type: ignore[arg-type]
    assert isinstance(step1, list)
    assert len(step1) == 2
    first_msg = step1[0]
    assert isinstance(first_msg, BaseMessage)
    assert first_msg.content == "Hello"

    # 2. 相同 ID 原地更新 (Upsert)
    msg2_updated = AIMessage(content="Hi there (updated)", id="msg_2")
    step2 = add_messages(step1, [msg2_updated])  # type: ignore[arg-type]
    assert isinstance(step2, list)
    assert len(step2) == 2
    updated_msg = step2[1]
    assert isinstance(updated_msg, BaseMessage)
    assert updated_msg.content == "Hi there (updated)"

    # 3. RemoveMessage 物理删除
    step3 = add_messages(step2, [RemoveMessage(id="msg_1")])  # type: ignore[arg-type]
    assert isinstance(step3, list)
    assert len(step3) == 1
    remaining_msg = step3[0]
    assert isinstance(remaining_msg, BaseMessage)
    assert remaining_msg.id == "msg_2"


def test_state_graph_creation_and_compilation() -> None:
    """验证 StateGraph 构建器实例化、节点边连接与编译流程"""
    builder = create_agent_graph_builder(AgentState)

    def dummy_node(state: AgentState) -> dict[str, Any]:
        return {
            "scratchpad": ["node_executed"],
            "branch_results": {"status": "ok"},
        }

    builder.add_node("dummy", dummy_node)
    builder.add_edge(START, "dummy")
    builder.add_edge("dummy", END)

    compiled = compile_agent_graph(builder)
    assert isinstance(compiled, CompiledStateGraph)

    # 验证编译后图拓扑结构包含所定义节点
    graph_repr = compiled.get_graph()
    assert "dummy" in graph_repr.nodes


def test_compiled_graph_invocation_with_reducers() -> None:
    """验证编译图运行调用与状态规约器的端到端执行"""
    builder = create_agent_graph_builder(AgentState)

    def step_node(state: AgentState) -> dict[str, Any]:
        return {
            "scratchpad": ["step_one_done"],
            "messages": [AIMessage(content="Step output")],
        }

    builder.add_node("step_node", step_node)
    builder.add_edge(START, "step_node")
    builder.add_edge("step_node", END)

    compiled = compile_agent_graph(builder)

    initial_input: AgentState = {
        "messages": [HumanMessage(content="Start task")],
        "task_goal": "Smoke test",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": ["init"],
        "branch_results": {},
        "metadata": {"test": True},
    }

    final_state = compiled.invoke(initial_input)

    # 验证 Reducers 生效：scratchpad 累加合并，messages 增量追加
    assert final_state["scratchpad"] == ["init", "step_one_done"]
    assert len(final_state["messages"]) == 2
    assert final_state["messages"][0].content == "Start task"
    assert final_state["messages"][1].content == "Step output"
    assert final_state["task_goal"] == "Smoke test"
