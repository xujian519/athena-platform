#!/bin/bash
# Athena多模态文件系统启动脚本
# Multimodal File System Startup Script for Athena Platform

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
MULTIMODAL_API_PORT=8020
GLM_VISION_PORT=8091
MULTIMODAL_PROCESSOR_PORT=8012

# 日志目录
LOG_DIR="/Users/xujian/Athena工作平台/logs"
mkdir -p "$LOG_DIR"

# PID文件
PID_DIR="/tmp/athena_pids"
mkdir -p "$PID_DIR"

echo -e "${BLUE}🚀 启动Athena多模态文件系统${NC}"
echo "=================================="

# 检查Python环境
echo -e "${YELLOW}📋 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python环境检查通过${NC}"

# 检查必要的服务状态
check_service() {
    local service_name=$1
    local service_url=$2
    local port=$3

    echo -e "${YELLOW}🔍 检查 $service_name 服务 (端口: $port)...${NC}"

    if lsof -i :$port > /dev/null 2>&1; then
        echo -e "${GREEN}✅ $service_name 服务已运行 (端口: $port)${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  $service_name 服务未运行${NC}"
        return 1
    fi
}

# 启动服务
start_service() {
    local service_name=$1
    local start_command=$2
    local log_file=$3
    local pid_file=$4

    echo -e "${BLUE}🚀 启动 $service_name 服务...${NC}"

    # 检查服务是否已经运行
    if [ -f "$pid_file" ] && kill -0 $(cat "$pid_file") 2>/dev/null; then
        echo -e "${YELLOW}⚠️  $service_name 服务已在运行${NC}"
        return 0
    fi

    # 启动服务
    nohup bash -c "$start_command" > "$log_file" 2>&1 &
    local pid=$!
    echo $pid > "$pid_file"

    # 等待服务启动
    sleep 3

    # 验证服务是否启动成功
    if kill -0 $pid 2>/dev/null; then
        echo -e "${GREEN}✅ $service_name 服务启动成功 (PID: $pid)${NC}"
        return 0
    else
        echo -e "${RED}❌ $service_name 服务启动失败${NC}"
        rm -f "$pid_file"
        return 1
    fi
}

# 1. 检查多模态处理服务
echo -e "\n${YELLOW}📝 检查多模态处理服务...${NC}"
if check_service "多模态处理服务" "http://localhost:$MULTIMODAL_PROCESSOR_PORT" $MULTIMODAL_PROCESSOR_PORT; then
    echo -e "${GREEN}✅ 多模态处理服务已运行${NC}"
else
    echo -e "${YELLOW}⚠️  多模态处理服务未运行，请手动启动${NC}"
    echo -e "${YELLOW}   命令: python3 services/multimodal_processing_service.py${NC}"
fi

# 2. 检查GLM视觉服务
echo -e "\n${YELLOW}📝 检查GLM视觉服务...${NC}"
if check_service "GLM视觉服务" "http://localhost:$GLM_VISION_PORT" $GLM_VISION_PORT; then
    echo -e "${GREEN}✅ GLM视觉服务已运行${NC}"
else
    echo -e "${YELLOW}⚠️  GLM视觉服务未运行，启动中...${NC}"

    GLM_PID_FILE="$PID_DIR/glm_vision.pid"
    GLM_LOG_FILE="$LOG_DIR/glm_vision.log"

    cd /Users/xujian/Athena工作平台/services/ai-models/glm-full-suite
    start_service "GLM视觉服务" "python3 athena_glm_full_suite_server.py" "$GLM_LOG_FILE" "$GLM_PID_FILE"

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ GLM视觉服务启动成功${NC}"
    else
        echo -e "${RED}❌ GLM视觉服务启动失败${NC}"
    fi
fi

# 3. 启动统一API服务
echo -e "\n${YELLOW}📝 启动统一多模态API服务...${NC}"

UNIFIED_API_PID_FILE="$PID_DIR/unified_multimodal_api.pid"
UNIFIED_API_LOG_FILE="$LOG_DIR/unified_multimodal_api.log"

# 检查端口是否被占用
if lsof -i :$MULTIMODAL_API_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 $MULTIMODAL_API_PORT 已被占用${NC}"

    # 尝试杀掉占用端口的进程
    echo -e "${YELLOW}🔄 尝试清理端口...${NC}"
    lsof -ti :$MULTIMODAL_API_PORT | xargs kill -9 2>/dev/null || true
    sleep 2
fi

cd /Users/xujian/Athena工作平台
start_service "统一多模态API服务" "python3 services/unified_multimodal_api.py" "$UNIFIED_API_LOG_FILE" "$UNIFIED_API_PID_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 统一多模态API服务启动成功${NC}"
else
    echo -e "${RED}❌ 统一多模态API服务启动失败${NC}"
    echo -e "${RED}   查看日志: tail -f $UNIFIED_API_LOG_FILE${NC}"
    exit 1
fi

# 4. 验证所有服务
echo -e "\n${YELLOW}🔍 验证服务状态...${NC}"

# 等待服务完全启动
echo -e "${YELLOW}⏳ 等待服务完全启动...${NC}"
sleep 10

# 健康检查
echo -e "${YELLOW}📋 执行健康检查...${NC}"

# 检查统一API
echo -n "  📡 统一API服务: "
if curl -s http://localhost:$MULTIMODAL_API_PORT/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
else
    echo -e "${RED}❌ 不健康${NC}"
fi

# 检查GLM视觉
echo -n "  🤖 GLM视觉服务: "
if curl -s http://localhost:$GLM_VISION_PORT/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
else
    echo -e "${RED}❌ 不健康${NC}"
fi

# 检查多模态处理
echo -n "  🔄 多模态处理服务: "
if curl -s http://localhost:$MULTIMODAL_PROCESSOR_PORT/ > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 健康${NC}"
else
    echo -e "${RED}❌ 不健康${NC}"
fi

# 5. 显示访问信息
echo -e "\n${GREEN}🎉 多模态文件系统启动完成！${NC}"
echo "=================================="
echo -e "${BLUE}📋 服务信息:${NC}"
echo -e "  🔗 统一API服务: ${GREEN}http://localhost:$MULTIMODAL_API_PORT${NC}"
echo -e "  📚 API文档: ${GREEN}http://localhost:$MULTIMODAL_API_PORT/docs${NC}"
echo -e "  🤖 GLM视觉服务: ${GREEN}http://localhost:$GLM_VISION_PORT${NC}"
echo -e "  🔄 多模态处理: ${GREEN}http://localhost:$MULTIMODAL_PROCESSOR_PORT${NC}"

echo -e "\n${BLUE}📋 功能特性:${NC}"
echo -e "  📄 文档处理: ${GREEN}PDF、Word、文本${NC}"
echo -e "  🖼️  图像分析: ${GREEN}技术图纸、化学结构、OCR识别${NC}"
echo -e "  🎵 音频处理: ${GREEN}语音识别、音频转录${NC}"
echo -e "  🎬 视频分析: ${GREEN}视频帧提取、内容分析${NC}"
echo -e "  🧪 化学分析: ${GREEN}化学式识别、分子量计算${NC}"

echo -e "\n${BLUE}📋 日志文件:${NC}"
echo -e "  📝 统一API: ${YELLOW}$UNIFIED_API_LOG_FILE${NC}"
echo -e "  🤖 GLM视觉: ${YELLOW}$GLM_LOG_FILE${NC}"

echo -e "\n${BLUE}📋 管理命令:${NC}"
echo -e "  📊 查看状态: ${YELLOW}curl http://localhost:$MULTIMODAL_API_PORT/health${NC}"
echo -e "  📚 API文档: ${YELLOW}open http://localhost:$MULTIMODAL_API_PORT/docs${NC}"
echo -e "  🛑 停止服务: ${YELLOW}bash scripts/shutdown_multimodal_system.sh${NC}"

# 创建停止脚本
cat > /Users/xujian/Athena工作平台/scripts/shutdown_multimodal_system.sh << 'EOF'
#!/bin/bash
# Athena多模态文件系统停止脚本

echo "🛑 停止Athena多模态文件系统..."

PID_DIR="/tmp/athena_pids"

# 停止统一API
if [ -f "$PID_DIR/unified_multimodal_api.pid" ]; then
    kill $(cat "$PID_DIR/unified_multimodal_api.pid") 2>/dev/null || true
    rm -f "$PID_DIR/unified_multimodal_api.pid"
    echo "✅ 统一API服务已停止"
fi

# 停止GLM视觉服务
if [ -f "$PID_DIR/glm_vision.pid" ]; then
    kill $(cat "$PID_DIR/glm_vision.pid") 2>/dev/null || true
    rm -f "$PID_DIR/glm_vision.pid"
    echo "✅ GLM视觉服务已停止"
fi

echo "🎉 多模态文件系统已停止"
EOF

chmod +x /Users/xujian/Athena工作平台/scripts/shutdown_multimodal_system.sh

echo -e "\n${GREEN}✨ 多模态文件系统已成功部署到Athena平台！${NC}"
echo -e "${YELLOW}💡 提示: 使用 'bash scripts/shutdown_multimodal_system.sh' 停止所有服务${NC}"