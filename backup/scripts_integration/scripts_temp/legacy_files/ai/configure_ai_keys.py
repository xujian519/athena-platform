#!/usr/bin/env python3
"""
AI服务API密钥配置助手
AI Service API Key Configuration Helper
"""

import os
import sys
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent.parent
env_file = project_root / "services" / "yunpat-agent" / ".env"


def check_current_keys():
    """检查当前配置的API密钥"""
    print("🔍 检查当前API密钥配置...")

    # 检查环境变量
    env_vars = {
        'DEEPSEEK_API_KEY': 'DeepSeek AI服务',
        'ZHIPU_API_KEY': '智谱GLM服务',
        'GLM_API_KEY': 'GLM服务（别名）',
        'QWEN_API_KEY': '通义千问服务',
        'OPENAI_API_KEY': 'OpenAI服务'
    }

    configured = []
    missing = []

    for var, desc in env_vars.items():
        value = os.getenv(var)
        if value and len(value) > 10:
            configured.append(f"✅ {var} ({desc})")
        else:
            missing.append(f"❌ {var} ({desc})")

    if configured:
        print("\n已配置的API密钥:")
        for item in configured:
            print(f"  {item}")

    if missing:
        print("\n缺失的API密钥:")
        for item in missing:
            print(f"  {item}")

    return len(missing) == 0


def show_registration_guide():
    """显示API密钥注册指南"""
    print("\n" + "="*60)
    print("📋 AI服务API密钥获取指南")
    print("="*60)

    services = [
        {
            "name": "DeepSeek",
            "url": "https://platform.deepseek.com/",
            "env_var": "DEEPSEEK_API_KEY",
            "free_quota": "免费额度：$10",
            "features": ["代码生成", "文档分析", "技术问答"]
        },
        {
            "name": "智谱GLM",
            "url": "https://open.bigmodel.cn/",
            "env_var": "ZHIPU_API_KEY",
            "free_quota": "免费额度：赠送平衡包",
            "features": ["中文对话", "文档理解", "知识问答"]
        }
    ]

    for service in services:
        print(f"\n🔸 {service['name']}")
        print(f"   注册地址: {service['url']}")
        print(f"   环境变量: {service['env_var']}")
        print(f"   {service['free_quota']}")
        print(f"   主要功能: {', '.join(service['features'])}")

    print("\n" + "="*60)


def configure_env_file():
    """配置.env文件"""
    print("\n🔧 配置.env文件...")

    # 读取当前.env文件
    if env_file.exists():
        with open(env_file, 'r') as f:
            content = f.read()
    else:
        content = ""

    # 检查是否已有AI配置
    if 'AI服务配置' not in content:
        # 添加AI配置部分
        ai_config = """

# AI服务配置
# AI Service Configuration

# DeepSeek API密钥 (https://platform.deepseek.com/)
# DEEPSEEK_API_KEY=sk-your-deepseek-api-key

# 智谱GLM API密钥 (https://open.bigmodel.cn/)
# ZHIPU_API_KEY=your-glm-api-key

# GLM API密钥（别名）
# GLM_API_KEY=your-glm-api-key

# 其他可选服务
# QWEN_API_KEY=sk-your-qwen-api-key
# OPENAI_API_KEY=sk-your-openai-api-key

# AI服务设置
AI_ENABLED=true
AI_TIMEOUT=30
AI_MAX_RETRIES=3
"""

        content += ai_config

        with open(env_file, 'w') as f:
            f.write(content)

        print(f"✅ 已添加AI配置到: {env_file}")
    else:
        print("✅ .env文件已包含AI配置")

    # 显示配置说明
    print("\n📝 配置说明:")
    print("1. 编辑文件:", env_file)
    print("2. 取消注释并填入您的API密钥")
    print("3. 保存文件后重启YunPat服务")


def set_env_variables():
    """设置环境变量（临时）"""
    print("\n🌍 设置环境变量（临时）...")

    # 检查shell类型
    shell = os.getenv('SHELL', '')
    if 'zsh' in shell:
        config_file = '~/.zshrc'
    elif 'bash' in shell:
        config_file = '~/.bashrc'
    else:
        config_file = '~/.profile'

    print(f"💡 要永久设置环境变量，请添加到 {config_file}:")
    print("\nexport DEEPSEEK_API_KEY='sk-your-deepseek-api-key'")
    print("export ZHIPU_API_KEY='your-glm-api-key'")
    print("\n然后运行: source", config_file)


def main():
    """主函数"""
    print("="*60)
    print("🤖 Athena AI服务API密钥配置助手")
    print("="*60)

    # 检查当前状态
    all_configured = check_current_keys()

    if all_configured:
        print("\n✅ 所有API密钥已配置，可以使用AI功能！")
        return

    # 显示注册指南
    show_registration_guide()

    # 配置.env文件
    configure_env_file()

    # 设置环境变量说明
    set_env_variables()

    print("\n🎯 快速开始:")
    print("1. 注册至少一个AI服务账号")
    print("2. 编辑 .env 文件，填入API密钥")
    print("3. 重启服务: python3 services/yunpat-agent/api_service.py")
    print("4. 测试AI功能: curl http://localhost:8087/api/v1/info")

    print("\n" + "="*60)


if __name__ == "__main__":
    main()