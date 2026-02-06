#!/usr/bin/env python3
"""
install.py - NeoPlugin 一键安装脚本

将 NeoPlugin 系统安装到 MoFox
"""

import argparse
import shutil
import sys
from pathlib import Path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="NeoPlugin 一键安装脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--mofox-path',
        type=str,
        required=True,
        help='MoFox 根目录路径'
    )
    parser.add_argument(
        '--skip-database',
        action='store_true',
        help='跳过插件仓库初始化'
    )

    args = parser.parse_args()

    # 获取路径
    mofox_root = Path(args.mofox_path).resolve()
    neoplugin_root = Path(__file__).parent.resolve()

    print("🚀 NeoPlugin 安装程序")
    print(f"📁 MoFox 路径: {mofox_root}")
    print(f"📁 NeoPlugin 路径: {neoplugin_root}")
    print()

    # 1. 检查 MoFox 目录
    print("1️⃣ 检查 MoFox 目录...")
    if not mofox_root.exists():
        print(f"❌ 错误: MoFox 目录不存在: {mofox_root}")
        sys.exit(1)

    if not (mofox_root / "bot.py").exists():
        print(f"❌ 错误: {mofox_root} 不是有效的 MoFox 目录")
        sys.exit(1)

    print("✅ MoFox 目录有效")
    print()

    # 2. 复制 nmfpm_loader 插件到 MoFox plugins 目录
    print("2️⃣ 安装 nmfpm_loader 插件...")
    plugins_dir = mofox_root / "plugins"
    plugins_dir.mkdir(exist_ok=True)

    target_loader_dir = plugins_dir / "nmfpm_loader"
    source_loader_dir = neoplugin_root / "nmfpm_loader"

    if target_loader_dir.exists():
        print("⚠️  nmfpm_loader 已存在，正在覆盖...")
        shutil.rmtree(target_loader_dir)

    shutil.copytree(source_loader_dir, target_loader_dir)
    print(f"✅ nmfpm_loader 插件已安装到: {target_loader_dir}")
    print()

    # 3. 复制 src 目录到 nmfpm_loader 插件目录
    print("3️⃣ 安装 NeoPlugin 核心模块...")
    target_src_dir = target_loader_dir / "src"
    source_src_dir = neoplugin_root / "src"

    if target_src_dir.exists():
        shutil.rmtree(target_src_dir)

    shutil.copytree(source_src_dir, target_src_dir)
    print(f"✅ NeoPlugin 核心模块已安装到: {target_src_dir}")
    print()

    # 4. 复制 nmfpm.py 到 MoFox scripts 目录
    print("4️⃣ 安装 nmfpm CLI 工具...")
    scripts_dir = mofox_root / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    target_nmfpm = scripts_dir / "nmfpm.py"
    source_nmfpm = neoplugin_root / "nmfpm.py"

    if target_nmfpm.exists():
        target_nmfpm.unlink()

    shutil.copy2(source_nmfpm, target_nmfpm)
    print(f"✅ nmfpm CLI 已安装到: {target_nmfpm}")
    print()

    # 5. 创建 .nmfpm 目录结构
    print("5️⃣ 创建 .nmfpm 目录结构...")
    nmfpm_dir = mofox_root / ".nmfpm"
    nmfpm_dir.mkdir(exist_ok=True)

    (nmfpm_dir / "installed").mkdir(exist_ok=True)
    (nmfpm_dir / "cache").mkdir(exist_ok=True)

    print(f"✅ .nmfpm 目录已创建: {nmfpm_dir}")
    print()

    # 6. 初始化插件仓库（可选）
    if not args.skip_database:
        print("6️⃣ 初始化插件仓库...")
        print("提示: 你可以稍后运行 'python scripts/nmfpm.py -Sy' 来同步插件仓库")
        print()

    # 完成
    print("=" * 60)
    print("🎉 NeoPlugin 安装完成！")
    print()
    print("📝 下一步:")
    print("  1. 同步插件仓库:")
    print(f"     cd {mofox_root}")
    print("     python scripts/nmfpm.py -Sy")
    print()
    print("  2. 搜索插件:")
    print("     python scripts/nmfpm.py -Ss <关键词>")
    print()
    print("  3. 安装插件:")
    print("     python scripts/nmfpm.py -S <插件名>")
    print()
    print("  4. 启动 MoFox:")
    print("     python bot.py")
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
