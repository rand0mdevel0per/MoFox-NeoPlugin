# Hello NeoPlugin 示例插件

这是一个简单的 NeoPlugin 示例，展示如何创建自己的 neoplugin。

## 📁 文件结构

```
hello_neoplugin/
├── manifest.toml    # 插件元数据
├── __init__.py      # 包初始化
└── plugin.py        # 主插件代码
```

## 🎯 功能展示

这个示例插件展示了：

1. **生命周期钩子**：`on_register()`, `on_load()`, `on_enable()`
2. **命令注册**：`/hello_neo` 命令
3. **工具注册**：`hello_neo_tool` 工具

## 🚀 使用方法

### 1. 复制到 .nmfpm/installed/

```bash
cp -r examples/hello_neoplugin /path/to/MoFox/.nmfpm/installed/
```

### 2. 重启 MoFox

```bash
cd /path/to/MoFox
python bot.py
```

### 3. 测试命令

在聊天中输入：
```
/hello_neo
```

## 📝 开发自己的插件

参考这个示例，你可以：

1. 创建 `manifest.toml` 定义插件元数据
2. 创建 `plugin.py` 实现 `NeoPlugin` 类
3. 重写生命周期钩子
4. 注册你的组件（Commands, Tools, Actions 等）

详细文档请查看主项目的 [docs/](../../docs/) 目录。
