"""
Jarvis Agent Pro - 工具执行层 (Tools Layer)

封装与外部物理环境交互的能力契约（文件系统、Shell、网络请求、MCP Client）。
工具与图引擎解耦，仅处理标准化参数输入并返回观察结果 (Observation)。
"""

__version__ = "0.1.0"
__all__ = ["__version__"]
