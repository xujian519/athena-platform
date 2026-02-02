#!/bin/bash
# 迭代专利搜索服务启动脚本
# Start Iterative Patent Search Service

echo "🚀 启动Athena迭代专利搜索服务"
echo "======================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 未安装，请先安装Python3"
    exit 1
fi

# 设置环境变量
export PYTHONPATH="/Users/xujian/Athena工作平台:$PYTHONPATH"

# 创建必要目录
mkdir -p "/Users/xujian/Athena工作平台/data"
mkdir -p "/Users/xujian/Athena工作平台/logs"
mkdir -p "/Users/xujian/Athena工作平台/reports"

# 进入项目目录
cd "/Users/xujian/Athena工作平台"

echo "📚 加载专利数据库..."
echo "🔧 初始化迭代改进引擎..."

# 启动服务
echo "🌟 启动服务..."
python3 -c "
import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path('.').resolve()
sys.path.append(str(project_root))

try:
    from deploy_iterative_search import StandaloneIterativeSearch
    
    async def start_service():
        service = StandaloneIterativeSearch()
        print('✅ 迭代专利搜索服务已启动')
        print('📡 服务地址: http://localhost:8089')
        print('📊 API文档: http://localhost:8089/docs')
        print('💡 使用示例:')
        print('   python3 -c \"import asyncio; from deploy_iterative_search import StandaloneIterativeSearch; s = StandaloneIterativeSearch(); print(asyncio.run(s.search_patents(\\\"机器学习\\\")))\"')
        print()
        print('🎯 服务已就绪，可以开始使用!')
        print('按 Ctrl+C 停止服务')
        
        # 保持服务运行
        while True:
            await asyncio.sleep(1)
    
    asyncio.run(start_service())
    
except Exception as e:
    print(f'❌ 服务启动失败: {e}')
    sys.exit(1)
"