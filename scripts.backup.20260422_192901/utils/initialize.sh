#!/bin/bash

# Athena工作平台初始化脚本
# 用于快速设置和初始化平台环境

set -e  # 遇到错误时退出

echo "🚀 开始初始化Athena工作平台..."
echo "=================================="

# 检查Python版本
echo "🔍 检查Python版本..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装，请先安装Python3.9或更高版本"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")')
echo "✅ Python版本: $PYTHON_VERSION"

# 检查是否为Python 3.9+
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "✅ Python版本符合要求 (3.9+)"
else
    echo "❌ Python版本过低，需要3.9或更高版本，当前版本: $PYTHON_VERSION"
    exit 1
fi

# 检查pip
echo "🔍 检查pip..."
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip未安装"
    exit 1
fi
echo "✅ pip已安装"

# 检查git
echo "🔍 检查git..."
if ! command -v git &> /dev/null; then
    echo "⚠️  git未安装 (可选，但推荐安装)"
else
    echo "✅ git已安装"
fi

# 检查项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 项目根目录: $PROJECT_ROOT"

# 设置Python路径
export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
cd "$PROJECT_ROOT"

# 检查依赖文件
echo "🔍 检查依赖文件..."
REQUIREMENTS_FILE="$PROJECT_ROOT/config/requirements.txt"
if [ ! -f "$REQUIREMENTS_FILE" ]; then
    echo "❌ 依赖文件不存在: $REQUIREMENTS_FILE"
    exit 1
fi
echo "✅ 依赖文件存在: $REQUIREMENTS_FILE"

# 安装Python依赖
echo "📦 安装Python依赖包..."
pip3 install -r "$REQUIREMENTS_FILE" || {
    echo "❌ 依赖包安装失败"
    exit 1
}
echo "✅ 依赖包安装完成"

# 创建必要的目录
echo "📁 创建平台目录结构..."
DIRECTORIES=(
    "$PROJECT_ROOT/logs"
    "$PROJECT_ROOT/data"
    "$PROJECT_ROOT/temp"
    "$PROJECT_ROOT/backup"
    "$PROJECT_ROOT/documentation/reports"
    "$PROJECT_ROOT/workspace"
    "$PROJECT_ROOT/storage/uploads"
    "$PROJECT_ROOT/storage/processed"
    "$PROJECT_ROOT/storage/cache"
)

for dir in "${DIRECTORIES[@]}"; do
    mkdir -p "$dir"
    echo "  创建目录: $dir"
done
echo "✅ 目录结构创建完成"

# 验证配置文件
echo "🔍 验证配置文件..."
CONFIG_DIRS=(
    "$PROJECT_ROOT/config/environments/development"
    "$PROJECT_ROOT/config/environments/production"
)

for config_dir in "${CONFIG_DIRS[@]}"; do
    if [ ! -d "$config_dir" ]; then
        echo "❌ 配置目录不存在: $config_dir"
        exit 1
    fi
    echo "  配置目录存在: $config_dir"
done
echo "✅ 配置文件验证通过"

# 初始化数据库 (如果存在初始化脚本)
echo "🗄️ 检查数据库初始化脚本..."
DB_INIT_SCRIPT="$PROJECT_ROOT/scripts/database/setup_postgresql_patent_db.py"
if [ -f "$DB_INIT_SCRIPT" ]; then
    echo "  找到数据库初始化脚本，开始初始化..."
    python3 "$DB_INIT_SCRIPT" || {
        echo "  ⚠️ 数据库初始化可能失败，继续执行其他步骤..."
    }
    echo "  ✅ 数据库初始化脚本执行完成"
else
    echo "  ⚠️ 未找到数据库初始化脚本"
fi

# 运行平台健康检查
echo "🧪 运行平台健康检查..."
HEALTH_CHECK_SCRIPT="$PROJECT_ROOT/scripts/scripts_manager.py"
if [ -f "$HEALTH_CHECK_SCRIPT" ]; then
    python3 "$HEALTH_CHECK_SCRIPT" --health-check || {
        echo "⚠️ 健康检查遇到问题，但继续执行..."
    }
    echo "✅ 健康检查完成"
else
    echo "⚠️ 未找到健康检查脚本"
fi

# 显示初始化完成信息
echo ""
echo "🎉 Athena工作平台初始化完成！"
echo "=================================="
echo ""
echo "💡 下一步建议:"
echo "   1. 配置环境变量 (数据库连接等)"
echo "   2. 启动核心服务: python3 setup.py start  或  bash scripts/start_core_services.sh"
echo "   3. 查看服务状态: python3 setup.py status"
echo ""
echo "📋 平台访问地址:"
echo "   - 主服务: http://localhost:8000"
echo "   - 记忆服务: http://localhost:8008"
echo "   - 小诺服务: http://localhost:8083"
echo ""
echo "🔧 管理命令:"
echo "   - 安装依赖: python3 setup.py install"
echo "   - 初始化: python3 setup.py init"
echo "   - 启动服务: python3 setup.py start"
echo "   - 检查状态: python3 setup.py status"
echo ""
echo "🏛️  Athena工作平台已准备就绪，开始您的智能工作之旅！"