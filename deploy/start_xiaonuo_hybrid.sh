#!/bin/bash
# 小诺混合架构系统启动脚本
# Xiaonuo Hybrid Architecture Startup Script

echo "🌸 小诺混合架构系统启动器"
echo "=================================="

# 检查Python版本
python3 --version >/dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "❌ 错误: 未找到 Python3"
    exit 1
fi

# 检查必要目录
if [ ! -d "core" ]; then
    echo "❌ 错误: 未找到 core 目录"
    exit 1
fi

# 创建必要目录
mkdir -p logs
mkdir -p data/backup

# 检查端口占用
check_port() {
    local port=$1
    local service=$2

    if lsof -i :$port >/dev/null 2>&1; then
        echo "⚠️  警告: 端口 $port 已被占用 ($service)"
        echo "   如果需要，请手动停止占用该端口的服务"
        return 1
    fi
    return 0
}

echo ""
echo "🔍 检查系统状态..."

# 检查关键端口
echo "检查专业智能体端口..."
check_port 8005 "Athena"
check_port 8006 "小娜"
check_port 8007 "云熙"
check_port 8008 "小宸"

# 初始化数据库
echo ""
echo "🗄️  初始化数据库..."
python3 -c "
from core.xiaonuo_basic_operations import DatabaseManager
db = DatabaseManager()
for db_name in ['performance_metrics.db', 'baochen_finance.db', 'xiaonuo_life.db', 'xiaonuo_knowledge.db']:
    conn = db.get_connection(db_name)
    print(f'✅ {db_name} 初始化完成')
    conn.close()
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ 数据库初始化成功"
else
    echo "⚠️  数据库初始化出现警告，但不影响运行"
fi

# 显示启动选项
echo ""
echo "🚀 启动选项:"
echo "1. 交互模式 (推荐) - 通过命令行与小诺交互"
echo "2. 测试模式 - 运行系统测试"
echo "3. 后台模式 - 以守护进程方式运行"
echo "4. 退出"

while true; do
    echo ""
    read -p "请选择启动模式 (1-4): " choice

    case $choice in
        1)
            echo ""
            echo "🎯 启动交互模式..."
            echo "输入 'help' 查看可用命令"
            echo "输入 'exit' 退出系统"
            echo ""
            python3 xiaonuo_hybrid_main.py
            break
            ;;
        2)
            echo ""
            echo "🧪 运行系统测试..."
            python3 test_hybrid_system.py
            break
            ;;
        3)
            echo ""
            echo "🔄 启动后台模式..."
            nohup python3 xiaonuo_hybrid_main.py > logs/xiaonuo_hybrid_$(date +%Y%m%d_%H%M%S).log 2>&1 &
            echo "✅ 系统已在后台启动"
            echo "📋 查看日志: tail -f logs/xiaonuo_hybrid_*.log"
            echo "🛑 停止系统: pkill -f xiaonuo_hybrid_main.py"
            break
            ;;
        4)
            echo "👋 退出"
            exit 0
            ;;
        *)
            echo "❌ 无效选择，请输入 1-4"
            ;;
    esac
done

echo ""
echo "✅ 小诺混合架构系统运行结束"