#!/bin/bash
# 快速启动多模态系统

echo "🚀 快速启动Athena多模态系统"
echo "=========================================="

# 检查服务状态
echo "📊 检查服务状态..."
curl -s "http://localhost:8085/health" | python3 -m json.tool

echo ""
echo "📋 可用API端点:"
echo "  - 系统健康: curl http://localhost:8085/health"
echo "  - 系统统计: curl http://localhost:8085/api/stats"
echo "  - 支持格式: curl http://localhost:8085/api/tools/formats"
echo "  - API文档: http://localhost:8085/docs"
echo ""
echo "🔧 管理命令:"
echo "  - 查看日志: tail -f documentation/logs/*.log"
echo "  - 停止服务: ./scripts/startup/stop_multimodal_system.sh"
echo "  - 重启服务: ./scripts/startup/start_multimodal_system.sh"

# 检查进程状态
echo ""
echo "📋 进程状态:"
ps aux | grep -E "(multimodal_api_server|patent_data_pipeline)" | grep -v grep
