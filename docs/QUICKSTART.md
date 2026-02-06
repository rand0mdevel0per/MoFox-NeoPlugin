# NeoPlugin 快速开始指南

本指南将帮助你快速安装和使用 NeoPlugin 系统。

## 📋 前置要求

- Python 3.10+
- MoFox Bot 2.0+
- Git

## 🚀 安装步骤

### 1. 克隆 NeoPlugin 仓库

```bash
git clone https://github.com/rand0mdevel0per/NeoPlugin.git
cd NeoPlugin
```

### 2. 运行安装脚本

```bash
python install.py --mofox-path /path/to/MoFox-Core
```

安装脚本会自动：
- 将 `nmfpm_loader` 插件安装到 MoFox
- 安装 `nmfpm` CLI 工具
- 创建 `.nmfpm` 目录结构

### 3. 同步插件仓库

```bash
cd /path/to/MoFox-Core
python scripts/nmfpm.py -Sy
```

## 📦 使用 nmfpm

### 搜索插件

```bash
python scripts/nmfpm.py -Ss <关键词>
```

### 安装插件

```bash
python scripts/nmfpm.py -S <插件名>
```

### 列出已安装的插件

```bash
python scripts/nmfpm.py -Q
```

### 移除插件

```bash
python scripts/nmfpm.py -R <插件名>
```

### 升级所有插件

```bash
python scripts/nmfpm.py -Syu
```

## 🎯 测试安装

### 1. 安装示例插件

```bash
# 复制示例插件到 installed 目录
cp -r NeoPlugin/examples/hello_neoplugin /path/to/MoFox-Core/.nmfpm/installed/
```

### 2. 启动 MoFox

```bash
cd /path/to/MoFox-Core
python bot.py
```

### 3. 测试命令

在聊天中输入：
```
/hello_neo
```

如果看到 "👋 Hello from NeoPlugin!" 的回复，说明安装成功！

## 🔧 开发自己的插件

参考 [examples/hello_neoplugin](../examples/hello_neoplugin/) 示例。

基本步骤：
1. 创建插件目录
2. 编写 `manifest.toml`
3. 实现 `NeoPlugin` 类
4. 复制到 `.nmfpm/installed/`
5. 重启 MoFox

详细开发指南请查看 [DESIGN.md](DESIGN.md)。

## ❓ 常见问题

### Q: 插件没有加载？
A: 检查 MoFox 日志，确认 nmfpm_loader 插件是否启用。

### Q: nmfpm 命令找不到？
A: 确保使用完整路径：`python scripts/nmfpm.py`

### Q: 如何卸载 NeoPlugin？
A: 删除 `plugins/nmfpm_loader` 目录和 `scripts/nmfpm.py` 文件。

## 📚 更多资源

- [设计文档](DESIGN.md)
- [示例插件](../examples/)
- [GitHub Issues](https://github.com/rand0mdevel0per/MoFox-NeoPlugin/issues)
