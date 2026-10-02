"""
Jarvis Agent Pro - 终端人机协同中断与恢复处理器 (HITL Interrupt & Resume Handler)

负责捕获状态图在敏感操作节点抛出的无状态挂起信号 (__interrupt__)，
协调终端 UI 向用户呈现待审批详情，并将审批决策以 Command(resume=...) 形式
注入图引擎以恢复执行。
"""

from collections.abc import Callable
from typing import Any

from langchain_core.runnables import RunnableConfig
from langgraph.types import Command

from cli.ui import prompt_hitl_approval


def resolve_graph_interrupts(
    app: Any,
    result: dict[str, Any],
    config: RunnableConfig,
    auto_approve: bool = False,
    prompt_callback: Callable[[str, list[dict[str, Any]]], tuple[bool, str]] | None = None,
) -> dict[str, Any]:
    """
    检查并循环处理图执行过程中的所有挂起中断 (Interrupts)。

    Args:
        app: 编译后的 CompiledStateGraph 实例
        result: app.invoke() 产生的执行输出
        config: 带有 thread_id 的 RunnableConfig 配置
        auto_approve: 是否自动批准（适用于非交互式脚本模式）
        prompt_callback: 自定义审批提示回调（默认为终端 UI 交互）

    Returns:
        dict[str, Any]: 最终恢复执行完毕后的状态字典
    """
    current_result = result
    ask_approval = prompt_callback or prompt_hitl_approval

    while "__interrupt__" in current_result:
        interrupts = current_result["__interrupt__"]
        if not interrupts:
            break

        first_interrupt = interrupts[0]
        payload = getattr(first_interrupt, "value", {})
        if not isinstance(payload, dict):
            payload = {}

        task_goal = str(payload.get("task_goal", ""))
        sensitive_calls = payload.get("sensitive_tool_calls", [])

        if auto_approve:
            approved = True
            reason = "非交互模式自动核准"
        else:
            approved, reason = ask_approval(task_goal, sensitive_calls)

        # 构造恢复命令并重新唤醒图执行
        resume_cmd: Any = Command(resume={"approved": approved, "reason": reason})
        current_result = app.invoke(resume_cmd, config=config)

    return current_result
