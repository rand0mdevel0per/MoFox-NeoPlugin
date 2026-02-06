"""
plugin.py - NeoPlugin 加载器插件

在 MoFox 启动时加载所有 neoplugins
"""

import sys
from pathlib import Path
from typing import ClassVar

from src.common.logger import get_logger
from src.plugin_system import (
    BaseEventHandler,
    BasePlugin,
    ComponentInfo,
    EventType,
    register_plugin,
)
from src.plugin_system.base.base_event import HandlerResult

logger = get_logger("nmfpm_loader")


class NeoPluginStartupHandler(BaseEventHandler):
    """启动时加载所有 neoplugins 的事件处理器"""

    handler_name = "neoplugin_startup_handler"
    handler_description = "在 MoFox 启动时加载所有 neoplugins"
    init_subscribe: ClassVar[list[EventType]] = [EventType.ON_START]

    async def execute(self, params: dict) -> HandlerResult:
        """执行 neoplugin 加载"""
        try:
            logger.info("🚀 NeoPlugin 系统启动中...")

            # 获取 MoFox 根目录
            mofox_root = Path.cwd()
            nmfpm_dir = mofox_root / ".nmfpm"
            installed_dir = nmfpm_dir / "installed"

            # 检查 .nmfpm 目录是否存在
            if not installed_dir.exists():
                logger.info("📦 .nmfpm/installed 目录不存在，跳过 neoplugin 加载")
                return HandlerResult(success=True, continue_process=True)

            # 添加 NeoPlugin 源码路径到 sys.path
            # 假设 nmfpm_loader 插件所在目录的父目录包含 src/
            loader_dir = Path(__file__).parent
            neoplugin_src = loader_dir.parent / "src"

            if neoplugin_src.exists():
                sys.path.insert(0, str(neoplugin_src.parent))
            else:
                logger.warning("⚠️ NeoPlugin 源码目录不存在，尝试从已安装位置导入")

            # 导入 NeoPlugin 核心模块
            try:
                from src.neoplugin_loader import NeoPluginLoader
                from src.neoplugin_registry import NeoPluginRegistry
            except ImportError as e:
                logger.error(f"❌ 无法导入 NeoPlugin 核心模块: {e}")
                return HandlerResult(success=False, continue_process=True)

            # 创建注册表和加载器
            registry = NeoPluginRegistry()
            loader = NeoPluginLoader(installed_dir, registry)

            # 注册所有 neoplugins
            logger.info("📋 正在扫描和注册 neoplugins...")
            success_count, fail_count = await loader.register_all_plugins()

            if success_count > 0:
                logger.info(f"✅ 成功注册 {success_count} 个 neoplugins")
            if fail_count > 0:
                logger.warning(f"⚠️ {fail_count} 个 neoplugins 注册失败")

            # 加载所有已注册的 neoplugins
            logger.info("🔄 正在加载 neoplugins...")
            loaded_count = 0
            for plugin_name in registry.list_all():
                if await loader.load_plugin(plugin_name):
                    loaded_count += 1
                    logger.debug(f"  ✓ {plugin_name} 加载成功")
                else:
                    logger.warning(f"  ✗ {plugin_name} 加载失败")

            logger.info(f"🎉 NeoPlugin 系统启动完成！已加载 {loaded_count} 个插件")

            return HandlerResult(success=True, continue_process=True)

        except Exception as e:
            logger.error(f"❌ NeoPlugin 系统启动失败: {e}", exc_info=True)
            return HandlerResult(success=False, continue_process=True)


@register_plugin
class NmfpmLoaderPlugin(BasePlugin):
    """NeoPlugin 加载器插件"""

    plugin_name = "nmfpm_loader"
    enable_plugin: bool = True
    dependencies: ClassVar = []
    python_dependencies: ClassVar = []

    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """返回插件的所有组件"""
        components: list[tuple[ComponentInfo, type]] = []

        # 注册启动事件处理器
        components.append((
            NeoPluginStartupHandler.get_handler_info(),
            NeoPluginStartupHandler
        ))

        return components
