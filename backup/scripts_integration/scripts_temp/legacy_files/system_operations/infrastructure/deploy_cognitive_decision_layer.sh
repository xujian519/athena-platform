#!/bin/bash

# 认知决策层部署脚本
# Cognitive Decision Layer Deployment Script
# Created by Athena + 小诺
# Date: 2025-12-05

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

# 项目配置
PROJECT_ROOT="/Users/xujian/Athena工作平台"
PATENT_WORKSPACE="${PROJECT_ROOT}/patent-platform/workspace"
COGNITION_DIR="${PATENT_WORKSPACE}/src/cognition"
API_DIR="${PATENT_WORKSPACE}/src/api"
PERCEPTION_DIR="${PATENT_WORKSPACE}/src/perception"
LOG_DIR="${PROJECT_ROOT}/logs"
PID_DIR="${PROJECT_ROOT}/pids"

# 创建必要目录
create_directories() {
    log_step "创建部署所需目录..."
    mkdir -p "${LOG_DIR}"
    mkdir -p "${PID_DIR}"
    mkdir -p "${PROJECT_ROOT}/data/knowledge_graphs"
    mkdir -p "${PROJECT_ROOT}/models/llm_cache"
    mkdir -p "${PROJECT_ROOT}/models/multimodal_cache"
    log_success "目录创建完成"
}

# 停止现有服务
stop_existing_services() {
    log_step "停止现有服务..."

    # 查找并停止相关进程
    pkill -f "simple_patent_api.py" || true
    pkill -f "enhanced_patent_feature_extractor.py" || true
    pkill -f "semantic_enhanced_feature_extractor.py" || true
    pkill -f "cognitive_integration_layer.py" || true
    pkill -f "large_language_model_integration.py" || true
    pkill -f "multimodal_patent_understanding.py" || true

    # 等待进程完全停止
    sleep 3

    log_success "现有服务停止完成"
}

# 检查依赖
check_dependencies() {
    log_step "检查系统依赖..."

    # 检查Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 未安装"
        exit 1
    fi

    # 检查必要的Python包
    python3 -c "
import sys
required_packages = [
    'torch', 'transformers', 'sentence_transformers',
    'networkx', 'numpy', 'pandas', 'asyncio',
    'uvicorn', 'fastapi', 'pydantic'
]
missing_packages = []
for package in required_packages:
    try:
        __import__(package)
    except ImportError:
        missing_packages.append(package)

if missing_packages:
    print(f'缺少依赖包: {missing_packages}')
    sys.exit(1)
else:
    print('所有依赖检查通过')
"

    if [ $? -ne 0 ]; then
        log_error "依赖检查失败，请安装缺少的包"
        exit 1
    fi

    log_success "依赖检查通过"
}

# 启动认知决策层主服务
start_cognitive_integration() {
    log_step "启动认知决策层集成服务..."

    cd "${COGNITION_DIR}"

    # 启动认知集成层服务
    nohup python3 -c "
import sys
sys.path.append('${COGNITION_DIR}')
from cognitive_integration_layer import cognitive_integration
import uvicorn
from fastapi import FastAPI
import asyncio

app = FastAPI(title='认知决策层API服务', version='2.0.0')

@app.post('/api/v2/cognitive/analyze')
async def analyze_patent(data: dict):
    '''专利认知分析接口'''
    from cognitive_integration_layer import CognitiveRequest, ProcessingMode
    import uuid

    request = CognitiveRequest(
        request_id=str(uuid.uuid4()),
        patent_data=data,
        processing_mode=ProcessingMode.BALANCED,
        task_type=data.get('task_type', 'patent_analysis')
    )

    result = await cognitive_integration.process_request(request)
    return {
        'success': True,
        'result': {
            'request_id': result.request_id,
            'decision': result.results.get('decision', '处理完成'),
            'confidence': result.confidence,
            'summary': result.summary,
            'recommendations': result.recommendations,
            'modules_used': result.modules_used,
            'processing_time': result.processing_time
        }
    }

@app.get('/api/v2/cognitive/status')
async def get_status():
    '''获取系统状态'''
    status = cognitive_integration.get_system_status()
    return {
        'success': True,
        'status': status,
        'timestamp': '2025-12-05T17:20:00Z'
    }

@app.get('/api/v2/cognitive/health')
async def health_check():
    '''健康检查'''
    return {
        'status': 'healthy',
        'service': 'cognitive_integration',
        'version': '2.0.0'
    }

if __name__ == '__main__':
    print('🚀 启动认知决策层集成服务...')
    uvicorn.run(app, host='0.0.0.0', port=8080, log_level='info')
" > "${LOG_DIR}/cognitive_integration.log" 2>&1 &

    COGNITIVE_PID=$!
    echo $COGNITIVE_PID > "${PID_DIR}/cognitive_integration.pid"

    log_success "认知决策层服务启动完成 (PID: $COGNITIVE_PID, Port: 8080)"
}

# 启动增强专利API服务
start_enhanced_api() {
    log_step "启动增强专利API服务..."

    cd "${API_DIR}"

    # 创建增强版API
    cat > enhanced_patent_api.py << 'EOF'
#!/usr/bin/env python3
"""
增强专利API服务
Enhanced Patent API Service
"""

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import sys
import os
from datetime import datetime

# 添加认知层路径
sys.path.append('/Users/xujian/Athena工作平台/patent-platform/workspace/src/cognition')

app = FastAPI(
    title="增强专利分析API",
    description="集成认知决策层的专利分析服务",
    version="2.0.0"
)

# 数据模型
class PatentAnalysisRequest(BaseModel):
    patent_id: str
    title: str
    abstract: str
    description: Optional[str] = ""
    claims: Optional[str] = ""
    task_type: Optional[str] = "comprehensive_analysis"
    processing_mode: Optional[str] = "balanced"

class PatentAnalysisResponse(BaseModel):
    success: bool
    patent_id: str
    analysis_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    timestamp: str

# 全局认知集成客户端
cognitive_client = None

async def get_cognitive_client():
    global cognitive_client
    if cognitive_client is None:
        try:
            from cognitive_integration_layer import CognitiveIntegrationLayer
            cognitive_client = CognitiveIntegrationLayer()
        except Exception as e:
            print(f"认知层初始化失败: {e}")
            cognitive_client = None
    return cognitive_client

@app.get("/")
async def root():
    return {
        "message": "增强专利分析API服务",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "智能专利分析",
            "认知决策集成",
            "多模态理解",
            "大模型对话",
            "知识图谱"
        ]
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "service": "enhanced_patent_api",
        "version": "2.0.0",
        "cognitive_layer": "connected" if cognitive_client else "disconnected"
    }

@app.post("/api/v2/analyze", response_model=PatentAnalysisResponse)
async def analyze_patent(request: PatentAnalysisRequest):
    """专利分析主接口"""
    try:
        # 获取认知客户端
        client = await get_cognitive_client()
        if not client:
            raise HTTPException(status_code=503, detail="认知决策层服务不可用")

        # 构建专利数据
        patent_data = {
            "patent_id": request.patent_id,
            "title": request.title,
            "text": f"{request.abstract}\n\n{request.description or ''}\n\n{request.claims or ''}",
            "abstract": request.abstract,
            "claims": request.claims,
            "timestamp": datetime.now().isoformat()
        }

        # 处理请求
        from cognitive_integration_layer import CognitiveRequest, ProcessingMode

        processing_mode = ProcessingMode.BALANCED
        if request.processing_mode == "fast":
            processing_mode = ProcessingMode.FAST
        elif request.processing_mode == "comprehensive":
            processing_mode = ProcessingMode.COMPREHENSIVE

        cognitive_request = CognitiveRequest(
            request_id=f"api_{request.patent_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            patent_data=patent_data,
            processing_mode=processing_mode,
            task_type=request.task_type
        )

        result = await client.process_request(cognitive_request)

        return PatentAnalysisResponse(
            success=True,
            patent_id=request.patent_id,
            analysis_result={
                "decision": result.results.get('decision', '分析完成'),
                "confidence": result.confidence,
                "summary": result.summary,
                "recommendations": result.recommendations,
                "modules_used": result.modules_used,
                "processing_time": result.processing_time,
                "detailed_results": result.results
            },
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        return PatentAnalysisResponse(
            success=False,
            patent_id=request.patent_id,
            error_message=str(e),
            timestamp=datetime.now().isoformat()
        )

@app.get("/api/v2/status")
async def get_system_status():
    """获取系统状态"""
    client = await get_cognitive_client()
    status = {
        "api_service": "running",
        "cognitive_layer": "connected" if client else "disconnected",
        "timestamp": datetime.now().isoformat()
    }

    if client:
        try:
            cognitive_status = client.get_system_status()
            status["cognitive_status"] = cognitive_status
        except Exception as e:
            status["cognitive_error"] = str(e)

    return {"success": True, "status": status}

if __name__ == "__main__":
    print("🚀 启动增强专利API服务...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
EOF

    # 启动API服务
    nohup python3 enhanced_patent_api.py > "${LOG_DIR}/enhanced_api.log" 2>&1 &

    API_PID=$!
    echo $API_PID > "${PID_DIR}/enhanced_api.pid"

    log_success "增强专利API服务启动完成 (PID: $API_PID, Port: 8000)"
}

# 启动前端服务
start_frontend() {
    log_step "启动前端服务..."

    cd "${PROJECT_ROOT}"

    # 创建简单的前端页面
    cat > patent_frontend.html << 'EOF'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能专利分析系统</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }

        .container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        h1 {
            text-align: center;
            margin-bottom: 30px;
            font-size: 2.5em;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .status-card {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 20px;
            margin: 20px 0;
            border-left: 5px solid #4CAF50;
        }

        .feature-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }

        .feature-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 15px;
            padding: 25px;
            text-align: center;
            transition: transform 0.3s ease;
        }

        .feature-card:hover {
            transform: translateY(-5px);
        }

        .feature-icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .api-test {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 15px;
            padding: 30px;
            margin: 30px 0;
        }

        .form-group {
            margin: 20px 0;
        }

        label {
            display: block;
            margin-bottom: 5px;
            font-weight: bold;
        }

        input, textarea, select {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            font-size: 16px;
        }

        button {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 18px;
            cursor: pointer;
            transition: background 0.3s ease;
        }

        button:hover {
            background: linear-gradient(45deg, #45a049, #4CAF50);
        }

        .result {
            background: rgba(255, 255, 255, 0.9);
            color: #333;
            border-radius: 10px;
            padding: 20px;
            margin: 20px 0;
            white-space: pre-wrap;
        }

        .loading {
            text-align: center;
            padding: 20px;
            font-size: 18px;
        }

        .error {
            background: rgba(244, 67, 54, 0.2);
            border-left: 5px solid #f44336;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }

        .success {
            background: rgba(76, 175, 80, 0.2);
            border-left: 5px solid #4CAF50;
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🧠 智能专利分析系统</h1>
        <div class="status-card">
            <h2>🚀 系统状态</h2>
            <div id="systemStatus">正在检查系统状态...</div>
        </div>

        <div class="feature-grid">
            <div class="feature-card">
                <div class="feature-icon">🤖</div>
                <h3>智能特征提取</h3>
                <p>基于BERT的深度语义理解</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">⚖️</div>
                <h3>法律推理</h3>
                <p>专业的专利法律规则推理</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🔄</div>
                <h3>混合推理</h3>
                <p>规则与神经网络深度结合</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🗺️</div>
                <h3>知识图谱</h3>
                <p>动态更新的专利知识网络</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">💬</div>
                <h3>大模型集成</h3>
                <p>专业的大语言模型对话</p>
            </div>
            <div class="feature-card">
                <div class="feature-icon">🖼️</div>
                <h3>多模态理解</h3>
                <p>图像、公式、表格智能分析</p>
            </div>
        </div>

        <div class="api-test">
            <h2>🧪 专利分析测试</h2>
            <form id="analysisForm">
                <div class="form-group">
                    <label for="patentId">专利号:</label>
                    <input type="text" id="patentId" value="TEST202412001" required>
                </div>

                <div class="form-group">
                    <label for="patentTitle">专利标题:</label>
                    <input type="text" id="patentTitle" value="基于人工智能的专利审查方法" required>
                </div>

                <div class="form-group">
                    <label for="patentAbstract">专利摘要:</label>
                    <textarea id="patentAbstract" rows="4" required>本发明公开了一种基于人工智能的专利审查方法，包括以下步骤：1. 获取待审查专利文本；2. 使用自然语言处理技术提取专利特征；3. 基于机器学习模型进行新颖性判断；4. 输出审查结果和修改建议。该方法提高了专利审查的效率和准确性。</textarea>
                </div>

                <div class="form-group">
                    <label for="processingMode">处理模式:</label>
                    <select id="processingMode">
                        <option value="fast">快速模式 (仅规则推理)</option>
                        <option value="balanced" selected>平衡模式 (规则+AI)</option>
                        <option value="comprehensive">全面模式 (所有模块)</option>
                    </select>
                </div>

                <button type="submit">开始分析</button>
            </form>

            <div id="analysisResult"></div>
        </div>
    </div>

    <script>
        // 检查系统状态
        async function checkSystemStatus() {
            try {
                const response = await fetch('/api/v2/status');
                const data = await response.json();

                if (data.success) {
                    document.getElementById('systemStatus').innerHTML = `
                        <div class="success">✅ 系统运行正常</div>
                        <p>API服务: ${data.status.api_service}</p>
                        <p>认知层: ${data.status.cognitive_layer}</p>
                        <p>更新时间: ${data.status.timestamp}</p>
                    `;
                } else {
                    document.getElementById('systemStatus').innerHTML = `
                        <div class="error">❌ 系统状态异常</div>
                    `;
                }
            } catch (error) {
                document.getElementById('systemStatus').innerHTML = `
                    <div class="error">❌ 无法连接到服务器</div>
                `;
            }
        }

        // 提交分析请求
        document.getElementById('analysisForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const resultDiv = document.getElementById('analysisResult');
            resultDiv.innerHTML = '<div class="loading">🔄 正在分析中，请稍候...</div>';

            const requestData = {
                patent_id: document.getElementById('patentId').value,
                title: document.getElementById('patentTitle').value,
                abstract: document.getElementById('patentAbstract').value,
                processing_mode: document.getElementById('processingMode').value
            };

            try {
                const response = await fetch('/api/v2/analyze', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(requestData)
                });

                const result = await response.json();

                if (result.success) {
                    const analysis = result.analysis_result;
                    resultDiv.innerHTML = `
                        <div class="success">✅ 分析完成</div>
                        <div class="result">
<b>📊 分析结果:</b>

<b>专利ID:</b> ${result.patent_id}
<b>处理时间:</b> ${analysis.processing_time.toFixed(2)}秒
<b>置信度:</b> ${(analysis.confidence * 100).toFixed(1)}%

<b>决策结果:</b> ${analysis.decision}

<b>🧠 使用的模块:</b> ${analysis.modules_used.join(', ')}

<b>📝 分析总结:</b> ${analysis.summary}

<b>💡 建议:</b> ${analysis.recommendations.map(rec => `• ${rec}`).join('\n')}

<b>⏰ 时间戳:</b> ${result.timestamp}
                        </div>
                    `;
                } else {
                    resultDiv.innerHTML = `
                        <div class="error">❌ 分析失败: ${result.error_message}</div>
                    `;
                }
            } catch (error) {
                resultDiv.innerHTML = `
                    <div class="error">❌ 请求失败: ${error.message}</div>
                `;
            }
        });

        // 页面加载时检查状态
        checkSystemStatus();

        // 每30秒更新一次状态
        setInterval(checkSystemStatus, 30000);
    </script>
</body>
</html>
EOF

    # 使用Python启动简单的HTTP服务器提供前端
    nohup python3 -m http.server 3000 > "${LOG_DIR}/frontend.log" 2>&1 &

    FRONTEND_PID=$!
    echo $FRONTEND_PID > "${PID_DIR}/frontend.pid"

    log_success "前端服务启动完成 (PID: $FRONTEND_PID, Port: 3000)"
}

# 等待服务启动
wait_for_services() {
    log_step "等待服务启动..."

    # 等待API服务
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API服务启动完成"
            break
        fi
        sleep 2
    done

    # 等待认知层服务
    for i in {1..30}; do
        if curl -s http://localhost:8080/api/v2/cognitive/health > /dev/null 2>&1; then
            log_success "认知层服务启动完成"
            break
        fi
        sleep 2
    done

    # 等待前端服务
    for i in {1..10}; do
        if curl -s http://localhost:3000 > /dev/null 2>&1; then
            log_success "前端服务启动完成"
            break
        fi
        sleep 1
    done
}

# 显示部署信息
show_deployment_info() {
    log_step "部署完成！"

    echo ""
    echo -e "${CYAN}🚀 认知决策层部署信息${NC}"
    echo -e "${CYAN}================================${NC}"
    echo ""
    echo -e "${GREEN}📋 服务状态:${NC}"
    echo "  • 认知决策层服务: http://localhost:8080"
    echo "  • 增强专利API服务: http://localhost:8000"
    echo "  • 前端界面: http://localhost:3000"
    echo ""
    echo -e "${GREEN}🔧 管理命令:${NC}"
    echo "  • 查看API日志: tail -f ${LOG_DIR}/enhanced_api.log"
    echo "  • 查看认知层日志: tail -f ${LOG_DIR}/cognitive_integration.log"
    echo "  • 停止服务: bash ${PROJECT_ROOT}/scripts/stop_cognitive_services.sh"
    echo ""
    echo -e "${GREEN}📖 API文档:${NC}"
    echo "  • API健康检查: http://localhost:8000/health"
    echo "  • 系统状态: http://localhost:8000/api/v2/status"
    echo "  • 认知层状态: http://localhost:8080/api/v2/cognitive/status"
    echo ""
    echo -e "${YELLOW}💡 使用建议:${NC}"
    echo "  1. 首先访问 http://localhost:3000 查看系统界面"
    echo "  2. 使用测试功能验证系统工作正常"
    echo "  3. 通过API接口进行批量专利分析"
    echo ""
}

# 主函数
main() {
    echo -e "${CYAN}"
    echo "=================================================="
    echo "    🧠 认知决策层部署脚本"
    echo "    Cognitive Decision Layer Deployment"
    echo "    Created by Athena + 小诺"
    echo "    Date: 2025-12-05"
    echo "=================================================="
    echo -e "${NC}"

    create_directories
    stop_existing_services
    check_dependencies
    start_cognitive_integration
    start_enhanced_api
    start_frontend
    wait_for_services
    show_deployment_info

    echo -e "${GREEN}🎉 部署完成！认知决策层已成功上线！${NC}"
}

# 执行主函数
main "$@"