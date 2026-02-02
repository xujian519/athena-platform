#!/bin/bash
# Dolphin文档解析服务启动脚本
# Dolphin Document Parser Service Startup Script for Athena Platform

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置
DOLPHIN_PORT=8013
SERVICE_NAME="Dolphin文档解析服务"

# 日志目录
LOG_DIR="/Users/xujian/Athena工作平台/logs"
mkdir -p "$LOG_DIR"

# PID文件
PID_DIR="/tmp/athena_pids"
mkdir -p "$PID_DIR"

# 临时目录
TEMP_DIRS="/tmp/dolphin_uploads /tmp/dolphin_processed /tmp/dolphin_cache"
for dir in $TEMP_DIRS; do
    mkdir -p "$dir"
done

echo -e "${BLUE}🚀 启动$SERVICE_NAME${NC}"
echo "=================================="

# 检查Python环境
echo -e "${YELLOW}📋 检查Python环境...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3未安装${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python环境检查通过${NC}"

# 检查依赖包
echo -e "${YELLOW}📦 检查依赖包...${NC}"
REQUIRED_PACKAGES=(
    "layoutparser"
    "paddleocr"
    "pdfplumber"
    "PyMuPDF"
    "opencv-python"
    "fastapi"
    "uvicorn"
)

MISSING_PACKAGES=()
for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${YELLOW}⚠️  缺少以下依赖包: ${MISSING_PACKAGES[*]}${NC}"
    echo -e "${YELLOW}   正在安装...${NC}"

    for package in "${MISSING_PACKAGES[@]}"; do
        echo -e "${YELLOW}   安装 $package...${NC}"
        pip3 install "$package" 2>/dev/null || {
            echo -e "${RED}❌ 安装 $package 失败${NC}"
            exit 1
        }
    done

    echo -e "${GREEN}✅ 依赖包安装完成${NC}"
else
    echo -e "${GREEN}✅ 所有依赖包已安装${NC}"
fi

# 检查端口占用
echo -e "${YELLOW}🔍 检查端口占用...${NC}"
if lsof -i :$DOLPHIN_PORT > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  端口 $DOLPHIN_PORT 已被占用${NC}"
    echo -e "${YELLOW}🔄 尝试清理端口...${NC}"

    # 杀掉占用端口的进程
    lsof -ti :$DOLPHIN_PORT | xargs kill -9 2>/dev/null || true
    sleep 2

    if lsof -i :$DOLPHIN_PORT > /dev/null 2>&1; then
        echo -e "${RED}❌ 无法清理端口 $DOLPHIN_PORT${NC}"
        exit 1
    else
        echo -e "${GREEN}✅ 端口清理成功${NC}"
    fi
else
    echo -e "${GREEN}✅ 端口 $DOLPHIN_PORT 可用${NC}"
fi

# 检查服务是否已经运行
DOLPHIN_PID_FILE="$PID_DIR/dolphin_parser.pid"
if [ -f "$DOLPHIN_PID_FILE" ]; then
    EXISTING_PID=$(cat "$DOLPHIN_PID_FILE")
    if kill -0 $EXISTING_PID 2>/dev/null; then
        echo -e "${YELLOW}⚠️  $SERVICE_NAME 已在运行 (PID: $EXISTING_PID)${NC}"
        echo -e "${YELLOW}   是否要重启服务? (y/N)${NC}"
        read -r response
        if [[ "$response" =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}🔄 停止现有服务...${NC}"
            kill $EXISTING_PID 2>/dev/null || true
            sleep 2
        else
            echo -e "${GREEN}✅ 服务继续运行${NC}"
            exit 0
        fi
    fi
fi

# 切换到服务目录
cd /Users/xujian/Athena工作平台/services

# 启动Dolphin服务
echo -e "${BLUE}🚀 启动$SERVICE_NAME...${NC}"

DOLPHIN_LOG_FILE="$LOG_DIR/dolphin_parser.log"

# 启动服务
nohup python3 dolphin_parser_service.py > "$DOLPHIN_LOG_FILE" 2>&1 &
DOLPHIN_PID=$!

# 保存PID
echo $DOLPHIN_PID > "$DOLPHIN_PID_FILE"

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 5

# 验证服务是否启动成功
if kill -0 $DOLPHIN_PID 2>/dev/null; then
    echo -e "${GREEN}✅ $SERVICE_NAME 启动成功 (PID: $DOLPHIN_PID)${NC}"

    # 健康检查
    echo -e "${YELLOW}🔍 执行健康检查...${NC}"
    sleep 3

    if curl -s http://localhost:$DOLPHIN_PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 健康检查通过${NC}"

        # 获取服务状态
        HEALTH_RESPONSE=$(curl -s http://localhost:$DOLPHIN_PORT/health 2>/dev/null)
        echo -e "${BLUE}📊 服务状态:${NC}"
        echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"

    else
        echo -e "${YELLOW}⚠️  健康检查失败，服务可能仍在启动中${NC}"
        echo -e "${YELLOW}   请稍后手动检查: curl http://localhost:$DOLPHIN_PORT/health${NC}"
    fi

else
    echo -e "${RED}❌ $SERVICE_NAME 启动失败${NC}"
    echo -e "${RED}   请查看日志: tail -f $DOLPHIN_LOG_FILE${NC}"
    rm -f "$DOLPHIN_PID_FILE"
    exit 1
fi

# 显示访问信息
echo -e "\n${GREEN}🎉 $SERVICE_NAME 启动完成！${NC}"
echo "=================================="
echo -e "${BLUE}📋 服务信息:${NC}"
echo -e "  🔗 服务地址: ${GREEN}http://localhost:$DOLPHIN_PORT${NC}"
echo -e "  📚 API文档: ${GREEN}http://localhost:$DOLPHIN_PORT/docs${NC}"
echo -e "  🔍 健康检查: ${GREEN}http://localhost:$DOLPHIN_PORT/health${NC}"

echo -e "\n${BLUE}📋 功能特性:${NC}"
echo -e "  📄 PDF解析: ${GREEN}多页PDF文档处理${NC}"
echo -e "  🖼️  图像OCR: ${GREEN}中英文文字识别${NC}"
echo -e "  📐 版面分析: ${GREEN}标题、段落、表格、图表识别${NC}"
echo -e "  📋 文档结构化: ${GREEN}智能内容分类和组织${NC}"

echo -e "\n${BLUE}📋 支持格式:${NC}"
echo -e "  📄 文档: ${GREEN}PDF, DOCX${NC}"
echo -e "  🖼️  图像: ${GREEN}JPG, PNG, TIFF, BMP${NC}"

echo -e "\n${BLUE}📋 管理命令:${NC}"
echo -e "  📊 查看状态: ${YELLOW}curl http://localhost:$DOLPHIN_PORT/stats${NC}"
echo -e "  📚 API文档: ${YELLOW}open http://localhost:$DOLPHIN_PORT/docs${NC}"
echo -e "  📝 查看日志: ${YELLOW}tail -f $DOLPHIN_LOG_FILE${NC}"
echo -e "  🛑 停止服务: ${YELLOW}bash scripts/shutdown_dolphin_service.sh${NC}"

echo -e "\n${BLUE}📋 使用示例:${NC}"
echo -e "  📄 解析文档:"
echo -e "  ${YELLOW}curl -X POST -F \"file=@document.pdf\" http://localhost:$DOLPHIN_PORT/parse${NC}"

# 创建停止脚本
cat > /Users/xujian/Athena工作平台/scripts/shutdown_dolphin_service.sh << 'EOF'
#!/bin/bash
# Dolphin文档解析服务停止脚本

echo "🛑 停止Dolphin文档解析服务..."

PID_DIR="/tmp/athena_pids"
DOLPHIN_PID_FILE="$PID_DIR/dolphin_parser.pid"

if [ -f "$DOLPHIN_PID_FILE" ]; then
    DOLPHIN_PID=$(cat "$DOLPHIN_PID_FILE")
    if kill -0 $DOLPHIN_PID 2>/dev/null; then
        echo "停止服务 (PID: $DOLPHIN_PID)..."
        kill $DOLPHIN_PID 2>/dev/null || true

        # 等待进程结束
        sleep 3

        # 强制杀死（如果还在运行）
        if kill -0 $DOLPHIN_PID 2>/dev/null; then
            echo "强制停止服务..."
            kill -9 $DOLPHIN_PID 2>/dev/null || true
        fi

        echo "✅ Dolphin文档解析服务已停止"
    else
        echo "⚠️  服务进程不存在"
    fi

    rm -f "$DOLPHIN_PID_FILE"
else
    echo "⚠️  PID文件不存在，服务可能未运行"
fi

# 清理临时目录
echo "🧹 清理临时目录..."
TEMP_DIRS="/tmp/dolphin_uploads /tmp/dolphin_processed /tmp/dolphin_cache"
for dir in $TEMP_DIRS; do
    if [ -d "$dir" ]; then
        rm -rf "$dir"/*
        echo "✅ 清理 $dir"
    fi
done

echo "🎉 清理完成"
EOF

chmod +x /Users/xujian/Athena工作平台/scripts/shutdown_dolphin_service.sh

echo -e "\n${GREEN}✨ Dolphin文档解析服务已成功部署到Athena平台！${NC}"
echo -e "${YELLOW}💡 提示: 使用 'bash scripts/shutdown_dolphin_service.sh' 停止服务${NC}"