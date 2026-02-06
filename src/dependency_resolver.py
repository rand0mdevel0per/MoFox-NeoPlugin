"""
dependency_resolver.py - 依赖解析器

处理版本约束和依赖图解析
"""

import json
import subprocess
import toml
from pathlib import Path
from typing import Optional
from packaging.version import Version, parse as parse_version
from packaging.specifiers import SpecifierSet


class VersionConflictError(Exception):
    """版本冲突错误"""
    pass


class CircularDependencyError(Exception):
    """循环依赖错误"""
    pass


class DependencyResolver:
    """依赖解析器 - 处理版本约束和依赖图"""

    def __init__(self, database_dir: Path):
        """
        初始化依赖解析器

        Args:
            database_dir: .nmfpm/database/ 目录路径（插件仓库）
        """
        self.database_dir = database_dir
        self.entries_dir = database_dir / "entries"

    # === 版本解析 ===

    def parse_version_spec(self, spec: str) -> SpecifierSet:
        """
        解析版本约束字符串

        支持的格式：
        - "^1.0.0" - 兼容 1.x.x (转换为 >=1.0.0,<2.0.0)
        - ">=1.0.0, <2.0.0" - 范围
        - "~1.2.3" - 兼容 1.2.x (转换为 >=1.2.3,<1.3.0)
        - "1.0.0" - 精确版本 (转换为 ==1.0.0)

        Args:
            spec: 版本约束字符串

        Returns:
            SpecifierSet 对象
        """
        spec = spec.strip()

        # 处理 ^ 语法（兼容主版本）
        if spec.startswith("^"):
            version_str = spec[1:]
            version = parse_version(version_str)
            major = version.major
            return SpecifierSet(f">={version_str},<{major + 1}.0.0")

        # 处理 ~ 语法（兼容次版本）
        if spec.startswith("~"):
            version_str = spec[1:]
            version = parse_version(version_str)
            major = version.major
            minor = version.minor
            return SpecifierSet(f">={version_str},<{major}.{minor + 1}.0")

        # 处理精确版本（无运算符）
        if not any(op in spec for op in [">=", "<=", ">", "<", "==", "!="]):
            return SpecifierSet(f"=={spec}")

        # 其他情况直接解析
        return SpecifierSet(spec)

    def satisfies(self, version: str, spec: str) -> bool:
        """
        检查版本是否满足约束

        Args:
            version: 版本号
            spec: 版本约束

        Returns:
            满足返回 True，否则返回 False
        """
        try:
            version_obj = parse_version(version)
            spec_set = self.parse_version_spec(spec)
            return version_obj in spec_set
        except Exception:
            return False

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
        # 获取所有可用版本
        available_versions = self.fetch_available_versions(package_name)
        if not available_versions:
            return []

        # 解析所有约束
        spec_sets = [self.parse_version_spec(c) for c in constraints]

        # 过滤满足所有约束的版本
        compatible_versions = []
        for version_str in available_versions:
            try:
                version_obj = parse_version(version_str)
                if all(version_obj in spec_set for spec_set in spec_sets):
                    compatible_versions.append(version_str)
            except Exception:
                continue

        # 降序排列
        compatible_versions.sort(key=lambda v: parse_version(v), reverse=True)
        return compatible_versions

    # === 依赖解析 ===

    def resolve_dependencies(
        self,
        package_name: str,
        version_spec: str = ""
    ) -> dict[str, str]:
        """
        解析依赖并返回安装计划

        1. 递归收集所有依赖
        2. 版本范围求交集
        3. 选择交集中的最大版本
        4. 检测循环依赖（允许，但记录）

        Args:
            package_name: 要安装的包名
            version_spec: 版本约束（空字符串表示最新版本）

        Returns:
            {package_name: version} 安装计划

        Raises:
            VersionConflictError: 版本冲突
        """
        # 收集所有依赖和版本约束
        dep_constraints: dict[str, list[str]] = {}
        visited = set()

        def collect_deps(pkg: str, ver_spec: str):
            if pkg in visited:
                return
            visited.add(pkg)

            # 获取可用版本
            if ver_spec:
                compatible_versions = self.find_compatible_versions(pkg, [ver_spec])
            else:
                compatible_versions = self.fetch_available_versions(pkg)

            if not compatible_versions:
                raise VersionConflictError(f"No compatible version found for {pkg}")

            # 使用最新版本获取依赖
            latest_version = compatible_versions[0]
            manifest = self.fetch_manifest(pkg, latest_version)

            # 记录约束
            if pkg not in dep_constraints:
                dep_constraints[pkg] = []
            if ver_spec:
                dep_constraints[pkg].append(ver_spec)

            # 递归收集依赖
            dependencies = manifest.get("dependencies", {})
            for dep_name, dep_ver_spec in dependencies.items():
                if dep_name not in dep_constraints:
                    dep_constraints[dep_name] = []
                dep_constraints[dep_name].append(dep_ver_spec)
                collect_deps(dep_name, dep_ver_spec)

        # 开始收集
        collect_deps(package_name, version_spec)

        # 解析版本冲突
        install_plan = {}
        for pkg, constraints in dep_constraints.items():
            compatible_versions = self.find_compatible_versions(pkg, constraints)
            if not compatible_versions:
                raise VersionConflictError(
                    f"Version conflict for {pkg}: no version satisfies {constraints}"
                )
            # 选择最大版本
            install_plan[pkg] = compatible_versions[0]

        return install_plan

    def topological_sort(
        self,
        install_plan: dict[str, str]
    ) -> list[tuple[str, str]]:
        """
        拓扑排序，返回安装顺序

        处理循环依赖：参考 pacman，允许循环依赖，
        但在安装时按拓扑排序尽可能优化顺序

        Args:
            install_plan: {package_name: version} 安装计划

        Returns:
            [(package_name, version), ...] 安装顺序
        """
        # 构建依赖图
        dep_graph: dict[str, list[str]] = {}
        for pkg, version in install_plan.items():
            manifest = self.fetch_manifest(pkg, version)
            dependencies = manifest.get("dependencies", {})
            dep_graph[pkg] = [dep for dep in dependencies.keys() if dep in install_plan]

        # Kahn 算法进行拓扑排序
        in_degree = {pkg: 0 for pkg in install_plan}
        for pkg, deps in dep_graph.items():
            for dep in deps:
                in_degree[dep] += 1

        queue = [pkg for pkg, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            pkg = queue.pop(0)
            result.append((pkg, install_plan[pkg]))

            for dep in dep_graph.get(pkg, []):
                in_degree[dep] -= 1
                if in_degree[dep] == 0:
                    queue.append(dep)

        # 如果有循环依赖，剩余的包按字母顺序添加
        remaining = [pkg for pkg in install_plan if pkg not in [p[0] for p in result]]
        remaining.sort()
        for pkg in remaining:
            result.append((pkg, install_plan[pkg]))

        return result

    # === 数据库查询 ===

    def fetch_manifest(self, package_name: str, version: str) -> dict:
        """
        从数据库获取插件的 manifest

        Args:
            package_name: 包名
            version: 版本号

        Returns:
            manifest 数据（dict）
        """
        entry_file = self.entries_dir / f"{package_name}.json"
        if not entry_file.exists():
            raise FileNotFoundError(f"Package {package_name} not found in database")

        try:
            with open(entry_file, 'r', encoding='utf-8') as f:
                entry_data = json.load(f)

            # 返回指定版本的 manifest（简化版，实际应该从仓库获取）
            # 这里假设 entry 文件包含了 manifest 信息
            return entry_data

        except Exception as e:
            raise ValueError(f"Failed to load manifest for {package_name}: {e}")

    def fetch_available_versions(self, package_name: str) -> list[str]:
        """
        获取包的所有可用版本

        Args:
            package_name: 包名

        Returns:
            版本列表（降序排列）
        """
        entry_file = self.entries_dir / f"{package_name}.json"
        if not entry_file.exists():
            return []

        try:
            with open(entry_file, 'r', encoding='utf-8') as f:
                entry_data = json.load(f)

            # 获取版本列表（假设 entry 文件包含 versions 字段）
            versions = entry_data.get("versions", [entry_data.get("version", "")])
            versions = [v for v in versions if v]

            # 降序排列
            versions.sort(key=lambda v: parse_version(v), reverse=True)
            return versions

        except Exception:
            return []

    def search_packages(self, keyword: str) -> list[dict]:
        """
        搜索包（使用 grep/rg）

        Args:
            keyword: 搜索关键词

        Returns:
            匹配的包列表
        """
        if not self.entries_dir.exists():
            return []

        results = []
        try:
            # 使用 rg 搜索（如果可用）
            cmd = ["rg", "-i", keyword, str(self.entries_dir), "--json"]
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode == 0:
                # 解析 rg 的 JSON 输出
                for line in result.stdout.strip().split('\n'):
                    if line:
                        try:
                            data = json.loads(line)
                            if data.get("type") == "match":
                                file_path = Path(data["data"]["path"]["text"])
                                if file_path not in [r["file"] for r in results]:
                                    results.append({"file": file_path})
                        except Exception:
                            continue

        except FileNotFoundError:
            # rg 不可用，使用 grep
            try:
                cmd = ["grep", "-ri", keyword, str(self.entries_dir)]
                result = subprocess.run(cmd, capture_output=True, text=True)

                if result.returncode == 0:
                    for line in result.stdout.strip().split('\n'):
                        if ':' in line:
                            file_path = Path(line.split(':')[0])
                            if file_path not in [r["file"] for r in results]:
                                results.append({"file": file_path})

            except Exception:
                pass

        # 加载匹配的包信息
        packages = []
        for item in results:
            try:
                with open(item["file"], 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    packages.append(package_data)
            except Exception:
                continue

        return packages
