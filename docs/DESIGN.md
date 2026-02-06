# NeoPlugin 系统设计文档

## 1. NeoPlugin 基类接口设计

### 1.1 状态枚举

```python
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
```

### 1.2 元数据类

```python
class NeoPluginMetadata:
    """NeoPlugin 元数据（从 manifest.toml 解析）"""

    name: str                           # 插件名称
    version: str                        # 版本号
    description: str                    # 描述
    authors: list[str]                  # 作者列表
    license: str                        # 许可证
    keywords: list[str]                 # 关键词
    categories: list[str]               # 分类
    is_lib: bool                        # 是否为 lib 类型
    mofox_version: str                  # MoFox 版本要求
    dependencies: dict[str, str]        # 依赖（name -> version_spec）
    python_dependencies: dict[str, str] # Python 依赖
    inject_configs: list[dict]          # 注入配置
    hooks: dict[str, str]               # 生命周期钩子脚本
```

### 1.3 NeoPlugin 基类

```python
class NeoPlugin(ABC):
    """NeoPlugin 基类 - 提供细致的生命周期管理和高级抽象"""

    # === 元数据（自动填充）===
    metadata: NeoPluginMetadata
    plugin_path: Path              # 插件安装路径
    state: NeoPluginState          # 当前状态

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

    def get_plugin_components(self) -> list[tuple[ComponentInfo, type]]:
        """返回插件的所有组件（Actions, Commands, Tools 等）"""
        return []

    # === 依赖注入 ===

    def get_dependency(self, name: str) -> Any:
        """获取依赖的 lib 或 plugin 实例"""
        pass

    # === 配置管理 ===

    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值（支持点号路径，如 'section.key'）"""
        pass

    def set_config(self, key: str, value: Any) -> None:
        """设置配置值"""
        pass
```

---

## 2. NeoPluginLoader 加载器接口设计

```python
class NeoPluginLoader:
    """NeoPlugin 加载器 - 负责扫描、加载和管理 neoplugins"""

    def __init__(self, install_dir: Path, registry: 'NeoPluginRegistry'):
        """
        Args:
            install_dir: .nmfpm/installed/ 目录路径
            registry: NeoPlugin 注册表实例
        """
        self.install_dir = install_dir
        self.registry = registry

    # === 扫描和发现 ===

    def scan_plugins(self) -> list[Path]:
        """扫描 .nmfpm/installed/ 目录，返回所有插件路径"""
        pass

    def load_manifest(self, plugin_path: Path) -> NeoPluginMetadata:
        """加载并解析插件的 manifest.toml"""
        pass

    # === 注册阶段（启动时一次性执行）===

    async def register_all_plugins(self) -> tuple[int, int]:
        """
        注册所有插件（启动时调用）

        Returns:
            (成功数量, 失败数量)
        """
        pass

    async def register_plugin(self, plugin_path: Path) -> bool:
        """
        注册单个插件

        1. 加载 manifest.toml
        2. 检查依赖
        3. 导入插件模块
        4. 查找 NeoPlugin 类（如果不是 lib）
        5. 创建实例并调用 on_register()
        6. 注册到 registry
        """
        pass

    # === 加载阶段（lazy-load，异步）===

    async def load_plugin(self, plugin_name: str) -> bool:
        """
        加载插件（lazy-load）

        1. 检查依赖是否已加载
        2. 加载依赖
        3. 调用 on_load()
        4. 注册组件到 MoFox 插件系统
        5. 更新状态为 LOADED
        """
        pass

    # === 热重载 ===

    async def reload_plugin(self, plugin_name: str) -> bool:
        """热重载插件"""
        pass

    # === 卸载 ===

    async def unload_plugin(self, plugin_name: str) -> bool:
        """卸载插件"""
        pass
```

---

## 3. NeoPluginRegistry 注册表接口设计

```python
class NeoPluginRegistry:
    """NeoPlugin 注册表 - 管理所有已注册的 neoplugins"""

    def __init__(self):
        self._plugins: dict[str, NeoPlugin] = {}      # name -> instance
        self._libs: dict[str, Any] = {}               # name -> module
        self._metadata: dict[str, NeoPluginMetadata] = {}  # name -> metadata
        self._dependency_graph: dict[str, list[str]] = {}  # name -> [deps]

    # === 注册和查询 ===

    def register(self, plugin: NeoPlugin) -> None:
        """注册插件实例"""
        pass

    def register_lib(self, name: str, module: Any, metadata: NeoPluginMetadata) -> None:
        """注册 lib 模块"""
        pass

    def get_plugin(self, name: str) -> Optional[NeoPlugin]:
        """获取插件实例"""
        pass

    def get_lib(self, name: str) -> Optional[Any]:
        """获取 lib 模块"""
        pass

    def get_metadata(self, name: str) -> Optional[NeoPluginMetadata]:
        """获取元数据"""
        pass

    def has_plugin(self, name: str) -> bool:
        """检查插件是否已注册"""
        pass

    def list_all(self) -> list[str]:
        """列出所有已注册的插件名称"""
        pass

    # === 依赖管理 ===

    def get_dependencies(self, name: str) -> list[str]:
        """获取插件的依赖列表"""
        pass

    def get_dependents(self, name: str) -> list[str]:
        """获取依赖此插件的其他插件列表"""
        pass

    def build_dependency_graph(self) -> None:
        """构建依赖图"""
        pass

    # === 状态管理 ===

    def get_state(self, name: str) -> Optional[NeoPluginState]:
        """获取插件状态"""
        pass

    def set_state(self, name: str, state: NeoPluginState) -> None:
        """设置插件状态"""
        pass
```

---

## 4. DependencyResolver 依赖解析器接口设计

```python
class DependencyResolver:
    """依赖解析器 - 处理版本约束和依赖图"""

    def __init__(self, database_dir: Path):
        """
        Args:
            database_dir: .nmfpm/database/ 目录路径（插件仓库）
        """
        self.database_dir = database_dir

    # === 版本解析 ===

    def parse_version_spec(self, spec: str) -> VersionSpec:
        """
        解析版本约束字符串

        支持的格式：
        - "^1.0.0" - 兼容 1.x.x
        - ">=1.0.0, <2.0.0" - 范围
        - "~1.2.3" - 兼容 1.2.x
        - "1.0.0" - 精确版本
        """
        pass

    def satisfies(self, version: str, spec: str) -> bool:
        """检查版本是否满足约束"""
        pass

    def find_compatible_versions(
        self,
        package_name: str,
        constraints: list[str]
    ) -> list[str]:
        """
        找到满足所有约束的版本列表

        Args:
            package_name: 包名
            constraints: 版本约束列表

        Returns:
            满足所有约束的版本列表（降序排列）
        """
        pass

    # === 依赖解析 ===

    def resolve_dependencies(
        self,
        package_name: str,
        version_spec: str
    ) -> dict[str, str]:
        """
        解析依赖并返回安装计划

        1. 递归收集所有依赖
        2. 版本范围求交集
        3. 选择交集中的最大版本
        4. 检测循环依赖（允许，但记录）

        Args:
            package_name: 要安装的包名
            version_spec: 版本约束

        Returns:
            {package_name: version} 安装计划

        Raises:
            VersionConflictError: 版本冲突
            CircularDependencyError: 循环依赖（如果不允许）
        """
        pass

    def topological_sort(
        self,
        install_plan: dict[str, str]
    ) -> list[tuple[str, str]]:
        """
        拓扑排序，返回安装顺序

        处理循环依赖：参考 pacman，允许循环依赖，
        但在安装时按拓扑排序尽可能优化顺序
        """
        pass

    # === 数据库查询 ===

    def fetch_manifest(self, package_name: str, version: str) -> dict:
        """从数据库获取插件的 manifest"""
        pass

    def fetch_available_versions(self, package_name: str) -> list[str]:
        """获取包的所有可用版本"""
        pass

    def search_packages(self, keyword: str) -> list[dict]:
        """搜索包（使用 grep/rg）"""
        pass
```

---

## 5. nmfpm CLI 工具接口设计

```python
class NmfpmCLI:
    """nmfpm CLI 工具 - 类似 pacman 的包管理器"""

    def __init__(self, mofox_root: Path):
        """
        Args:
            mofox_root: MoFox 根目录路径
        """
        self.mofox_root = mofox_root
        self.nmfpm_dir = mofox_root / ".nmfpm"
        self.installed_dir = self.nmfpm_dir / "installed"
        self.cache_dir = self.nmfpm_dir / "cache"
        self.database_dir = self.nmfpm_dir / "database"

    # === 数据库管理 ===

    def sync_database(self) -> bool:
        """
        同步插件仓库数据库（-Sy）

        git clone 或 git pull 插件仓库到 .nmfpm/database/
        """
        pass

    # === 安装和移除 ===

    async def install(self, package_name: str, version_spec: str = "") -> bool:
        """
        安装插件（-S）

        1. 解析依赖
        2. 按顺序安装每个包：
           a. Clone 仓库到 cache
           b. 处理注入配置
           c. 安装 Python 依赖（uv）
           d. 复制到 installed
           e. 执行 post_install hook
        """
        pass

    async def remove(self, package_name: str) -> bool:
        """
        移除插件（-R）

        1. 检查是否有其他插件依赖此插件
        2. 执行 pre_uninstall hook
        3. 从 installed 删除
        4. 执行 post_uninstall hook
        """
        pass

    async def upgrade(self, package_name: str = "") -> bool:
        """
        升级插件（-Syu 或 -S <package>）

        如果 package_name 为空，升级所有插件
        """
        pass

    # === 查询 ===

    def list_installed(self) -> list[dict]:
        """列出已安装的插件（-Q）"""
        pass

    def search(self, keyword: str) -> list[dict]:
        """搜索插件（-Ss）"""
        pass

    def info(self, package_name: str) -> dict:
        """显示插件信息（-Si）"""
        pass

    # === 注入和钩子处理 ===

    async def process_injections(
        self,
        plugin_path: Path,
        inject_configs: list[dict]
    ) -> None:
        """
        处理注入配置

        对于每个注入配置：
        1. Clone git 仓库到临时目录
        2. 如果指定了 subfolder，只复制子文件夹
        3. 复制到 target 指定的相对路径
        """
        pass

    async def run_hook(
        self,
        plugin_path: Path,
        hook_name: str
    ) -> bool:
        """
        执行生命周期钩子脚本

        支持的钩子：
        - pre_install
        - post_install
        - pre_uninstall
        - post_uninstall
        - pre_upgrade
        - post_upgrade
        """
        pass

    # === Python 依赖管理 ===

    async def install_python_deps(self, plugin_path: Path) -> bool:
        """
        使用 uv 安装 Python 依赖

        如果插件目录下有 pyproject.toml，使用 uv 安装依赖
        """
        pass
```

### 5.1 命令行参数设计

```bash
# 同步数据库
nmfpm.py -Sy

# 安装插件
nmfpm.py -S <package-name>
nmfpm.py -S <package-name>=<version>

# 移除插件
nmfpm.py -R <package-name>

# 搜索插件
nmfpm.py -Ss <keyword>

# 列出已安装
nmfpm.py -Q
nmfpm.py -Ql  # 详细列表

# 显示插件信息
nmfpm.py -Si <package-name>

# 升级所有
nmfpm.py -Syu

# 升级单个
nmfpm.py -S <package-name>  # 如果已安装则升级

# 升级 core
nmfpm.py -Sc
# 或
nmfpm.py -S mofox-core
```

---

## 6. 注入机制详细设计

### 6.1 注入配置格式

```toml
[[inject]]
source = "https://github.com/user/repo.git"
subfolder = "src"           # 可选，指定子文件夹
target = "lib/injected"     # 注入到的相对路径（相对于插件目录）
ref = "v1.0.0"              # 可选，指定 tag/branch/commit
```

### 6.2 注入流程

1. **Clone 仓库**：使用 GitPython clone 到临时目录
2. **Checkout 指定版本**：如果指定了 ref，checkout 到该版本
3. **确定源路径**：如果指定了 subfolder，源路径为 `temp_dir/subfolder`，否则为 `temp_dir`
4. **确定目标路径**：`plugin_path/target`
5. **复制文件**：使用 `shutil.copytree` 复制
6. **清理临时目录**

### 6.3 Core 升级示例

Core 作为特殊插件的 manifest.toml：

```toml
[package]
name = "mofox-core"
version = "2.1.0"
description = "MoFox 核心系统"
authors = ["MoFox Team"]
lib = false

[[inject]]
source = "https://github.com/mofox/mofox-core.git"
target = "/"  # 注入到 MoFox 根目录
ref = "v2.1.0"

[hooks]
post_upgrade = "scripts/restart.sh"  # 重启服务
```

---

设计文档完成！接下来可以开始实现各个模块。

