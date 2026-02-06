"""
neoplugin_registry.py - NeoPlugin 注册表

管理所有已注册的 neoplugins，包括插件实例、lib 模块、元数据和依赖关系
"""

from typing import Any, Optional
from .neoplugin_base import NeoPlugin, NeoPluginMetadata, NeoPluginState


class NeoPluginRegistry:
    """NeoPlugin 注册表 - 管理所有已注册的 neoplugins"""

    def __init__(self):
        """初始化注册表"""
        self._plugins: dict[str, NeoPlugin] = {}  # name -> instance
        self._libs: dict[str, Any] = {}  # name -> module
        self._metadata: dict[str, NeoPluginMetadata] = {}  # name -> metadata
        self._dependency_graph: dict[str, list[str]] = {}  # name -> [deps]

    # === 注册和查询 ===

    def register(self, plugin: NeoPlugin) -> None:
        """
        注册插件实例

        Args:
            plugin: NeoPlugin 实例
        """
        if plugin.metadata is None:
            raise ValueError("Plugin metadata not set")

        name = plugin.metadata.name
        self._plugins[name] = plugin
        self._metadata[name] = plugin.metadata

        # 构建依赖图
        self._dependency_graph[name] = list(plugin.metadata.dependencies.keys())

    def register_lib(self, name: str, module: Any, metadata: NeoPluginMetadata) -> None:
        """
        注册 lib 模块

        Args:
            name: lib 名称
            module: lib 模块对象
            metadata: lib 元数据
        """
        self._libs[name] = module
        self._metadata[name] = metadata

        # 构建依赖图
        self._dependency_graph[name] = list(metadata.dependencies.keys())

    def get_plugin(self, name: str) -> Optional[NeoPlugin]:
        """
        获取插件实例

        Args:
            name: 插件名称

        Returns:
            插件实例，如果不存在则返回 None
        """
        return self._plugins.get(name)

    def get_lib(self, name: str) -> Optional[Any]:
        """
        获取 lib 模块

        Args:
            name: lib 名称

        Returns:
            lib 模块对象，如果不存在则返回 None
        """
        return self._libs.get(name)

    def get_metadata(self, name: str) -> Optional[NeoPluginMetadata]:
        """
        获取元数据

        Args:
            name: 插件/lib 名称

        Returns:
            元数据对象，如果不存在则返回 None
        """
        return self._metadata.get(name)

    def has_plugin(self, name: str) -> bool:
        """
        检查插件是否已注册

        Args:
            name: 插件名称

        Returns:
            如果已注册返回 True，否则返回 False
        """
        return name in self._plugins or name in self._libs

    def list_all(self) -> list[str]:
        """
        列出所有已注册的插件名称

        Returns:
            插件名称列表
        """
        return list(set(self._plugins.keys()) | set(self._libs.keys()))

    # === 依赖管理 ===

    def get_dependencies(self, name: str) -> list[str]:
        """
        获取插件的依赖列表

        Args:
            name: 插件名称

        Returns:
            依赖列表
        """
        return self._dependency_graph.get(name, [])

    def get_dependents(self, name: str) -> list[str]:
        """
        获取依赖此插件的其他插件列表

        Args:
            name: 插件名称

        Returns:
            依赖此插件的插件列表
        """
        dependents = []
        for plugin_name, deps in self._dependency_graph.items():
            if name in deps:
                dependents.append(plugin_name)
        return dependents

    def build_dependency_graph(self) -> None:
        """构建依赖图（已在注册时自动构建）"""
        pass

    # === 状态管理 ===

    def get_state(self, name: str) -> Optional[NeoPluginState]:
        """
        获取插件状态

        Args:
            name: 插件名称

        Returns:
            插件状态，如果不存在则返回 None
        """
        plugin = self._plugins.get(name)
        if plugin:
            return plugin.state
        return None

    def set_state(self, name: str, state: NeoPluginState) -> None:
        """
        设置插件状态

        Args:
            name: 插件名称
            state: 新状态
        """
        plugin = self._plugins.get(name)
        if plugin:
            plugin._set_state(state)

    def __repr__(self) -> str:
        return f"<NeoPluginRegistry plugins={len(self._plugins)} libs={len(self._libs)}>"
