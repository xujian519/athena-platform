#!/usr/bin/env python3
"""
修复BGE-M3硬编码路径脚本
Fix hardcoded BGE-M3 paths to use API service URL

作者: Claude Code
日期: 2026-04-21
"""

import re
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path("/Users/xujian/Athena工作平台")

# 硬编码路径（需要修复）
HARDCODED_PATH = "/Users/xujian/Athena工作平台/models/converted/BAAI/bge-m3"

# 新的API服务URL
BGE_M3_API_URL = "http://127.0.0.1:8766/v1/embeddings"
BGE_M3_SERVICE_URL = "http://127.0.0.1:8766"

# 需要修复的文件
FILES_TO_FIX = [
    "core/fusion/vector_graph_fusion_service.py",
    "core/legal_kg/triple_store_liaison_docker.py",
    "core/legal_kg/triple_store_liaison.py",
    "core/legal_kg/legal_vectorizer.py",
    "core/storm_integration/local_embedding_integration.py",
    "core/storm_integration/optimized_database_connectors.py",
    "core/memory/unified_memory/utils.py",
    "core/memory/unified_family_memory.py",
    "core/memory/family_memory_pg.py",
    "core/embedding/bge_m3_embedder.py",
    "core/embedding/memory_leak_fix.py",
    "core/tokenization/bge_tokenizer.py",
    "core/reasoning/semantic_reasoning_engine.py",
    "core/intent/bge_m3_intent_classifier.py",
    "core/intent/local_bge_phase2_classifier.py",
    "core/intent/local_bge_intent_classifier.py",
    "core/intent/patent_enhanced_intent_classifier.py",
    "core/intent/local_bge_phase3_legal_classifier.py",
    "core/nlp/bge_m3_loader.py",
    "core/nlp/bert_semantic_intent_classifier.py",
]

# 不需要修复的文件（使用远程模型名称）
SKIP_FILES = [
    # 这些文件可能使用 "BAAI/bge-m3" 作为模型名称（HuggingFace）
    # 不需要修改
]

def fix_file(file_path: Path) -> int:
    """修复单个文件中的硬编码路径"""
    if not file_path.exists():
        print(f"  ⚠️  文件不存在: {file_path}")
        return 0

    try:
        content = file_path.read_text(encoding='utf-8')
        original_content = content

        # 检查是否包含硬编码路径
        if HARDCODED_PATH not in content:
            return 0

        # 替换策略
        # 1. 如果是model_path变量赋值，替换为API URL
        # 2. 如果是注释，添加说明
        # 3. 如果是字符串，替换为API URL

        # 替换各种模式
        patterns = [
            # 模式1: 直接的完整路径字符串
            (re.escape(HARDCODED_PATH), BGE_M3_API_URL),

            # 模式2: project_root / "models/converted/BAAI/bge-m3" (相对路径构造)
            (r'project_root\s*/\s*["\']models/converted/BAAI/bge-m3["\']',
             '"' + BGE_M3_API_URL + '"'),

            # 模式3: PROJECT_ROOT / "models/converted/BAAI/bge-m3" (相对路径构造)
            (r'PROJECT_ROOT\s*/\s*["\']models/converted/BAAI/bge-m3["\']',
             '"' + BGE_M3_API_URL + '"'),

            # 模式4: model_path = "...bge-m3"
            (r'(\s*model_path\s*=\s*)["\'][^"\']*bge-m3[^"\']*["\']',
             r'\1"' + BGE_M3_API_URL + '"'),

            # 模式5: "path": "...bge-m3"
            (r'(\s*"path"\s*:\s*)["\'][^"\']*bge-m3[^"\']*["\']',
             r'\1"' + BGE_M3_API_URL + '"'),

            # 模式6: bge_model_path = "...bge-m3"
            (r'(\s*bge_model_path\s*=\s*)["\'][^"\']*bge-m3[^"\']*["\']',
             r'\1"' + BGE_M3_API_URL + '"'),
        ]

        changes = 0
        for pattern, replacement in patterns:
            new_content, count = re.subn(pattern, replacement, content)
            if count > 0:
                content = new_content
                changes += count

        # 如果有更改，写回文件
        if changes > 0 and content != original_content:
            file_path.write_text(content, encoding='utf-8')
            print(f"  ✅ {file_path.relative_to(PROJECT_ROOT)}: {changes} 处修改")
            return changes

        return 0

    except Exception as e:
        print(f"  ❌ {file_path.relative_to(PROJECT_ROOT)}: 错误 - {e}")
        return 0

def main():
    """主函数"""
    print("🔧 修复BGE-M3硬编码路径")
    print("=" * 60)
    print("")
    print("📋 修复方案:")
    print(f"  硬编码路径: {HARDCODED_PATH}")
    print(f"  替换为API: {BGE_M3_API_URL}")
    print("")

    total_changes = 0
    fixed_files = 0

    print("🔍 扫描并修复文件:")
    for file_path_str in FILES_TO_FIX:
        file_path = PROJECT_ROOT / file_path_str
        changes = fix_file(file_path)
        if changes > 0:
            fixed_files += 1
            total_changes += changes

    print("")
    print("📊 修复统计:")
    print(f"  修复文件数: {fixed_files}")
    print(f"  总修改数: {total_changes}")
    print("")

    if total_changes > 0:
        print("✅ 硬编码路径修复完成！")
        print("")
        print("📝 后续步骤:")
        print("  1. 测试embedding功能是否正常")
        print("  2. 确认BGE-M3 API服务运行在8766端口")
        print("  3. 提交修复后的代码")
    else:
        print("ℹ️  未发现需要修复的硬编码路径")

if __name__ == "__main__":
    main()
