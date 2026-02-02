#!/usr/bin/env python3
"""
修复版增强专利感知服务
"""

import asyncio
import json
import logging
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 添加项目路径
sys.path.append('/Users/xujian/Athena工作平台')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/tmp/enhanced_patent_perception_simple.log')
    ]
)

logger = logging.getLogger(__name__)

class SimplePatentPerceptionService:
    def __init__(self):
        self.running = False
        self.patent_cache = {}
        self.analysis_results = {}

    def analyze_patent_text(self, patent_text: str, patent_id: str = None, analysis_type: str = 'comprehensive') -> Dict[str, Any]:
        """分析专利文本"""
        logger.info(f"分析专利文本: {patent_id or 'unknown'} - {analysis_type}")

        try:
            # 简单的基于规则的分析
            analysis = {
                'patent_id': patent_id,
                'analysis_type': analysis_type,
                'technical_summary': self._extract_technical_summary(patent_text),
                'novelty_assessment': self._assess_novelty(patent_text),
                'patentability_score': self._calculate_patentability_score(patent_text),
                'key_features': self._extract_key_features(patent_text),
                'potential_issues': self._identify_potential_issues(patent_text),
                'recommendations': self._generate_recommendations(patent_text),
                'confidence': 0.8,
                'processing_time': 0.1
            }

            return analysis

        except Exception as e:
            logger.error(f"专利文本分析失败: {e}")
            return {
                'patent_id': patent_id,
                'error': str(e),
                'confidence': 0.0
            }

    def _extract_technical_summary(self, text: str) -> str:
        """提取技术摘要"""
        # 简单的技术摘要提取
        sentences = text.split('。')
        technical_sentences = []

        for sentence in sentences[:5]:  # 取前5句
            if any(keyword in sentence for keyword in ['技术', '方案', '系统', '方法', '结构', '装置', '实现', '采用']):
                technical_sentences.append(sentence.strip())

        return '。'.join(technical_sentences) if technical_sentences else text[:200]

    def _assess_novelty(self, text: str) -> str:
        """评估新颖性"""
        novelty_indicators = ['新', '首创', '创新', '突破', '独特', '先进']
        existing_indicators = ['现有', '已知', '常规', '传统']

        novelty_score = 0
        for indicator in novelty_indicators:
            if indicator in text:
                novelty_score += 1

        for indicator in existing_indicators:
            if indicator in text:
                novelty_score -= 0.5

        if novelty_score >= 3:
            return '高新颖性'
        elif novelty_score >= 1:
            return '中等新颖性'
        else:
            return '低新颖性'

    def _calculate_patentability_score(self, text: str) -> float:
        """计算专利性评分"""
        # 简化的评分算法
        score = 0.0

        # 技术特征关键词
        tech_keywords = ['技术方案', '创新点', '技术效果', '技术优势', '应用前景']
        for keyword in tech_keywords:
            if keyword in text:
                score += 0.2

        # 问题解决关键词
        problem_keywords = ['解决', '克服', '改善', '优化', '提升', '降低']
        for keyword in problem_keywords:
            if keyword in text:
                score += 0.3

        # 法律术语
        legal_keywords = ['权利要求', '保护范围', '知识产权', '法律保护']
        for keyword in legal_keywords:
            if keyword in text:
                score += 0.2

        return min(1.0, score)

    def _extract_key_features(self, text: str) -> List[str]:
        """提取关键特征"""
        features = []

        # 提取技术特征模式
        patterns = [
            r'([^，。；:\n]*?包括[:：]\s*([^，。；:\n]*?(?=[，。；:\n]|$)))',
            r'([^，。；:\n]*?具有[:：]\s*([^，。；:\n]*?(?=[，。；:\n]|$)))',
            r'([^，。；:\n]*?设置[:：]\s*([^，。；:\n]*?(?=[，。；:\n]|$)))',
        ]

        import re
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                if isinstance(match, tuple):
                    feature = ''.join(match).strip()
                else:
                    feature = match.strip()
                if len(feature) > 3:
                    features.append(feature)

        return features[:10]  # 限制数量

    def _identify_potential_issues(self, text: str) -> List[str]:
        """识别潜在问题"""
        issues = []

        # 检查常见问题
        if len(text) < 100:
            issues.append('描述过于简短，可能无法满足专利申请要求')

        if not any(keyword in text for keyword in ['权利要求', '技术方案', '创新点']):
            issues.append('缺少明确的技术方案描述')

        if text.count('，') < 5:
            issues.append('技术细节描述不够详细')

        return issues

    def _generate_recommendations(self, text: str) -> List[str]:
        """生成建议"""
        recommendations = []

        # 基于文本分析提供建议
        if len(text) < 500:
            recommendations.append('建议增加技术细节描述')

        if not any(keyword in text for keyword in ['权利要求', '法律保护']):
            recommendations.append('建议明确权利要求保护范围')

        if not any(keyword in text for keyword in ['创新点', '优势', '效果']):
            recommendations.append('建议强调技术创新点和优势')

        recommendations.append('建议咨询专业专利代理机构')

        return recommendations

    def search_similar_patents(self, query_text: str, limit: int = 10) -> List[Dict[str, Any]]:
        """搜索相似专利"""
        logger.info(f"搜索相似专利: {query_text}")

        # 简化实现：返回模拟结果
        # 在实际应用中，这里会调用向量检索系统
        mock_results = [
            {
                'patent_id': f"patent_{i}",
                'title': f"相似专利标题 {i}",
                'abstract': f"这是与查询内容相似的专利摘要 {i}",
                'similarity_score': 0.9 - i * 0.1,
                'ranking_position': i + 1
            }
            for i in range(min(limit, 3))
        ]

        return mock_results

    def get_service_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            'service_running': self.running,
            'timestamp': datetime.now().isoformat(),
            'cache_size': len(self.patent_cache),
            'analysis_count': len(self.analysis_results),
            'available_features': [
                'patent_text_analysis',
                'patent_similarity_search',
                'technical_feature_extraction'
            ]
        }

    def start(self):
        """启动服务"""
        self.running = True
        logger.info('✅ 简化专利感知服务已启动')

    def shutdown(self):
        """关闭服务"""
        self.running = False
        logger.info('🔄 简化专利感知服务已关闭')

# 全局服务实例
service = SimplePatentPerceptionService()

def run_fastapi_server():
    """运行FastAPI服务器"""
    try:
        import uvicorn
        from fastapi import FastAPI, HTTPException
        from pydantic import BaseModel

        app = FastAPI(title='简化专利感知API', version='1.0.0')

        # 数据模型
        class PatentAnalysisRequest(BaseModel):
            patent_text: str
            patent_id: str | None = None
            analysis_type: Optional[str] = 'comprehensive'
            language: str = 'zh-CN'

        class PatentSearchRequest(BaseModel):
            query_text: str
            limit: int = 10
            threshold: float = 0.7

        @app.post('/api/analyze/patent')
        async def analyze_patent(request: PatentAnalysisRequest):
            """分析专利"""
            try:
                analysis = service.analyze_patent_text(
                    request.patent_text,
                    request.patent_id,
                    request.analysis_type or 'comprehensive'
                )

                return {
                    'success': True,
                    'result': analysis
                }

            except Exception as e:
                logger.error(f"专利分析错误: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.post('/api/search/patents')
        async def search_patents(request: PatentSearchRequest):
            """检索专利"""
            try:
                results = service.search_similar_patents(
                    request.query_text,
                    request.limit
                )

                return {
                    'success': True,
                    'results': results,
                    'total': len(results)
                }

            except Exception as e:
                logger.error(f"专利检索错误: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @app.get('/api/status')
        async def get_status():
            """获取服务状态"""
            return service.get_service_status()

        @app.get('/')
        async def root():
            return {
                'service': '简化专利感知服务',
                'version': '1.0.0',
                'status': 'running',
                'timestamp': datetime.now().isoformat()
            }

        # 在新线程中运行uvicorn
        def run_server():
            uvicorn.run(app, host='0.0.0.0', port=8026, log_level='info')

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        return True

    except ImportError:
        logger.warning('FastAPI未安装，无法启动高级API服务器')
        return False

def main():
    """主函数"""
    logger.info('🚀 启动简化专利感知服务...')

    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"\n⚠️ 收到信号 {signum}，正在关闭服务...")
        service.shutdown()
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # 启动服务
        service.start()

        # 尝试启动FastAPI服务器
        if not run_fastapi_server():
            # 如果FastAPI不可用，启动简单HTTP服务器
            logger.info('启动简单HTTP服务器...')
            import http.server
            import socketserver

            class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
                def do_POST(self):
                    if self.path == '/api/analyze/patent':
                        try:
                            content_length = int(self.headers['Content-Length'])
                            post_data = self.rfile.read(content_length)
                            request_data = json.loads(post_data.decode('utf-8'))

                            result = service.analyze_patent_text(
                                request_data.get('patent_text', ''),
                                request_data.get('patent_id'),
                                request_data.get('analysis_type', 'comprehensive')
                            )

                            self.send_response(200)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'success': True, 'result': result}).encode())
                        except Exception as e:
                            self.send_response(500)
                            self.send_header('Content-type', 'application/json')
                            self.end_headers()
                            self.wfile.write(json.dumps({'success': False, 'error': str(e)}).encode())

                def do_GET(self):
                    if self.path == '/api/status':
                        status = service.get_service_status()
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps(status).encode())
                    else:
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        self.wfile.write(json.dumps({
                            'service': '简化专利感知服务',
                            'version': '1.0.0',
                            'status': 'running',
                            'timestamp': datetime.now().isoformat()
                        }).encode())

            with socketserver.TCPServer(('', 8026), SimpleHTTPRequestHandler) as httpd:
                logger.info('🌐 简单HTTP服务器启动在端口 8026')
                httpd.serve_forever()

        logger.info('✅ 感知服务已成功启动在端口 8026')

        # 保持主线程运行
        while True:
            import time
            time.sleep(1)

    except KeyboardInterrupt:
        service.shutdown()
        logger.info('👋 感知服务已关闭')
    except Exception as e:
        logger.error(f"服务启动失败: {e}")
        service.shutdown()
        sys.exit(1)

if __name__ == '__main__':
    main()