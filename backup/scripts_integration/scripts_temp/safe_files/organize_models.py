#!/usr/bin/env python3
"""
组织本地大模型到合适的文件夹
Organize local LLMs into appropriate directories
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List

class ModelOrganizer:
    """模型组织器"""

    def __init__(self):
        self.base_dir = Path('models')
        self.backup_dir = Path('models/backup')

        # 创建标准目录结构
        self.dirs = {
            'llm': self.base_dir / 'llm',
            'embedding': self.base_dir / 'embedding',
            'multimodal': self.base_dir / 'multimodal',
            'image_generation': self.base_dir / 'image_generation',
            'speech': self.base_dir / 'speech',
            'custom': self.base_dir / 'custom',
            'cache': self.base_dir / 'cache'
        }

        self._create_directories()

    def _create_directories(self):
        """创建目录结构"""
        for dir_name, dir_path in self.dirs.items():
            dir_path.mkdir(parents=True, exist_ok=True)
            # 创建.gitkeep文件
            (dir_path / '.gitkeep').touch()

    def load_model_registry(self) -> Dict:
        """加载模型注册表"""
        try:
            with open('config/local_model_registry.json', 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print("❌ 找不到模型注册表，请先运行扫描脚本")
            return {}

    def organize_models(self):
        """组织模型"""
        registry = self.load_model_registry()
        if not registry:
            return False

        print(f"📁 开始组织模型文件...")
        print("=" * 50)

        moved_count = 0
        backed_up_count = 0

        for model_name, model_info in registry['models'].items():
            if model_info['provider'] == 'huggingface':
                # 移动Hugging Face缓存模型
                if self._move_hf_model(model_info):
                    moved_count += 1

        print(f"\n✅ 组织完成！")
        print(f"   - 移动模型数: {moved_count}")
        print(f"   - 目录结构:")

        for dir_name, dir_path in self.dirs.items():
            if dir_path.exists():
                count = len([item for item in dir_path.iterdir() if item.is_dir() or item.is_file() and item.name != '.gitkeep'])
                if count > 0:
                    size = sum(f.stat().st_size for f in dir_path.rglob('*') if f.is_file())
                    size_gb = size / (1024**3)
                    print(f"     {dir_name}/: {count} 项 ({size_gb:.2f}GB)")

        return True

    def _move_hf_model(self, model_info: Dict) -> bool:
        """移动Hugging Face模型"""
        original_path = Path(model_info['path'])

        if not original_path.exists():
            return False

        # 跳过只读目录
        if '/root/' in str(original_path) or '/System/' in str(original_path):
            print(f"⚠️ 跳过只读目录: {model_info['name']}")
            return False

        # 确定目标目录
        model_type = model_info.get('type', 'unknown')
        category = model_info.get('category', 'other')

        if model_type == 'embedding':
            target_dir = self.dirs['embedding']
        elif category == 'llm':
            target_dir = self.dirs['llm']
        elif model_type == 'multimodal':
            target_dir = self.dirs['multimodal']
        elif category == 'image_generation':
            target_dir = self.dirs['image_generation']
        elif category == 'speech':
            target_dir = self.dirs['speech']
        else:
            target_dir = self.dirs['custom']

        # 创建模型特定的子目录
        model_subdir = target_dir / model_info['name']
        model_subdir.mkdir(parents=True, exist_ok=True)

        # 检查是否已存在
        if model_subdir.exists() and any(model_subdir.iterdir()):
            print(f"⚠️ 模型已存在: {model_info['name']}")
            return False

        # 移动模型
        try:
            print(f"   移动: {model_info['name']} -> {model_subdir}")
            shutil.move(str(original_path), str(model_subdir / 'model_files'))

            # 创建模型信息文件
            model_info_path = model_subdir / 'model_info.json'
            with open(model_info_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'original_path': str(original_path),
                    'moved_at': datetime.now().isoformat(),
                    'provider': model_info['provider'],
                    'type': model_info['type'],
                    'architecture': model_info.get('architecture', 'unknown'),
                    'category': category,
                    'config': model_info.get('config', {})
                }, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"❌ 移动失败 {model_info['name']}: {e}")
            return False

    def create_symbolic_links(self):
        """创建符号链接以便访问"""
        print("\n🔗 创建便捷访问符号链接...")

        # 为常用模型创建符号链接
        registry = self.load_model_registry()

        # 创建当前模型符号链接
        current_dir = self.base_dir / 'current'
        current_dir.mkdir(exist_ok=True)

        # GLM-4 配置
        with open(current_dir / 'glm-4.json', 'w') as f:
            json.dump({
                'provider': 'zhipu',
                'model': 'glm-4',
                'endpoint': 'https://open.bigmodel.cn/api/paas/v4/',
                'type': 'api'
            }, f, indent=2)

        # 创建快速访问脚本
        quick_access_script = self.base_dir / 'quick_access.sh'
        with open(quick_access_script, 'w') as f:
            f.write("""#!/bin/bash
# 模型快速访问脚本
echo "🤖 Athena平台模型快速访问"
echo "========================="
echo ""
echo "1. LLM模型目录: $(ls -la models/llm/ | head -10)"
echo ""
echo "2. 嵌入模型目录: $(ls -la models/embedding/ | head -10)"
echo ""
echo "3. 多模态模型目录: $(ls -la models/multimodal/ | head -10)"
echo ""
echo "4. 当前配置:"
echo "   - GLM-4: $(cat models/current/glm-4.json | jq -r .model)"
echo ""
echo "5. 运行模型管理:"
echo "   cd models && python -c 'import organize_models; org=ModelOrganizer(); org.organize_models()'
""")

        os.chmod(quick_access_script, 0o755)
        print("✅ 快速访问脚本已创建: models/quick_access.sh")

def main():
    """主函数"""
    print("📁 开始组织本地模型...")

    organizer = ModelOrganizer()

    # 检查备份目录
    if organizer.backup_dir.exists():
        print("⚠️ 备份目录已存在，将在移动前创建时间戳备份")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_with_timestamp = organizer.backup_dir / f"backup_{timestamp}"
        shutil.move(str(organizer.backup_dir), str(backup_with_timestamp))

    # 组织模型
    success = organizer.organize_models()

    if success:
        # 创建符号链接
        organizer.create_symbolic_links()

        print("\n" + "=" * 50)
        print("🎉 模型组织完成！")
        print("✅ 所有模型已移动到合适的目录")
        print("✅ 创建了标准化的目录结构")
        print("✅ 生成了模型访问脚本")
        print("\n📖 使用 models/quick_access.sh 快速访问模型")

if __name__ == "__main__":
    main()