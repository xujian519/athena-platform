#!/usr/bin/env python3
"""
简化的Athena API包装器
Simplified Athena API Wrapper

绕过Python 3.14兼容性问题，提供基础的Athena功能API
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入核心模块
try:
    from dotenv import load_dotenv
    load_dotenv()
    logger.info("✅ 环境变量加载成功")
except ImportError:
    logger.warning("⚠️  python-dotenv未安装，跳过环境变量加载")

# 导入Athena核心模块
import_success = False
athena_available = False

try:
    # 导入数据库连接模块
    from core.database.patent_data_connector import get_patent_data_connector
    logger.info("✅ 专利数据连接器加载成功")
    athena_available = True
except ImportError as e:
    logger.warning(f"⚠️  专利数据连接器加载失败: {e}")

try:
    # 导入知识图谱模块
    from core.kg.knowledge_graph_manager import get_knowledge_graph_manager
    logger.info("✅ 知识图谱管理器加载成功")
    athena_available = True
except ImportError as e:
    logger.warning(f"⚠️  知识图谱管理器加载失败: {e}")

try:
    # 导入NLP模块
    from core.nlp.nlp_service import get_nlp_service
    logger.info("✅ NLP服务加载成功")
    athena_available = True
except ImportError as e:
    logger.warning(f"⚠️  NLP服务加载失败: {e}")

# 检查是否有FastAPI
FASTAPI_AVAILABLE = False
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
    logger.info("✅ FastAPI可用")
except ImportError:
    logger.warning("⚠️  FastAPI不可用，将使用基础HTTP服务")


# API模型定义
if FASTAPI_AVAILABLE:
    class OCRRequest(BaseModel):
        file_path: str

    class NLPRequest(BaseModel):
        text: str
        task: Optional[str] = "analyze"

    class KGQueryRequest(BaseModel):
        query: str
        limit: Optional[int] = 10

    class VectorSearchRequest(BaseModel):
        query: str
        limit: Optional[int] = 10


# 创建应用
if FASTAPI_AVAILABLE:
    app = FastAPI(
        title="Athena简化API",
        description="简化的Athena平台API（绕过Python 3.14兼容性问题）",
        version="1.0.0-simplified"
    )

    # CORS中间件
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ==================== API端点 ====================

if FASTAPI_AVAILABLE:
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "name": "Athena简化API",
            "version": "1.0.0-simplified",
            "athena_available": athena_available,
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/health")
    async def health_check():
        """健康检查"""
        return {
            "status": "healthy",
            "athena_available": athena_available,
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/api/v1/status")
    async def status():
        """服务状态"""
        status_info = {
            "service": "athena_simplified",
            "version": "1.0.0-simplified",
            "athena_available": athena_available,
            "modules": {},
            "timestamp": datetime.now().isoformat()
        }

        # 检查各个模块
        try:
            from core.database.patent_data_connector import get_patent_data_connector
            status_info["modules"]["patent_db"] = "available"
        except:
            status_info["modules"]["patent_db"] = "unavailable"

        try:
            from core.kg.knowledge_graph_manager import get_knowledge_graph_manager
            status_info["modules"]["knowledge_graph"] = "available"
        except:
            status_info["modules"]["knowledge_graph"] = "unavailable"

        try:
            from core.nlp.nlp_service import get_nlp_service
            status_info["modules"]["nlp"] = "available"
        except:
            status_info["modules"]["nlp"] = "unavailable"

        try:
            from core.rag.rag_service import get_rag_service
            status_info["modules"]["rag"] = "available"
        except:
            status_info["modules"]["rag"] = "unavailable"

        return status_info

    @app.post("/api/v1/patent/search")
    async def patent_search(keyword: str, limit: int = 10):
        """专利搜索"""
        if not athena_available:
            raise HTTPException(status_code=503, detail="Athena服务不可用")

        try:
            from core.database.patent_data_connector import get_patent_data_connector
            connector = get_patent_data_connector()

            results = connector.search_patents(
                keyword=keyword,
                limit=limit
            )

            return {
                "success": True,
                "keyword": keyword,
                "count": len(results),
                "results": results
            }
        except Exception as e:
            logger.error(f"专利搜索失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/nlp/analyze")
    async def nlp_analyze(request: NLPRequest):
        """NLP分析"""
        if not athena_available:
            raise HTTPException(status_code=503, detail="Athena服务不可用")

        try:
            from core.nlp.nlp_service import get_nlp_service
            nlp_service = get_nlp_service()

            result = await nlp_service.analyze(
                text=request.text,
                task=request.task
            )

            return {
                "success": True,
                "task": request.task,
                "result": result
            }
        except Exception as e:
            logger.error(f"NLP分析失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/kg/query")
    async def kg_query(request: KGQueryRequest):
        """知识图谱查询"""
        if not athena_available:
            raise HTTPException(status_code=503, detail="Athena服务不可用")

        try:
            from core.kg.knowledge_graph_manager import get_knowledge_graph_manager
            kg_manager = get_knowledge_graph_manager()

            result = await kg_manager.query(
                cypher_query=request.query,
                limit=request.limit
            )

            return {
                "success": True,
                "query": request.query,
                "result": result
            }
        except Exception as e:
            logger.error(f"知识图谱查询失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/v1/vector/search")
    async def vector_search(request: VectorSearchRequest):
        """向量检索"""
        if not athena_available:
            raise HTTPException(status_code=503, detail="Athena服务不可用")

        try:
            from core.rag.rag_service import get_rag_service
            rag_service = get_rag_service()

            result = await rag_service.search(
                query=request.query,
                limit=request.limit
            )

            return {
                "success": True,
                "query": request.query,
                "result": result
            }
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            raise HTTPException(status_code=500, detail=str(e))


# ==================== 主函数 ====================

def main():
    """主函数"""
    print("=" * 60)
    print("🚀 Athena简化API服务")
    print("=" * 60)
    print()

    print(f"📅 启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🐍 Python版本: {sys.version}")
    print(f"📦 Athena可用: {athena_available}")
    print(f"🔧 FastAPI可用: {FASTAPI_AVAILABLE}")
    print()

    if not FASTAPI_AVAILABLE:
        print("❌ FastAPI不可用，无法启动API服务")
        print("   请安装FastAPI: pip install fastapi uvicorn")
        sys.exit(1)

    if not athena_available:
        print("⚠️  Athena模块未完全加载")
        print("   某些API端点可能不可用")
        print()

    print("✅ 服务配置:")
    print("   端口: 8000")
    print("   主机: 0.0.0.0")
    print("   API文档: http://localhost:8000/docs")
    print("   健康检查: http://localhost:8000/health")
    print()

    try:
        import uvicorn

        print("🚀 启动服务...")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  服务被中断")
    except Exception as e:
        print(f"\n\n❌ 服务启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
