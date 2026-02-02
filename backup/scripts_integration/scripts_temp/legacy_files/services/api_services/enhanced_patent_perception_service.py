#!/usr/bin/env python3
"""
增强专利感知服务
Enhanced Patent Perception Service
"""

import asyncio
import json
import logging
import signal
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

from core.perception.enhanced_patent_perception import EnhancedPatentPerceptionEngine
from core.perception.enhanced_patent_vector_search import EnhancedPatentVectorSearch
from core.perception.patent_llm_integration import PatentLLMConfig, PatentLLMIntegration

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/enhanced_patent_perception.log')
    ]
)

logger = logging.getLogger(__name__)

class EnhancedPatentPerceptionService:
    def __init__(self):
        self.perception_engine = None
        self.llm_integration = None
        self.vector_search = None
        self.running = False
        self.config = None

    async def initialize(self):
        """初始化服务"""
        logger.info('🚀 初始化增强专利感知服务')

        # 加载配置
        config_path = Path('/Users/xujian/Athena工作平台/config/perception/enhanced_patent_config.json')
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
        else:
            logger.warning('配置文件不存在，使用默认配置')
            self.config = {}

        # 初始化组件
        try:
            # 1. 初始化专利感知引擎
            self.perception_engine = EnhancedPatentPerceptionEngine(self.config)
            await self.perception_engine.initialize()

            # 2. 初始化大模型集成
            llm_config = PatentLLMConfig(**self.config.get('llm_config', {}))
            self.llm_integration = PatentLLMIntegration(llm_config)
            await self.llm_integration.initialize()

            # 3. 初始化向量检索
            vector_config = self.config.get('vector_search', {})
            self.vector_search = EnhancedPatentVectorSearch(vector_config)
            await self.vector_search.initialize()

            self.running = True
            logger.info('✅ 增强专利感知服务初始化完成')

        except Exception as e:
            logger.error(f"❌ 服务初始化失败: {e}")
            raise

    async def start_api_server(self):
        """启动API服务器"""
        from typing import List, Optional

        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel

        app = FastAPI(title='增强专利感知API', version='1.0.0')

        # 数据模型
        class PatentAnalysisRequest(BaseModel):
            patent_text: str
            analysis_type: str = 'comprehensive'
            patent_id: str | None = None
            language: str = 'zh-CN'

        class PatentSearchRequest(BaseModel):
            query_text: str
            search_mode: str = 'hybrid'
            limit: int = 10
            threshold: float = 0.7

        class PatentIndexRequest(BaseModel):
            patent_id: str
            title: str
            abstract: str
            technical_field: str | None = None

        @app.post('/api/analyze/patent')
        async def analyze_patent(request: PatentAnalysisRequest):
            """分析专利"""
            try:
                analysis_request = PatentAnalysisRequest(
                    patent_text=request.patent_text,
                    analysis_type=request.analysis_type,
                    patent_id=request.patent_id,
                    language=request.language
                )

                result = await self.llm_integration.analyze_patent(analysis_request)

                return {
                    'success': True,
                    'result': {
                        'patent_id': result.patent_id,
                        'analysis_type': result.analysis_type,
                        'technical_summary': result.technical_summary,
                        'novelty_assessment': result.novelty_assessment,
                        'patentability_score': result.patentability_score,
                        'confidence': result.confidence,
                        'processing_time': result.processing_time
                    }
                }

            except Exception as e:
                logger.error(f"专利分析API错误: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post('/api/search/patents')
        async def search_patents(request: PatentSearchRequest):
            """检索专利"""
            try:
                from core.perception.enhanced_patent_vector_search import (
                    PatentSearchQuery,
                    VectorSearchMode,
                )

                search_query = PatentSearchQuery(
                    query_text=request.query_text,
                    search_mode=VectorSearchMode(request.search_mode),
                    limit=request.limit,
                    threshold=request.threshold
                )

                results = await self.vector_search.search_patents(search_query)

                return {
                    'success': True,
                    'results': [
                        {
                            'patent_id': result.patent_id,
                            'title': result.title,
                            'abstract': result.abstract[:200] + '...' if len(result.abstract) > 200 else result.abstract,
                            'similarity_score': result.similarity_score,
                            'technical_field': result.technical_field,
                            'ranking_position': result.ranking_position
                        }
                        for result in results
                    ],
                    'total': len(results)
                }

            except Exception as e:
                logger.error(f"专利检索API错误: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post('/api/index/patent')
        async def index_patent(request: PatentIndexRequest):
            """索引专利"""
            try:
                success = await self.vector_search.index_patent(
                    patent_id=request.patent_id,
                    title=request.title,
                    abstract=request.abstract,
                    technical_field=request.technical_field
                )

                return {
                    'success': success,
                    'patent_id': request.patent_id
                }

            except Exception as e:
                logger.error(f"专利索引API错误: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get('/api/status')
        async def get_status():
            """获取服务状态"""
            try:
                perception_status = await self.perception_engine.get_status() if self.perception_engine else {'error': '未初始化'}
                llm_status = await self.llm_integration.get_model_info() if self.llm_integration else {'error': '未初始化'}
                search_status = await self.vector_search.get_statistics() if self.vector_search else {'error': '未初始化'}

                return {
                    'service_running': self.running,
                    'timestamp': datetime.now().isoformat(),
                    'components': {
                        'perception_engine': perception_status,
                        'llm_integration': llm_status,
                        'vector_search': search_status
                    }
                }

            except Exception as e:
                logger.error(f"状态查询API错误: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get('/')
        async def root():
            return {
                'service': '增强专利感知服务',
                'version': '1.0.0',
                'status': 'running',
                'timestamp': datetime.now().isoformat()
            }

        # 启动API服务器
        import uvicorn
        await uvicorn.run(app, host='0.0.0.0', port=8025, log_level='info')

    async def shutdown(self):
        """关闭服务"""
        logger.info('🔄 关闭增强专利感知服务')

        if self.vector_search:
            await self.vector_search.shutdown()
        if self.llm_integration:
            await self.llm_integration.shutdown()
        if self.perception_engine:
            await self.perception_engine.shutdown()

        self.running = False
        logger.info('✅ 增强专利感知服务已关闭')

async def main():
    """主函数"""
    logger.info('🚀 启动增强专利感知服务...')

    service = EnhancedPatentPerceptionService()

    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"\n⚠️ 收到信号 {signum}，正在关闭服务...")
        asyncio.create_task(service.shutdown())
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await service.initialize()
        await service.start_api_server()
    except KeyboardInterrupt:
        await service.shutdown()
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        await service.shutdown()
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
