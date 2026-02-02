#!/usr/bin/env python3
"""
检查现有BERT模型
Check Existing BERT Models
"""

import os
import sys
from pathlib import Path

def check_hf_cache():
    """检查HuggingFace缓存中的BERT模型"""
    print("🔍 检查HuggingFace缓存中的BERT模型...")
    hf_cache = Path.home() / ".cache/huggingface/hub"

    if not hf_cache.exists():
        print("❌ HuggingFace缓存目录不存在")
        return {}

    bert_models = {}
    for item in hf_cache.iterdir():
        if item.is_dir() and "bert" in item.name.lower() or "roberta" in item.name.lower() or "deberta" in item.name.lower() or "electra" in item.name.lower():
            print(f"📁 发现可能的BERT模型: {item.name}")

            # 检查快照
            snapshots_dir = item / "snapshots"
            if snapshots_dir.exists():
                snapshots = list(snapshots_dir.iterdir())
                if snapshots:
                    latest = max(snapshots, key=lambda x: x.stat().st_mtime)
                    print(f"   📸 最新快照: {latest.name}")

                    # 检查config.json
                    config_file = latest / "config.json"
                    if config_file.exists():
                        bert_models[item.name] = {
                            "path": str(latest),
                            "has_config": True
                        }
                    else:
                        bert_models[item.name] = {
                            "path": str(latest),
                            "has_config": False
                        }

    return bert_models

def check_modelscope_cache():
    """检查ModelScope缓存"""
    print("\n🔍 检查ModelScope缓存...")
    ms_cache = Path.home() / ".cache/modelscope"

    if not ms_cache.exists():
        print("❌ ModelScope缓存目录不存在")
        return {}

    bert_models = {}
    for item in ms_cache.rglob("*"):
        if item.is_file() and item.suffix == ".json":
            try:
                import json
                with open(item, 'r') as f:
                    data = json.load(f)
                    if "Model" in data or "bert" in str(data).lower():
                        print(f"📄 发现相关配置: {item.relative_to(ms_cache)}")
            except:
                pass

    return bert_models

def check_local_bert():
    """检查本地BERT模型"""
    print("\n🔍 检查本地BERT模型路径...")

    local_paths = [
        "/Users/xujian/Athena工作平台/models",
        "/Users/xujian/Athena工作平台/models/bert_cache",
        "/Users/xujian/.cache/huggingface/hub"
    ]

    found_models = []
    for path in local_paths:
        if Path(path).exists():
            for item in Path(path).rglob("*"):
                if item.is_dir() and ("bert" in item.name.lower() or "roberta" in item.name.lower()):
                    found_models.append(str(item))
                    print(f"📂 发现模型目录: {item.name}")

    return found_models

def main():
    """主函数"""
    print("🤖 BERT模型检查器")
    print("=" * 50)

    # 检查HuggingFace缓存
    hf_models = check_hf_cache()

    # 检查ModelScope缓存
    ms_models = check_modelscope_cache()

    # 检查本地路径
    local_models = check_local_bert()

    # 总结
    print("\n" + "=" * 50)
    print("📊 检查结果总结:")
    print(f"   - HuggingFace缓存模型: {len(hf_models)}")
    print(f"   - 本地发现模型: {len(local_models)}")

    if hf_models:
        print(f"\n✅ 可直接使用的HuggingFace模型:")
        for name, info in hf_models.items():
            status = "📄 有配置" if info["has_config"] else "⚠️ 无配置"
            print(f"   - {name}: {status}")

    if not hf_models and not local_models:
        print("\n⚠️ 未发现BERT模型")
        print("\n💡 建议:")
        print("1. 运行: pip install transformers torch")
        print("2. 下载模型:")
        print("   - hfl/chinese-roberta-wwm-ext-ext")
        print("   - THUDM/Lawformer")
        print("   - hfl/chinese-deberta-v3-base")

if __name__ == "__main__":
    main()