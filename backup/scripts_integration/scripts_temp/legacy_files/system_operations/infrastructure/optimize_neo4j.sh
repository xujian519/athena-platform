#!/bin/bash
# Neo4j优化配置应用脚本
# Athena知识图谱Neo4j性能优化

set -e

echo "🚀 开始优化Neo4j配置..."

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查是否以管理员权限运行
if [[ $EUID -eq 0 ]]; then
   echo -e "${RED}请不要以root权限运行此脚本${NC}"
   exit 1
fi

# 获取Neo4j路径
NEO4J_CONF_PATH="/opt/homebrew/Cellar/neo4j/2025.09.0/libexec/conf/neo4j.conf"
BACKUP_PATH="/opt/homebrew/Cellar/neo4j/2025.09.0/libexec/conf/neo4j.conf.backup.$(date +%Y%m%d_%H%M%S)"

echo -e "${BLUE}📍 检查Neo4j配置文件路径...${NC}"

if [[ ! -f "$NEO4J_CONF_PATH" ]]; then
    echo -e "${RED}❌ 找不到Neo4j配置文件: $NEO4J_CONF_PATH${NC}"
    echo "请确认Neo4j安装路径正确"
    exit 1
fi

echo -e "${GREEN}✅ 找到Neo4j配置文件${NC}"

# 备份原配置
echo -e "${YELLOW}📦 备份原始配置文件...${NC}"
cp "$NEO4J_CONF_PATH" "$BACKUP_PATH"
echo -e "${GREEN}✅ 配置文件已备份到: $BACKUP_PATH${NC}"

# 获取当前工作目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
OPTIMIZED_CONF_PATH="$PROJECT_DIR/config/neo4j_optimized.conf"

echo -e "${BLUE}📋 应用优化配置...${NC}"

# 创建临时配置文件
TEMP_CONF="/tmp/neo4j_optimized_temp.conf"

# 复制原配置
cp "$NEO4J_CONF_PATH" "$TEMP_CONF"

# 应用关键优化配置
# 内存配置
sed -i '' 's/#server.memory.heap.initial_size=512m/server.memory.heap.initial_size=2G/' "$TEMP_CONF"
sed -i '' 's/#server.memory.heap.max_size=512m/server.memory.heap.max_size=4G/' "$TEMP_CONF"

# 添加页面缓存配置（如果不存在）
if ! grep -q "server.memory.pagecache.size" "$TEMP_CONF"; then
    echo "" >> "$TEMP_CONF"
    echo "# Athena优化配置 - 页面缓存" >> "$TEMP_CONF"
    echo "server.memory.pagecache.size=2G" >> "$TEMP_CONF"
fi

# 添加查询缓存配置（如果不存在）
if ! grep -q "server.memory.query_cache.size" "$TEMP_CONF"; then
    echo "" >> "$TEMP_CONF"
    echo "# Athena优化配置 - 查询缓存" >> "$TEMP_CONF"
    echo "server.memory.query_cache.size=1000" >> "$TEMP_CONF"
    echo "server.memory.query_cache.enable=true" >> "$TEMP_CONF"
fi

# 添加连接池配置（如果不存在）
if ! grep -q "server.bolt.thread_pool_max_size" "$TEMP_CONF"; then
    echo "" >> "$TEMP_CONF"
    echo "# Athena优化配置 - 连接池" >> "$TEMP_CONF"
    echo "server.bolt.thread_pool_min_size=5" >> "$TEMP_CONF"
    echo "server.bolt.thread_pool_max_size=400" >> "$TEMP_CONF"
fi

# 应用优化配置
cp "$TEMP_CONF" "$NEO4J_CONF_PATH"
rm "$TEMP_CONF"

echo -e "${GREEN}✅ 优化配置已应用${NC}"

# 检查配置语法
echo -e "${BLUE}🔍 检查配置语法...${NC}"
if grep -q "server.memory.heap.max_size=4G" "$NEO4J_CONF_PATH"; then
    echo -e "${GREEN}✅ 内存配置验证通过${NC}"
else
    echo -e "${RED}❌ 内存配置验证失败${NC}"
    exit 1
fi

# 重启Neo4j服务
echo -e "${YELLOW}🔄 重启Neo4j服务以应用新配置...${NC}"

# 检查Neo4j服务状态
if brew services list | grep neo4j | grep started > /dev/null; then
    echo "停止Neo4j服务..."
    brew services stop neo4j
    sleep 3

    echo "启动Neo4j服务..."
    brew services start neo4j
    sleep 5
else
    echo "启动Neo4j服务..."
    brew services start neo4j
    sleep 5
fi

# 验证Neo4j是否正常启动
echo -e "${BLUE}🏥 验证Neo4j服务状态...${NC}"
sleep 3

if pgrep -f "neo4j" > /dev/null; then
    echo -e "${GREEN}✅ Neo4j服务已启动${NC}"
else
    echo -e "${RED}❌ Neo4j服务启动失败${NC}"
    echo "请检查配置文件和系统日志"
    exit 1
fi

# 测试连接
echo -e "${BLUE}🔗 测试Neo4j连接...${NC}"
python3 -c "
import sys
sys.path.append('.')
from neo4j import GraphDatabase
import time

try:
    print('正在连接Neo4j...')
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'password'))

    # 等待连接建立
    time.sleep(2)

    with driver.session() as session:
        result = session.run('RETURN 1 as test')
        record = result.single()
        if record['test'] == 1:
            print('✅ Neo4j连接测试成功!')
        else:
            print('❌ Neo4j连接测试失败')
            sys.exit(1)

    # 测试一个简单查询
    with driver.session() as session:
        result = session.run('MATCH (n) RETURN count(n) as node_count LIMIT 1')
        record = result.single()
        print(f'📊 当前图谱节点数: {record[\"node_count\"]}')

    driver.close()

except Exception as e:
    print(f'❌ Neo4j连接测试失败: {e}')
    sys.exit(1)
" 2>/dev/null

if [ $? -eq 0 ]; then
    echo -e "${GREEN}🎉 Neo4j优化配置应用成功！${NC}"
    echo -e "${GREEN}📈 性能提升预期：${NC}"
    echo "  - 堆内存: 512MB → 4GB (8倍提升)"
    echo "  - 页面缓存: 新增 2GB"
    echo "  - 查询缓存: 新增 1000条缓存"
    echo "  - 连接池: 优化至400连接"
    echo ""
    echo -e "${YELLOW}💡 下一步建议：${NC}"
    echo "1. 运行知识图谱API服务测试"
    echo "2. 执行复杂查询验证性能提升"
    echo "3. 监控系统资源使用情况"
else
    echo -e "${RED}❌ Neo4j连接测试失败${NC}"
    echo "请检查配置并手动重启Neo4j服务"
    exit 1
fi

echo -e "${BLUE}📋 配置摘要：${NC}"
echo "  堆内存: 4GB"
echo "  页面缓存: 2GB"
echo "  查询缓存: 1000条"
echo "  连接池: 最大400连接"
echo "  备份文件: $BACKUP_PATH"

echo -e "${GREEN}✅ Neo4j优化完成！${NC}"