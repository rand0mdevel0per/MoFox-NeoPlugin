#!/usr/bin/env python3
"""
check_neoplugin.py - NeoPlugin 检查工具

参考 MPDT 的 7 层检查系统，对 neoplugin 进行质量检查
"""

import sys
import toml
from pathlib import Path
from typing import Optional


class NeoPluginChecker:
    """NeoPlugin 检查器"""

    def __init__(self, plugin_path: Path):
        self.plugin_path = plugin_path
        self.errors = []
        self.warnings = []

    def check_all(self) -> bool:
        """执行所有检查"""
        print(f"🔍 检查插件: {self.plugin_path}")
        print()

        # 1. 结构检查
        if not self.check_structure():
            return False

        # 2. 元数据检查
        if not self.check_metadata():
            return False

        # 3. 组件检查
        self.check_components()

        # 输出结果
        self.print_results()

        return len(self.errors) == 0

    def check_structure(self) -> bool:
        """检查文件结构"""
        print("📁 [1/3] 结构检查...")

        # 检查必要文件
        manifest_path = self.plugin_path / "manifest.toml"
        if not manifest_path.exists():
            self.errors.append("缺少 manifest.toml 文件")
            return False

        # 检查插件入口
        has_init = (self.plugin_path / "__init__.py").exists()
        has_plugin = (self.plugin_path / "plugin.py").exists()

        if not has_init and not has_plugin:
            self.errors.append("缺少 __init__.py 或 plugin.py")
            return False

        print("  ✅ 文件结构正确")
        return True

    def check_metadata(self) -> bool:
        """检查元数据"""
        print("📋 [2/3] 元数据检查...")

        manifest_path = self.plugin_path / "manifest.toml"
        try:
            manifest = toml.load(manifest_path)
        except Exception as e:
            self.errors.append(f"manifest.toml 解析失败: {e}")
            return False

        # 检查必填字段
        package = manifest.get("package", {})
        required_fields = ["name", "version", "description"]

        for field in required_fields:
            if not package.get(field):
                self.errors.append(f"manifest.toml 缺少必填字段: package.{field}")

        # 检查版本格式
        version = package.get("version", "")
        if version and not self._is_valid_version(version):
            self.warnings.append(f"版本号格式可能不规范: {version}")

        if len(self.errors) == 0:
            print("  ✅ 元数据完整")
        return len(self.errors) == 0

    def check_components(self) -> None:
        """检查组件"""
        print("🔧 [3/3] 组件检查...")
        # TODO: 检查 NeoPlugin 类是否正确导出
        print("  ⚠️  组件检查暂未实现")

    def _is_valid_version(self, version: str) -> bool:
        """检查版本号格式"""
        parts = version.split(".")
        if len(parts) != 3:
            return False
        return all(part.isdigit() for part in parts)

    def print_results(self) -> None:
        """输出检查结果"""
        print()
        print("=" * 60)

        if self.errors:
            print(f"❌ 发现 {len(self.errors)} 个错误:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print(f"⚠️  发现 {len(self.warnings)} 个警告:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors and not self.warnings:
            print("✅ 所有检查通过！")

        print("=" * 60)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法: python check_neoplugin.py <插件目录>")
        sys.exit(1)

    plugin_path = Path(sys.argv[1])
    if not plugin_path.exists():
        print(f"错误: 插件目录不存在: {plugin_path}")
        sys.exit(1)

    checker = NeoPluginChecker(plugin_path)
    success = checker.check_all()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
