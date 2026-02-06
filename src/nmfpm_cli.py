"""
nmfpm_cli.py - nmfpm CLI 核心逻辑

实现包管理的核心功能
"""

import asyncio
import json
import shutil
import subprocess
import tempfile
import toml
from pathlib import Path
from typing import Optional
from git import Repo
from .dependency_resolver import DependencyResolver


class NmfpmCLI:
    """nmfpm CLI 工具 - 类似 pacman 的包管理器"""

    def __init__(self, mofox_root: Path):
        """
        初始化 CLI

        Args:
            mofox_root: MoFox 根目录路径
        """
        self.mofox_root = mofox_root
        self.nmfpm_dir = mofox_root / ".nmfpm"
        self.installed_dir = self.nmfpm_dir / "installed"
        self.cache_dir = self.nmfpm_dir / "cache"
        self.database_dir = self.nmfpm_dir / "database"

        # 确保目录存在
        self.nmfpm_dir.mkdir(exist_ok=True)
        self.installed_dir.mkdir(exist_ok=True)
        self.cache_dir.mkdir(exist_ok=True)

        # 创建依赖解析器
        self.resolver = DependencyResolver(self.database_dir)

        # 插件仓库 URL（使用用户的 GitHub）
        self.registry_url = "https://github.com/rand0mdevel0per/neoplugin-registry.git"

    # === 数据库管理 ===

    def sync_database(self) -> bool:
        """
        同步插件仓库数据库（-Sy）

        git clone 或 git pull 插件仓库到 .nmfpm/database/

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            if self.database_dir.exists() and (self.database_dir / ".git").exists():
                # 已存在，执行 pull
                repo = Repo(self.database_dir)
                origin = repo.remotes.origin
                origin.pull()
            else:
                # 不存在，执行 clone
                if self.database_dir.exists():
                    shutil.rmtree(self.database_dir)
                Repo.clone_from(self.registry_url, self.database_dir)

            return True

        except Exception as e:
            print(f"同步数据库失败: {e}")
            return False

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

        Args:
            package_name: 包名
            version_spec: 版本约束（空字符串表示最新版本）

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 1. 解析依赖
            print(f"正在解析 {package_name} 的依赖...")
            install_plan = self.resolver.resolve_dependencies(package_name, version_spec)
            install_order = self.resolver.topological_sort(install_plan)

            print(f"需要安装 {len(install_order)} 个包:")
            for pkg, ver in install_order:
                print(f"  - {pkg} {ver}")

            # 2. 按顺序安装每个包
            for pkg, ver in install_order:
                # 检查是否已安装
                if (self.installed_dir / pkg).exists():
                    print(f"  {pkg} 已安装，跳过")
                    continue

                print(f"  正在安装 {pkg} {ver}...")
                if not await self._install_package(pkg, ver):
                    print(f"  安装 {pkg} 失败")
                    return False

            print(f"✓ {package_name} 及其依赖安装完成")
            return True

        except Exception as e:
            print(f"安装失败: {e}")
            return False

    async def _install_package(self, package_name: str, version: str) -> bool:
        """
        安装单个包

        Args:
            package_name: 包名
            version: 版本号

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 获取包信息
            manifest = self.resolver.fetch_manifest(package_name, version)
            repo_url = manifest.get("repository", "")
            if not repo_url:
                print(f"    错误: {package_name} 没有仓库 URL")
                return False

            # a. Clone 仓库到 cache
            cache_path = self.cache_dir / f"{package_name}-{version}"
            if cache_path.exists():
                shutil.rmtree(cache_path)

            print(f"    正在下载 {repo_url}...")
            repo = Repo.clone_from(repo_url, cache_path)

            # Checkout 到指定版本
            if version:
                try:
                    repo.git.checkout(f"v{version}")
                except Exception:
                    try:
                        repo.git.checkout(version)
                    except Exception:
                        print(f"    警告: 无法 checkout 到版本 {version}")

            # 加载插件的 manifest.toml
            plugin_manifest_path = cache_path / "manifest.toml"
            if not plugin_manifest_path.exists():
                print(f"    错误: {package_name} 没有 manifest.toml")
                return False

            plugin_manifest = toml.load(plugin_manifest_path)

            # b. 处理注入配置
            inject_configs = plugin_manifest.get("inject", [])
            if inject_configs:
                print(f"    正在处理注入配置...")
                await self.process_injections(cache_path, inject_configs)

            # c. 安装 Python 依赖（uv）
            if (cache_path / "pyproject.toml").exists():
                print(f"    正在安装 Python 依赖...")
                if not await self.install_python_deps(cache_path):
                    print(f"    警告: Python 依赖安装失败")

            # d. 复制到 installed
            install_path = self.installed_dir / package_name
            if install_path.exists():
                shutil.rmtree(install_path)

            shutil.copytree(cache_path, install_path)

            # e. 执行 post_install hook
            hooks = plugin_manifest.get("hooks", {})
            if "post_install" in hooks:
                print(f"    正在执行 post_install hook...")
                await self.run_hook(install_path, "post_install")

            return True

        except Exception as e:
            print(f"    安装包失败: {e}")
            return False

    async def remove(self, package_name: str) -> bool:
        """
        移除插件（-R）

        1. 检查是否有其他插件依赖此插件
        2. 执行 pre_uninstall hook
        3. 从 installed 删除
        4. 执行 post_uninstall hook

        Args:
            package_name: 包名

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            install_path = self.installed_dir / package_name
            if not install_path.exists():
                print(f"{package_name} 未安装")
                return False

            # TODO: 检查依赖

            # 加载 manifest
            manifest_path = install_path / "manifest.toml"
            if manifest_path.exists():
                manifest = toml.load(manifest_path)
                hooks = manifest.get("hooks", {})

                # 执行 pre_uninstall hook
                if "pre_uninstall" in hooks:
                    print(f"正在执行 pre_uninstall hook...")
                    await self.run_hook(install_path, "pre_uninstall")

            # 删除
            shutil.rmtree(install_path)

            # 执行 post_uninstall hook（如果有）
            # （已删除，无法执行）

            return True

        except Exception as e:
            print(f"移除失败: {e}")
            return False

    async def upgrade(self, package_name: str = "") -> bool:
        """
        升级插件（-Syu 或 -S <package>）

        如果 package_name 为空，升级所有插件

        Args:
            package_name: 包名（空字符串表示升级所有）

        Returns:
            成功返回 True，失败返回 False
        """
        # TODO: 实现升级逻辑
        print("升级功能尚未实现")
        return False

    # === 查询 ===

    def list_installed(self) -> list[dict]:
        """
        列出已安装的插件（-Q）

        Returns:
            插件信息列表
        """
        if not self.installed_dir.exists():
            return []

        installed = []
        for item in self.installed_dir.iterdir():
            if item.is_dir():
                manifest_path = item / "manifest.toml"
                if manifest_path.exists():
                    try:
                        manifest = toml.load(manifest_path)
                        package = manifest.get("package", {})
                        installed.append({
                            "name": package.get("name", item.name),
                            "version": package.get("version", "unknown"),
                            "description": package.get("description", "")
                        })
                    except Exception:
                        installed.append({
                            "name": item.name,
                            "version": "unknown",
                            "description": ""
                        })

        return installed

    def search(self, keyword: str) -> list[dict]:
        """
        搜索插件（-Ss）

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的插件列表
        """
        return self.resolver.search_packages(keyword)

    def info(self, package_name: str) -> Optional[dict]:
        """
        显示插件信息（-Si）

        Args:
            package_name: 包名

        Returns:
            插件信息，未找到返回 None
        """
        # 先查找已安装的
        install_path = self.installed_dir / package_name
        if install_path.exists():
            manifest_path = install_path / "manifest.toml"
            if manifest_path.exists():
                try:
                    manifest = toml.load(manifest_path)
                    return manifest.get("package", {})
                except Exception:
                    pass

        # 查找数据库中的
        try:
            versions = self.resolver.fetch_available_versions(package_name)
            if versions:
                manifest = self.resolver.fetch_manifest(package_name, versions[0])
                return manifest
        except Exception:
            pass

        return None

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

        Args:
            plugin_path: 插件目录路径
            inject_configs: 注入配置列表
        """
        for inject_config in inject_configs:
            source = inject_config.get("source", "")
            subfolder = inject_config.get("subfolder", "")
            target = inject_config.get("target", "")
            ref = inject_config.get("ref", "main")

            if not source or not target:
                continue

            try:
                # 1. Clone 仓库到临时目录
                with tempfile.TemporaryDirectory() as temp_dir:
                    temp_path = Path(temp_dir)
                    print(f"      正在注入 {source}...")

                    repo = Repo.clone_from(source, temp_path)

                    # Checkout 到指定版本
                    if ref:
                        try:
                            repo.git.checkout(ref)
                        except Exception:
                            print(f"      警告: 无法 checkout 到 {ref}")

                    # 2. 确定源路径
                    if subfolder:
                        source_path = temp_path / subfolder
                    else:
                        source_path = temp_path

                    if not source_path.exists():
                        print(f"      错误: 源路径 {source_path} 不存在")
                        continue

                    # 3. 确定目标路径
                    if target == "/":
                        # 注入到 MoFox 根目录（用于 core 升级）
                        target_path = self.mofox_root
                    else:
                        target_path = plugin_path / target

                    # 4. 复制文件
                    if target_path.exists():
                        shutil.rmtree(target_path)

                    shutil.copytree(source_path, target_path)
                    print(f"      ✓ 注入完成: {target}")

            except Exception as e:
                print(f"      注入失败: {e}")

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

        Args:
            plugin_path: 插件目录路径
            hook_name: 钩子名称

        Returns:
            成功返回 True，失败返回 False
        """
        manifest_path = plugin_path / "manifest.toml"
        if not manifest_path.exists():
            return False

        try:
            manifest = toml.load(manifest_path)
            hooks = manifest.get("hooks", {})
            hook_script = hooks.get(hook_name, "")

            if not hook_script:
                return True  # 没有钩子，视为成功

            hook_path = plugin_path / hook_script
            if not hook_path.exists():
                print(f"      警告: 钩子脚本 {hook_script} 不存在")
                return False

            # 执行钩子脚本
            if hook_path.suffix == ".py":
                result = subprocess.run(
                    ["python", str(hook_path)],
                    cwd=plugin_path,
                    capture_output=True,
                    text=True
                )
            else:
                result = subprocess.run(
                    [str(hook_path)],
                    cwd=plugin_path,
                    capture_output=True,
                    text=True,
                    shell=True
                )

            if result.returncode != 0:
                print(f"      钩子执行失败: {result.stderr}")
                return False

            return True

        except Exception as e:
            print(f"      执行钩子失败: {e}")
            return False

    # === Python 依赖管理 ===

    async def install_python_deps(self, plugin_path: Path) -> bool:
        """
        使用 uv 安装 Python 依赖

        如果插件目录下有 pyproject.toml，使用 uv 安装依赖

        Args:
            plugin_path: 插件目录路径

        Returns:
            成功返回 True，失败返回 False
        """
        pyproject_path = plugin_path / "pyproject.toml"
        if not pyproject_path.exists():
            return True  # 没有 pyproject.toml，视为成功

        try:
            # 检查 uv 是否可用
            uv_path = self.mofox_root / "uv"
            if not uv_path.exists():
                uv_path = shutil.which("uv")
                if not uv_path:
                    print(f"      警告: uv 不可用，跳过 Python 依赖安装")
                    return False

            # 使用 uv 安装依赖
            result = subprocess.run(
                [str(uv_path), "pip", "install", "-e", str(plugin_path)],
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print(f"      Python 依赖安装失败: {result.stderr}")
                return False

            return True

        except Exception as e:
            print(f"      安装 Python 依赖失败: {e}")
            return False
