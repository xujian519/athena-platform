#!/bin/bash
# 专利全文检索系统启动脚本

echo "========================================"
echo " 专利全文检索系统启动脚本"
echo "========================================"

# 创建必要的目录
mkdir -p outputs
mkdir -p logs

# 检查Python环境
echo "检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装"
    exit 1
fi

# 检查PostgreSQL
echo "检查PostgreSQL服务..."
if ! pg_isready -q -h localhost -p 5432; then
    echo "❌ PostgreSQL 未运行"
    echo "请先启动PostgreSQL服务："
    echo "  macOS: brew services start postgresql"
    echo "  或手动启动 PostgreSQL"
    exit 1
fi

# 检查必要的Python包
echo "检查Python依赖包..."
packages=("fastapi" "uvicorn" "psycopg2-binary" "requests" "beautifulsoup4")
for package in "${packages[@]}"; do
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        echo "安装 $package..."
        pip3 install $package
    fi
done

# 设置环境变量
export PYTHONPATH=/Users/xujian/Athena工作平台:$PYTHONPATH

# 启动基础专利搜索API
echo "启动基础专利搜索API (端口 8030)..."
nohup python3 -m uvicorn services.patent_search_api:app \
    --host 0.0.0.0 \
    --port 8030 \
    --reload > documentation/logs/patent_api_8030.log 2>&1 &
PID_8030=$!
echo "  PID: $PID_8030"

# 等待基础API启动
sleep 3

# 启动增强版API（集成Google专利）
echo "启动增强版专利API (端口 8031)..."
nohup python3 -m uvicorn services.enhanced_patent_api:app \
    --host 0.0.0.0 \
    --port 8031 \
    --reload > documentation/logs/enhanced_patent_api_8031.log 2>&1 &
PID_8031=$!
echo "  PID: $PID_8031"

# 等待增强版API启动
sleep 3

# 检查服务状态
echo "检查服务状态..."

# 检查基础API
if curl -s http://localhost:8030/health > /dev/null; then
    echo "✅ 基础专利API (8030) - 运行正常"
else
    echo "❌ 基础专利API (8030) - 启动失败"
fi

# 检查增强版API
if curl -s http://localhost:8031/health > /dev/null; then
    echo "✅ 增强版专利API (8031) - 运行正常"
else
    echo "❌ 增强版专利API (8031) - 启动失败"
fi

# 保存PID到文件
echo "$PID_8030" > .patent_api_8030.pid
echo "$PID_8031" > .enhanced_patent_api_8031.pid

# 显示使用信息
echo ""
echo "========================================"
echo "系统启动完成！"
echo "========================================"
echo ""
echo "服务地址："
echo "  基础API: http://localhost:8030"
echo "  增强API: http://localhost:8031"
echo ""
echo "快速测试："
echo "  # 搜索专利"
echo "  curl 'http://localhost:8030/api/v1/search?q=电动汽车&limit=5'"
echo ""
echo "  # 获取专利全文"
echo "  curl 'http://localhost:8031/api/v2/patent/CN202310123456.7/full'"
echo ""
echo "使用客户端工具："
echo "  python3 scripts/patent_fulltext_client.py --search '电动汽车'"
echo ""
echo "查看日志："
echo "  tail -f documentation/logs/patent_api_8030.log"
echo "  tail -f documentation/logs/enhanced_patent_api_8031.log"
echo ""
echo "停止服务："
echo "  ./scripts/stop_patent_fulltext_system.sh"
echo ""
echo "========================================"