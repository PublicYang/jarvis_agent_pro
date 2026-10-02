"""
Jarvis Agent Pro - 大语言模型适配工厂 (LLM Adapter Factory)

提供双模支持：
1. 离线零依赖智能 Mock 模型 (DemoModel)：开箱即用，支持多轮意图识别与工具触发；
2. 基于 httpx 实现的通用 OpenAI 兼容客户端 (OpenAICompatibleModel)：兼容 DeepSeek / Ollama / OpenAI / vLLM。
"""

import json
import os
import re
from collections.abc import Sequence
from typing import Any

import httpx
from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)


class DemoModel:
    """
    智能交互 Demo 模型桩。

    用于在无网络或无 API Key 场景下提供确定性的意图规划、工具调度与问答推演。
    """

    def __init__(self) -> None:
        pass

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        if not messages:
            return AIMessage(content="你好！我是 Jarvis Agent Pro。请问有什么我可以帮你的？")

        # 检查最新消息是否为 ToolMessage（表示处于工具执行后的 Observation 阶段）
        last_message = messages[-1]
        if isinstance(last_message, ToolMessage):
            tool_name = getattr(last_message, "name", "工具")
            content = str(last_message.content)
            if "人工驳回" in content:
                return AIMessage(
                    content=f"收到，操作已被人工驳回（{content}）。我已终止该计划并重置状态。"
                )
            return AIMessage(
                content=f"依据【{tool_name}】的执行返回结果：\n\n```\n{content}\n```\n以上任务已顺利完成！"
            )

        # 提取用户的最新提问文本
        user_queries = [m.content for m in messages if isinstance(m, HumanMessage)]
        query = str(user_queries[-1]) if user_queries else ""

        # 1. 意图：删除/高危敏感操作 -> 触发 danger_delete_file (验证 HITL 审批)
        if any(keyword in query for keyword in ("删除", "delete", "清理", "rm", "清空")):
            file_target = "important_data.log"
            match = re.search(r"([a-zA-Z0-9_\-\./]+\.[a-zA-Z0-9]+)", query)
            if match:
                file_target = match.group(1)
            return AIMessage(
                content=f"检测到敏感文件清理需求，我准备调用危险删除工具清理 '{file_target}'。",
                tool_calls=[
                    {
                        "name": "danger_delete_file",
                        "args": {"file_path": file_target},
                        "id": "call_delete_demo",
                        "type": "tool_call",
                    }
                ],
            )

        # 2. 意图：系统信息查询 -> 触发 get_system_info
        if any(
            keyword in query.lower() for keyword in ("系统", "环境", "system", "os", "platform")
        ):
            return AIMessage(
                content="我将调用系统探测工具采集当前宿主机运行环境与 Python 状态。",
                tool_calls=[
                    {
                        "name": "get_system_info",
                        "args": {},
                        "id": "call_sysinfo_demo",
                        "type": "tool_call",
                    }
                ],
            )

        # 3. 意图：数学运算 -> 触发 calculator
        math_match = re.search(r"(\d+[\s\+\-\*/\(\)\.]+\d+)", query)
        if math_match or any(keyword in query for keyword in ("计算", "算式", "求值", "+", "*")):
            expr = math_match.group(1).strip() if math_match else "25 * 40 + 150"
            return AIMessage(
                content=f"为了保证数值准确，我将调用计算器工具对算式 `{expr}` 进行精确求值。",
                tool_calls=[
                    {
                        "name": "calculator",
                        "args": {"expression": expr},
                        "id": "call_calc_demo",
                        "type": "tool_call",
                    }
                ],
            )

        # 4. 默认闲聊/通用问答
        return AIMessage(
            content=(
                f"收到你的指令: “{query}”。\n\n"
                "当前处于 **Jarvis Demo 演示模式**（未连接外部大模型 API）。\n"
                "你可以尝试以下指令体验真实状态图特性：\n"
                "- 🧮 **计算任务**: `帮我计算 125 * 8 + 36` (触发 ReAct 条件边与工具调用)\n"
                "- 💻 **环境查询**: `查看当前系统信息` (触发系统工具)\n"
                "- ⚠️ **敏感审批**: `帮我删除 app.log` (触发 Phase 7 人机协同中断与终端审批)\n"
            )
        )


class OpenAICompatibleModel:
    """
    轻量级 OpenAI 兼容客户端适配器。

    支持接入 DeepSeek / OpenAI / Ollama / LocalAI 等所有标准 chat/completions 服务。
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model_name: str = "gpt-4o",
        temperature: float = 0.0,
        tools_schema: list[dict[str, Any]] | None = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model_name = model_name
        self.temperature = temperature
        self.tools_schema = tools_schema

    def invoke(self, messages: Sequence[BaseMessage]) -> AIMessage:
        """调用远程 API 并将响应解析转换为 LangChain AIMessage。"""
        formatted_messages: list[dict[str, Any]] = []

        for msg in messages:
            if isinstance(msg, SystemMessage):
                formatted_messages.append({"role": "system", "content": str(msg.content)})
            elif isinstance(msg, HumanMessage):
                formatted_messages.append({"role": "user", "content": str(msg.content)})
            elif isinstance(msg, AIMessage):
                payload: dict[str, Any] = {
                    "role": "assistant",
                    "content": str(msg.content or ""),
                }
                tool_calls = getattr(msg, "tool_calls", None)
                if tool_calls:
                    payload["tool_calls"] = [
                        {
                            "id": tc.get("id", "call_default"),
                            "type": "function",
                            "function": {
                                "name": tc.get("name", ""),
                                "arguments": json.dumps(tc.get("args", {})),
                            },
                        }
                        for tc in tool_calls
                    ]
                formatted_messages.append(payload)
            elif isinstance(msg, ToolMessage):
                formatted_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": getattr(msg, "tool_call_id", ""),
                        "content": str(msg.content),
                    }
                )

        payload_body: dict[str, Any] = {
            "model": self.model_name,
            "messages": formatted_messages,
            "temperature": self.temperature,
        }
        if self.tools_schema:
            payload_body["tools"] = self.tools_schema

        try:
            with httpx.Client(timeout=60.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
                resp = client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload_body,
                )
                resp.raise_for_status()
                data = resp.json()

            choice = data["choices"][0]["message"]
            content = choice.get("content") or ""
            raw_tool_calls = choice.get("tool_calls") or []

            parsed_tool_calls: list[dict[str, Any]] = []
            for tc in raw_tool_calls:
                func = tc.get("function", {})
                args_str = func.get("arguments", "{}")
                try:
                    args_dict = json.loads(args_str)
                except Exception:
                    args_dict = {"raw": args_str}
                parsed_tool_calls.append(
                    {
                        "name": func.get("name", ""),
                        "args": args_dict,
                        "id": tc.get("id", ""),
                        "type": "tool_call",
                    }
                )

            return AIMessage(
                content=content,
                tool_calls=parsed_tool_calls if parsed_tool_calls else [],
            )

        except Exception as exc:
            return AIMessage(content=f"❌ LLM API 调用失败: {exc!s}")


def get_model(
    provider: str | None = None,
    model_name: str | None = None,
    api_key: str | None = None,
    base_url: str | None = None,
    demo: bool = False,
    tools_schema: list[dict[str, Any]] | None = None,
) -> tuple[Any, str]:
    """
    解析模型配置并返回模型实例及展示标签。

    Returns:
        tuple[Any, str]: (模型实例, 模型标识标签)
    """
    # 强制指定 Demo 或环境缺少 key 时走 Demo 模型
    active_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if demo or provider == "demo" or not active_api_key:
        return DemoModel(), "DemoMock (离线推演模式)"

    active_base_url = base_url or os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
    active_model = model_name or os.getenv("OPENAI_MODEL_NAME") or "gpt-4o"

    client = OpenAICompatibleModel(
        api_key=active_api_key,
        base_url=active_base_url,
        model_name=active_model,
        tools_schema=tools_schema,
    )
    return client, f"{active_model} ({active_base_url})"
