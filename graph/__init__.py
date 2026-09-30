"""
Jarvis Agent Pro - 图拓扑组装与编排层 (StateGraph Layer)

负责声明有向图拓扑、静态边 (Static Edge)、条件边 (Conditional Edge)、
路由分发 (Router) 以及图生命周期编译 (Compile)。
"""

from graph.builder import (
    compile_agent_graph,
    create_agent_graph_builder,
)

__version__ = "0.1.0"
__all__ = [
    "__version__",
    "create_agent_graph_builder",
    "compile_agent_graph",
]
