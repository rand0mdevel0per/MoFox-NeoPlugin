"""
init.py - 初始化新插件项目

创建插件项目的基本结构和模板文件
"""

import sys
from pathlib import Path


def init_project(name: str, template: str):
    """初始化新插件项目"""
    print(f"🚀 初始化插件项目: {name}")
    print(f"📋 模板: {template}")
    print()

    # 创建项目目录
    project_dir = Path(name)
    if project_dir.exists():
        print(f"❌ 错误: 目录 {name} 已存在")
        sys.exit(1)

    project_dir.mkdir()
    print(f"✅ 创建目录: {name}/")

    # 创建 manifest.toml
    manifest_content = f"""[package]
name = "{name}"
version = "1.0.0"
description = "插件描述"
authors = ["Your Name"]
license = "MIT"
keywords = []
categories = []

lib = false

mofox_version = ">=0.10.0"

[dependencies]

[python_dependencies]
"""

    manifest_file = project_dir / "manifest.toml"
    manifest_file.write_text(manifest_content, encoding='utf-8')
    print(f"✅ 创建文件: manifest.toml")

    # 创建 __init__.py
    init_content = f'''"""
{name} - NeoPlugin

插件描述
"""

from .plugin import {_to_class_name(name)}

__all__ = ["{_to_class_name(name)}"]
'''

    init_file = project_dir / "__init__.py"
    init_file.write_text(init_content, encoding='utf-8')
    print(f"✅ 创建文件: __init__.py")

    # 创建 plugin.py
    if template == "basic":
        plugin_content = _create_basic_plugin(name)
    else:
        plugin_content = _create_full_plugin(name)

    plugin_file = project_dir / "plugin.py"
    plugin_file.write_text(plugin_content, encoding='utf-8')
    print(f"✅ 创建文件: plugin.py")

    print()
    print("🎉 项目初始化完成！")
    print()
    print("📝 下一步:")
    print(f"  cd {name}")
    print("  # 编辑 manifest.toml 和 plugin.py")
    print("  # 运行检查: python -m nmpdt check")


def _to_class_name(name: str) -> str:
    """将插件名转换为类名"""
    parts = name.replace('-', '_').replace(' ', '_').split('_')
    return ''.join(word.capitalize() for word in parts)


def _create_basic_plugin(name: str) -> str:
    """创建基础插件模板"""
    class_name = _to_class_name(name)
    return f'''"""
plugin.py - {name} 插件

插件主要代码
"""

from src.neoplugin_base import NeoPlugin


class {class_name}(NeoPlugin):
    """
    {name} 插件
    """

    async def on_register(self) -> None:
        """注册时调用"""
        print(f"✨ {{self.metadata.name}} 已注册")

    async def on_load(self) -> None:
        """加载时调用"""
        print(f"🚀 {{self.metadata.name}} 已加载")
'''


def _create_full_plugin(name: str) -> str:
    """创建完整插件模板（包含示例组件）"""
    class_name = _to_class_name(name)
    return f'''"""
plugin.py - {name} 插件

插件主要代码
"""

from src.neoplugin_base import NeoPlugin
from src.plugin_system import (
    BaseCommand,
    ChatType,
    CommandArgs,
    ComponentInfo,
)


class {class_name}(NeoPlugin):
    """
    {name} 插件
    """

    async def on_register(self) -> None:
        """注册时调用"""
        print(f"✨ {{self.metadata.name}} 已注册")

    async def on_load(self) -> None:
        """加载时调用"""
        print(f"🚀 {{self.metadata.name}} 已加载")

    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """返回插件的所有组件"""
        components = []

        # 注册命令
        components.append((ExampleCommand.get_command_info(), ExampleCommand))

        return components


class ExampleCommand(BaseCommand):
    """示例命令"""

    command_name = "example"
    command_description = "示例命令"
    chat_type_allow = ChatType.ALL

    async def execute(self, args: CommandArgs) -> tuple[bool, str | None, bool]:
        """执行命令"""
        await self.send_text("Hello from {name}!")
        return True, "成功", True
'''
