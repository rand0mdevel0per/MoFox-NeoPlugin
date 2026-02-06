#!/usr/bin/env python3
"""
nmfpm - NeoPlugin 包管理器

类似 pacman 的命令行工具，用于管理 MoFox 的 neoplugins
"""

import argparse
import asyncio
import sys
from pathlib import Path


def create_parser() -> argparse.ArgumentParser:
    """创建命令行参数解析器"""
    parser = argparse.ArgumentParser(
        description="nmfpm - NeoPlugin 包管理器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  nmfpm -Sy                    同步数据库
  nmfpm -S plugin-name         安装插件
  nmfpm -R plugin-name         移除插件
  nmfpm -Ss keyword            搜索插件
  nmfpm -Q                     列出已安装的插件
  nmfpm -Syu                   升级所有插件
        """
    )

    # 操作选项
    parser.add_argument('-S', '--sync', action='store_true',
                        help='安装或升级包')
    parser.add_argument('-R', '--remove', action='store_true',
                        help='移除包')
    parser.add_argument('-Q', '--query', action='store_true',
                        help='查询已安装的包')
    parser.add_argument('-Ss', '--search', action='store_true',
                        help='搜索包')
    parser.add_argument('-Si', '--info', action='store_true',
                        help='显示包信息')

    # 同步选项
    parser.add_argument('-y', '--refresh', action='store_true',
                        help='同步数据库')
    parser.add_argument('-u', '--sysupgrade', action='store_true',
                        help='升级所有包')
    parser.add_argument('-c', '--core', action='store_true',
                        help='升级 core')

    # 查询选项
    parser.add_argument('-l', '--list', action='store_true',
                        help='详细列表')

    # 包名参数
    parser.add_argument('packages', nargs='*',
                        help='包名')

    # MoFox 路径
    parser.add_argument('--mofox-path', type=str,
                        help='MoFox 根目录路径（默认：当前目录）')

    return parser


async def main():
    """主函数"""
    parser = create_parser()
    args = parser.parse_args()

    # 确定 MoFox 路径
    if args.mofox_path:
        mofox_root = Path(args.mofox_path)
    else:
        mofox_root = Path.cwd()

    # 检查是否在 MoFox 目录
    if not (mofox_root / "bot.py").exists():
        print(f"错误: {mofox_root} 不是有效的 MoFox 目录")
        sys.exit(1)

    # 导入核心模块（延迟导入，避免循环依赖）
    sys.path.insert(0, str(Path(__file__).parent))
    from src.nmfpm_cli import NmfpmCLI

    # 创建 CLI 实例
    cli = NmfpmCLI(mofox_root)

    # 处理命令
    try:
        # 同步数据库
        if args.refresh:
            print("正在同步数据库...")
            if cli.sync_database():
                print("✓ 数据库同步成功")
            else:
                print("✗ 数据库同步失败")
                sys.exit(1)

        # 安装/升级
        if args.sync:
            if args.sysupgrade:
                # 升级所有
                print("正在升级所有插件...")
                if await cli.upgrade():
                    print("✓ 升级完成")
                else:
                    print("✗ 升级失败")
                    sys.exit(1)
            elif args.core:
                # 升级 core
                print("正在升级 MoFox core...")
                if await cli.upgrade("mofox-core"):
                    print("✓ Core 升级完成")
                else:
                    print("✗ Core 升级失败")
                    sys.exit(1)
            elif args.packages:
                # 安装指定包
                for package in args.packages:
                    print(f"正在安装 {package}...")
                    if await cli.install(package):
                        print(f"✓ {package} 安装成功")
                    else:
                        print(f"✗ {package} 安装失败")
                        sys.exit(1)
            else:
                print("错误: 请指定要安装的包")
                sys.exit(1)

        # 移除
        elif args.remove:
            if args.packages:
                for package in args.packages:
                    print(f"正在移除 {package}...")
                    if await cli.remove(package):
                        print(f"✓ {package} 移除成功")
                    else:
                        print(f"✗ {package} 移除失败")
                        sys.exit(1)
            else:
                print("错误: 请指定要移除的包")
                sys.exit(1)

        # 查询
        elif args.query:
            installed = cli.list_installed()
            if not installed:
                print("没有已安装的插件")
            else:
                print(f"已安装 {len(installed)} 个插件:")
                for pkg in installed:
                    if args.list:
                        print(f"  {pkg['name']} {pkg['version']}")
                        print(f"    {pkg.get('description', '')}")
                    else:
                        print(f"  {pkg['name']} {pkg['version']}")

        # 搜索
        elif args.search:
            if args.packages:
                keyword = args.packages[0]
                results = cli.search(keyword)
                if not results:
                    print(f"没有找到匹配 '{keyword}' 的插件")
                else:
                    print(f"找到 {len(results)} 个匹配的插件:")
                    for pkg in results:
                        print(f"  {pkg.get('name', 'unknown')} {pkg.get('version', '')}")
                        print(f"    {pkg.get('description', '')}")
            else:
                print("错误: 请指定搜索关键词")
                sys.exit(1)

        # 显示信息
        elif args.info:
            if args.packages:
                package = args.packages[0]
                info = cli.info(package)
                if info:
                    print(f"名称: {info.get('name', '')}")
                    print(f"版本: {info.get('version', '')}")
                    print(f"描述: {info.get('description', '')}")
                    print(f"作者: {', '.join(info.get('authors', []))}")
                    print(f"许可证: {info.get('license', '')}")
                    if info.get('dependencies'):
                        print(f"依赖: {', '.join(info['dependencies'].keys())}")
                else:
                    print(f"错误: 找不到包 {package}")
                    sys.exit(1)
            else:
                print("错误: 请指定包名")
                sys.exit(1)

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\n操作已取消")
        sys.exit(130)
    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
