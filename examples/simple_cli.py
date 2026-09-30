"""
Jarvis Agent Pro - 原型交互式 CLI (Simple Prototype CLI)

演示基于 Phase 6 条件边与 ReAct 自适应闭环的自动化推演过程。
运行方式:
    uv run python examples/simple_cli.py
"""

from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from graph.react_graph import build_react_agent_graph
from nodes.planner import create_planner_node
from nodes.tool_executor import create_tool_node
from state.agent_state import AgentState


class DemoModel:
    """轻量演示模型桩：模拟根据上下文自主判断是否调用工具"""

    def __init__(self) -> None:
        self.step = 0

    def invoke(self, messages: list[Any]) -> AIMessage:
        self.step += 1
        # 第一步：根据用户问题决定调用计算工具
        if self.step == 1:
            return AIMessage(
                content="我需要使用计算工具来评估该算式。",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": "25 * 40 + 150"},
                        "id": "call_calc_demo",
                        "type": "tool_call",
                    }
                ],
            )
        # 第二步：接收到工具计算结果后输出最终答复
        return AIMessage(content="经过计算，25 * 40 + 150 的准确结果是 1150。")


def calculator(expression: str) -> str:
    """简单的算术计算器工具"""
    try:
        # 安全计算简单算式
        allowed_chars = set("0123456789+-*/ ()")
        if not set(expression).issubset(allowed_chars):
            return "错误: 非法字符"
        return str(eval(expression))  # noqa: S307
    except Exception as e:
        return f"计算错误: {e!s}"


def main() -> None:
    print("==================================================")
    print("   Jarvis Agent Pro - 原型验证 CLI (ReAct 闭环)   ")
    print("==================================================")

    model = DemoModel()
    planner = create_planner_node(model=model, system_prompt="你是由 DeepMind 设计的自主助理。")
    tool_executor = create_tool_node(tools={"calculator": calculator})

    # 装配 ReAct 自适应闭环状态图
    app = build_react_agent_graph(planner_node=planner, tool_node=tool_executor)

    query = "请帮我计算 25 * 40 + 150 的数值并给出总结。"
    print(f"\n[用户指令]: {query}\n")

    initial_state: AgentState = {
        "messages": [HumanMessage(content=query)],
        "task_goal": "数学求值",
        "plan": None,
        "pending_action": None,
        "approval_status": None,
        "scratchpad": [],
        "branch_results": {},
        "metadata": {},
    }

    # 执行图推演
    result = app.invoke(initial_state)

    print("[执行链路追踪]:")
    for idx, msg in enumerate(result["messages"]):
        if isinstance(msg, HumanMessage):
            print(f"  {idx + 1}. [User] {msg.content}")
        elif isinstance(msg, AIMessage) and getattr(msg, "tool_calls", None):
            calls = [f"{tc['name']}({tc['args']})" for tc in msg.tool_calls]
            print(f"  {idx + 1}. [Thought/Action] {msg.content} -> 触发: {', '.join(calls)}")
        elif isinstance(msg, ToolMessage):
            print(f"  {idx + 1}. [Observation] 来自工具 [{msg.name}]: {msg.content}")
        elif isinstance(msg, AIMessage):
            print(f"  {idx + 1}. [Final Answer] {msg.content}")

    print("\n[状态草稿痕迹]:")
    for log in result["scratchpad"]:
        print(f"  - {log}")

    print("\n==================================================")
    print("执行完毕，ReAct 自适应循环成功抵达 END 节点。")
    print("==================================================")


if __name__ == "__main__":
    main()
