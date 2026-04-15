#!/usr/bin/env python3
"""
Qwen 2.5 模型加载调试脚本
"""

from __future__ import annotations
from pathlib import Path

print("=" * 80)
print("🔍 Qwen 2.5 模型加载调试")
print("=" * 80)

# 模型路径
model_dir = Path("/Users/xujian/Athena工作平台/models/converted/._____temp/Qwen/Qwen2.5-7B-Instruct-GGUF")

# 查找所有GGUF文件
gguf_files = list(model_dir.glob("*.gguf"))
print(f"\n📦 发现 {len(gguf_files)} 个GGUF文件:")

# 分类文件
single_files = []
split_files = {}

for f in gguf_files:
    if "of-" in f.name:
        # 分片文件
        parts = f.name.split("-of-")
        if len(parts) == 2:
            key = parts[1].replace(".gguf", "")
            if key not in split_files:
                split_files[key] = []
            split_files[key].append(f)
    else:
        single_files.append(f)

print(f"\n✅ 完整单文件模型 ({len(single_files)}):")
for f in sorted(single_files, key=lambda x: x.stat().st_size):
    size_gb = f.stat().st_size / (1024**3)
    print(f"  - {f.name} ({size_gb:.2f} GB)")

print(f"\n📦 分片模型 ({len(split_files)} 组):")
for key, files in split_files.items():
    total_size = sum(f.stat().st_size for f in files) / (1024**3)
    print(f"  - {key}: {len(files)} 个文件, 总大小 {total_size:.2f} GB")

# 选择最佳文件（优先使用最小的量化版本）
if single_files:
    # 按优先级排序：q2_k > q3_k > q4 > q5 > q6 > q8 > fp16
    priority = {"q2_k": 1, "q3_k": 2, "q4": 3, "q5": 4, "q6": 5, "q8": 6, "fp16": 7}

    def get_priority(filename) -> None:
        for key, p in priority.items():
            if key in filename:
                return p
        return 999

    best_file = min(single_files, key=lambda x: (get_priority(x.name), x.stat().st_size))
    print(f"\n🎯 推荐使用: {best_file.name}")
    print(f"   大小: {best_file.stat().st_size / (1024**3):.2f} GB")

    # 测试加载
    print("\n🔄 测试加载模型...")
    try:
        from llama_cpp import Llama

        print(f"   模型路径: {best_file}")
        print("   参数: n_ctx=2048, n_threads=4, n_gpu_layers=0")

        model = Llama(
            model_path=str(best_file),
            n_ctx=2048,  # 减小上下文以节省内存
            n_threads=4,
            n_gpu_layers=0,  # 先不用GPU
            verbose=True
        )

        print("\n✅ 模型加载成功!")

        # 测试生成
        print("\n🔄 测试文本生成...")
        response = model(
            "Hello, how are you?",
            max_tokens=50,
            stop=["\n"],
            echo=False
        )
        print("✅ 生成测试成功!")
        print(f"   响应: {response['choices'][0]['text'][:100]}")

    except Exception as e:
        print("\n❌ 模型加载失败!")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {e}")

        import traceback
        print("\n详细堆栈:")
        traceback.print_exc()

else:
    print("\n⚠️ 没有找到完整的单文件模型")
    print("   需要下载完整的GGUF文件")
