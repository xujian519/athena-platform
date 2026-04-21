#!/bin/bash
# Athena平台根目录整理脚本
# Root Directory Organization Script

set -e

echo "🗂️  Athena平台根目录整理"
echo "================================"
echo ""

# 创建归档目录
mkdir -p docs/archive/phase_reports
mkdir -p scripts/standalone
mkdir -p build/coverage

# 1. 整理历史报告
echo "📁 步骤 1/6: 整理历史报告文件"
phase_reports=(
    "PHASE1_DAY1_2_CHECKLIST.md"
    "PHASE1_DAY3_SUMMARY.md"
    "PHASE1_DAY4_5_SUMMARY.md"
    "PHASE1_DAY6_SUMMARY.md"
    "PHASE1_DAY7_SUMMARY.md"
    "PHASE1_FINAL_REPORT.md"
    "PHASE1_VERIFICATION_REPORT.md"
    "PHASE2_WEEK1_PLAN.md"
    "PHASE2_WEEK1_PROGRESS.md"
)

moved_count=0
for report in "${phase_reports[@]}"; do
    if [ -f "$report" ]; then
        mv "$report" "docs/archive/phase_reports/"
        ((moved_count++))
    fi
done
echo "  ✅ 已移动 $moved_count 个历史阶段报告"

# 2. 整理其他报告文档
echo "📁 步骤 2/6: 整理其他报告文档"
other_reports=(
    "PROJECT_COMPLETE.md"
    "PROJECT_CLEANUP_REPORT_20260419.md"
    "REPORT_CLEANUP_SUMMARY_20260419.md"
    "PATENT_WEBUI_BACKUP_COMPLETE_20260419.md"
    "MIGRATION_REPORT_20260420.md"
    "DOCKER_COMPOSE_MERGE_REPORT.md"
    "DOCKER_COMPOSE_MIGRATION_GUIDE.md"
    "DOCKER_COMPOSE_QUICK_REFERENCE.md"
    "TEAM_NOTIFICATION_DOCKER_COMPOSE_MIGRATION.md"
    "QUICK_START_MONITORING.md"
    "Athena_项目现状扫描报告_20260421.md"
    "cleanup_log_20260420.md"
    "架构.md"
)

for report in "${other_reports[@]}"; do
    if [ -f "$report" ]; then
        mv "$report" "docs/reports/archive/"
        ((moved_count++))
    fi
done
echo "  ✅ 已移动 $((${moved_count} - ${moved_count:-0})) 个其他报告"

# 3. 整理独立Python脚本
echo "📁 步骤 3/6: 整理独立Python脚本"
standalone_scripts=(
    "enhanced_patent_search.py"
    "google_patents_retriever_v2.py"
    "simple_patent_search.py"
    "google_patents_simple.py"
    "athena_simplified_api.py"
    "test_infringement_determiner.py"
    "advanced_patent_search.py"
)

script_count=0
for script in "${standalone_scripts[@]}"; do
    if [ -f "$script" ]; then
        mv "$script" "scripts/standalone/"
        ((script_count++))
    fi
done
echo "  ✅ 已移动 $script_count 个独立脚本"

# 4. 整理日志和覆盖率文件
echo "📁 步骤 4/6: 整理临时文件"
temp_files=(
    "ai_reasoning_engine.log"
    "cleanup_log_20260420_230841.log"
    "coverage.json"
    "coverage_day2.json"
)

temp_count=0
for file in "${temp_files[@]}"; do
    if [ -f "$file" ]; then
        if [[ "$file" == coverage* ]]; then
            mv "$file" "build/coverage/"
        else
            mv "$file" "logs/"
        fi
        ((temp_count++))
    fi
done
echo "  ✅ 已移动 $temp_count 个临时文件"

# 5. 保留在根目录的重要文件
echo "📁 步骤 5/6: 确认保留文件"
keep_files=(
    "README.md"
    "QUICK_START.md"
    "CLAUDE.md"
    "Athena_渐进式重构计划_20260421.md"
    "start_xiaona.py"
    "package.json"
    "package-lock.json"
    "pyrightconfig.json"
)

echo "  ✅ 保留以下重要文件在根目录:"
for file in "${keep_files[@]}"; do
    if [ -f "$file" ]; then
        echo "     - $file"
    fi
done

# 6. 更新.gitignore
echo "📁 步骤 6/6: 更新.gitignore"
cat >> .gitignore << 'EOF'

# Root directory organization (added 2026-04-21)
*.log
coverage*.json
build/
scripts/standalone/*.py
!start_xiaona.py
docs/archive/phase_reports/
EOF

echo "  ✅ 已更新.gitignore"

echo ""
echo "✅ 根目录整理完成！"
echo ""
echo "📊 整理统计:"
echo "  历史报告: $moved_count 个已归档"
echo "  独立脚本: $script_count 个已整理"
echo "  临时文件: $temp_count 个已移动"
echo ""
echo "📁 新的目录结构:"
echo "  docs/archive/phase_reports/  - 历史阶段报告"
echo "  docs/reports/archive/        - 其他历史报告"
echo "  scripts/standalone/          - 独立Python脚本"
echo "  build/coverage/              - 覆盖率报告"
echo "  logs/                        - 日志文件"
echo ""
echo "📝 保留在根目录的重要文件:"
echo "  - README.md, QUICK_START.md, CLAUDE.md"
echo "  - Athena_渐进式重构计划_20260421.md"
echo "  - start_xiaona.py (启动脚本)"
echo "  - package.json, pyrightconfig.json"
echo ""
