# nmpdt - NeoPlugin Development Toolkit

类似 MPDT 的开发工具，为 NeoPlugin 插件开发提供完整的工具链支持。

## 功能特性

- **项目初始化** - 快速创建插件项目结构和模板
- **代码检查** - 运行结构检查和代码风格检查
- **自动发布** - 一键发布插件到 NeoPlugin Registry

## 安装

```bash
pip install nmpdt
```

## 快速开始

### 1. 初始化新插件项目

```bash
# 创建基础插件
nmpdt init my-plugin

# 创建完整插件（包含示例组件）
nmpdt init my-plugin --template full
```

### 2. 检查插件质量

```bash
# 检查当前目录的插件
nmpdt check

# 检查指定路径的插件
nmpdt check /path/to/plugin

# 自动修复代码风格问题
nmpdt check --fix
```

### 3. 发布插件到 Registry

```bash
# 自动检测 git origin 并发布
nmpdt publish

# 指定仓库 URL 发布
nmpdt publish --repo https://github.com/username/my-plugin
```

发布命令会自动：
- 检测或创建 git 仓库
- Fork neoplugin-registry
- 生成 entry 文件
- 提交并推送更改
- 创建 Pull Request

## 检查系统

nmpdt 提供 3 层检查系统：

1. **结构检查** - 验证插件目录结构和必需文件
2. **元数据检查** - 验证 manifest.toml 格式和字段
3. **代码风格检查** - 使用 ruff 进行代码风格检查

## 要求

- Python 3.8+
- Git
- GitHub CLI (gh) - 用于发布功能

## 相关项目

- [MoFox-NeoPlugin](https://github.com/rand0mdevel0per/MoFox-NeoPlugin) - NeoPlugin 主项目
- [neoplugin-registry](https://github.com/rand0mdevel0per/neoplugin-registry) - 插件注册表

## 许可证

MIT License
