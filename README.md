# NeoPlugin 🚀

MoFox 的非官方插件系统 - 类似 pacman 的包管理器

## ✨ 特性

- 🎯 **细致的生命周期管理** - 支持完整的插件生命周期钩子
- 📦 **强大的依赖管理** - 自动解析依赖、版本冲突处理
- 🔧 **灵活的注入机制** - 支持从 git 仓库注入文件到任意路径
- 🐍 **Python 依赖集成** - 使用 uv 管理 Python 依赖
- 🔄 **热重载支持** - 运行时动态加载/卸载插件
- 📚 **Lib & Plugin 双类型** - 支持纯库和功能插件

## 🎯 核心概念

### Plugin vs Lib

- **Plugin**: 导出 `NeoPlugin` 类的完整功能插件
- **Lib**: 纯依赖库（`lib=true`），不导出 NeoPlugin 类

### 目录结构

```
.nmfpm/
├── installed/      # 已安装的插件
├── cache/          # 下载缓存
└── database/       # 插件仓库（git clone）
```

## 🚀 快速开始

### 前置要求：安装 MoFox

如果你还没有安装 MoFox，可以使用以下命令快速安装（Windows PowerShell）：

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb "https://hk.gh-proxy.org/https://github.com/rand0mdevel0per/acscripts/raw/refs/heads/main/mofox-qsetup.ps1" | iex
```

这个命令会在当前目录下自动安装 MoFox。

### 安装 NeoPlugin

**方式一：一键安装（推荐）**

在 MoFox 根目录下运行（Windows PowerShell）：

```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force; iwr -useb "https://hk.gh-proxy.org/https://raw.githubusercontent.com/rand0mdevel0per/NeoPlugin/master/install-neoplugin.ps1" | iex
```

**方式二：手动安装**

```bash
# 克隆仓库
git clone https://github.com/rand0mdevel0per/NeoPlugin.git
cd NeoPlugin

# 一键安装到 MoFox
python install.py --mofox-path /path/to/MoFox-Core

# 同步插件仓库
cd /path/to/MoFox-Core
python scripts/nmfpm.py -Sy
```

详细安装指南请查看 [快速开始文档](docs/QUICKSTART.md)。

### 使用 nmfpm

```bash
# 搜索插件
python scripts/nmfpm.py -Ss <关键词>

# 安装插件
python scripts/nmfpm.py -S <插件名>

# 列出已安装
python scripts/nmfpm.py -Q

# 移除插件
python scripts/nmfpm.py -R <插件名>

# 升级所有
python scripts/nmfpm.py -Syu
```

## 🎨 示例

查看 [examples/hello_neoplugin](examples/hello_neoplugin/) 了解如何创建自己的插件。

## 📖 文档

- [快速开始指南](docs/QUICKSTART.md) - 安装和基本使用
- [设计文档](docs/DESIGN.md) - 系统架构和接口设计
- [示例插件](examples/) - 学习如何开发插件

## 🏗️ 项目结构

```
NeoPlugin/
├── src/                    # 核心代码
│   ├── neoplugin_base.py      # NeoPlugin 基类
│   ├── neoplugin_loader.py    # 插件加载器
│   ├── neoplugin_registry.py  # 插件注册表
│   ├── dependency_resolver.py # 依赖解析器
│   └── nmfpm_cli.py           # CLI 核心逻辑
├── nmfpm_loader/           # MoFox 加载器插件
├── nmfpm.py                # CLI 工具入口
├── install.py              # 一键安装脚本
├── examples/               # 示例插件
└── docs/                   # 文档
```

## 🤝 贡献

欢迎贡献！请查看 [GitHub Issues](https://github.com/rand0mdevel0per/NeoPlugin/issues)。

## 📝 License

MIT License
