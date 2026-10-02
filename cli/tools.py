"""
Jarvis Agent Pro - CLI 内置工具集与敏感工具注册 (CLI Builtin Tools & Registry)

提供终端运行环境下的常用工具（计算、系统信息、安全读文件）
以及用于验证人机协同 (HITL) 中断机制的敏感高危工具。
"""

import os
import platform
from collections.abc import Callable
from typing import Any


def calculator(expression: str) -> str:
    """安全基础算术计算器，支持 +, -, *, /, (, ) 与数字。"""
    try:
        allowed = set("0123456789+-*/ ().")
        if not set(expression).issubset(allowed):
            return "错误: 表达式包含不支持的非法字符。"
        result = eval(expression)  # noqa: S307
        return str(result)
    except Exception as exc:
        return f"计算失败: {exc!s}"


def get_system_info() -> str:
    """获取当前宿主机操作系统及 Python 环境信息。"""
    return (
        f"OS: {platform.system()} {platform.release()} ({platform.machine()})\n"
        f"Python: {platform.python_version()}\n"
        f"Working Directory: {os.getcwd()}"
    )


def read_file(file_path: str) -> str:
    """读取本地文件前 100 行内容。"""
    try:
        if not os.path.exists(file_path):
            return f"错误: 文件未找到: {file_path}"
        with open(file_path, encoding="utf-8", errors="replace") as f:
            lines = [f.readline() for _ in range(100)]
        return "".join(lines)
    except Exception as exc:
        return f"读取文件失败: {exc!s}"


def danger_delete_file(file_path: str) -> str:
    """高危工具：模拟删除指定敏感文件（需经由终端人工核准）。"""
    return f"[模拟执行] 文件 '{file_path}' 已被安全移至回收站。"


# CLI 注册的全部可用工具
CLI_TOOLS: dict[str, Callable[..., Any]] = {
    "calculator": calculator,
    "get_system_info": get_system_info,
    "read_file": read_file,
    "danger_delete_file": danger_delete_file,
}

# 必须触发人工审批的中断高危工具列表
CLI_SENSITIVE_TOOLS: frozenset[str] = frozenset({"danger_delete_file", "execute_shell"})
