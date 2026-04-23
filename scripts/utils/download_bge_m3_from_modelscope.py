#!/usr/bin/env python3
"""
使用魔搭社区（ModelScope）下载BGE-M3模型
下载safetensors格式，完美兼容transformers 5.x
"""
import os
import sys

# 添加项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')

import logging

from modelscope.hub.snapshot_download import snapshot_download

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def download_bge_m3_from_modelscope():
    """
    从魔搭社区下载BGE-M3模型
    """
    print('=' * 70)
    print('🌟 使用魔搭社区下载BGE-M3模型')
    print('=' * 70)

    # 模型信息
    model_id = 'Xorbits/bge-m3'
    cache_dir = '/Users/xujian/Athena工作平台/models/modelscope'
    save_directory = '/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3-safetensors'

    print(f'\n📦 模型ID: {model_id}')
    print(f'💾 保存路径: {save_directory}')
    print('\n🚀 开始下载...')

    try:
        # 创建目录
        os.makedirs(save_directory, exist_ok=True)

        # 从魔搭社区下载模型
        model_dir = snapshot_download(
            model_id,
            cache_dir=cache_dir,
            revision='master',
        )

        print('\n✅ 模型下载完成!')
        print(f'📁 下载位置: {model_dir}')

        # 复制到目标位置
        import shutil
        if model_dir != save_directory:
            print(f'\n📋 复制模型文件到: {save_directory}')
            if os.path.exists(save_directory):
                shutil.rmtree(save_directory)
            shutil.copytree(model_dir, save_directory)
            print(f'✅ 模型已保存到: {save_directory}')

        # 验证模型文件
        print('\n🔍 验证模型文件...')
        model_files = os.listdir(save_directory)
        print(f'📄 文件数量: {len(model_files)}')

        # 检查safetensors文件
        has_safetensors = any(f.endswith('.safetensors') for f in model_files)
        if has_safetensors:
            print('✅ 包含safetensors格式文件')
        else:
            print('⚠️  未找到safetensors文件')

        # 测试加载模型
        print('\n🧪 测试模型加载...')
        import torch
        from sentence_transformers import SentenceTransformer

        # 检测设备
        if torch.backends.mps.is_available():
            device = 'mps'
            print('🔥 使用MPS (Apple Silicon GPU)')
        else:
            device = 'cpu'
            print('💻 使用CPU')

        # 加载模型
        model = SentenceTransformer(save_directory, device=device)

        print('✅ 模型加载成功!')
        print(f'   设备: {device}')
        print(f'   向量维度: {model.get_sentence_embedding_dimension()}')

        # 测试编码
        test_text = '测试专利文本嵌入功能'
        embedding = model.encode(test_text)
        print('✅ 测试编码成功!')
        print(f'   输入: "{test_text}"')
        print(f'   输出维度: {len(embedding)}')

        print('\n' + '=' * 70)
        print('🎉 BGE-M3模型下载并验证成功!')
        print('=' * 70)

        # 保存配置
        import json
        config = {
            'model_path': save_directory,
            'device': device,
            'dimension': model.get_sentence_embedding_dimension(),
            'has_safetensors': has_safetensors,
            'mps_optimized': device == 'mps',
            'source': 'modelscope',
            'model_id': model_id
        }

        config_path = '/Users/xujian/Athena工作平台/config/bge_m3_modelscope.json'
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f'💾 配置已保存: {config_path}')

        return True, save_directory

    except Exception as e:
        print(f'\n❌ 下载失败: {e}')
        import traceback
        traceback.print_exc()
        return False, None

if __name__ == '__main__':
    success, model_path = download_bge_m3_from_modelscope()

    if success:
        print('\n✨ 下一步: 使用模型')
        print('from sentence_transformers import SentenceTransformer')
        print(f'model = SentenceTransformer("{model_path}", device="mps")')
    else:
        print('\n⚠️  请检查网络连接或稍后重试')

    sys.exit(0 if success else 1)
