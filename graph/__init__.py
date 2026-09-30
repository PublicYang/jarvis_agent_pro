"""
Jarvis Agent Pro - 图拓扑组装与编排层 (StateGraph Layer)

负责声明有向图拓扑、静态边 (Static Edge)、条件边 (Conditional Edge)、
路由分发 (Router) 以及图生命周期编译 (Compile)。
"""

from langgraph.graph import END, START

from graph.builder import (
    compile_agent_graph,
    create_agent_graph_builder,
)
from graph.edges import (
    build_linear_agent_graph,
    connect_sequence,
    export_mermaid_diagram,
)

__version__ = "0.1.0"
__all__ = [
    "END",
    "START",
    "__version__",
    "build_linear_agent_graph",
    "compile_agent_graph",
    "connect_sequence",
    "create_agent_graph_builder",
    "export_mermaid_diagram",
]
