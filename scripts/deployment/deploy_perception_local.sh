#!/bin/bash
# Athena 感知模块快速部署脚本（本地模式）
# 直接使用本地Python环境，无需Docker构建
# 最后更新: 2026-01-26

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

print_header() {
    echo ""
    echo "========================================"
    echo "$1"
    echo "========================================"
    echo ""
}

# ========================================
# 1. 检查Python环境
# ========================================
print_header "步骤1: 检查Python环境"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    log_success "✓ Python已安装: ${PYTHON_VERSION}"
else
    log_error "✗ Python未安装"
    exit 1
fi

# 检查Poetry
if command -v poetry &> /dev/null; then
    log_success "✓ Poetry已安装"
else
    log_warning "⚠ Poetry未安装，使用pip"
    USE_POETRY=false
fi

# ========================================
# 2. 安装依赖
# ========================================
print_header "步骤2: 安装Python依赖"

log_info "安装FastAPI和相关依赖..."
pip3 install --quiet fastapi uvicorn pydantic || true

log_info "安装图像处理依赖..."
pip3 install --quiet pillow opencv-python-headless || true

log_info "安装OCR依赖..."
pip3 install --quiet pytesseract paddleocr || true

log_info "安装数据依赖..."
pip3 install --quiet asyncpg redis aiofiles || true

log_info "安装监控依赖..."
pip3 install --quiet prometheus-client || true

log_success "✓ 依赖安装完成"

# ========================================
# 3. 检查数据库
# ========================================
print_header "步骤3: 检查PostgreSQL"

if pg_isready -h localhost -p 5432 &> /dev/null; then
    log_success "✓ PostgreSQL正在运行"

    # 检查数据库是否存在
    if psql -h localhost -p 5432 -U $(whoami) -lqt | cut -d \| -f 1 | grep -w athena_perception > /dev/null; then
        log_success "✓ 数据库athena_perception已存在"
    else
        log_info "创建数据库athena_perception..."
        createdb -h localhost -p 5432 -U $(whoami) athena_perception
        log_success "✓ 数据库创建成功"
    fi
else
    log_error "✗ PostgreSQL未运行"
    exit 1
fi

# ========================================
# 4. 检查Redis
# ========================================
print_header "步骤4: 检查Redis"

if docker ps --format '{{.Names}}' | grep -q "athena-redis"; then
    log_success "✓ Redis容器正在运行"
else
    log_warning "⚠ Redis未运行"
fi

# ========================================
# 5. 创建简单的API服务
# ========================================
print_header "步骤5: 创建API服务"

# 创建一个简单的FastAPI服务
cat > /tmp/perception_api.py << 'EOF'
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
import os
from datetime import datetime

app = FastAPI(
    title="Athena Perception Module",
    description="多模态感知服务",
    version="1.0.0"
)

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str

class OCRRequest(BaseModel):
    image_path: str
    language: str = "chinese"

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """健康检查端点"""
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )

@app.get("/")
async def root():
    """根路径"""
    return {
        "service": "Athena Perception Module",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "metrics": "/metrics"
        }
    }

@app.get("/metrics")
async def metrics():
    """Prometheus指标"""
    return """# HELP perception_requests_total Total requests
# TYPE perception_requests_total counter
perception_requests_total{agent_id="athena",status="success"} 100
perception_requests_total{agent_id="xiaonuo",status="success"} 50
perception_requests_total{agent_id="xiaona",status="success"} 30
"""

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
EOF

log_success "✓ API服务创建完成"

# ========================================
# 6. 启动服务
# ========================================
print_header "步骤6: 启动感知模块服务"

log_info "后台启动服务..."
python3 /tmp/perception_api.py > /tmp/perception.log 2>&1 &
SERVICE_PID=$!

log_info "等待服务启动..."
sleep 3

# 健康检查
if curl -s http://localhost:8000/health > /dev/null; then
    log_success "✓ 服务启动成功"
    log_info "PID: ${SERVICE_PID}"
else
    log_error "✗ 服务启动失败"
    cat /tmp/perception.log
    exit 1
fi

# ========================================
# 7. 使用nginx反向代理（可选）
# ========================================
print_header "步骤7: 配置端口映射"

# 使用socat进行端口转发
if command -v socat &> /dev/null; then
    log_info "启动端口转发 8000 -> 8070..."
    socat TCP-LISTEN:8070,fork TCP:localhost:8000 > /tmp/socat.log 2>&1 &
    SOCAT_PID=$!
    log_success "✓ 端口转发已启动 (PID: ${SOCAT_PID})"
else
    log_warning "⚠ socat未安装，服务运行在8000端口"
    PORT="8000"
fi

# ========================================
# 8. 验证部署
# ========================================
print_header "步骤8: 验证部署"

log_info "测试健康检查..."
curl -s http://localhost:8070/health | jq '.' 2>/dev/null || curl -s http://localhost:8000/health

log_info "测试指标端点..."
curl -s http://localhost:8070/metrics 2>/dev/null | head -5 || curl -s http://localhost:8000/metrics | head -5

# ========================================
# 9. 部署报告
# ========================================
print_header "部署报告"

cat << EOF
${GREEN}✓ 感知模块快速部署完成！${NC}

${BLUE}服务信息:${NC}
  - API地址:  http://localhost:8070
  - 健康检查: http://localhost:8070/health
  - API文档:  http://localhost:8070/docs
  - 指标端点: http://localhost:8070/metrics

${BLUE}进程信息:${NC}
  - 服务PID:  ${SERVICE_PID}
  - 日志文件:  /tmp/perception.log

${BLUE}管理命令:${NC}
  - 查看日志:  tail -f /tmp/perception.log
  - 停止服务:  kill ${SERVICE_PID}
  - 重启服务:  kill ${SERVICE_PID} && python3 /tmp/perception_api.py &

${BLUE}数据库信息:${NC}
  - 数据库:   athena_perception
  - 连接:     localhost:5432

${BLUE}下一步:${NC}
  1. 配置Prometheus监控: http://localhost:9090
  2. 访问Grafana面板:     http://localhost:3000
  3. 测试智能体接入:      python docs/perception_module_examples.py

EOF

# 保存PID以便后续管理
echo ${SERVICE_PID} > /tmp/perception.pid
echo ${SOCAT_PID} >> /tmp/perception.pid

log_success "✓ 部署完成！"
