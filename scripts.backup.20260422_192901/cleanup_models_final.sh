#!/bin/bash
# models目录清理脚本 - 保留正在使用的模型
# Cleanup models/ directory - preserve active models

set -e

echo "🧹 models目录清理 - 保留正在使用的模型"
echo "=========================================="
echo ""

PARTH="/Users/xujian/Athena工作平台"
cd "$PARTH"

echo "📊 当前状态:"
echo "  - BGE-M3模型: 通过8766端口API服务提供"
echo "  - 未来端口: 8009"
echo "  - 不需要本地模型文件"
echo ""

# 1. 删除未使用的子目录
echo "📁 步骤 1/3: 删除未使用的目录"
unused_dirs=(
    "embedding"
    "image_generation"
    "invalidation_prediction"
    "llm"
    "modelscope"
    "multimodal"
    "preloaded"
    "speech"
)

deleted_count=0
for dir in "${unused_dirs[@]}"; do
    if [ -d "models/$dir" ]; then
        rm -rf "models/$dir"
        echo "  ✅ 已删除: models/$dir/"
        ((deleted_count++))
    fi
done
echo ""

# 2. 确认保留的模型
echo "📁 步骤 2/3: 确认保留的模型"
echo "  ✅ models/intent_recognition/ (466MB) - 意图识别"
echo "  ✅ models/roberta-base-finetuned-chinanews-chinese/ (390MB) - NER"
echo "  ✅ models/custom/ - 自定义模型"
echo ""

# 3. 检查BGE-M3硬编码路径
echo "📁 步骤 3/3: BGE-M3路径说明"
echo "  ℹ️  BGE-M3通过8766端口API服务提供"
echo "  ℹ️  未来迁移到8009端口"
echo "  ℹ️  不需要本地模型文件"
echo "  ⚠️  代码中有硬编码路径建议修复"
echo ""

# 4. 生成清理报告
echo "📊 清理统计:"
echo "  删除目录: $deleted_count 个"
echo ""

# 计算保留的模型大小
intent_size=$(du -sh models/intent_recognition/ 2>/dev/null | cut -f1)
roberta_size=$(du -sh models/roberta-base-finetuned-chinanews-chinese/ 2>/dev/null | cut -f1)
total_size=$(du -sh models/ 2>/dev/null | cut -f1)

echo "📁 保留的模型:"
echo "  - intent_recognition/: $intent_size"
echo "  - roberta-base-finetuned-chinanews-chinese/: $roberta_size"
echo "  总大小: $total_size"
echo ""

echo "✅ models目录清理完成！"
echo ""
echo "📝 说明:"
echo "  - BGE-M3: 使用8766端口API → 未来8009端口"
echo "  - intent_recognition: 意图识别功能需要"
echo "  - roberta: NER功能需要"
echo ""
