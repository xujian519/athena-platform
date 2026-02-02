#!/usr/bin/env python3
"""
扫描并管理本地大模型
Scan and manage local large language models
"""

import os
import json
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import requests

class LocalModelScanner:
    """本地模型扫描器"""

    def __init__(self):
        self.logger = self._setup_logger()
        self.scanned_models = []
        self.model_registry = {}

    def _setup_logger(self):
        """设置日志"""
        import logging
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def scan_ollama_models(self) -> Dict[str, Any]:
        """扫描Ollama本地模型"""
        try:
            response = requests.get('http://localhost:11434/api/tags', timeout=10)
            if response.status_code == 200:
                data = response.json()
                models = data.get('models', [])

                ollama_models = {}
                for model in models:
                    model_info = {
                        'name': model['name'],
                        'size': model['size'],
                        'modified_at': model['modified_at'],
                        'digest': model['digest'],
                        'details': model.get('details', {}),
                        'provider': 'ollama',
                        'type': self._detect_model_type(model['name']),
                        'category': self._categorize_model(model['name'])
                    }
                    ollama_models[model['name']] = model_info
                    self.scanned_models.append(model_info)

                self.logger.info(f"发现 {len(ollama_models)} 个Ollama模型")
                return ollama_models
        except Exception as e:
            self.logger.error(f"扫描Ollama模型失败: {e}")
            return {}

    def scan_hf_models(self) -> Dict[str, Any]:
        """扫描Hugging Face本地模型"""
        hf_models = {}

        # 常见的HF模型目录
        hf_dirs = [
            os.path.expanduser('~/.cache/huggingface/hub'),
            os.path.expanduser('~/models'),
            '/tmp/models',
            '/models'
        ]

        for model_dir in hf_dirs:
            if os.path.exists(model_dir):
                self.logger.info(f"扫描目录: {model_dir}")
                for root, dirs, files in os.walk(model_dir):
                    # 查找模型标识文件
                    if 'config.json' in files:
                        model_path = os.path.join(root, 'config.json')
                        try:
                            with open(model_path, 'r', encoding='utf-8') as f:
                                config = json.load(f)

                            model_info = {
                                'name': config.get('_name_or_path', os.path.basename(root)),
                                'path': root,
                                'size': self._calculate_dir_size(root),
                                'provider': 'huggingface',
                                'type': config.get('model_type', 'unknown'),
                                'architecture': config.get('architectures', ['unknown'])[0] if config.get('architectures') else 'unknown',
                                'category': self._categorize_model(config.get('_name_or_path', '')),
                                'config': config
                            }

                            hf_models[model_info['name']] = model_info
                            self.scanned_models.append(model_info)

                        except Exception as e:
                            self.logger.warning(f"读取模型配置失败 {model_path}: {e}")

        self.logger.info(f"发现 {len(hf_models)} 个Hugging Face模型")
        return hf_models

    def scan_custom_models(self) -> Dict[str, Any]:
        """扫描自定义模型目录"""
        custom_models = {}

        # 检查是否有自定义模型目录
        custom_dirs = [
            'models/local',
            'models/custom',
            'storage-system/models',
            'data/models'
        ]

        for model_dir in custom_dirs:
            if os.path.exists(model_dir):
                self.logger.info(f"扫描自定义目录: {model_dir}")
                for item in os.listdir(model_dir):
                    item_path = os.path.join(model_dir, item)
                    if os.path.isdir(item_path):
                        model_info = {
                            'name': item,
                            'path': item_path,
                            'size': self._calculate_dir_size(item_path),
                            'provider': 'custom',
                            'type': 'unknown',
                            'category': self._categorize_model(item)
                        }

                        # 尝试检测模型类型
                        if os.path.exists(os.path.join(item_path, 'config.json')):
                            try:
                                with open(os.path.join(item_path, 'config.json'), 'r') as f:
                                    config = json.load(f)
                                    model_info['config'] = config
                                    model_info['type'] = config.get('type', 'unknown')
                            except:
                                pass

                        custom_models[item] = model_info
                        self.scanned_models.append(model_info)

        self.logger.info(f"发现 {len(custom_models)} 个自定义模型")
        return custom_models

    def _detect_model_type(self, model_name: str) -> str:
        """检测模型类型"""
        model_name_lower = model_name.lower()

        if any(keyword in model_name_lower for keyword in ['embed', 'embedding', 'sentence-bert', 'bge']):
            return 'embedding'
        elif any(keyword in model_name_lower for keyword in ['chat', 'llama', 'qwen', 'mistral', 'vicuna']):
            return 'chat'
        elif any(keyword in model_name_lower for keyword in ['vl', 'vision', 'multimodal', 'clip']):
            return 'multimodal'
        elif any(keyword in model_name_lower for keyword in ['code', 'coder', 'starcoder', 'deepseek']):
            return 'code'
        else:
            return 'general'

    def _categorize_model(self, model_name: str) -> str:
        """模型分类"""
        model_name_lower = model_name.lower()

        if any(keyword in model_name_lower for keyword in ['llama', 'vicuna', 'mistral']):
            return 'llm'
        elif any(keyword in model_name_lower for keyword in ['embed', 'embedding', 'bge']):
            return 'embedding'
        elif any(keyword in model_name_lower for keyword in ['stable-diffusion', 'sd']):
            return 'image_generation'
        elif any(keyword in model_name_lower for keyword in ['whisper', 'asr']):
            return 'speech'
        elif any(keyword in model_name_lower for keyword in ['tts', 'voice']):
            return 'tts'
        else:
            return 'other'

    def _calculate_dir_size(self, path: str) -> int:
        """计算目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def save_registry(self, registry_path: str = 'config/local_model_registry.json'):
        """保存模型注册表"""
        registry = {
            'scan_time': datetime.now().isoformat(),
            'total_models': len(self.scanned_models),
            'models_by_provider': {},
            'models_by_category': {},
            'models': {}
        }

        for model in self.scanned_models:
            registry['models'][model['name']] = model

            # 按提供商分组
            provider = model['provider']
            if provider not in registry['models_by_provider']:
                registry['models_by_provider'][provider] = []
            registry['models_by_provider'][provider].append(model['name'])

            # 按类别分组
            category = model['category']
            if category not in registry['models_by_category']:
                registry['models_by_category'][category] = []
            registry['models_by_category'][category].append(model['name'])

        # 确保目录存在
        os.makedirs(os.path.dirname(registry_path), exist_ok=True)

        with open(registry_path, 'w', encoding='utf-8') as f:
            json.dump(registry, f, indent=2, ensure_ascii=False)

        self.logger.info(f"模型注册表已保存到: {registry_path}")
        return registry

def main():
    """主函数"""
    scanner = LocalModelScanner()

    print("🔍 开始扫描本地大模型...")
    print("=" * 50)

    # 1. 扫描Ollama模型
    print("\n1️⃣ 扫描Ollama模型...")
    ollama_models = scanner.scan_ollama_models()
    if ollama_models:
        for name, info in ollama_models.items():
            size_gb = info['size'] / (1024**3)
            print(f"   - {name} ({size_gb:.2f}GB)")

    # 2. 扫描Hugging Face模型
    print("\n2️⃣ 扫描Hugging Face模型...")
    hf_models = scanner.scan_hf_models()
    if hf_models:
        for name, info in hf_models.items():
            size_gb = info['size'] / (1024**3)
            print(f"   - {name} ({info.get('architecture', 'unknown')}, {size_gb:.2f}GB)")

    # 3. 扫描自定义模型
    print("\n3️⃣ 扫描自定义模型...")
    custom_models = scanner.scan_custom_models()
    if custom_models:
        for name, info in custom_models.items():
            size_gb = info['size'] / (1024**3)
            print(f"   - {name} ({size_gb:.2f}GB)")

    # 4. 保存注册表
    print("\n4️⃣ 保存模型注册表...")
    registry = scanner.save_registry()

    print("\n" + "=" * 50)
    print(f"✅ 扫描完成！")
    print(f"   - 总模型数: {registry['total_models']}")
    print(f"   - 注册表位置: config/local_model_registry.json")
    print(f"   - 按提供商: {dict(registry['models_by_provider'])}")
    print(f"   - 按类别: {dict(registry['models_by_category'])}")

if __name__ == "__main__":
    main()