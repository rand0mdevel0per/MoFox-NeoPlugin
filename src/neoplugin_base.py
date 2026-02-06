"""
neoplugin_base.py - NeoPlugin 基类

提供细致的生命周期管理和高级抽象
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.plugin_system.base.component_types import ComponentInfo


class NeoPluginState(Enum):
    """NeoPlugin 状态枚举"""
    UNREGISTERED = "unregistered"  # 未注册
    REGISTERED = "registered"      # 已注册（启动时）
    LOADING = "loading"            # 加载中（lazy-load）
    LOADED = "loaded"              # 已加载
    ENABLED = "enabled"            # 已启用
    DISABLED = "disabled"          # 已禁用
    UNLOADING = "unloading"        # 卸载中
    UNLOADED = "unloaded"          # 已卸载
    ERROR = "error"                # 错误状态


class NeoPluginMetadata:
    """NeoPlugin 元数据（从 manifest.toml 解析）"""

    def __init__(self, manifest_data: dict):
        """
        从 manifest.toml 数据初始化元数据

        Args:
            manifest_data: 解析后的 manifest.toml 数据
        """
        package = manifest_data.get("package", {})

        self.name: str = package.get("name", "")
        self.version: str = package.get("version", "")
        self.description: str = package.get("description", "")
        self.authors: list[str] = package.get("authors", [])
        self.license: str = package.get("license", "")
        self.keywords: list[str] = package.get("keywords", [])
        self.categories: list[str] = package.get("categories", [])

        # 类型标识
        self.is_lib: bool = package.get("lib", False)

        # 版本要求
        self.mofox_version: str = package.get("mofox_version", "")

        # 依赖
        self.dependencies: dict[str, str] = manifest_data.get("dependencies", {})
        self.python_dependencies: dict[str, str] = manifest_data.get("python_dependencies", {})

        # 注入配置
        self.inject_configs: list[dict] = manifest_data.get("inject", [])

        # 生命周期钩子
        self.hooks: dict[str, str] = manifest_data.get("hooks", {})

    def __repr__(self) -> str:
        return f"<NeoPluginMetadata {self.name} v{self.version}>"


class NeoPlugin(ABC):
    """NeoPlugin 基类 - 提供细致的生命周期管理和高级抽象"""

    def __init__(self):
        """初始化 NeoPlugin 实例"""
        self.metadata: Optional[NeoPluginMetadata] = None
        self.plugin_path: Optional[Path] = None
        self.state: NeoPluginState = NeoPluginState.UNREGISTERED
        self._registry: Optional[Any] = None  # NeoPluginRegistry 实例

    # === 生命周期钩子（子类可重写）===

    async def on_register(self) -> None:
        """注册时调用（启动时，所有插件一次性注册）"""
        pass

    async def on_load(self) -> None:
        """加载时调用（lazy-load，异步）"""
        pass

    async def on_enable(self) -> None:
        """启用时调用"""
        pass

    async def on_disable(self) -> None:
        """禁用时调用"""
        pass

    async def on_unload(self) -> None:
        """卸载时调用"""
        pass

    async def on_reload(self) -> None:
        """热重载时调用"""
        pass

    async def on_config_change(self, key: str, old_value: Any, new_value: Any) -> None:
        """配置变更时调用"""
        pass

    async def on_dependency_loaded(self, dep_name: str) -> None:
        """依赖加载完成时调用"""
        pass

    # === 组件注册（类似现有系统）===

    def get_plugin_components(self) -> list[tuple['ComponentInfo', type]]:
        """返回插件的所有组件（Actions, Commands, Tools 等）"""
        return []

    # === 依赖注入 ===

    def get_dependency(self, name: str) -> Any:
        """获取依赖的 lib 或 plugin 实例"""
        if self._registry is None:
            raise RuntimeError("Plugin registry not set")

        # 先尝试获取 plugin
        plugin = self._registry.get_plugin(name)
        if plugin is not None:
            return plugin

        # 再尝试获取 lib
        lib = self._registry.get_lib(name)
        if lib is not None:
            return lib

        raise KeyError(f"Dependency '{name}' not found")

    # === 配置管理 ===

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径，如 'section.key'）"""
        # TODO: 实现配置管理
        return default

    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        # TODO: 实现配置管理
        pass

    # === 内部方法 ===

    def _set_registry(self, registry: Any) -> None:
        """设置注册表实例（由加载器调用）"""
        self._registry = registry

    def _set_metadata(self, metadata: NeoPluginMetadata) -> None:
        """设置元数据（由加载器调用）"""
        self.metadata = metadata

    def _set_plugin_path(self, path: Path) -> None:
        """设置插件路径（由加载器调用）"""
        self.plugin_path = path

    def _set_state(self, state: NeoPluginState) -> None:
        """设置状态（由加载器调用）"""
        self.state = state

    def __repr__(self) -> str:
        if self.metadata:
            return f"<NeoPlugin {self.metadata.name} v{self.metadata.version} [{self.state.value}]>"
        return f"<NeoPlugin [uninitialized]>"
