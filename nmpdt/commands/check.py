"""
check.py - 检查插件质量

运行代码质量检查和静态分析
"""

import subprocess
import sys
from pathlib import Path


def check_plugin(plugin_path: Path, fix: bool = False):
    """检查插件质量"""
    print(f"🔍 检查插件: {plugin_path}")
    print()

    if not plugin_path.exists():
        print(f"❌ 错误: 路径不存在: {plugin_path}")
        sys.exit(1)

    # 1. 运行结构检查
    print("📁 [1/2] 结构检查...")
    check_script = Path(__file__).parent.parent.parent / "scripts" / "check_neoplugin.py"

    if check_script.exists():
        result = subprocess.run(
            ["python", str(check_script), str(plugin_path)],
            capture_output=True,
            text=True
        )
        print(result.stdout)
        if result.returncode != 0:
            sys.exit(1)
    else:
        print("  ⚠️  找不到检查脚本")

    # 2. 运行 ruff 检查
    print("🎨 [2/2] 代码风格检查...")
    try:
        cmd = ["ruff", "check", str(plugin_path)]
        if fix:
            cmd.append("--fix")

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.stdout:
            print(result.stdout)

        if result.returncode != 0:
            print("  ⚠️  发现代码风格问题")
            if not fix:
                print("  提示: 使用 --fix 自动修复")
        else:
            print("  ✅ 代码风格良好")
    except FileNotFoundError:
        print("  ⚠️  ruff 未安装，跳过代码风格检查")

    print()
    print("✅ 检查完成！")
