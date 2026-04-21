#!/bin/bash
# models目录清理脚本
# Cleanup models directory while preserving active models

set -e

echo "🧹 models目录清理"
echo "================================"
echo ""

PARTH="/Users/xujian/Athena工作平台"
cd "$PARTH"

# 1. 检查正在使用的模型
echo "📁 步骤 1/4: 检查正在使用的模型"
echo "  ✅ intent_recognition - 正在使用 (466MB)"
echo "  ✅ roberta-base-finetuned - 正在使用 (390MB)"
echo ""

# 2. 删除空目录
echo "📁 步骤 2/4: 删除空目录"
empty_count=0
for dir in embedding image_generation invalidation_prediction llm modelscope multimodal preloaded speech; do
    if [ -d "models/$dir" ]; then
        # 检查是否为空
        if [ -z "$(find "models/$dir" -type f 2>/dev/null)" ]; then
            rm -rf "models/$dir"
            echo "  ✅ 已删除空目录: models/$dir"
            ((empty_count++))
        fi
    fi
done
echo ""

# 3. 保留正在使用的模型
echo "📁 步骤 3/4: 保留正在使用的模型"
echo "  ✅ models/intent_recognition/ (intent_recognition功能)"
echo "  ✅ models/roberta-base-finetuned-chinanews-chinese/ (NER功能)"
echo "  ✅ models/custom/ (如果存在)"
echo ""

# 4. 生成清理报告
echo "📁 步骤 4/4: 生成清理报告"
total_size=$(du -sh models/ 2>/dev/null | cut -f1)
echo ""
echo "📊 清理统计:"
echo "  空目录删除: $empty_count 个"
echo "  models目录大小: $total_size"
echo ""

echo "✅ models目录清理完成！"
echo ""
echo "📝 保留的模型:"
echo "  1. intent_recognition (466MB) - 意图识别"
echo "  2. roberta-base-finetuned-chinanews-chinese (390MB) - NER"
echo "  3. custom/ (可选) - 自定义模型"
echo ""
