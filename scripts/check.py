"""
Jarvis Agent Pro - 自动化工程质量门禁检查脚本 (check.py)

一键执行:
1. Ruff Linting (静态代码规范与缺陷检查)
2. Ruff Format Check (代码格式与排版检查)
3. Mypy Typecheck (静态强类型校验)
4. Pytest (全量单元测试与回归套件)
"""

import subprocess
import sys


def run_step(step_name: str, cmd: list[str]) -> bool:
    print("\n==================================================")
    print(f"[*] 正在执行: {step_name}")
    print(f"[*] 执行命令: {' '.join(cmd)}")
    print("==================================================")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"[FAIL] 步骤 [{step_name}] 校验失败 (Exit code: {result.returncode})")
        return False
    print(f"[PASS] 步骤 [{step_name}] 校验通过")
    return True


def main() -> None:
    steps = [
        ("Ruff 代码风格检查 (Lint)", ["ruff", "check", "."]),
        ("Ruff 格式排版检查 (Format Check)", ["ruff", "format", "--check", "."]),
        (
            "Mypy 严格类型推导检查 (Typecheck)",
            ["mypy", "graph", "nodes", "state", "tools", "checkpoints", "tests"],
        ),
        ("Pytest 自动化测试套件 (Tests)", ["pytest", "-v"]),
    ]

    for name, cmd in steps:
        if not run_step(name, cmd):
            print("\n[FAILED] 工程质量门禁未通过，请根据上方日志修复后重试。")
            sys.exit(1)

    print("\n==================================================")
    print("[SUCCESS] 全量工程质量门禁 100% 顺利通过！")
    print("==================================================")


if __name__ == "__main__":
    main()
