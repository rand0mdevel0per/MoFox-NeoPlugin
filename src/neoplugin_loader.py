"""
neoplugin_loader.py - NeoPlugin 加载器

负责扫描、加载和管理 neoplugins
"""

import importlib.util
import sys
import toml
from pathlib import Path
from typing import Optional, Any
from .neoplugin_base import NeoPlugin, NeoPluginMetadata, NeoPluginState
from .neoplugin_registry import NeoPluginRegistry


class NeoPluginLoader:
    """NeoPlugin 加载器 - 负责扫描、加载和管理 neoplugins"""

    def __init__(self, install_dir: Path, registry: NeoPluginRegistry):
        """
        初始化加载器

        Args:
            install_dir: .nmfpm/installed/ 目录路径
            registry: NeoPlugin 注册表实例
        """
        self.install_dir = install_dir
        self.registry = registry
        self._loaded_modules: dict[str, Any] = {}  # name -> module

    # === 扫描和发现 ===

    def scan_plugins(self) -> list[Path]:
        """
        扫描 .nmfpm/installed/ 目录，返回所有插件路径

        Returns:
            插件路径列表
        """
        if not self.install_dir.exists():
            return []

        plugin_paths = []
        for item in self.install_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                manifest_path = item / "manifest.toml"
                if manifest_path.exists():
                    plugin_paths.append(item)

        return plugin_paths

    def load_manifest(self, plugin_path: Path) -> NeoPluginMetadata:
        """
        加载并解析插件的 manifest.toml

        Args:
            plugin_path: 插件目录路径

        Returns:
            NeoPluginMetadata 实例

        Raises:
            FileNotFoundError: manifest.toml 不存在
            ValueError: manifest.toml 格式错误
        """
        manifest_path = plugin_path / "manifest.toml"
        if not manifest_path.exists():
            raise FileNotFoundError(f"manifest.toml not found in {plugin_path}")

        try:
            manifest_data = toml.load(manifest_path)
            return NeoPluginMetadata(manifest_data)
        except Exception as e:
            raise ValueError(f"Failed to parse manifest.toml: {e}")

    # === 注册阶段（启动时一次性执行）===

    async def register_all_plugins(self) -> tuple[int, int]:
        """
        注册所有插件（启动时调用）

        Returns:
            (成功数量, 失败数量)
        """
        plugin_paths = self.scan_plugins()
        success_count = 0
        fail_count = 0

        for plugin_path in plugin_paths:
            try:
                if await self.register_plugin(plugin_path):
                    success_count += 1
                else:
                    fail_count += 1
            except Exception as e:
                print(f"Failed to register plugin at {plugin_path}: {e}")
                fail_count += 1

        return success_count, fail_count

    async def register_plugin(self, plugin_path: Path) -> bool:
        """
        注册单个插件

        1. 加载 manifest.toml
        2. 检查依赖
        3. 导入插件模块
        4. 查找 NeoPlugin 类（如果不是 lib）
        5. 创建实例并调用 on_register()
        6. 注册到 registry

        Args:
            plugin_path: 插件目录路径

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 1. 加载 manifest.toml
            metadata = self.load_manifest(plugin_path)

            # 2. 导入插件模块
            module = self._import_plugin_module(plugin_path, metadata.name)
            if module is None:
                return False

            # 3. 如果是 lib，直接注册模块
            if metadata.is_lib:
                self.registry.register_lib(metadata.name, module, metadata)
                return True

            # 4. 查找 NeoPlugin 类
            plugin_class = self._find_neoplugin_class(module)
            if plugin_class is None:
                print(f"No NeoPlugin class found in {metadata.name}")
                return False

            # 5. 创建实例
            plugin_instance = plugin_class()
            plugin_instance._set_metadata(metadata)
            plugin_instance._set_plugin_path(plugin_path)
            plugin_instance._set_registry(self.registry)
            plugin_instance._set_state(NeoPluginState.REGISTERED)

            # 6. 调用 on_register()
            await plugin_instance.on_register()

            # 7. 注册到 registry
            self.registry.register(plugin_instance)

            return True

        except Exception as e:
            print(f"Failed to register plugin at {plugin_path}: {e}")
            return False

    def _import_plugin_module(self, plugin_path: Path, plugin_name: str) -> Optional[Any]:
        """
        导入插件模块

        Args:
            plugin_path: 插件目录路径
            plugin_name: 插件名称

        Returns:
            模块对象，失败返回 None
        """
        # 查找 __init__.py 或 plugin.py
        init_file = plugin_path / "__init__.py"
        plugin_file = plugin_path / "plugin.py"

        module_file = None
        if init_file.exists():
            module_file = init_file
        elif plugin_file.exists():
            module_file = plugin_file
        else:
            print(f"No __init__.py or plugin.py found in {plugin_path}")
            return None

        try:
            spec = importlib.util.spec_from_file_location(plugin_name, module_file)
            if spec is None or spec.loader is None:
                return None

            module = importlib.util.module_from_spec(spec)
            sys.modules[plugin_name] = module
            spec.loader.exec_module(module)

            self._loaded_modules[plugin_name] = module
            return module

        except Exception as e:
            print(f"Failed to import module {plugin_name}: {e}")
            return None

    def _find_neoplugin_class(self, module: Any) -> Optional[type[NeoPlugin]]:
        """
        在模块中查找 NeoPlugin 类

        Args:
            module: 模块对象

        Returns:
            NeoPlugin 类，未找到返回 None
        """
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, NeoPlugin) and attr is not NeoPlugin:
                return attr
        return None

    # === 加载阶段（lazy-load，异步）===

    async def load_plugin(self, plugin_name: str) -> bool:
        """
        加载插件（lazy-load）

        1. 检查依赖是否已加载
        2. 加载依赖
        3. 调用 on_load()
        4. 注册组件到 MoFox 插件系统
        5. 更新状态为 LOADED

        Args:
            plugin_name: 插件名称

        Returns:
            成功返回 True，失败返回 False
        """
        plugin = self.registry.get_plugin(plugin_name)
        if plugin is None:
            print(f"Plugin {plugin_name} not registered")
            return False

        # 检查是否已加载
        if plugin.state == NeoPluginState.LOADED or plugin.state == NeoPluginState.ENABLED:
            return True

        try:
            # 更新状态为 LOADING
            self.registry.set_state(plugin_name, NeoPluginState.LOADING)

            # 加载依赖
            dependencies = self.registry.get_dependencies(plugin_name)
            for dep_name in dependencies:
                if not await self.load_plugin(dep_name):
                    print(f"Failed to load dependency {dep_name} for {plugin_name}")
                    self.registry.set_state(plugin_name, NeoPluginState.ERROR)
                    return False

                # 通知插件依赖已加载
                await plugin.on_dependency_loaded(dep_name)

            # 调用 on_load()
            await plugin.on_load()

            # 更新状态为 LOADED
            self.registry.set_state(plugin_name, NeoPluginState.LOADED)

            return True

        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
            self.registry.set_state(plugin_name, NeoPluginState.ERROR)
            return False

    # === 热重载 ===

    async def reload_plugin(self, plugin_name: str) -> bool:
        """
        热重载插件

        Args:
            plugin_name: 插件名称

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 1. 卸载插件
            if not await self.unload_plugin(plugin_name):
                return False

            # 2. 重新导入模块
            if plugin_name in sys.modules:
                del sys.modules[plugin_name]

            if plugin_name in self._loaded_modules:
                del self._loaded_modules[plugin_name]

            # 3. 重新注册
            plugin = self.registry.get_plugin(plugin_name)
            if plugin and plugin.plugin_path:
                if not await self.register_plugin(plugin.plugin_path):
                    return False

            # 4. 重新加载
            if not await self.load_plugin(plugin_name):
                return False

            # 5. 调用 on_reload()
            plugin = self.registry.get_plugin(plugin_name)
            if plugin:
                await plugin.on_reload()

            return True

        except Exception as e:
            print(f"Failed to reload plugin {plugin_name}: {e}")
            return False

    # === 卸载 ===

    async def unload_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件

        Args:
            plugin_name: 插件名称

        Returns:
            成功返回 True，失败返回 False
        """
        plugin = self.registry.get_plugin(plugin_name)
        if plugin is None:
            return True  # 已经不存在，视为成功

        try:
            # 更新状态为 UNLOADING
            self.registry.set_state(plugin_name, NeoPluginState.UNLOADING)

            # 调用 on_unload()
            await plugin.on_unload()

            # 更新状态为 UNLOADED
            self.registry.set_state(plugin_name, NeoPluginState.UNLOADED)

            return True

        except Exception as e:
            print(f"Failed to unload plugin {plugin_name}: {e}")
            self.registry.set_state(plugin_name, NeoPluginState.ERROR)
            return False
