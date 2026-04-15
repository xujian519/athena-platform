#!/bin/bash
# =============================================================================
# 专利检索基础示例
# =============================================================================

# 数据库连接配置
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-patent_db}"
DB_USER="${DB_USER:-postgres}"

# 连接命令
PSQL="psql -h ${DB_HOST} -p ${DB_PORT} -U ${DB_USER} -d ${DB_NAME}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📚 专利检索基础示例"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 示例1: 关键词检索
echo "🔍 示例1: 关键词检索 - '人工智能'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PSQL -c "
SELECT patent_name, applicant, ipc_main_class
FROM patents
WHERE patent_name ILIKE '%人工智能%'
LIMIT 5;
"
echo ""
read -p "按回车继续..."
echo ""

# 示例2: IPC分类检索
echo "🔍 示例2: IPC分类检索 - 'G06F' (电数字数据处理)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PSQL -c "
SELECT patent_name, ipc_main_class, applicant
FROM patents
WHERE ipc_main_class LIKE 'G06F%'
LIMIT 5;
"
echo ""
read -p "按回车继续..."
echo ""

# 示例3: 申请人检索
echo "🔍 示例3: 申请人检索 - '华为'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PSQL -c "
SELECT patent_name, application_number, application_date
FROM patents
WHERE applicant ILIKE '%华为%'
ORDER BY application_date DESC
LIMIT 5;
"
echo ""
read -p "按回车继续..."
echo ""

# 示例4: 组合条件检索
echo "🔍 示例4: 组合条件检索 - IPC分类 + 关键词"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PSQL -c "
SELECT patent_name, ipc_main_class, applicant
FROM patents
WHERE ipc_main_class LIKE 'A61K%'
  AND patent_name ILIKE '%注射%'
LIMIT 5;
"
echo ""
read -p "按回车继续..."
echo ""

# 示例5: 统计分析
echo "📊 示例5: 统计分析 - 按年份统计"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
$PSQL -c "
SELECT source_year, COUNT(*) as patent_count
FROM patents
WHERE source_year >= 2020
GROUP BY source_year
ORDER BY source_year DESC;
"
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 示例演示完成！"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 提示:"
echo "  • 修改查询条件来检索不同的专利"
echo "  • 参考 SKILL.md 了解更多检索方式"
echo "  • 使用 patent_search_cli.py 进行Python脚本检索"
echo ""
