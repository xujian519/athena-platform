#!/bin/bash
# 测试所有API接口

echo "🧪 测试Athena工作平台所有API接口..."
echo "================================"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local name=$1
    local url=$2
    local expected=$3

    echo -e "${YELLOW}测试 $name...${NC}"

    response=$(curl -s "$url" 2>/dev/null)

    if [ $? -eq 0 ]; then
        if echo "$response" | grep -q "$expected"; then
            echo -e "${GREEN}✅ $name: 正常${NC}"
            echo "$response" | jq '.' 2>/dev/null | head -n 10 || echo "$response" | head -n 5
        else
            echo -e "${RED}❌ $name: 响应异常${NC}"
            echo "$response"
        fi
    else
        echo -e "${RED}❌ $name: 无法连接${NC}"
    fi
    echo ""
}

# 测试基础服务
echo -e "${BLUE}📊 基础服务检查:${NC}"
echo ""

# 1. AI模型服务 (端口8082)
test_api "AI模型服务" "http://localhost:8082/" "AI Models Service Gateway"

# 2. AI模型服务健康检查
test_api "AI模型健康检查" "http://localhost:8082/health" "status"

# 3. AI模型服务模型列表
test_api "AI模型列表" "http://localhost:8082/models" "models"

# 4. Athena搜索服务 (端口8008)
test_api "Athena搜索服务" "http://localhost:8008/" "Athena Iterative Search"

# 5. Athena搜索健康检查
test_api "Athena搜索健康检查" "http://localhost:8008/health" "healthy"

# 6. YunPat Web服务 (端口8020)
test_api "YunPat Web服务" "http://localhost:8020/docs" "swagger"

# 7. YunPat Agent API (端口8087)
test_api "YunPat Agent API" "http://localhost:8087/" "YunPat Agent API"

# 8. YunPat Agent健康检查
test_api "YunPat Agent健康检查" "http://localhost:8087/api/v2/health" "ok"

# 9. YunPat Agent信息
test_api "云熙信息" "http://localhost:8087/api/v1/info" "云熙"

# 10. Ollama服务 (端口11434)
test_api "Ollama服务" "http://localhost:11434/api/tags" "models"

# 测试API功能
echo -e "${BLUE}🔧 API功能测试:${NC}"
echo ""

# 测试专利搜索
test_api "专利搜索功能" "http://localhost:8087/api/v1/patent/search" \
      "-d '{\"query\": \"人工智能\"}'"

# 测试专利分析
test_api "专利分析功能" "http://localhost:8087/api/v1/patent/analyze" \
      "-d '{\"patent_id\": \"CN202312345678\"}'"

# 测试搜索功能
test_api "Athena搜索功能" "http://localhost:8008/api/v1/search" \
      "-d '{\"query\": \"机器学习\"}'"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}✨ API测试完成！${NC}"
echo ""
echo -e "${BLUE}📋 API文档地址:${NC}"
echo "  - AI模型服务:    http://localhost:8082/docs"
echo "  - YunPat Web:     http://localhost:8020/docs"
echo "  - YunPat API:     http://localhost:8087/docs"
echo ""
echo -e "${BLUE}💡 快速测试命令:${NC}"
echo "  curl http://localhost:8082/"
echo "  curl http://localhost:8087/api/v2/health"
echo "  curl http://localhost:8008/health"