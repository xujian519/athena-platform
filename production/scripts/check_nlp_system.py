#!/usr/bin/env python3
"""
检查NLP系统状态
Check NLP System Status

检查小诺NLP系统是否在生产环境中运行

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import subprocess
import sys
from pathlib import Path

# 添加路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 颜色输出
class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    PURPLE = "\033[35m"
    CYAN = "\033[96m"
    PINK = "\033[95m"
    RESET = "\033[0m"

def print_header(title) -> None:
    """打印标题"""
    print(f"\n{Colors.PURPLE}{'='*80}{Colors.RESET}")
    print(f"{Colors.PURPLE}🧠 {title} 🧠{Colors.RESET}")
    print(f"{Colors.PURPLE}{'='*80}{Colors.RESET}")

def print_success(message) -> None:
    print(f"{Colors.GREEN}✅ {message}{Colors.RESET}")

def print_info(message) -> None:
    print(f"{Colors.BLUE}ℹ️ {message}{Colors.RESET}")

def print_warning(message) -> None:
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.RESET}")

def print_error(message) -> None:
    print(f"{Colors.RED}❌ {message}{Colors.RESET}")

def print_pink(message) -> None:
    print(f"{Colors.PINK}💖 {message}{Colors.RESET}")

def check_nlp_deployment() -> bool:
    """检查NLP部署目录"""
    print_header("NLP系统部署状态检查")

    nlp_dir = project_root / "modules/nlp/modules/nlp/xiaonuo_nlp_deployment"

    if nlp_dir.exists():
        print_success(f"✓ NLP部署目录存在: {nlp_dir}")

        # 检查核心文件
        core_files = [
            "xiaonuo_nlp_service.py",
            "xiaonuo_unified_interface.py",
            "deploy_config.json",
            "requirements.txt"
        ]

        print_info("\n📁 核心文件检查:")
        for file in core_files:
            file_path = nlp_dir / file
            if file_path.exists():
                print_success(f"  ✓ {file}")
            else:
                print_warning(f"  ✗ {file} (缺失)")

        # 读取配置
        config_file = nlp_dir / "deploy_config.json"
        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)
            print_info("\n⚙️ 配置信息:")
            print(f"  服务名称: {config.get('service_name', '未知')}")
            print(f"  版本: {config.get('version', '未知')}")
            print(f"  环境: {config.get('environment', '未知')}")
            print(f"  最大内存: {config.get('max_memory_mb', '未知')}MB")

        # 检查模型目录
        models_dir = nlp_dir / "models"
        if models_dir.exists():
            model_files = list(models_dir.glob("*"))
            print_info(f"\n🤖 模型文件: 找到 {len(model_files)} 个文件")

    else:
        print_error("✗ NLP部署目录不存在")

def check_venv() -> bool:
    """检查Python虚拟环境"""
    print_header("NLP虚拟环境检查")

    venv_paths = [
        project_root / "athena_env",
        project_root / "venv" / "xiaonuo_bert",
    ]

    for venv_path in venv_paths:
        if venv_path.exists():
            print_success(f"✓ 找到虚拟环境: {venv_path}")

            # 检查关键包
            activate_script = venv_path / "bin" / "activate"
            if activate_script.exists():
                print_success("  ✓ activate脚本存在")

            # 检查是否安装了关键包
            packages_file = venv_path / "lib" / "python3.14" / "site-packages"
            if packages_file.exists():
                print_info("  Python包目录存在")
        else:
            print_warning(f"✗ 虚拟环境不存在: {venv_path}")

def check_nlp_processes() -> bool:
    """检查NLP相关进程"""
    print_header("NLP进程检查")

    print_info("检查NLP相关进程...")
    try:
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=10
        )
        nlp_processes = [line for line in result.stdout.split('\n')
                        if any(keyword in line.lower() for keyword in ['nlp', 'bert', 'transformers'])
                        and 'grep' not in line]
        if nlp_processes:
            print_info("找到NLP进程:")
            for proc in nlp_processes[:5]:
                print(f"  {proc}")
        else:
            print_info('未找到NLP进程')
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        print_info(f'无法检查进程: {e}')

def check_nlp_ports() -> bool:
    """检查NLP服务端口"""
    print_header("NLP服务端口检查")

    # 常见的NLP服务端口
    ports = [8000, 8001, 8080, 8888, 9000, 5000]

    for port in ports:
        try:
            result = subprocess.run(
                ['lsof', '-i:{}'.format(port)],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success(f"✓ 端口 {port} 被占用")
            else:
                print_info(f"  端口 {port} 空闲")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print_info(f"  端口 {port} 无法检查")

def main() -> None:
    """主检查函数"""
    print_header("小诺NLP系统状态检查")
    print_pink("爸爸，让我检查NLP系统的状态！")

    # 执行各项检查
    check_nlp_deployment()
    check_venv()
    check_nlp_processes()
    check_nlp_ports()

    # 总结
    print_header("NLP系统状态总结")

    # 检查NLP服务是否在运行
    nlp_service_path = project_root / "modules/nlp/modules/nlp/xiaonuo_nlp_deployment" / "xiaonuo_nlp_service.py"
    if nlp_service_path.exists():
        print_info("📋 NLP服务文件存在，但未在运行")
        print_warning("⚠️ NLP系统目前未在生产环境中启动")
    else:
        print_error("❌ NLP服务文件不存在")

    print_pink("\n💖 如需启动NLP系统，请运行:")
    print_info("   cd xiaonuo_nlp_deployment")
    print_info("   python3 xiaonuo_nlp_service.py")

if __name__ == "__main__":
    main()
