#!/usr/bin/env python3
"""
nmpdt - NeoPlugin Development Toolkit

类似 MPDT 的开发工具，提供项目初始化、模板生成、代码检查等功能
"""

import argparse
import sys
from pathlib import Path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="nmpdt - NeoPlugin Development Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # init 命令
    init_parser = subparsers.add_parser('init', help='初始化新插件项目')
    init_parser.add_argument('name', help='插件名称')
    init_parser.add_argument('--template', choices=['basic', 'full'], default='basic', help='模板类型')

    # check 命令
    check_parser = subparsers.add_parser('check', help='检查插件质量')
    check_parser.add_argument('path', nargs='?', default='.', help='插件路径')
    check_parser.add_argument('--fix', action='store_true', help='自动修复问题')

    # publish 命令
    publish_parser = subparsers.add_parser('publish', help='发布插件到 registry')
    publish_parser.add_argument('--repo', required=True, help='插件仓库 URL')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # 执行命令
    if args.command == 'init':
        from .commands.init import init_project
        init_project(args.name, args.template)
    elif args.command == 'check':
        from .commands.check import check_plugin
        check_plugin(Path(args.path), args.fix)
    elif args.command == 'publish':
        from .commands.publish import publish_plugin
        publish_plugin(args.repo)


if __name__ == "__main__":
    main()
