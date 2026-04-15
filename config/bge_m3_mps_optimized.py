#!/usr/bin/env python3
"""
BGE-M3 Apple Silicon MPS优化配置
自动检测并使用最优设备加载BGE-M3模型
"""
import sys

# 添加项目路径
sys.path.insert(0, '/Users/xujian/Athena工作平台')

def get_optimal_bge_m3_model():
    """
    获取最优化的BGE-M3模型配置
    自动检测MPS可用性并返回最佳配置
    """
    # 检测MPS可用性
    try:
        import torch
        mps_available = torch.backends.mps.is_available()
    except Exception:
        mps_available = False

    # 模型配置
    config = {
        'model_name': 'BAAI/bge-m3',
        'device': 'mps' if mps_available else 'cpu',
        'model_path': '/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3',
        'fallback_path': '/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3-st',
        'use_safetensors': False,  # 使用pytorch格式
        'trust_remote_code': True,
        'dimension': 1024,
        'max_seq_length': 8192,
        'normalize_embeddings': True,
        'mps_optimized': mps_available
    }

    return config

def load_bge_m3_model():
    """
    加载BGE-M3模型（Apple Silicon优化）
    """
    config = get_optimal_bge_m3_model()

    print('=' * 70)
    print('🍎 BGE-M3 Apple Silicon优化加载器')
    print('=' * 70)
    print('\n📋 配置信息:')
    print(f'   设备: {config["device"]} {"🔥 MPS加速" if config["mps_optimized"] else "💻 CPU"}')
    print(f'   向量维度: {config["dimension"]}')
    print(f'   最大序列长度: {config["max_seq_length"]}')

    try:
        from sentence_transformers import SentenceTransformer

        # 尝试加载模型
        print('\n📦 加载BGE-M3模型...')
        model = SentenceTransformer(
            config['model_path'],
            device=config['device'],
            trust_remote_code=config['trust_remote_code']
        )

        print('✅ 模型加载成功!')
        print(f'   实际设备: {model.device}')
        print(f'   向量维度: {model.get_sentence_embedding_dimension()}')

        return model, config

    except Exception as e:
        print(f'⚠️ 主路径加载失败: {e}')
        print(f'📦 尝试备用路径: {config["fallback_path"]}')

        try:
            model = SentenceTransformer(
                config['fallback_path'],
                device=config['device'],
                trust_remote_code=config['trust_remote_code']
            )
            print('✅ 备用模型加载成功!')
            return model, config
        except Exception as e2:
            print(f'❌ 备用模型也失败: {e2}')
            return None, config

# 测试代码
if __name__ == '__main__':
    model, config = load_bge_m3_model()

    if model:
        print('\n' + '=' * 70)
        print('🎉 BGE-M3模型可用!')
        print('=' * 70)

        # 测试编码
        test_text = '测试Apple Silicon MPS加速的BGE-M3模型'
        embedding = model.encode(test_text)

        print('\n✅ 测试编码成功!')
        print(f'   输入: "{test_text}"')
        print(f'   输出形状: {embedding.shape}')
        print(f'   数据类型: {embedding.dtype}')
