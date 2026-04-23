#!/usr/bin/env bash
#
# Prompt System 主链路 API 基线压测一键执行脚本
#
# 用法:
#   ./scripts/run_load_test.sh [HOST] [USERS] [DURATION]
#
# 参数:
#   HOST     -- 目标服务地址（默认: http://localhost:8000）
#   USERS    -- 并发用户数（默认: 10）
#   DURATION -- 压测持续时间（默认: 5m）
#
# 示例:
#   ./scripts/run_load_test.sh http://localhost:8000 50 10m
#   ./scripts/run_load_test.sh https://api.athena.example.com 100 15m

set -euo pipefail

# ---------------------------------------------------------------------------
# 参数解析
# ---------------------------------------------------------------------------
HOST="${1:-http://localhost:8000}"
USERS="${2:-10}"
DURATION="${3:-5m}"

# ---------------------------------------------------------------------------
# 常量
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPORT_DIR="${PROJECT_ROOT}/reports/load"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPORT_PREFIX="locust_report_${TIMESTAMP}_u${USERS}_d${DURATION}"

# Locust 参数
LOCUSTFILE="${PROJECT_ROOT}/tests/load/locustfile.py"
CSV_PREFIX="${REPORT_DIR}/${REPORT_PREFIX}"
HTML_REPORT="${REPORT_DIR}/${REPORT_PREFIX}.html"

# ---------------------------------------------------------------------------
# 前置检查
# ---------------------------------------------------------------------------
echo "======================================================================"
echo "  Athena Prompt System — 主链路 API 性能基线压测"
echo "======================================================================"
echo "  目标地址 : ${HOST}"
echo "  并发用户 : ${USERS}"
echo "  持续时间 : ${DURATION}"
echo "  报告目录 : ${REPORT_DIR}"
echo "======================================================================"

# 检查 locust 是否安装
if ! command -v locust &>/dev/null; then
    echo "[ERROR] locust 未安装，请先安装: pip install locust"
    exit 1
fi

# 检查 locustfile 是否存在
if [[ ! -f "${LOCUSTFILE}" ]]; then
    echo "[ERROR] locustfile 不存在: ${LOCUSTFILE}"
    exit 1
fi

# 检查 payloads 目录
if [[ ! -d "${PROJECT_ROOT}/tests/load/payloads" ]]; then
    echo "[ERROR] 压测数据集不存在: ${PROJECT_ROOT}/tests/load/payloads"
    exit 1
fi

# 创建报告目录
mkdir -p "${REPORT_DIR}"

# ---------------------------------------------------------------------------
# 执行压测（headless 模式）
# ---------------------------------------------------------------------------
echo "[INFO] 压测启动中..."

locust -f "${LOCUSTFILE}" \
    --host "${HOST}" \
    --users "${USERS}" \
    --spawn-rate "$(echo "${USERS} / 5" | bc | awk '{print int($1+0.5)}')" \
    --run-time "${DURATION}" \
    --headless \
    --csv "${CSV_PREFIX}" \
    --html "${HTML_REPORT}" \
    --print-stats \
    --only-summary

# ---------------------------------------------------------------------------
# 结果输出
# ---------------------------------------------------------------------------
echo ""
echo "======================================================================"
echo "  压测完成"
echo "======================================================================"
echo "  CSV 统计 : ${CSV_PREFIX}_stats.csv"
echo "  失败明细 : ${CSV_PREFIX}_failures.csv"
echo "  历史记录 : ${CSV_PREFIX}_stats_history.csv"
echo "  HTML 报告: ${HTML_REPORT}"
echo "======================================================================"
