#!/bin/bash
# Athena智能体统一启动脚本
# Unified Agent Launch Script for Athena Platform

# 设置环境变量
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 显示帮助信息
show_help() {
    echo "🤖 Athena智能体启动脚本"
    echo ""
    echo "📋 使用方法："
    echo "   ./start_agent.sh <智能体名称>"
    echo ""
    echo "👥 可用智能体："
    echo "   xiaonuo       - 小诺·双鱼座（平台总调度官）"
    echo "   xiaona        - 小娜·天秤女神（专利法律专家）"
    echo "   yunxi         - 云熙.vega（IP管理系统）"
    echo "   xiaochen      - 小宸（自媒体运营专家）"
    echo "   athena        - Athena.智慧女神（核心智能体）"
    echo ""
    echo "🔧 其他选项："
    echo "   status        - 查看所有智能体状态"
    echo "   stop <name>   - 停止指定智能体"
    echo "   stop-all      - 停止所有智能体"
    echo "   help          - 显示此帮助信息"
    echo ""
    echo "💡 示例："
    echo "   ./start_agent.sh xiaonuo     # 启动小诺"
    echo "   ./start_agent.sh xiaona      # 启动小娜"
    echo "   ./start_agent.sh status      # 查看状态"
}

# 启动小诺
start_xiaonuo() {
    echo "🌸 启动小诺·双鱼座（平台总调度官）..."

    # 检查是否已经运行
    if pgrep -f "xiaonuo_fixed.py" > /dev/null; then
        echo "💖 小诺已经在运行中"
        return 0
    fi

    # 停止其他可能冲突的智能体
    stop_agent xiaona

    # 启动小诺
    cd /Users/xujian/Athena工作平台/xiaonuo
    nohup python3 xiaonuo_fixed.py > /tmp/xiaonuo.log 2>&1 &
    sleep 2

    if pgrep -f "xiaonuo_fixed.py" > /dev/null; then
        echo "✅ 小诺启动成功！"
        echo "💝 日志: tail -f /tmp/xiaonuo.log"
    else
        echo "❌ 小诺启动失败，检查日志："
        tail -20 /tmp/xiaonuo.log
    fi
}

# 启动小娜
start_xiaona() {
    echo "⚖️ 启动小娜·天秤女神（专利法律专家）..."

    # 检查PostgreSQL
    if ! /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        echo "❌ PostgreSQL未运行，请先启动"
        return 1
    fi

    # 检查向量知识库
    if ! curl -s http://localhost:8002/health >/dev/null 2>&1; then
        echo "⚠️ 启动向量知识库..."
        cd /Users/xujian/Athena工作平台/services/vectorkg-unified
        nohup python3 unified_intelligent_backend.py > /tmp/vectorkg_unified.log 2>&1 &
        sleep 5
    fi

    # 检查是否已经运行
    if curl -s http://localhost:8001/ | grep -q "小娜" 2>/dev/null; then
        echo "⚖️ 小娜已经在运行中"
        return 0
    fi

    # 停止其他可能冲突的智能体
    stop_agent xiaonuo

    # 启动小娜
    ./scripts/start_xiaona_enhanced.sh
}

# 启动云熙
start_yunxi() {
    echo "🌟 启动云熙.vega（IP管理系统）..."
    echo "🔧 云熙系统升级中，暂未可用"
}

# 启动小宸
start_xiaochen() {
    echo "🎨 启动小宸（自媒体运营专家）..."
    echo "🔧 小宸系统开发中，暂未可用"
}

# 启动Athena
start_athena() {
    echo "🏛️ 启动Athena.智慧女神（核心智能体）..."
    echo "🔧 Athena系统与平台集成中"
}

# 停止指定智能体
stop_agent() {
    local agent_name=$1
    case $agent_name in
        xiaonuo)
            echo "🛑 停止小诺..."
            pkill -f "xiaonuo_fixed.py" 2>/dev/null && echo "✅ 小诺已停止"
            ;;
        xiaona)
            echo "🛑 停止小娜..."
            pkill -f "xiaona_enhanced_integrated.py" 2>/dev/null && echo "✅ 小娜已停止"
            ;;
        yunxi)
            echo "🛑 停止云熙..."
            # 停止云熙相关进程
            ;;
        xiaochen)
            echo "🛑 停止小宸..."
            # 停止小宸相关进程
            ;;
        athena)
            echo "🛑 停止Athena..."
            # 停止Athena相关进程
            ;;
        *)
            echo "❌ 未知的智能体: $agent_name"
            ;;
    esac
}

# 停止所有智能体
stop_all() {
    echo "🛑 停止所有智能体..."
    stop_agent xiaonuo
    stop_agent xiaona
    stop_agent yunxi
    stop_agent xiaochen
    stop_agent athena
    echo "✅ 所有智能体已停止"
}

# 显示状态
show_status() {
    echo "📊 智能体状态检查："
    echo ""

    # 小诺状态
    if pgrep -f "xiaonuo_fixed.py" > /dev/null; then
        echo "🌸 小诺·双鱼座: ✅ 运行中"
    else
        echo "🌸 小诺·双鱼座: ❌ 未运行"
    fi

    # 小娜状态
    if curl -s http://localhost:8001/ | grep -q "小娜" 2>/dev/null; then
        echo "⚖️ 小娜·天秤女神: ✅ 运行中 (端口8001)"
    else
        echo "⚖️ 小娜·天秤女神: ❌ 未运行"
    fi

    # 后端服务状态
    if curl -s http://localhost:8002/health >/dev/null 2>&1; then
        echo "🔧 向量知识库: ✅ 运行中 (端口8002)"
    else
        echo "🔧 向量知识库: ❌ 未运行"
    fi

    if /opt/homebrew/Cellar/postgresql@17/17.7/bin/pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
        echo "🗄️  PostgreSQL: ✅ 运行中"
    else
        echo "🗄️  PostgreSQL: ❌ 未运行"
    fi
}

# 主逻辑
main() {
    case $1 in
        xiaonuo|小诺|nuo)
            start_xiaonuo
            ;;
        xiaona|小娜|na)
            start_xiaona
            ;;
        yunxi|云熙|yun)
            start_yunxi
            ;;
        xiaochen|小宸|chen)
            start_xiaochen
            ;;
        athena|智慧女神|ath)
            start_athena
            ;;
        status|状态)
            show_status
            ;;
        stop)
            if [ -z "$2" ]; then
                echo "❌ 请指定要停止的智能体"
                show_help
                return 1
            fi
            stop_agent "$2"
            ;;
        stop-all|全部停止)
            stop_all
            ;;
        help|帮助|--help|-h)
            show_help
            ;;
        *)
            echo "❌ 未知的命令: $1"
            echo ""
            show_help
            return 1
            ;;
    esac
}

# 执行主逻辑
main "$@"