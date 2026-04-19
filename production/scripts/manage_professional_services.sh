#!/bin/bash
# 专业服务管理脚本

case "$1" in
    "status")
        echo "📊 专业服务状态:"
        curl -s http://localhost:9000/all_services | python3 -m json.tool
        ;;
    "start")
        if [ -z "$2" ]; then
            echo "❌ 请指定服务名称: legal_expert_service 或 patent_rules_service"
            exit 1
        fi
        echo "🚀 启动服务: $2"
        curl -X POST http://localhost:9000/start_service \
             -H "Content-Type: application/json" \
             -d "{\"service_name\": \"$2\", \"user_request\": \"手动启动\"}"
        ;;
    "stop")
        if [ -z "$2" ]; then
            echo "❌ 请指定服务名称"
            exit 1
        fi
        echo "🛑 停止服务: $2"
        curl -X POST http://localhost:9000/stop_service/$2
        ;;
    "restart")
        if [ -z "$2" ]; then
            echo "❌ 请指定服务名称"
            exit 1
        fi
        echo "🔄 重启服务: $2"
        curl -X POST http://localhost:9000/stop_service/$2
        sleep 3
        curl -X POST http://localhost:9000/start_service \
             -H "Content-Type: application/json" \
             -d "{\"service_name\": \"$2\", \"user_request\": \"手动重启\"}"
        ;;
    "logs")
        echo "📄 查看管理器日志:"
        tail -f production/logs/professional_manager.log
        ;;
    *)
        echo "用法: $0 {status|start|stop|restart|logs} [service_name]"
        echo ""
        echo "命令示例:"
        echo "  $0 status                    # 查看所有服务状态"
        echo "  $0 start legal_expert_service  # 启动法律专家服务"
        echo "  $0 stop patent_rules_service    # 停止专利规则服务"
        echo "  $0 restart legal_expert_service # 重启法律专家服务"
        echo "  $0 logs                      # 查看日志"
        exit 1
        ;;
esac
