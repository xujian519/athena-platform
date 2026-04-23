#!/bin/bash
# 清理空文件夹和整理docs/reports目录
# Cleanup Empty Directories and Organize docs/reports

set -e

echo "🧹 Athena平台空文件夹清理和文档整理"
echo "================================"
echo ""

PARTH="/Users/xujian/Athena工作平台"
cd "$PARTH"

# 1. 删除空文件夹
echo "📁 步骤 1/5: 删除空文件夹"
empty_count=0

# 使用find删除空文件夹，递归处理直到没有空文件夹
while true; do
    empty_dirs=$(find . -type d -empty ! -path "*/.*" ! -path "./.git/*" 2>/dev/null)
    if [ -z "$empty_dirs" ]; then
        break
    fi

    while IFS= read -r dir; do
        if [ -d "$dir" ]; then
            rmdir "$dir" 2>/dev/null && ((empty_count++)) || true
        fi
    done <<< "$empty_dirs"
done

echo "  ✅ 已删除 $empty_count 个空文件夹"
echo ""

# 2. 整理docs目录结构
echo "📁 步骤 2/5: 整理docs目录结构"

# 移除编号前缀的目录（如01-architecture, 02-references等）
if [ -d "docs/01-architecture" ]; then
    mv docs/01-architecture/* docs/architecture/ 2>/dev/null || true
    rmdir docs/01-architecture 2>/dev/null || true
fi

if [ -d "docs/02-references" ]; then
    mv docs/02-references/* docs/reference/ 2>/dev/null || true
    rmdir docs/02-references 2>/dev/null || true
fi

if [ -d "docs/03-reports" ]; then
    mv docs/03-reports/* docs/reports/ 2>/dev/null || true
    rmdir docs/03-reports 2>/dev/null || true
fi

if [ -d "docs/04-deployment" ]; then
    mv docs/04-deployment/* docs/deployment/ 2>/dev/null || true
    rmdir docs/04-deployment 2>/dev/null || true
fi

if [ -d "docs/07-projects" ]; then
    mv docs/07-projects/* docs/projects/ 2>/dev/null || true
    rmdir docs/07-projects 2>/dev/null || true
fi

echo "  ✅ 已移除编号前缀目录"
echo ""

# 3. 清理docs/reports目录
echo "📁 步骤 3/5: 清理docs/reports目录"

# 删除嵌套的reports目录
if [ -d "docs/reports/reports" ]; then
    mv docs/reports/reports/* docs/reports/archive/ 2>/dev/null || true
    rm -rf docs/reports/reports
    echo "  ✅ 已删除嵌套的reports目录"
fi

# 移动JSON验证文件到archive
json_files=(
    "code_statistics_report.json"
    "COMPREHENSIVE_VERIFICATION_REPORT_20260421.json"
    "DOCUMENT_PARSER_VERIFICATION_RESULT.json"
    "file_operator_verification.json"
)

for json_file in "${json_files[@]}"; do
    if [ -f "docs/reports/$json_file" ]; then
        mv "docs/reports/$json_file" "docs/reports/archive/"
        echo "  ✅ 已归档: $json_file"
    fi
done

# 移动task-tool-system相关目录到archive
for dir in task-tool-system-* tool-registry-migration; do
    if [ -d "docs/reports/$dir" ]; then
        mv "docs/reports/$dir" "docs/reports/archive/"
        echo "  ✅ 已归档目录: $dir"
    fi
done

echo ""

# 4. 优化docs目录结构
echo "📁 步骤 4/5: 优化docs目录结构"

# 创建新的结构
mkdir -p docs/archive

# 移动不常用的目录到archive
archive_dirs=(
    "development-logs"
    "test_reports"
    "prompts-archive"
    "共读书籍"
)

for dir in "${archive_dirs[@]}"; do
    if [ -d "docs/$dir" ]; then
        mv "docs/$dir" "docs/archive/"
        echo "  ✅ 已归档: docs/$dir"
    fi
done

# 合并重复目录
if [ -d "docs/reference" ] && [ -d "docs/references" ]; then
    mv docs/references/* docs/reference/ 2>/dev/null || true
    rmdir docs/references 2>/dev/null || true
    echo "  ✅ 已合并 reference 和 references"
fi

if [ -d "docs/development_plans" ]; then
    mv docs/development_plans/* docs/plans/ 2>/dev/null || true
    rmdir docs/development_plans 2>/dev/null || true
    echo "  ✅ 已合并 development_plans 到 plans"
fi

echo ""

# 5. 最终统计
echo "📁 步骤 5/5: 生成整理统计"
echo ""
echo "📊 整理统计:"
echo "  空文件夹删除: $empty_count 个"
echo "  docs目录优化: 完成"
echo "  reports目录优化: 完成"
echo ""

# 显示docs目录结构
echo "📂 docs目录结构（优化后）:"
ls -1 docs/ | head -20
echo ""

# 显示reports目录内容
echo "📂 docs/reports目录（优化后）:"
ls -1 docs/reports/*.md 2>/dev/null | xargs -n1 basename
echo ""

echo "✅ 空文件夹清理和文档整理完成！"
echo ""
echo "📝 主要改进:"
echo "  - 删除 $empty_count 个空文件夹"
echo "  - 移除编号前缀目录"
echo "  - 清理嵌套的reports目录"
echo "  - 归档不常用文档"
echo "  - 合并重复目录"
echo ""
