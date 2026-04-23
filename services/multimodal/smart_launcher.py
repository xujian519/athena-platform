#!/usr/bin/env python3
"""
Athena多模态文件系统智能启动器
Smart Launcher for Multimodal File System

根据需求智能选择启动组件，优化资源使用
"""

import argparse
import asyncio
import json
import os
import sys
from typing import Any

from core.logging_config import setup_logging

# 添加路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()

class ComponentManager:
    """组件管理器"""

    def __init__(self):
        self.components = {
            # 核心组件（通常需要）
            'core': {
                'enabled': True,
                'required': True,
                'modules': [
                    'secure_multimodal_api',  # 主API
                    'base_settings_manager',  # 设置管理
                    'cache_manager',  # 缓存
                    'security.auth_manager'  # 安全认证
                ],
                'description': '核心文件管理功能',
                'memory_usage': 'low'
            },

            # 性能监控（可选，建议启用）
            'monitoring': {
                'enabled': True,
                'required': False,
                'modules': [
                    'monitoring.performance_monitor',
                    'monitoring.metrics_collector'
                ],
                'description': '性能监控和指标收集',
                'memory_usage': 'medium'
            },

            # 批量处理（按需）
            'batch': {
                'enabled': False,
                'required': False,
                'modules': [
                    'batch.batch_operations'
                ],
                'description': '批量文件处理',
                'memory_usage': 'high',
                'trigger_keywords': ['批量', 'batch', '多个文件', '文件夹处理']
            },

            # 版本管理（按需）
            'versioning': {
                'enabled': False,
                'required': False,
                'modules': [
                    'version.file_version_manager'
                ],
                'description': '文件版本控制',
                'memory_usage': 'medium',
                'trigger_keywords': ['版本', 'version', '历史', '回滚']
            },

            # AI处理（按需）
            'ai': {
                'enabled': False,
                'required': False,
                'modules': [
                    'ai.ai_processor'
                ],
                'description': 'AI智能处理（图像分析、OCR、文本分析）',
                'memory_usage': 'high',
                'trigger_keywords': ['ai', 'ai处理', '图像', 'ocr', '分析', '识别']
            },

            # 分布式存储（可选）
            'distributed_storage': {
                'enabled': False,
                'required': False,
                'modules': [
                    'storage.distributed_storage',
                    'storage.storage_policy'
                ],
                'description': '分布式存储和云存储支持',
                'memory_usage': 'medium',
                'trigger_keywords': ['云存储', 's3', 'oss', '分布式']
            }
        }

        self.active_components: set[str] = set()
        self.startup_reason: str = ""

    def determine_startup_mode(self, mode: str = None,
                             keywords: list[str] = None) -> str:
        """确定启动模式"""

        if mode:
            self.startup_reason = f"用户指定模式: {mode}"
            return mode

        if keywords:
            self.startup_reason = f"关键词触发: {', '.join(keywords)}"
            return self._analyze_keywords(keywords)

        # 默认启动核心组件
        self.startup_reason = "默认启动核心组件"
        return 'minimal'

    def _analyze_keywords(self, keywords: list[str]) -> str:
        """根据关键词确定启动模式"""
        mode = 'minimal'  # 默认只启动核心
        enabled_components = set()

        keyword_to_component = {
            'monitor': 'monitoring',
            '监控': 'monitoring',
            '性能': 'monitoring',
            'batch': 'batch',
            '批量': 'batch',
            '多个文件': 'batch',
            '文件夹': 'batch',
            'version': 'versioning',
            '版本': 'versioning',
            '历史': 'versioning',
            '回滚': 'versioning',
            'ai': 'ai',
            'ai处理': 'ai',
            '图像': 'ai',
            'ocr': 'ai',
            '分析': 'ai',
            '识别': 'ai',
            '云存储': 'distributed_storage',
            's3': 'distributed_storage',
            'oss': 'distributed_storage',
            '分布式': 'distributed_storage'
        }

        for keyword in keywords:
            for pattern, component in keyword_to_component.items():
                if pattern in keyword.lower():
                    enabled_components.add(component)

        if enabled_components:
            for comp in enabled_components:
                self.components[comp]['enabled'] = True
            mode = 'custom'

        return mode

    async def startup(self, mode: str = None, keywords: list[str] = None):
        """启动组件"""
        startup_mode = self.determine_startup_mode(mode, keywords)

        logger.info(f"启动模式: {startup_mode}")
        logger.info(f"启动原因: {self.startup_reason}")

        try:
            # 核心组件总是启动
            await self._start_component('core')

            if startup_mode == 'full':
                # 启动所有组件
                for comp_name in self.components:
                    if comp_name != 'core':
                        await self._start_component(comp_name)

            elif startup_mode == 'custom':
                # 启动启用的组件
                for comp_name, comp_config in self.components.items():
                    if comp_config['enabled'] and comp_name != 'core':
                        await self._start_component(comp_name)

            # 打印启动摘要
            self._print_startup_summary()

        except Exception as e:
            logger.error(f"启动失败: {e}")
            raise

    async def _start_component(self, component_name: str):
        """启动单个组件"""
        component = self.components[component_name]

        try:
            logger.info(f"启动组件: {component_name} - {component['description']}")

            # 动态导入并启动模块
            for module_name in component['modules']:
                try:
                    module = __import__(module_name, fromlist=[component_name.split('.')[1])

                    # 查找启动函数
                    startup_func = getattr(module, 'start', None)
                    if startup_func and asyncio.iscoroutinefunction(startup_func):
                        await startup_func()
                        logger.info(f"  ✓ {module_name} 已启动")
                    else:
                        logger.info(f"  • {module_name} 已加载")

                except ImportError as e:
                    logger.warning(f"  ⚠️ {module_name} 未找到: {e}")
                except Exception as e:
                    logger.error(f"  ❌ {module_name} 启动失败: {e}")

            self.active_components.add(component_name)

        except Exception as e:
            logger.error(f"组件 {component_name} 启动失败: {e}")
            if component['required']:
                raise RuntimeError(f"必需组件 {component_name} 启动失败") from e

    def _print_startup_summary(self) -> Any:
        """打印启动摘要"""
        print("\n" + "="*60)
        print("🚀 Athena多模态文件系统启动完成")
        print("="*60)
        print(f"📊 启动模式: {self.determine_startup_mode()}")
        print(f"📝 启动原因: {self.startup_reason}")
        print()

        print("📦 已启动组件:")
        for comp_name in self.active_components:
            comp = self.components[comp_name]
            status = "✅ 必需" if comp['required'] else "🔧 可选"
            memory = comp['memory_usage']
            print(f"  {status} {comp_name:<15} ({comp['description']}) [{memory}内存]")

        print()
        print("📋 可用功能:")
        if 'core' in self.active_components:
            print("  📁 文件上传下载")
            print("  🔐 安全认证")
            print("  💾 缓存系统")
        if 'monitoring' in self.active_components:
            print("  📊 性能监控")
            print("  📈 指标收集")
        if 'batch' in self.active_components:
            print("  🔄 批量处理")
        if 'versioning' in self.active_components:
            print("  📝 版本管理")
        if 'ai' in self.active_components:
            print("  🤖 AI处理")
            print("  🔍 OCR识别")
        if 'distributed_storage' in self.active_components:
            print("  ☁️ 云存储")
        print()

        print("📍 服务地址:")
        print("  🌐 API服务: http://localhost:8000")
        print("  📚 API文档: http://localhost:8000/docs")
        print("  ❤️ 健康检查: http://localhost:8000/health")
        print()

        print("💡 使用提示:")
        print("  - 启动特定模式: python smart_launcher.py --mode full")
        print("  - 关键词启动: python smart_launcher.py --keywords 监控 ai")
        print("  - 查看状态: python smart_launcher.py --status")

    def get_status(self) -> dict[str, any]:
        """获取组件状态"""
        return {
            "active_components": list(self.active_components),
            "all_components": list(self.components.keys()),
            "startup_reason": self.startup_reason,
            "total_memory": self._calculate_memory_usage()
        }

    def _calculate_memory_usage(self) -> str:
        """估算内存使用"""
        memory_weights = {
            'low': 1,
            'medium': 2,
            'high': 3
        }

        total_weight = sum(
            memory_weights[self.components[comp]['memory_usage']
            for comp in self.active_components
        )

        if total_weight <= 2:
            return "低 (<100MB)"
        elif total_weight <= 5:
            return "中 (100-300MB)"
        else:
            return "高 (>300MB)"

async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Athena多模态文件系统智能启动器')
    parser.add_argument('--mode', choices=['minimal', 'core', 'full', 'custom'],
                       help='启动模式')
    parser.add_argument('--keywords', nargs='+',
                       help='关键词列表（自动识别需求）')
    parser.add_argument('--status', action='store_true',
                       help='显示组件状态')
    parser.add_argument('--config',
                       help='配置文件路径')

    args = parser.parse_args()

    # 创建组件管理器
    manager = ComponentManager()

    if args.status:
        # 显示状态
        status = manager.get_status()
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return

    # 从配置文件加载
    if args.config and os.path.exists(args.config):
        with open(args.config, encoding='utf-8') as f:
            config = json.load(f)

        # 应用配置
        for comp_name, comp_config in config.get('components', {}).items():
            if comp_name in manager.components:
                manager.components[comp_name].update(comp_config)

    try:
        # 启动系统
        await manager.startup(args.mode, args.keywords)

        # 保持运行（可选）
        logger.info("系统运行中... 按Ctrl+C停止")

        # 这里可以添加保持运行的逻辑
        # 比如启动主API服务

    except KeyboardInterrupt:
        logger.info("\n系统已停止")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        sys.exit(1)

# 入口点: @async_main装饰器已添加到main函数
