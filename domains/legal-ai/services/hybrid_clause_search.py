#!/usr/bin/env python3
"""
混合条款检索系统
结合精确匹配和语义搜索，支持条款级别的精确检索
"""

import logging
import re
import time

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import FieldCondition, Filter, MatchValue, SearchRequest
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    logger.info(f"❌ 缺少依赖: {e}")
    logger.info('请安装: pip install sentence-transformers qdrant-client')
    exit(1)


class HybridClauseSearch:
    """混合条款检索系统"""

    def __init__(self):
        # 配置
        self.model_path = '/Users/xujian/Athena工作平台/models/bge-large-zh-v1.5'
        self.document_collection = 'legal_documents'    # 文档级向量库
        self.clause_collection = 'legal_clauses'        # 条款级向量库

        # 加载模型
        logger.info('📦 加载BGE模型...')
        self.model = SentenceTransformer(self.model_path, device='cpu')
        logger.info('✅ 模型加载成功')

        # 连接Qdrant
        try:
            self.qdrant = QdrantClient(host='localhost', port=6333)
            logger.info('✅ Qdrant连接成功')
        except Exception as e:
            logger.error(f"❌ Qdrant连接失败: {e}")
            raise

        # 条款号提取模式
        self.clause_number_patterns = [
            # 第X条
            re.compile(r'第([一二三四五六七八九十百千万零0-9]+)条', re.IGNORECASE),
            # 第X款
            re.compile(r'第([一二三四五六七八九十百千万零0-9]+)款', re.IGNORECASE),
            # 第X项
            re.compile(r'第([一二三四五六七八九十百千万零0-9]+)项', re.IGNORECASE),
            # X条 (阿拉伯数字)
            re.compile(r'(\d+)条', re.IGNORECASE),
            # Article X (英文)
            re.compile(r'article\s+(\d+)', re.IGNORECASE),
        ]

    def extract_clause_number(self, query: str) -> tuple[str, str | None]:
        """从查询中提取条款号

        Returns:
            (条款号, 条款类型) 或 None
        """
        query_lower = query.lower()

        for pattern in self.clause_number_patterns:
            match = pattern.search(query)
            if match:
                number = match.group(1)
                # 转换阿拉伯数字为中文数字
                if number.isdigit():
                    chinese_num = self._arabic_to_chinese(int(number))
                else:
                    chinese_num = number

                # 确定条款类型
                if '条' in match.group(0):
                    clause_type = '条'
                elif '款' in match.group(0):
                    clause_type = '款'
                elif '项' in match.group(0):
                    clause_type = '项'
                elif 'article' in query_lower:
                    clause_type = '条'
                else:
                    clause_type = '条'

                return f"第{chinese_num}{clause_type}", clause_type

        return None, None

    def _arabic_to_chinese(self, num: int) -> str:
        """将阿拉伯数字转换为中文数字"""
        chinese_map = {
            0: '零', 1: '一', 2: '二', 3: '三', 4: '四',
            5: '五', 6: '六', 7: '七', 8: '八', 9: '九',
            10: '十', 20: '二十', 30: '三十', 40: '四十',
            50: '五十', 60: '六十', 70: '七十', 80: '八十',
            90: '九十', 100: '一百', 200: '二百', 300: '三百',
            400: '四百', 500: '五百', 600: '六百', 700: '七百',
            800: '八百', 900: '九百', 1000: '一千'
        }

        if num <= 10:
            return chinese_map.get(num, str(num))
        elif num < 20:
            return '十' + chinese_map.get(num % 10, '')
        elif num < 100:
            tens = num // 10 * 10
            ones = num % 10
            result = chinese_map.get(tens, str(tens))
            if ones > 0:
                result += chinese_map.get(ones, str(ones))
            return result
        else:
            return str(num)  # 对于更大的数字，直接返回字符串

    def exact_clause_search(self, clause_number: str, law_name: str | None = None) -> list[dict]:
        """精确条款搜索"""
        try:
            # 构建过滤条件
            filter_conditions = [FieldCondition(key='clause_number', match=MatchValue(value=clause_number))]

            if law_name:
                filter_conditions.append(FieldCondition(key='law_name', match=MatchValue(value=law_name)))

            search_filter = Filter(must=filter_conditions)

            # 执行搜索
            results = self.qdrant.scroll(
                collection_name=self.clause_collection,
                scroll_filter=search_filter,
                limit=10,
                with_payload=True,
                with_vectors=False
            )[0]

            return results

        except Exception as e:
            logger.error(f"❌ 精确条款搜索失败: {e}")
            return []

    def semantic_clause_search(self, query: str, limit: int = 5) -> list[dict]:
        """语义条款搜索"""
        try:
            # 生成查询向量
            query_vector = self.model.encode(query, normalize_embeddings=True)

            # 执行语义搜索
            results = self.qdrant.search(
                collection_name=self.clause_collection,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=0.4,
                with_payload=True
            )

            return results

        except Exception as e:
            logger.error(f"❌ 语义条款搜索失败: {e}")
            return []

    def semantic_document_search(self, query: str, limit: int = 3) -> list[dict]:
        """语义文档搜索（备选方案）"""
        try:
            # 生成查询向量
            query_vector = self.model.encode(query, normalize_embeddings=True)

            # 执行语义搜索
            results = self.qdrant.search(
                collection_name=self.document_collection,
                query_vector=query_vector.tolist(),
                limit=limit,
                score_threshold=0.5,
                with_payload=True
            )

            return results

        except Exception as e:
            logger.error(f"❌ 语义文档搜索失败: {e}")
            return []

    def hybrid_search(self, query: str, limit: int = 5) -> dict:
        """混合搜索主函数"""
        logger.info(f"🔍 执行混合搜索: '{query}'")
        start_time = time.time()

        # 1. 尝试提取条款号
        clause_info = self.extract_clause_number(query)

        results = {
            'query': query,
            'clause_extracted': clause_info is not None,
            'exact_matches': [],
            'semantic_matches': [],
            'document_matches': [],
            'processing_time': 0,
            'total_results': 0
        }

        # 2. 如果提取到条款号，执行精确搜索
        if clause_info:
            clause_number, clause_type = clause_info
            logger.info(f"📍 检测到条款号: {clause_number}")

            exact_results = self.exact_clause_search(clause_number)
            results['exact_matches'] = self._format_results(exact_results, 'exact')

            if exact_results:
                logger.info(f"✅ 找到 {len(exact_results)} 个精确匹配")

        # 3. 同时执行语义搜索
        semantic_results = self.semantic_clause_search(query, limit)
        results['semantic_matches'] = self._format_results(semantic_results, 'semantic')

        if semantic_results:
            logger.info(f"🔍 找到 {len(semantic_results)} 个语义匹配")

        # 4. 如果条款级结果不足，使用文档级搜索作为备选
        if len(results['exact_matches']) + len(results['semantic_matches']) < limit:
            doc_results = self.semantic_document_search(query, limit)
            results['document_matches'] = self._format_results(doc_results, 'document')

            if doc_results:
                logger.info(f"📄 找到 {len(doc_results)} 个文档匹配")

        # 5. 计算统计信息
        results['processing_time'] = time.time() - start_time
        results['total_results'] = (
            len(results['exact_matches']) +
            len(results['semantic_matches']) +
            len(results['document_matches'])
        )

        return results

    def _format_results(self, results: list, result_type: str) -> list[dict]:
        """格式化搜索结果"""
        formatted = []

        for i, result in enumerate(results):
            if hasattr(result, 'payload'):  # Qdrant搜索结果
                payload = result.payload
                score = getattr(result, 'score', None)

                formatted_result = {
                    'rank': i + 1,
                    'score': score,
                    'type': result_type,
                    'clause_id': payload.get('clause_id', ''),
                    'clause_number': payload.get('clause_number', ''),
                    'clause_type': payload.get('clause_type', ''),
                    'content': payload.get('content', ''),
                    'law_name': payload.get('law_name', ''),
                    'chapter': payload.get('chapter', ''),
                    'file_path': payload.get('file_path', ''),
                    'line_number': payload.get('line_number', 0)
                }
            else:  # Scroll结果
                payload = result.payload
                formatted_result = {
                    'rank': i + 1,
                    'score': 1.0,  # 精确匹配给满分
                    'type': result_type,
                    'clause_id': payload.get('clause_id', ''),
                    'clause_number': payload.get('clause_number', ''),
                    'clause_type': payload.get('clause_type', ''),
                    'content': payload.get('content', ''),
                    'law_name': payload.get('law_name', ''),
                    'chapter': payload.get('chapter', ''),
                    'file_path': payload.get('file_path', ''),
                    'line_number': payload.get('line_number', 0)
                }

            formatted.append(formatted_result)

        return formatted

    def print_search_results(self, results: dict):
        """打印搜索结果"""
        logger.info(f"\n{'='*80}")
        logger.info(f"🔍 搜索查询: {results['query']}")
        logger.info(f"⏱️ 处理时间: {results['processing_time']:.3f}秒")
        logger.info(f"📊 结果统计: 共找到 {results['total_results']} 个结果")

        if results['clause_extracted']:
            logger.info("🎯 条款检测: 已识别具体条款号")

        logger.info(f"\n{'='*80}")

        # 1. 精确匹配
        if results['exact_matches']:
            logger.info(f"\n🎯 【精确匹配】 ({len(results['exact_matches'])} 个结果)")
            logger.info(str('-' * 60))

            for result in results['exact_matches']:
                logger.info(f"\n📍 {result['clause_number']} ({result['clause_type']})")
                logger.info(f"📜 法律: {result['law_name']}")
                if result['chapter']:
                    logger.info(f"📖 章节: {result['chapter']}")
                logger.info(f"📄 内容: {result['content']}")
                logger.info(f"📁 来源: {result['file_path']}")

        # 2. 语义匹配
        if results['semantic_matches']:
            logger.info(f"\n🔍 【语义匹配】 ({len(results['semantic_matches'])} 个结果)")
            logger.info(str('-' * 60))

            for result in results['semantic_matches']:
                logger.info(f"\n📍 {result['clause_number']} ({result['clause_type']}) - 相似度: {result['score']:.4f}")
                logger.info(f"📜 法律: {result['law_name']}")
                if result['chapter']:
                    logger.info(f"📖 章节: {result['chapter']}")
                logger.info(f"📄 内容: {result['content']}")
                logger.info(f"📁 来源: {result['file_path']}")

        # 3. 文档匹配
        if results['document_matches']:
            logger.info(f"\n📄 【文档匹配】 ({len(results['document_matches'])} 个结果)")
            logger.info(str('-' * 60))

            for result in results['document_matches']:
                logger.info(f"\n📜 文档: {result['law_name']}")
                logger.info(f"📊 相似度: {result['score']:.4f}")
                logger.info(f"📁 来源: {result['file_path']}")
                logger.info("💡 提示: 这是一整个文档，请使用全文搜索功能查找具体条款")


def main():
    """测试混合搜索系统"""
    logger.info('🚀 启动混合条款检索系统')

    # 初始化搜索系统
    try:
        searcher = HybridClauseSearch()
        logger.info('✅ 系统初始化成功')
    except Exception as e:
        logger.info(f"❌ 系统初始化失败: {e}")
        return

    # 测试查询列表
    test_queries = [
        '专利法第26条',
        '第二十六条',
        'article 26 patent',
        '劳动合同纠纷处理',
        '盗窃罪量刑标准',
        '公司设立条件'
    ]

    logger.info(f"\n{'='*80}")
    logger.info('🧪 开始测试查询...')

    for i, query in enumerate(test_queries, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"测试 {i}/{len(test_queries)}: {query}")

        # 执行混合搜索
        results = searcher.hybrid_search(query)

        # 打印结果
        searcher.print_search_results(results)

        # 短暂暂停
        time.sleep(0.5)

    logger.info(f"\n{'='*80}")
    logger.info('🎉 测试完成！')


if __name__ == '__main__':
    main()
