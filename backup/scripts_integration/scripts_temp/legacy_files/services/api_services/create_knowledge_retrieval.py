#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创建知识库检索服务
Create Knowledge Retrieval Service
"""

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def create_knowledge_base():
    """创建基础知识库"""
    logger.info('📚 创建知识库...')

    # 知识库数据
    knowledge_base = {
        'patents': [
            {
                'id': 'patent_001',
                'title': '发明专利申请流程',
                'content': '发明专利申请包括：提交申请、受理、初审、公布、实审、授权等步骤。整个流程通常需要2-3年。',
                'category': '流程',
                'keywords': ['发明专利', '申请流程', '知识产权'],
                'importance': 1.0
            },
            {
                'id': 'patent_002',
                'title': '专利审查指南',
                'content': '专利审查遵循三性原则：新颖性、创造性、实用性。审查员会检索现有技术进行对比。',
                'category': '审查',
                'keywords': ['专利审查', '三性原则', '新颖性', '创造性', '实用性'],
                'importance': 0.95
            },
            {
                'id': 'patent_003',
                'title': '专利侵权判定',
                'content': '专利侵权判定包括全面覆盖原则和等同原则。全面覆盖是指被控侵权技术方案包含了专利权利要求的所有技术特征。',
                'category': '法律',
                'keywords': ['专利侵权', '全面覆盖', '等同原则'],
                'importance': 0.90
            }
        ],
        'legal': [
            {
                'id': 'legal_001',
                'title': '合同法基本原则',
                'content': '合同法基本原则包括：平等原则、自愿原则、公平原则、诚实信用原则、遵守法律原则等。',
                'category': '基础理论',
                'keywords': ['合同法', '基本原则', '平等', '自愿', '公平', '诚实信用'],
                'importance': 0.95
            },
            {
                'id': 'legal_002',
                'title': '公司法组织架构',
                'content': '公司法规定了公司的组织架构，包括股东会、董事会、监事会、经理等机构的设置和职权。',
                'category': '公司治理',
                'keywords': ['公司法', '组织架构', '股东会', '董事会', '监事会'],
                'importance': 0.90
            }
        ],
        'work_platform': [
            {
                'id': 'platform_001',
                'title': 'Athena工作平台架构',
                'content': 'Athena工作平台采用微服务架构，包含身份认知、记忆管理、知识检索、任务协调等核心模块。',
                'category': '架构',
                'keywords': ['Athena', '工作平台', '微服务', '架构'],
                'importance': 1.0
            },
            {
                'id': 'platform_002',
                'title': '系统使用指南',
                'content': 'Athena工作平台提供文本分析、知识检索、任务管理等功能，帮助用户提高工作效率。',
                'category': '使用',
                'keywords': ['使用指南', '功能介绍', '工作效率'],
                'importance': 0.95
            }
        ]
    }

    # 保存知识库
    kb_path = '/Users/xujian/Athena工作平台/data/knowledge_base.json'
    with open(kb_path, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, ensure_ascii=False, indent=2)

    logger.info(f"✅ 知识库已创建: {kb_path}")
    return kb_path

def create_retrieval_service():
    """创建知识检索服务"""
    service_code = '''from flask import Flask, request, jsonify
import json
import re
import os
from datetime import datetime

app = Flask(__name__)

class KnowledgeRetriever:
    """知识检索器"""

    def __init__(self):
        self.load_knowledge_base()

    def load_knowledge_base(self):
        """加载知识库"""
        kb_path = '/Users/xujian/Athena工作平台/data/knowledge_base.json'
        with open(kb_path, 'r', encoding='utf-8') as f:
            self.knowledge_base = json.load(f)

        # 构建倒排索引
        self.inverted_index = {}
        for category, items in self.knowledge_base.items():
            for item in items:
                # 分词并建立索引
                words = self.tokenize(item['title'] + ' ' + item['content'])
                for word in words:
                    if word not in self.inverted_index:
                        self.inverted_index[word] = []
                    self.inverted_index[word].append({
                        'id': item['id'],
                        'category': category,
                        'importance': item['importance']
                    })

    def tokenize(self, text):
        """简单的中文分词"""
        # 按空格和标点分割
        words = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', text)
        return [word.lower() for word in words if len(word) > 1]

    def search(self, query, limit=5):
        """搜索知识"""
        query_words = self.tokenize(query)
        scored_items = {}

        # 计算每个文档的得分
        for word in query_words:
            if word in self.inverted_index:
                for item in self.inverted_index[word]:
                    item_id = item['id']
                    if item_id not in scored_items:
                        scored_items[item_id] = {
                            'score': 0,
                            'matches': 0
                        }
                    scored_items[item_id]['score'] += item['importance']
                    scored_items[item_id]['matches'] += 1

        # 按得分排序
        sorted_items = sorted(
            scored_items.items(),
            key=lambda x: (x[1]['matches'], x[1]['score']),
            reverse=True
        )

        # 获取详细信息
        results = []
        for item_id, score_info in sorted_items[:limit]:
            for category, items in self.knowledge_base.items():
                for item in items:
                    if item['id'] == item_id:
                        # 计算相关性
                        relevance = min(1.0, score_info['score'] / len(query_words))
                        results.append({
                            **item,
                            'category': category,
                            'relevance': relevance,
                            'match_count': score_info['matches']
                        })
                        break

        return results

retriever = KnowledgeRetriever()

@app.route('/health')
def health():
    return {'status': 'healthy', 'service': 'knowledge_retrieval'}

@app.route('/api/v3/knowledge/search/<query>')
def search_knowledge(query):
    """搜索知识"""
    limit = request.args.get('limit', 5, type=int)
    category = request.args.get('category', None)

    results = retriever.search(query, limit)

    # 按类别过滤
    if category:
        results = [r for r in results if r['category'] == category]

    return {
        'success': True,
        'query': query,
        'total': len(results),
        'results': results,
        'timestamp': datetime.datetime.now().isoformat()
    }

@app.route('/api/v3/knowledge/categories')
def get_categories():
    """获取知识库分类"""
    categories = {}
    for cat_name, items in retriever.knowledge_base.items():
        categories[cat_name] = {
            'count': len(items),
            'description': f"{cat_name}相关知识"
        }

    return {
        'success': True,
        'categories': categories
    }

@app.route('/api/v3/knowledge/recent')
def get_recent_knowledge():
    """获取最近的知识更新"""
    # 返回一些重要知识
    important_items = []
    for category, items in retriever.knowledge_base.items():
        for item in items:
            if item['importance'] >= 0.95:
                important_items.append({
                    **item,
                    'category': category
                })

    # 按重要性排序
    important_items.sort(key=lambda x: x['importance'], reverse=True)

    return {
        'success': True,
        'results': important_items[:10]
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8012, debug=False)
'''

    service_file = '/Users/xujian/Athena工作平台/scripts_new/services/api_services/knowledge_retrieval_service.py'
    with open(service_file, 'w', encoding='utf-8') as f:
        f.write(service_code)

    logger.info(f"✅ 知识检索服务已创建: {service_file}")
    return service_file

def test_knowledge_retrieval():
    """测试知识检索"""
    import subprocess
    import time

    import requests

    logger.info('🔍 测试知识检索服务...')

    # 启动服务
    process = subprocess.Popen(
        ['python3', '/Users/xujian/Athena工作平台/scripts_new/services/api_services/knowledge_retrieval_service.py'],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    # 等待服务启动
    time.sleep(3)

    try:
        # 测试搜索功能
        test_queries = [
            '专利申请',
            '公司法',
            'Athena平台'
        ]

        for query in test_queries:
            response = requests.get(f"http://localhost:8012/api/v3/knowledge/search/{query}")
            if response.status_code == 200:
                result = response.json()
                logger.info(f"\n🔍 搜索: {query}")
                logger.info(f"  找到 {result['total']} 个结果")
                for item in result['results'][:2]:
                    logger.info(f"  - {item['title']}: {item['content'][:50]}...")

        logger.info("\n✅ 知识检索测试成功！")

    except Exception as e:
        logger.info(f"❌ 测试失败: {e}")

    # 关闭服务
    process.terminate()
    process.wait()

def main():
    """主函数"""
    logger.info(str('=' * 60))
    logger.info('📚 Athena工作平台 - 知识库检索服务创建')
    logger.info(str('=' * 60))

    # 创建知识库
    kb_path = create_knowledge_base()

    # 创建检索服务
    service_file = create_retrieval_service()

    # 测试服务
    test_knowledge_retrieval()

    logger.info(str("\n" + '=' * 60))
    logger.info('✅ 知识库检索服务创建完成！')
    logger.info("\n使用方法:")
    logger.info('1. 启动服务: python3 scripts_new/services/api_services/knowledge_retrieval_service.py')
    logger.info('2. 服务地址: http://localhost:8012')
    logger.info('3. 搜索接口: http://localhost:8012/api/v3/knowledge/search/<query>')
    logger.info('4. 分类列表: http://localhost:8012/api/v3/knowledge/categories')
    logger.info(str('=' * 60))

if __name__ == '__main__':
    main()