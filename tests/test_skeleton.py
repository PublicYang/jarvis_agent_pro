"""
Phase 1 测试: 验证项目骨架、包定义、模块边界与导入连通性
"""

import importlib
import sys
import pytest

CORE_PACKAGES = [
    "graph",
    "nodes",
    "state",
    "tools",
    "checkpoints",
]


@pytest.mark.parametrize("package_name", CORE_PACKAGES)
def test_package_importability(package_name: str):
    """验证核心分层包均可被正常导入，不存在语法错误或路径中断"""
    module = importlib.import_module(package_name)
    assert module is not None
    assert hasattr(module, "__version__")
    assert module.__version__ == "0.1.0"
    assert module.__doc__ is not None
    assert len(module.__doc__.strip()) > 0


def test_circular_imports():
    """验证模块间没有产生任何循环导入"""
    # 模拟重载测试循环依赖
    for pkg in CORE_PACKAGES:
        if pkg in sys.modules:
            del sys.modules[pkg]
        mod = importlib.import_module(pkg)
        assert mod is not None


def test_layer_boundary_declarations():
    """验证分层包的语义定位与文档契约匹配"""
    import graph
    import nodes
    import state
    import tools
    import checkpoints

    assert "图拓扑" in graph.__doc__
    assert "节点计算" in nodes.__doc__
    assert "状态语义" in state.__doc__
    assert "工具执行" in tools.__doc__
    assert "检查点" in checkpoints.__doc__
