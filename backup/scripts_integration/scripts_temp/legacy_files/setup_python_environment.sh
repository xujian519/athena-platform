#!/bin/bash
# Athena工作平台Python环境统一设置脚本

echo "🐍 Athena工作平台Python环境统一设置"
echo "=================================="

# 1. 验证当前Python环境
echo ""
echo "📊 当前Python环境检查："
echo "python3版本: $(python3 --version)"
echo "python3路径: $(which python3)"
echo "pip3版本: $(pip3 --version)"
echo "pip3路径: $(which pip3)"

# 2. 验证Homebrew Python是否为默认
if [[ $(python3 --version) == *"Python 3.14"* ]]; then
    echo "✅ 检测到Homebrew Python 3.14.0 作为默认"
else
    echo "❌ 默认Python不是Homebrew版本，请调整PATH"
    echo "添加到 ~/.zshrc:"
    echo 'export PATH="/opt/homebrew/bin:$PATH"'
    exit 1
fi

# 3. 安装项目依赖
echo ""
echo "📦 安装项目依赖..."
pip3 install --user --break-system-packages \
    aiohttp \
    fastapi \
    uvicorn \
    asyncpg \
    redis \
    python-multipart \
    pydantic \
    sqlalchemy \
    python-jose \
    passlib \
    bcrypt \
    networkx

# 4. 验证关键包安装
echo ""
echo "🔍 验证包安装..."
packages=("aiohttp" "fastapi" "asyncpg" "redis" "pydantic" "sqlalchemy")
for package in "${packages[@]}"; do
    if python3 -c "import $package" 2>/dev/null; then
        echo "✅ $package"
    else
        echo "❌ $package 安装失败"
    fi
done

# 5. 创建环境配置
echo ""
echo "⚙️ 创建环境配置..."
cat > ~/.athena_python_env << 'EOF'
# Athena工作平台Python环境配置
export PATH="/opt/homebrew/bin:$PATH"
export PATH="$HOME/Library/Python/3.14/bin:$PATH"
export PYTHONPATH="/Users/xujian/Athena工作平台"
export ATHENA_PLATFORM_HOME="/Users/xujian/Athena工作平台"
EOF

# 6. 检查shell配置文件
echo ""
echo "🔧 检查shell配置..."
if [[ -f ~/.zshrc ]]; then
    if ! grep -q "athena_python_env" ~/.zshrc; then
        echo "" >> ~/.zshrc
        echo "# Athena工作平台Python环境" >> ~/.zshrc
        echo 'source ~/.athena_python_env' >> ~/.zshrc
        echo "✅ 已添加到 ~/.zshrc"
    else
        echo "✅ ~/.zshrc 已包含Athena环境配置"
    fi
else
    echo "⚠️ 未找到 ~/.zshrc，请手动配置"
fi

# 7. 创建Python环境检查脚本
cat > /Users/xujian/Athena工作平台/check_python_env.py << 'EOF'
#!/usr/bin/env python3
"""Athena工作平台Python环境检查"""
import sys
import subprocess

def main():
    print("🐍 Athena工作平台Python环境检查")
    print("=" * 40)

    print(f"Python版本: {sys.version}")
    print(f"Python路径: {sys.executable}")

    # 检查关键包
    packages = {
        'aiohttp': '异步HTTP服务器',
        'fastapi': 'Web框架',
        'uvicorn': 'ASGI服务器',
        'asyncpg': 'PostgreSQL异步驱动',
        'redis': 'Redis客户端',
        'pydantic': '数据验证',
        'sqlalchemy': 'ORM框架'
    }

    print("\n📦 包检查:")
    for package, description in packages.items():
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description}")

if __name__ == "__main__":
    main()
EOF

chmod +x /Users/xujian/Athena工作平台/check_python_env.py

# 8. 提示用户
echo ""
echo "✅ Python环境设置完成！"
echo ""
echo "📋 下一步："
echo "1. 重新启动终端或运行: source ~/.zshrc"
echo "2. 验证环境: python3 /Users/xujian/Athena工作平台/check_python_env.py"
echo "3. 现在可以启动小诺了: python3 /Users/xujian/Athena工作平台/start_xiaonuo_dialogue.py"

echo ""
echo "💡 环境变量已设置，重启终端后生效！"