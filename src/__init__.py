"""
NeoPlugin - MoFox 的非官方插件系统

提供细致的生命周期管理、强大的依赖管理和灵活的注入机制
"""

from .neoplugin_base import NeoPlugin, NeoPluginMetadata, NeoPluginState

__version__ = "1.0.0"

__all__ = [
    "NeoPlugin",
    "NeoPluginMetadata",
    "NeoPluginState",
]
