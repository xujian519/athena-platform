#!/bin/bash
# Athena平台重构完成后的清理和整理脚本
# Cleanup and Organization Script After Refactoring

echo "🧹 Athena平台清理和整理脚本"
echo "================================"
echo ""

# 1. 清理.DS_Store文件（macOS系统文件）
echo "📁 步骤 1/6: 清理.DS_Store文件"
ds_store_count=$(find . -name ".DS_Store" 2>/dev/null | wc -l | xargs)
echo "  发现 $ds_store_count 个.DS_Store文件"
if [ $ds_store_count -gt 0 ]; then
    find . -name ".DS_Store" -delete 2>/dev/null
    echo "  ✅ 已删除所有.DS_Store文件"
else
    echo "  ℹ️  没有发现.DS_Store文件"
fi
echo ""

# 2. 删除备份的测试文件
echo "📁 步骤 2/6: 删除备份的测试文件"
backup_files=(
    "tests/core/utils/test_error_handler.py.bak"
    "tests/core/utils/test_error_handling.py.bak"
)
deleted_count=0
for file in "${backup_files[@]}"; do
    if [ -f "$file" ]; then
        rm -f "$file"
        echo "  ✅ 已删除: $file"
        ((deleted_count++))
    fi
done
if [ $deleted_count -eq 0 ]; then
    echo "  ℹ️  没有发现备份测试文件"
fi
echo ""

# 3. 整理报告目录
echo "📁 步骤 3/6: 整理报告目录"
mkdir -p docs/reports/archive

# 保留的重要报告（最新）
keep_reports=(
    "ATHENA_REFACTORING_FINAL_SUMMARY_20260421.md"
    "ATHENA_REFACTORING_STAGE4_FINAL_REPORT_20260421.md"
    "STAGE4_SECURITY_AUDIT_REPORT_20260421.md"
    "STAGE4_TASK116_COMPLETION_REPORT.md"
    "ATHENA_ARCHITECTURE_V2.md"
)

# 归档历史报告
archived_count=0
for report in docs/reports/*.md; do
    if [ -f "$report" ]; then
        filename=$(basename "$report")
        # 检查是否需要保留
        keep=false
        for keep_report in "${keep_reports[@]}"; do
            if [[ "$filename" == *"$keep_report"* ]]; then
                keep=true
                break
            fi
        done

        # 如果不是保留报告，移动到归档
        if [ "$keep" = false ]; then
            mv "$report" "docs/reports/archive/"
            ((archived_count++))
        fi
    fi
done

echo "  ✅ 已归档 $archived_count 个历史报告"
echo "  📂 归档位置: docs/reports/archive/"
echo ""

# 4. 清理Python缓存（可选）
echo "📁 步骤 4/6: 清理Python缓存"
read -p "  是否清理Python缓存文件？这将清理__pycache__目录和.pyc文件 [y/N]: " clean_cache
if [[ "$clean_cache" =~ ^[Yy]$ ]]; then
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    echo "  ✅ 已清理Python缓存"
else
    echo "  ⏭️  跳过Python缓存清理"
fi
echo ""

# 5. 创建清理摘要报告
echo "📁 步骤 5/6: 生成清理摘要"
cat > docs/reports/CLEANUP_SUMMARY_$(date +%Y%m%d).md << 'EOF'
# 文件清理和整理摘要

> **清理日期**: $(date +%Y-%m-%d)
> **执行脚本**: cleanup_and_organize.sh

---

## 清理内容

### 1. 系统文件清理
- ✅ 删除所有.DS_Store文件（macOS系统文件）
- ✅ 数量: $ds_store_count 个

### 2. 备份文件清理
- ✅ 删除备份的测试文件
- ✅ 文件: test_error_handler.py.bak, test_error_handling.py.bak

### 3. 报告文件整理
- ✅ 归档历史报告到 docs/reports/archive/
- ✅ 保留最新报告在 docs/reports/

### 4. Python缓存清理
- $(date +%Y-%m-%d) 清理状态: ${clean_cache:-未执行}

---

## 保留的重要报告

- ATHENA_REFACTORING_FINAL_SUMMARY_20260421.md - 总体完成报告
- ATHENA_REFACTORING_STAGE4_FINAL_REPORT_20260421.md - Stage 4最终报告
- STAGE4_SECURITY_AUDIT_REPORT_20260421.md - 安全审计报告
- STAGE4_TASK116_COMPLETION_REPORT.md - 性能优化报告

---

## 归档位置

历史报告已归档到: `docs/reports/archive/`
EOF

echo "  ✅ 清理摘要已生成"
echo ""

# 6. 显示清理统计
echo "📊 步骤 6/6: 清理统计"
echo "  --------------------------------"
echo "  .DS_Store文件:    $ds_store_count 个已删除"
echo "  备份测试文件:     $deleted_count 个已删除"
echo "  历史报告:         $archived_count 个已归档"
echo "  --------------------------------"
echo ""

echo "✅ 清理和整理完成！"
echo ""
echo "📚 重要文档位置:"
echo "  - 总体报告: docs/reports/ATHENA_REFACTORING_FINAL_SUMMARY_20260421.md"
echo "  - Stage 4报告: docs/reports/ATHENA_REFACTORING_STAGE4_FINAL_REPORT_20260421.md"
echo "  - 安全审计: docs/reports/STAGE4_SECURITY_AUDIT_REPORT_20260421.md"
echo "  - 归档报告: docs/reports/archive/"
echo ""
echo "🎯 下一步建议:"
echo "  1. 提交git变更（删除废弃配置、新增文档）"
echo "  2. 创建完成里程碑标签（git tag）"
echo "  3. 更新CHANGELOG.md"
echo ""
