#!/usr/bin/env python3
"""
分析M4 Pro硬件资源利用情况
Analyze M4 Pro Hardware Resource Usage
"""

import subprocess


def run_command(cmd):
    """执行系统命令"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception:
        return ""

def check_m4_specs():
    """检查M4 Pro规格"""
    print("="*80)
    print("🍎 M4 Pro 芯片规格信息")
    print("="*80)

    # 获取CPU信息
    cpu_info = run_command("sysctl -n machdep.cpu.brand_string")
    cpu_cores = run_command("sysctl -n hw.ncpu")
    cpu_freq = run_command("sysctl -n hw.cpufrequency")

    print(f"CPU型号: {cpu_info}")
    print(f"CPU核心数: {cpu_cores}")
    if cpu_freq and cpu_freq.isdigit():
        print(f"CPU频率: {int(cpu_freq)//1000000} GHz")
    else:
        print("CPU频率: 需要查询")

    # 获取内存信息
    mem_size = run_command("sysctl -n hw.memsize")
    mem_gb = int(mem_size) / (1024**3)
    print(f"系统内存: {mem_gb:.1f} GB")

    # 获取GPU信息
    gpu_info = run_command("system_profiler SPDisplaysDataType | grep -A 5 'Chipset Model'")
    print(f"\nGPU信息:\n{gpu_info}")

    # 获取Neural Engine信息
    neural_info = run_command("system_profiler SPHardwareDataType | grep -A 2 'Neural Engine'")
    print(f"\nNeural Engine:\n{neural_info}")

def check_current_usage():
    """检查当前资源使用情况"""
    print("\n\n" + "="*80)
    print("📊 当前资源使用情况")
    print("="*80)

    # CPU使用率
    cpu_usage = run_command("top -l 1 | grep 'CPU usage'")
    print(f"CPU使用: {cpu_usage}")

    # 内存使用
    mem_usage = run_command("vm_stat | grep 'Pages free\\|Pages active\\|Pages inactive'")
    print(f"\n内存使用情况:\n{mem_usage}")

    # GPU使用（如果有）
    gpu_usage = run_command("ioreg -l | grep -i gpu")
    print(f"\nGPU状态: {gpu_usage[:200]}...")

def check_ml_libs():
    """检查ML库使用情况"""
    print("\n\n" + "="*80)
    print("🤖 机器学习库使用分析")
    print("="*80)

    # 检查是否使用MLX
    try:
        import mlx.core as mx
        mlx_version = mx.__version__
        print(f"✅ MLX版本: {mlx_version}")

        # 检查MLX是否使用GPU
        if mx.metal.is_available():
            print("✅ MLX正在使用Metal (Apple GPU)")
            device = mx.metal.default_device()
            print(f"   设备: {device}")
        else:
            print("⚠️ MLX未检测到GPU加速")
    except ImportError:
        print("❌ MLX未安装")

    # 检查PyTorch
    try:
        import torch
        print(f"\n✅ PyTorch版本: {torch.__version__}")
        if torch.backends.mps.is_available():
            print("✅ PyTorch支持MPS (Apple GPU)")
            if torch.backends.mps.is_built():
                print("   MPS已启用")
        else:
            print("⚠️ PyTorch未启用MPS")
    except ImportError:
        print("❌ PyTorch未安装")

    # 检查TensorFlow
    try:
        import tensorflow as tf
        print(f"\n✅ TensorFlow版本: {tf.__version__}")
        # TF 2.x默认不支持MPS，需要特殊配置
    except ImportError:
        print("❌ TensorFlow未安装")

    # 检查Ollama（如果运行）
    ollama_running = run_command("pgrep -f ollama")
    if ollama_running:
        print(f"\n✅ Ollama正在运行 (PID: {ollama_running})")
    else:
        print("\n❌ Ollama未运行")

def check_platform_optimization():
    """检查平台优化情况"""
    print("\n\n" + "="*80)
    print("⚡ 平台优化分析")
    print("="*80)

    optimizations = {
        "多线程并行处理": "检查是否使用multiprocessing",
        "向量化计算": "检查是否使用NumPy/SIMD",
        "Metal性能着色器": "检查是否利用GPU并行",
        "Neural Engine": "检查是否使用CoreML",
        "统一内存架构": "检查CPU/GPU数据传输"
    }

    for feature, desc in optimizations.items():
        print(f"📌 {feature}: {desc}")

    # 检查当前运行的Python进程
    python_procs = run_command("ps aux | grep python | grep -v grep")
    if python_procs:
        print(f"\n当前Python进程数: {len(python_procs.splitlines())}")
        # 分析内存占用
        for proc in python_procs.splitlines()[:3]:
            parts = proc.split()
            if len(parts) > 3:
                mem = parts[3]
                if 'M' in mem or 'G' in mem:
                    print(f"  - {parts[-1][:50]}... (内存: {mem})")

def suggest_optimizations():
    """优化建议"""
    print("\n\n" + "="*80)
    print("💡 M4 Pro优化建议")
    print("="*80)

    print("\n1. 🚀 充分利用M4 Pro的建议:")
    print("   - 使用MLX替代PyTorch，更好利用Apple Silicon")
    print("   - 启用Metal Performance Shaders (MPS)")
    print("   - 使用CoreML进行模型推理")
    print("   - 利用Neural Engine加速AI任务")

    print("\n2. 📈 代码优化建议:")
    print("   - 使用multiprocessing.Pool利用多核心")
    print("   - 使用NumPy的向量化操作")
    print("   - 批处理数据减少内存拷贝")
    print("   - 预分配内存避免频繁分配")

    print("\n3. 🎯 具体实施建议:")
    print("   - 安装MLX: pip install mlx")
    print("   - 配置PyTorch MPS: export PYTORCH_ENABLE_MPS_FALLBACK=1")
    print("   - 使用joblib进行并行处理")
    print("   - 考虑使用Swift进行Metal着色器编程")

    print("\n4. 🔧 系统级优化:")
    print("   - 增加虚拟内存swap大小")
    print("   - 使用SSD缓存大数据集")
    print("   - 优化PostgreSQL配置以利用SSD")

def main():
    print("🔍 M4 Pro 硬件资源利用分析")
    print("="*80)

    check_m4_specs()
    check_current_usage()
    check_ml_libs()
    check_platform_optimization()
    suggest_optimizations()

    print("\n\n" + "="*80)
    print("✅ 分析完成")
    print("="*80)

if __name__ == "__main__":
    main()
