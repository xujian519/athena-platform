#!/bin/bash
# 启动所有数据服务

echo "🚀 启动Athena数据服务..."

# 创建必要的目录
mkdir -p logs
mkdir -p data/{raw,processed,crawled}

# 启动专利分析服务
echo "启动专利分析服务..."
cd patent-analysis
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
fi
python main.py > ../logs/patent-analysis.log 2>&1 &
PATENT_PID=$!
echo "专利分析服务 PID: $PATENT_PID"

# 启动爬虫服务
echo "启动爬虫服务..."
cd ../crawler
if [ -f "main.py" ]; then
    python main.py > ../logs/crawler.log 2>&1 &
    CRAWLER_PID=$!
    echo "爬虫服务 PID: $CRAWLER_PID"
else
    echo "爬虫服务尚未实现"
    CRAWLER_PID=0
fi

# 启动优化服务
echo "启动优化服务..."
cd ../optimization
if [ -f "main.py" ]; then
    python main.py > ../logs/optimization.log 2>&1 &
    OPT_PID=$!
    echo "优化服务 PID: $OPT_PID"
else
    echo "优化服务尚未实现"
    OPT_PID=0
fi

# 保存PID
cd ..
echo $PATENT_PID > logs/patent-analysis.pid
echo $CRAWLER_PID > logs/crawler.pid
echo $OPT_PID > logs/optimization.pid

echo ""
echo "✅ 数据服务启动完成"
echo ""
echo "服务地址："
echo "- 专利分析: http://localhost:9100"
echo "- 爬虫服务: http://localhost:9101"
echo "- 优化服务: http://localhost:9102"
echo ""
echo "日志位置："
echo "- tail -f logs/patent-analysis.log"
echo "- tail -f logs/crawler.log"
echo "- tail -f logs/optimization.log"