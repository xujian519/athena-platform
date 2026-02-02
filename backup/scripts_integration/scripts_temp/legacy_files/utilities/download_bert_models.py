#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BERT模型下载管理器
从127.0.0.1:9981端口下载所需的中文BERT模型
"""

import asyncio
import json
import logging
import os
import sys
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import requests

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BERTModelDownloader:
    """BERT模型下载管理器"""

    def __init__(self):
        self.base_url = 'http://127.0.0.1:9981'
        self.models_dir = Path('/Users/xujian/Athena工作平台/models')
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # 模型配置
        self.required_models = {
            # 中文BERT基础模型
            'bert-base-chinese': {
                'description': '中文BERT基础模型',
                'model_files': [
                    'config.json',
                    'pytorch_model.bin',
                    'vocab.txt',
                    'tokenizer.json'
                ],
                'local_path': self.models_dir / 'bert-base-chinese',
                'url_path': 'bert/chinese/bert-base-chinese',
                'size_gb': 0.4,
                'priority': 'high'
            },

            # BGE大型中文向量模型
            'bge-large-zh-v1.5': {
                'description': 'BGE大型中文语义向量模型',
                'model_files': [
                    'config.json',
                    'pytorch_model.bin',
                    'vocab.txt',
                    'tokenizer_config.json',
                    'sentencepiece.bpe.model'
                ],
                'local_path': self.models_dir / 'bge-large-zh-v1.5',
                'url_path': 'bge/chinese/bge-large-zh-v1.5',
                'size_gb': 1.3,
                'priority': 'high'
            },

            # 专利专用中文模型
            'text2vec-base-chinese': {
                'description': '中文专利文本向量模型',
                'model_files': [
                    'config.json',
                    'pytorch_model.bin',
                    'vocab.txt',
                    'tokenizer.json'
                ],
                'local_path': self.models_dir / 'text2vec-base-chinese',
                'url_path': 'text2vec/chinese/text2vec-base-chinese',
                'size_gb': 0.8,
                'priority': 'medium'
            },

            # 多语言MiniLM模型
            'paraphrase-multilingual-MiniLM-L12-v2': {
                'description': '多语言语义向量模型',
                'model_files': [
                    'config.json',
                    'pytorch_model.bin',
                    'vocab.txt',
                    'tokenizer_config.json'
                ],
                'local_path': self.models_dir / 'paraphrase-multilingual-MiniLM-L12-v2',
                'url_path': 'sentence-transformers/multilingual/paraphrase-multilingual-MiniLM-L12-v2',
                'size_gb': 0.5,
                'priority': 'medium'
            },

            # 中文法律BERT
            'chinese-bert-wwm-ext': {
                'description': '中文法律BERT模型（扩展版）',
                'model_files': [
                    'config.json',
                    'pytorch_model.bin',
                    'vocab.txt',
                    'tokenizer_config.json'
                ],
                'local_path': self.models_dir / 'chinese-bert-wwm-ext',
                'url_path': 'bert/chinese/chinese-bert-wwm-ext',
                'size_gb': 0.4,
                'priority': 'low'
            }
        }

    def check_models_status(self) -> Dict[str, Dict]:
        """检查所有模型的状态"""
        status = {}

        for model_name, config in self.required_models.items():
            local_path = config['local_path']

            # 检查目录是否存在
            if not local_path.exists():
                status[model_name] = {
                    'status': 'missing',
                    'downloaded': False,
                    'complete': False,
                    'files_present': 0,
                    'total_files': len(config['model_files']),
                    'description': config['description'],
                    'priority': config['priority']
                }
                continue

            # 检查文件完整性
            files_present = 0
            missing_files = []
            for file_name in config['model_files']:
                file_path = local_path / file_name
                if file_path.exists():
                    files_present += 1
                else:
                    missing_files.append(file_name)

            is_complete = files_present == len(config['model_files'])
            status[model_name] = {
                'status': 'complete' if is_complete else 'incomplete',
                'downloaded': True,
                'complete': is_complete,
                'files_present': files_present,
                'total_files': len(config['model_files']),
                'missing_files': missing_files,
                'description': config['description'],
                'priority': config['priority']
            }

        return status

    def print_status_report(self, status: Dict[str, Dict]):
        """打印状态报告"""
        logger.info(str("\n" + '='*80))
        logger.info('🤖 BERT模型状态报告')
        logger.info(str('='*80))

        # 统计信息
        total_models = len(status)
        complete_models = sum(1 for s in status.values() if s['complete'])
        missing_models = sum(1 for s in status.values() if not s['downloaded'])

        logger.info(f"📊 总计模型: {total_models}")
        logger.info(f"✅ 完整模型: {complete_models}")
        logger.info(f"❌ 缺失模型: {missing_models}")
        logger.info(f"⚠️ 不完整模型: {total_models - complete_models - missing_models}")

        # 详细状态
        logger.info(f"\n📋 详细状态:")
        logger.info(str('-' * 80))

        for model_name, info in status.items():
            status_icon = '✅' if info['complete'] else '❌' if not info['downloaded'] else '⚠️'
            priority_tag = info['priority'].upper()

            logger.info(f"{status_icon} {model_name}")
            logger.info(f"   📝 描述: {info['description']}")
            logger.info(f"   🎯 优先级: {priority_tag}")
            logger.info(f"   📁 状态: {info['status']}")
            logger.info(f"   📊 进度: {info['files_present']}/{info['total_files']} 文件")

            if info.get('missing_files'):
                logger.info(f"   ❌ 缺失: {', '.join(info['missing_files'])}")
            print()

    async def download_model(self, model_name: str, session: aiohttp.ClientSession) -> bool:
        """下载指定模型"""
        if model_name not in self.required_models:
            logger.error(f"未知模型: {model_name}")
            return False

        config = self.required_models[model_name]
        local_path = config['local_path']

        # 创建模型目录
        local_path.mkdir(parents=True, exist_ok=True)

        logger.info(f"🚀 开始下载模型: {model_name}")
        logger.info(f"📝 描述: {config['description']}")
        logger.info(f"📦 大小: ~{config['size_gb']}GB")

        success_count = 0

        try:
            # 下载每个文件
            for file_name in config['model_files']:
                file_url = f"{self.base_url}/{config['url_path']}/{file_name}"
                local_file_path = local_path / file_name

                # 如果文件已存在，跳过
                if local_file_path.exists():
                    logger.info(f"⏭️ 文件已存在，跳过: {file_name}")
                    success_count += 1
                    continue

                logger.info(f"⬇️ 下载文件: {file_name}")

                try:
                    async with session.get(file_url, timeout=aiohttp.ClientTimeout(total=300)) as response:
                        if response.status == 200:
                            # 流式下载大文件
                            with open(local_file_path, 'wb') as f:
                                async for chunk in response.content.iter_chunked(8192):
                                    f.write(chunk)

                            logger.info(f"✅ 文件下载完成: {file_name}")
                            success_count += 1
                        else:
                            logger.error(f"❌ 下载失败: {file_name} (状态码: {response.status})")

                except asyncio.TimeoutError:
                    logger.error(f"❌ 下载超时: {file_name}")
                except Exception as e:
                    logger.error(f"❌ 下载异常: {file_name} - {e}")

            # 检查下载结果
            if success_count == len(config['model_files']):
                logger.info(f"🎉 模型 {model_name} 下载完成!")
                return True
            else:
                logger.warning(f"⚠️ 模型 {model_name} 部分下载成功: {success_count}/{len(config['model_files'])}")
                return False

        except Exception as e:
            logger.error(f"❌ 下载模型 {model_name} 时发生错误: {e}")
            return False

    async def download_all_models(self, priority_filter: str | None = None):
        """批量下载模型"""
        # 筛选要下载的模型
        models_to_download = []
        for model_name, config in self.required_models.items():
            if priority_filter and config['priority'] != priority_filter:
                continue
            models_to_download.append((model_name, config))

        if not models_to_download:
            logger.info('没有需要下载的模型')
            return

        logger.info(f"🚀 开始批量下载 {len(models_to_download)} 个模型...")

        # 创建HTTP会话
        connector = aiohttp.TCPConnector(limit=5)  # 限制并发连接数
        timeout = aiohttp.ClientTimeout(total=600)  # 10分钟超时

        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # 逐个下载（避免同时下载多个大文件）
            for model_name, config in models_to_download:
                success = await self.download_model(model_name, session)
                if not success:
                    logger.warning(f"⚠️ 模型 {model_name} 下载失败，继续下载其他模型")

                # 短暂暂停，避免服务器压力过大
                await asyncio.sleep(2)

        logger.info('🏁 批量下载完成!')

    def create_model_symlinks(self):
        """创建模型符号链接，方便各种路径引用"""
        logger.info('🔗 创建模型符号链接...')

        # 创建常用模型的符号链接
        symlinks = [
            # BGE模型
            {
                'source': self.models_dir / 'bge-large-zh-v1.5',
                'target': self.models_dir / 'bge-large-zh',
                'description': 'BGE大型中文模型简短链接'
            },
            # BERT基础模型
            {
                'source': self.models_dir / 'bert-base-chinese',
                'target': self.models_dir / 'bert-chinese',
                'description': '中文BERT基础模型简短链接'
            }
        ]

        for symlink in symlinks:
            if symlink['target'].exists():
                logger.info(f"⏭️ 链接已存在: {symlink['description']}")
                continue

            try:
                symlink['target'].symlink_to(symlink['source'], target_is_directory=True)
                logger.info(f"✅ 创建链接: {symlink['description']}")
            except Exception as e:
                logger.warning(f"⚠️ 创建链接失败: {symlink['description']} - {e}")

    def generate_config_file(self):
        """生成模型配置文件"""
        config_file = self.models_dir / 'model_config.json'

        status = self.check_models_status()

        config = {
            'generated_time': '2025-12-11T00:00:00Z',
            'models_directory': str(self.models_dir),
            'available_models': {},
            'model_paths': {}
        }

        for model_name, model_config in self.required_models.items():
            model_status = status[model_name]

            if model_status['complete']:
                config['available_models'][model_name] = {
                    'description': model_config['description'],
                    'local_path': str(model_config['local_path']),
                    'priority': model_config['priority'],
                    'size_gb': model_config['size_gb']
                }

                # 添加常用路径映射
                config['model_paths'][model_name] = str(model_config['local_path'])

        # 写入配置文件
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)

        logger.info(f"💾 配置文件已生成: {config_file}")
        return config_file

async def main():
    """主函数"""
    downloader = BERTModelDownloader()

    logger.info('🤖 BERT模型管理器')
    logger.info(str('=' * 50))

    # 检查当前状态
    status = downloader.check_models_status()
    downloader.print_status_report(status)

    # 询问用户操作
    logger.info("\n🎯 请选择操作:")
    logger.info('1. 下载高优先级模型')
    logger.info('2. 下载全部模型')
    logger.info('3. 下载指定模型')
    logger.info('4. 仅检查状态')
    logger.info('5. 生成配置文件')

    try:
        choice = input("\n请输入选项 (1-5): ").strip()

        if choice == '1':
            logger.info("\n🚀 下载高优先级模型...")
            await downloader.download_all_models(priority_filter='high')
        elif choice == '2':
            logger.info("\n🚀 下载全部模型...")
            await downloader.download_all_models()
        elif choice == '3':
            logger.info("\n🚀 下载指定模型...")
            model_list = list(downloader.required_models.keys())
            for i, model in enumerate(model_list, 1):
                logger.info(f"{i}. {model} - {downloader.required_models[model]['description']}")

            model_choice = input('请输入模型编号: ').strip()
            if model_choice.isdigit() and 1 <= int(model_choice) <= len(model_list):
                selected_model = model_list[int(model_choice) - 1]
                async with aiohttp.ClientSession() as session:
                    await downloader.download_model(selected_model, session)
            else:
                logger.info('❌ 无效选择')
        elif choice == '4':
            logger.info("\n📊 当前状态检查完成")
        elif choice == '5':
            logger.info("\n📝 生成配置文件...")
            downloader.generate_config_file()
        else:
            logger.info('❌ 无效选项')

    except KeyboardInterrupt:
        logger.info("\n👋 用户中断操作")
    except Exception as e:
        logger.error(f"❌ 操作失败: {e}")

    # 完成后操作
    if choice in ['1', '2', '3']:
        logger.info("\n🔗 创建符号链接...")
        downloader.create_model_symlinks()

        logger.info("\n📝 生成配置文件...")
        downloader.generate_config_file()

    logger.info("\n🎉 操作完成!")

if __name__ == '__main__':
    asyncio.run(main())