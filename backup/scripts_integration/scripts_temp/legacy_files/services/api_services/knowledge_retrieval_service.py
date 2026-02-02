import json
import logging
import os
import re
from datetime import datetime

from flask import Flask, jsonify, request

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
        words = re.findall(r'[一-鿿]+|[a-zA-Z]+', text)
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
