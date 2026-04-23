#!/bin/bash
# DSPy训练启动脚本
# 作者: 小娜·天秤女神
# 创建时间: 2025-12-30

set -e  # 遇到错误立即退出

# 配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
PYTHON="$(which python3)"  # 自动检测python3路径
TRAINING_SCRIPT="${PROJECT_ROOT}/core/intelligence/dspy/training_system_v2.py"
LOG_DIR="${PROJECT_ROOT}/logs/dspy_training"

# 创建日志目录
mkdir -p "${LOG_DIR}"

# 加载项目环境变量
if [ -f "${PROJECT_ROOT}/config/env/.env.production" ]; then
    echo "加载生产环境配置..."
    set -a  # 自动导出所有变量
    source "${PROJECT_ROOT}/config/env/.env.production"
    set +a

    # 设置DSPy需要的环境变量
    export ZHIPUAI_API_KEY="${GLM_API_KEY}"

    echo "✓ API密钥已加载"
else
    echo "警告: 未找到环境配置文件"
fi

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 显示帮助信息
show_help() {
    cat << EOF
DSPy专利案例分析训练脚本

用法: $0 [选项] [模式]

模式:
  test               运行测试模式（默认）
  train-mipro        运行MIPROv2分批训练
  resume             从检查点恢复训练

选项:
  -m, --model MODEL  使用的模型 (glm-4-plus, glm-4.7, deepseek-chat) [默认: glm-4-plus]
  -t, --trials N     优化试验次数 [默认: 30]
  -r, --rounds N     最大优化轮数 [默认: 3]
  -b, --batch N      批次大小 [默认: 50]
  -s, --max-samples N  最大训练样本数，0表示使用全部数据 [默认: 100]
  -c, --checkpoint PATH  从指定检查点恢复
  -h, --help         显示此帮助信息

示例:
  # 快速训练测试（100个样本）
  $0 train-mipro -s 100

  # 完整训练（使用全部数据）
  $0 train-mipro -s 0

  # 使用较小批次训练（适合内存受限环境）
  $0 train-mipro -s 100 -b 20 -t 20

  # 使用DeepSeek模型训练
  $0 train-mipro -s 100 -m deepseek-chat

  # 从检查点恢复训练
  $0 resume -c /path/to/checkpoint.pkl

EOF
}

# 解析命令行参数
MODE="test"
MODEL="glm-4-plus"
TRIALS=30
ROUNDS=3
BATCH_SIZE=50
MAX_SAMPLES=100  # 默认使用100个样本快速测试
CHECKPOINT=""

while [[ $# -gt 0 ]]; do
    case $1 in
        test|train-mipro|resume)
            MODE="$1"
            shift
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -t|--trials)
            TRIALS="$2"
            shift 2
            ;;
        -r|--rounds)
            ROUNDS="$2"
            shift 2
            ;;
        -b|--batch)
            BATCH_SIZE="$2"
            shift 2
            ;;
        -s|--max-samples)
            MAX_SAMPLES="$2"
            shift 2
            ;;
        -c|--checkpoint)
            CHECKPOINT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            print_error "未知参数: $1"
            show_help
            exit 1
            ;;
    esac
done

# 检查Python环境
if [ ! -f "${PYTHON}" ]; then
    print_error "未找到Python环境: ${PYTHON}"
    exit 1
fi

# 检查训练脚本
if [ ! -f "${TRAINING_SCRIPT}" ]; then
    print_error "未找到训练脚本: ${TRAINING_SCRIPT}"
    exit 1
fi

# 显示配置信息
print_info "DSPy训练启动脚本"
echo "=========================================="
echo "模式:       ${MODE}"
echo "模型:       ${MODEL}"
echo "试验次数:   ${TRIALS}"
echo "优化轮数:   ${ROUNDS}"
echo "批次大小:   ${BATCH_SIZE}"
echo "最大样本数: ${MAX_SAMPLES} (0=全部)"
if [ -n "${CHECKPOINT}" ]; then
    echo "检查点:     ${CHECKPOINT}"
fi
echo "=========================================="

# 构建命令
CMD="${PYTHON} ${TRAINING_SCRIPT} --mode ${MODE} --model ${MODEL} --trials ${TRIALS} --rounds ${ROUNDS} --batch-size ${BATCH_SIZE} --max-samples ${MAX_SAMPLES}"

if [ -n "${CHECKPOINT}" ]; then
    CMD="${CMD} --resume-checkpoint ${CHECKPOINT}"
fi

# 生成日志文件名
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
LOG_FILE="${LOG_DIR}/training_${MODE}_${TIMESTAMP}.log"

print_info "日志文件: ${LOG_FILE}"
echo ""
print_info "开始训练..."
echo ""

# 执行训练并记录日志
${CMD} 2>&1 | tee "${LOG_FILE}"

# 检查执行结果
if [ ${PIPESTATUS[0]} -eq 0 ]; then
    echo ""
    print_info "训练完成! ✓"
    print_info "日志已保存到: ${LOG_FILE}"
    exit 0
else
    echo ""
    print_error "训练失败! ✗"
    print_error "请查看日志文件: ${LOG_FILE}"
    exit 1
fi
