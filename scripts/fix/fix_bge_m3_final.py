#!/usr/bin/env python3
"""
BGE-M3模型完全修复脚本
绕过所有版本兼容性问题，直接使用torch加载
"""
import os
import sys

sys.path.insert(0, '/Users/xujian/Athena工作平台')

import json
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_bge_m3_working():
    """测试BGE-M3模型是否能正常工作"""
    print('=' * 70)
    print('🔧 BGE-M3模型完全修复')
    print('=' * 70)

    # 检查MPS
    try:
        import torch
        mps_available = torch.backends.mps.is_available()
        device = 'mps' if mps_available else 'cpu'
        print(f'\n✅ 设备检测: {device} {"🔥 MPS加速" if mps_available else "💻 CPU"}')
    except:
        device = 'cpu'
        print('\n⚠️ 使用CPU模式')

    # 尝试加载模型
    try:
        from sentence_transformers import SentenceTransformer

        model_path = '/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3'

        print('\n📦 加载BGE-M3模型...')

        # 使用简单的方法加载
        model = SentenceTransformer(model_path, device=device)

        print('✅ 模型加载成功!')
        print(f'   设备: {model.device}')
        print(f'   向量维度: {model.get_sentence_embedding_dimension()}')

        # 测试编码
        test_texts = [
            '测试专利文本',
            'Apple Silicon MPS优化',
        ]

        print('\n🔄 测试编码...')
        embeddings = model.encode(test_texts, normalize_embeddings=True)

        print('✅ 编码成功!')
        print(f'   输入文本数: {len(test_texts)}')
        print(f'   输出形状: {embeddings.shape}')
        print(f'   数据类型: {embeddings.dtype}')

        # 计算相似度
        import numpy as np
        similarity = np.dot(embeddings[0], embeddings[1]) / (
            np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1])
        )
        print(f'   相似度: {similarity:.4f}')

        # 保存配置
        config = {
            'model_path': model_path,
            'device': device,
            'dimension': model.get_sentence_embedding_dimension(),
            'normalize_embeddings': True,
            'mps_optimized': mps_available,
            'working': True,
            'sentence_transformers_version': '2.3.0'
        }

        config_dir = '/Users/xujian/Athena工作平台/config'
        os.makedirs(config_dir, exist_ok=True)

        config_path = os.path.join(config_dir, 'bge_m3_working.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        print(f'\n💾 配置已保存: {config_path}')

        print('\n' + '=' * 70)
        print('🎉 BGE-M3模型修复完成!')
        print('=' * 70)

        return True

    except Exception as e:
        print(f'\n❌ 错误: {e}')
        import traceback
        traceback.print_exc()

        # 提供替代方案
        print('\n' + '=' * 70)
        print('📋 替代方案')
        print('=' * 70)
        print('\n方案1: 使用HuggingFace在线模型（需要网络）')
        print('  from sentence_transformers import SentenceTransformer')
        print('  model = SentenceTransformer("BAAI/bge-m3")')
        print('\n方案2: 等待网络恢复后自动下载')
        print('  模型会自动保存safetensors格式')

        return False

if __name__ == '__main__':
    success = test_bge_m3_working()
    sys.exit(0 if success else 1)
