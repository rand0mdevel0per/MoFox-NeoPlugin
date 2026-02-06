"""
plugin.py - Hello NeoPlugin 示例插件

展示如何创建一个简单的 NeoPlugin
"""

from src.neoplugin_base import NeoPlugin
from src.plugin_system import (
    BaseCommand,
    BaseTool,
    ChatType,
    CommandArgs,
    ComponentInfo,
    ToolParamType,
)


class HelloNeoPlugin(NeoPlugin):
    """Hello NeoPlugin 示例插件"""

    # === 生命周期钩子 ===

    async def on_register(self) -> None:
        """注册时调用"""
        print(f"✨ {self.metadata.name} 已注册")

    async def on_load(self) -> None:
        """加载时调用"""
        print(f"🚀 {self.metadata.name} 已加载")

    async def on_enable(self) -> None:
        """启用时调用"""
        print(f"✅ {self.metadata.name} 已启用")

    # === 组件注册 ===

    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """返回插件的所有组件"""
        components = []

        # 注册命令
        components.append((HelloCommand.get_command_info(), HelloCommand))

        # 注册工具
        components.append((HelloTool.get_tool_info(), HelloTool))

        return components


# === 组件定义 ===

class HelloCommand(BaseCommand):
    """一个简单的 /hello 命令"""

    command_name = "hello_neo"
    command_description = "来自 NeoPlugin 的问候"
    chat_type_allow = ChatType.ALL

    async def execute(self, args: CommandArgs) -> tuple[bool, str | None, bool]:
        """执行命令"""
        await self.send_text("👋 Hello from NeoPlugin! 这是一个示例插件。")
        return True, "成功发送问候", True


class HelloTool(BaseTool):
    """一个简单的示例工具"""

    name = "hello_neo_tool"
    description = "一个来自 NeoPlugin 的示例工具"
    available_for_llm = True
    parameters = [
        ("message", ToolParamType.STRING, "要处理的消息", True, None),
    ]

    async def execute(self, function_args: dict) -> dict:
        """执行工具"""
        message = function_args.get("message", "")
        return {
            "name": self.name,
            "content": f"NeoPlugin 收到消息: {message}"
        }
