#!/bin/bash

# Apple Silicon M4 环境设置脚本
# 安装和配置M4芯片专用的AI优化库

echo "🍎 Apple Silicon M4 AI优化环境设置"
echo "=================================="

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查M4芯片
check_m4_chip() {
    log_info "检查Apple Silicon芯片..."

    CHIP_INFO=$(sysctl -n machdep.cpu.brand_string)
    if [[ $CHIP_INFO == *"M4"* ]]; then
        log_info "✅ 检测到M4芯片: $CHIP_INFO"
        return 0
    else
        log_warn "未检测到M4芯片，当前芯片: $CHIP_INFO"
        return 1
    fi
}

# 安装Homebrew（如果未安装）
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        log_info "安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    else
        log_info "Homebrew已安装"
    fi
}

# 安装Python依赖
install_python_deps() {
    log_info "安装Python依赖..."

    # 更新pip
    python3 -m pip install --upgrade pip

    # 安装PyTorch（MPS版本）
    log_info "安装PyTorch MPS版本..."
    pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

    # 安装MLX（Apple Silicon专用）
    log_info "安装MLX框架..."
    if command -v mlx &> /dev/null; then
        log_info "MLX已安装"
    else
        log_info "从源码安装MLX..."
        # 创建临时目录
        TEMP_DIR=$(mktemp -d)
        cd $TEMP_DIR

        # 克隆MLX
        git clone https://github.com/ml-explore/mlx.git
        cd mlx

        # 安装MLX
        pip3 install -e .

        # 清理
        cd /
        rm -rf $TEMP_DIR
    fi

    # 安装Apple ML相关库
    log_info "安装Core ML工具..."
    pip3 install coremltools

    # 安装其他优化库
    log_info "安装其他优化库..."
    pip3 install \
        accelerate \
        bitsandbytes \
        optimum \
        transformers \
        onnx \
        onnxruntime \
        huggingface_hub

    # 安装性能监控工具
    pip3 install psutil gpustat
}

# 安装Xcode命令行工具
install_xcode_tools() {
    if ! xcode-select -p &> /dev/null; then
        log_info "安装Xcode命令行工具..."
        xcode-select --install
    else
        log_info "Xcode命令行工具已安装"
    fi
}

# 配置环境变量
setup_environment() {
    log_info "配置环境变量..."

    # 添加到.zshrc或.bash_profile
    SHELL_RC=""
    if [[ $SHELL == *"zsh"* ]]; then
        SHELL_RC="$HOME/.zshrc"
    else
        SHELL_RC="$HOME/.bash_profile"
    fi

    # 备份原文件
    if [ -f "$SHELL_RC" ]; then
        cp "$SHELL_RC" "$SHELL_RC.backup"
    fi

    # 添加Apple Silicon优化配置
    cat >> "$SHELL_RC" << 'EOF'

# Apple Silicon M4 AI优化配置
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
export PYTORCH_ENABLE_MPS_FALLBACK=1
export PYTORCH_MPS_ALLOW_HIGH_PRECISION_SUM=1

# Core ML配置
export CORE_ML_DEBUG=0
export CORE_ML_QUANTIZATION=1

# 内存优化
export OMP_NUM_THREADS=1
export MKL_NUM_THREADS=1

# 性能配置
export ACCELERATE=1
export VECLIB_MAXIMUM_LENGTH=2048

EOF

    log_info "环境变量已添加到 $SHELL_RC"
}

# 验证安装
verify_installation() {
    log_info "验证安装..."

    # 检查Python版本
    PYTHON_VERSION=$(python3 --version)
    log_info "Python版本: $PYTHON_VERSION"

    # 检查PyTorch
    if python3 -c "import torch; print('PyTorch版本:', torch.__version__)" 2>/dev/null; then
        log_info "✅ PyTorch安装成功"
    else
        log_error "❌ PyTorch安装失败"
    fi

    # 检查MPS可用性
    if python3 -c "import torch; print('MPS可用:', torch.backends.mps.is_available())" 2>/dev/null; then
        log_info "✅ MPS后端可用"
    else
        log_warn "⚠️ MPS后端不可用"
    fi

    # 检查MLX
    if python3 -c "import mlx; print('MLX版本:', mlx.__version__)" 2>/dev/null; then
        log_info "✅ MLX安装成功"
    else
        log_warn "⚠️ MLX未安装"
    fi

    # 检查Core ML
    if python3 -c "import coremltools; print('Core ML版本:', coremltools.__version__)" 2>/dev/null; then
        log_info "✅ Core ML工具安装成功"
    else
        log_warn "⚠️ Core ML未安装"
    fi
}

# 创建测试脚本
create_test_script() {
    log_info "创建M4性能测试脚本..."

    cat > /Users/xujian/Athena工作平台/scripts/test_m4_performance.py << 'EOF'
#!/usr/bin/env python3
"""
M4芯片AI性能测试脚本
"""

import time
import torch
import numpy as np

def test_mps_performance():
    """测试MPS性能"""
    print("🚀 测试MPS性能")

    if not torch.backends.mps.is_available():
        print("❌ MPS不可用")
        return

    # 创建测试模型
    device = torch.device("mps")
    model = torch.nn.Sequential(
        torch.nn.Linear(1000, 512),
        torch.nn.ReLU(),
        torch.nn.Linear(512, 256),
        torch.nn.ReLU(),
        torch.nn.Linear(256, 10)
    ).to(device)

    # 测试数据
    batch_size = 64
    input_data = torch.randn(batch_size, 1000).to(device)

    # 预热
    for _ in range(10):
        _ = model(input_data)

    # 性能测试
    times = []
    for _ in range(100):
        start = time.time()
        output = model(input_data)
        torch.mps.synchronize()
        times.append(time.time() - start)

    avg_time = np.mean(times)
    throughput = batch_size / avg_time

    print(f"✅ MPS性能测试完成")
    print(f"   平均时间: {avg_time:.4f}s")
    print(f"   吞吐量: {throughput:.2f} samples/s")
    print(f"   输出形状: {output.shape}")

def test_memory_usage():
    """测试内存使用"""
    print("\n💾 测试内存使用")

    if not torch.backends.mps.is_available():
        print("❌ MPS不可用，跳过内存测试")
        return

    allocated = torch.mps.current_allocated_memory() / (1024**2)
    reserved = torch.mps.driver_allocated_memory() / (1024**2)

    print(f"✅ 内存使用情况")
    print(f"   已分配: {allocated:.2f} MB")
    print(f"   驱动保留: {reserved:.2f} MB")

if __name__ == "__main__":
    test_mps_performance()
    test_memory_usage()
    print("\n🎉 M4性能测试完成！")
EOF

    chmod +x /Users/xujian/Athena工作平台/scripts/test_m4_performance.py
    log_info "测试脚本已创建: scripts/test_m4_performance.py"
}

# 主函数
main() {
    echo -e "${BLUE}Apple Silicon M4 AI优化环境设置${NC}"
    echo "==================================="
    echo

    # 检查芯片
    if ! check_m4_chip; then
        echo -e "\n${YELLOW}警告: 不是M4芯片，某些优化可能不可用${NC}"
        read -p "是否继续安装？(y/n): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # 执行安装步骤
    install_xcode_tools
    echo
    install_homebrew
    echo
    install_python_deps
    echo
    setup_environment
    echo
    verify_installation
    echo
    create_test_script
    echo

    echo -e "\n${GREEN}✅ Apple Silicon M4环境设置完成！${NC}"
    echo -e "\n${BLUE}下一步：${NC}"
    echo "1. 运行 'source ~/.zshrc' 或 'source ~/.bash_profile' 加载环境变量"
    echo "2. 运行 'python3 scripts/test_m4_performance.py' 测试性能"
    echo "3. 启动优化版Athena平台"
    echo -e "\n${BLUE}性能提示：${NC}"
    echo "- 使用MPS加速PyTorch模型"
    echo "- 使用MLX进行Apple Silicon优化"
    echo "- 启用FP16混合精度训练"
    echo "- 调整批处理大小以优化Neural Engine"
}

# 执行主函数
main "$@"