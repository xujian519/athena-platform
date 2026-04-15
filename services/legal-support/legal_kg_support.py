#!/usr/bin/env python3
"""
法律知识图谱支持系统
为小娜提供法律专业能力支持
作者: 小诺·双鱼座
"""

import json
import logging
import sqlite3
import subprocess
import time
from typing import Any

import jieba
import numpy as np
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LegalKnowledgeGraphSupport:
    """法律知识图谱支持系统"""

    def __init__(self, config: dict = None):
        """初始化法律知识图谱支持系统"""
        self.config = config or {
            # NebulaGraph配置
            "nebula": {
                "host": "localhost",
                "port": 9669,
                "username": "root",
                "password": "nebula",
                "space": "法律知识图谱"
            },
            # 向量数据库配置
            "vector_db": "/Users/xujian/Athena工作平台/tools/Laws-1.0.0/db.sqlite3",
            # 向量模型配置
            "model": "shibing624/text2vec-base-chinese",
            # 缓存配置
            "cache_ttl": 3600,  # 1小时
            "cache_size": 1000
        }

        # 初始化组件
        self.vector_model = None
        self.cache = {}
        self.cache_timestamps = {}

        # 初始化系统
        self._initialize()

    def _initialize(self):
        """初始化各个组件"""
        logger.info("🚀 初始化法律知识图谱支持系统...")

        try:
            # 加载向量模型
            logger.info("📚 加载向量模型...")
            self.vector_model = SentenceTransformer(self.config["model"])

            # 连接向量数据库
            logger.info("📊 连接向量数据库...")
            self.vector_conn = sqlite3.connect(self.config["vector_db"], check_same_thread=False)

            # 测试NebulaGraph连接
            logger.info("🕸️ 测试知识图谱连接...")
            self._test_nebula_connection()

            logger.info("✅ 法律知识图谱支持系统初始化完成！")

        except Exception as e:
            logger.error(f"❌ 初始化失败: {e}")
            raise

    def _test_nebula_connection(self):
        """测试NebulaGraph连接"""
        try:
            success, _, _ = self._execute_nebula("SHOW SPACES;")
            if not success:
                logger.error("NebulaGraph连接失败")
                raise Exception("无法连接到NebulaGraph")
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            raise

    def _execute_nebula(self, nql: str) -> tuple[bool, str, str]:
        """执行NebulaGraph查询"""
        cmd = f'''
        docker run --rm --network nebula-net \
            vesoft/nebula-console:v3.6.0 \
            -addr {self.config["nebula"]["host"]} \
            -port {self.config["nebula"]["port"]} \
            -u {self.config["nebula"]["username"]} \
            -p {self.config["nebula"]["password"]} \
            -e "USE {self.config['nebula']['space']}; {nql}"
        '''

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        return result.returncode == 0, result.stdout, result.stderr

    def _get_cache(self, key: str) -> Any | None:
        """获取缓存"""
        if key in self.cache:
            # 检查是否过期
            if time.time() - self.cache_timestamps[key] < self.config["cache_ttl"]:
                return self.cache[key]
            else:
                # 删除过期缓存
                del self.cache[key]
                del self.cache_timestamps[key]
        return None

    def _set_cache(self, key: str, value: Any):
        """设置缓存"""
        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.config["cache_size"]:
            oldest_key = min(self.cache_timestamps.keys(),
                           key=self.cache_timestamps.get)
            del self.cache[oldest_key]
            del self.cache_timestamps[oldest_key]

        self.cache[key] = value
        self.cache_timestamps[key] = time.time()

    def search_by_vector(self, query: str, top_k: int = 5) -> list[dict]:
        """基于向量搜索相似法律条文"""
        cache_key = f"vector_{query}_{top_k}"
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return cached_result

        logger.info(f"🔍 向量搜索: {query}")

        # 生成查询向量
        query_vector = self.vector_model.encode(query)

        # 在向量数据库中搜索
        cursor = self.vector_conn.cursor()
        cursor.execute("""
            SELECT name, content, embedding
            FROM law
            WHERE embedding IS NOT NULL
            LIMIT 1000
        """)

        results = []
        for row in cursor.fetchall():
            name, content, embedding_blob = row

            # 解码向量
            if embedding_blob:
                # 假设embedding是BLOB格式
                try:
                    if isinstance(embedding_blob, bytes):
                        # 将bytes转换为numpy数组
                        embedding = np.frombuffer(embedding_blob, dtype=np.float32)
                    else:
                        # 如果已经是字符串格式
                        embedding = np.array(json.loads(embedding_blob))

                    # 计算余弦相似度
                    similarity = np.dot(query_vector, embedding) / (
                        np.linalg.norm(query_vector) * np.linalg.norm(embedding)
                    )

                    results.append({
                        "title": name,
                        "content": content[:200] + "..." if len(content) > 200 else content,
                        "similarity": float(similarity),
                        "source": "vector_search"
                    })
                except Exception as e:
                    logger.warning(f"处理向量时出错: {e}")
                    continue

        # 按相似度排序
        results.sort(key=lambda x: x["similarity"], reverse=True)

        # 缓存结果
        self._set_cache(cache_key, results[:top_k])

        return results[:top_k]

    def search_by_graph(self, query: str, entity_type: str = None) -> list[dict]:
        """基于知识图谱搜索"""
        cache_key = f"graph_{query}_{entity_type}"
        cached_result = self._get_cache(cache_key)
        if cached_result:
            return cached_result

        logger.info(f"🕸️ 知识图谱搜索: {query}")

        # 提取关键词
        keywords = self._extract_keywords(query)
        results = []

        # 根据关键词在图谱中搜索
        for keyword in keywords[:3]:  # 限制关键词数量
            if entity_type == "legal_document" or not entity_type:
                # 搜索法律文档
                success, output, _ = self._execute_nebula(
                    f'MATCH (v:legal_document) WHERE v.title CONTAINS "{keyword}" '
                    f'RETURN v.doc_id, v.title LIMIT 10'
                )
                if success:
                    results.extend(self._parse_nebula_output(output, "legal_document"))

            if entity_type == "legal_article" or not entity_type:
                # 搜索法律条文
                success, output, _ = self._execute_nebula(
                    f'MATCH (v:legal_article) WHERE v.content CONTAINS "{keyword}" '
                    f'RETURN v.article_id, v.content LIMIT 10'
                )
                if success:
                    results.extend(self._parse_nebula_output(output, "legal_article"))

        # 缓存结果
        self._set_cache(cache_key, results[:10])

        return results[:10]

    def _extract_keywords(self, text: str) -> list[str]:
        """提取关键词"""
        # 使用jieba分词
        words = jieba.cut(text)

        # 过滤停用词和短词
        stop_words = {'的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看', '好', '自己', '这'}

        keywords = []
        for word in words:
            if len(word) > 1 and word not in stop_words:
                keywords.append(word)

        return list(set(keywords))

    def _parse_nebula_output(self, output: str, result_type: str) -> list[dict]:
        """解析NebulaGraph输出"""
        results = []
        lines = output.split('\n')

        for line in lines:
            if '|' in line and not line.strip().startswith(('+', '|', 'Got', '---')):
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2 and parts[0] and parts[1]:
                    if result_type == "legal_document":
                        results.append({
                            "doc_id": parts[0].strip('"'),
                            "title": parts[1].strip('"'),
                            "source": "kg_search",
                            "type": "法律文档"
                        })
                    elif result_type == "legal_article":
                        results.append({
                            "article_id": parts[0].strip('"'),
                            "content": parts[1].strip('"')[:200] + "..." if len(parts[1]) > 200 else parts[1].strip('"'),
                            "source": "kg_search",
                            "type": "法律条文"
                        })

        return results

    def hybrid_search(self, query: str, top_k: int = 10) -> list[dict]:
        """混合搜索：结合向量搜索和知识图谱搜索"""
        logger.info(f"🔥 混合搜索: {query}")

        # 获取向量搜索结果
        vector_results = self.search_by_vector(query, top_k // 2)

        # 获取知识图谱搜索结果
        graph_results = self.search_by_graph(query)

        # 合并和重排序结果
        all_results = []

        # 向量搜索结果权重0.6
        for result in vector_results:
            result["score"] = result["similarity"] * 0.6
            all_results.append(result)

        # 图谱搜索结果权重0.4
        for result in graph_results:
            # 给图谱搜索结果一个基础分数
            result["score"] = 0.4
            all_results.append(result)

        # 去重（基于标题或内容）
        seen = set()
        unique_results = []
        for result in all_results:
            key = result.get("title") or result.get("content", "")[:50]
            if key not in seen:
                seen.add(key)
                unique_results.append(result)

        # 按分数排序
        unique_results.sort(key=lambda x: x["score"], reverse=True)

        return unique_results[:top_k]

    def get_related_laws(self, law_title: str) -> list[dict]:
        """获取相关法律（通过知识图谱关系）"""
        logger.info(f"🔗 查找相关法律: {law_title}")

        # 查找属于同一分类的其他法律
        success, output, _ = self._execute_nebula(
            f'MATCH (doc1:legal_document)-[:belongs_to]->(cat:legal_category) '
            f'<-[:belongs_to]-(doc2:legal_document) '
            f'WHERE doc1.title CONTAINS "{law_title}" '
            f'RETURN DISTINCT doc2.title LIMIT 10'
        )

        related_laws = []
        if success:
            for line in output.split('\n'):
                if '|' in line and not line.strip().startswith(('+', '|', 'Got')):
                    title = line.split('|')[1].strip() if len(line.split('|')) > 1 else ""
                    if title and title != law_title:
                        related_laws.append({
                            "title": title.strip('"'),
                            "relation": "同一分类",
                            "source": "knowledge_graph"
                        })

        return related_laws

    def generate_dynamic_prompt(self, query: str, context: dict = None) -> str:
        """生成动态提示词"""
        logger.info(f"💡 生成动态提示词: {query}")

        # 搜索相关法律依据
        search_results = self.hybrid_search(query, top_k=5)

        # 构建上下文
        legal_basis = []
        for result in search_results:
            if result.get("title"):
                legal_basis.append(f"《{result['title']}》")
            if result.get("content"):
                legal_basis.append(f"- {result['content']}")

        # 查找相关法律
        if search_results and search_results[0].get("title"):
            related = self.get_related_laws(search_results[0]["title"])
            if related:
                legal_basis.append("\n相关法律：")
                for law in related[:3]:
                    legal_basis.append(f"- {law['title']}")

        # 生成提示词
        prompt = f"""你是小娜，专业的法律AI助手。

用户问题：{query}

法律依据：
{chr(10).join(legal_basis[:10]) if legal_basis else "暂无直接相关法律依据"}

请基于上述法律依据，以专业、准确、易懂的方式回答用户问题。

回答要求：
1. 引用具体的法律条文
2. 解释法律条款的含义
3. 提供实用的建议或指导
4. 如有必要，说明相关程序的步骤
5. 保持客观中立，不构成正式法律建议

回答：
"""

        return prompt

    def get_conversation_support(self, message: str, conversation_history: list[dict] | None = None) -> dict:
        """为对话提供支持"""
        logger.info(f"💬 对话支持: {message}")

        # 分析用户意图
        intent = self._analyze_intent(message)

        # 根据意图提供不同支持
        if intent["type"] == "legal_consultation":
            # 法律咨询
            return {
                "type": "legal_consultation",
                "prompt": self.generate_dynamic_prompt(message),
                "references": self.hybrid_search(message, top_k=3),
                "suggestions": self._generate_suggestions(message)
            }
        elif intent["type"] == "legal_concept":
            # 法律概念查询
            return {
                "type": "legal_concept",
                "definition": self._get_legal_concept_definition(intent["concept"]),
                "related_articles": self.search_by_graph(intent["concept"], "legal_article")
            }
        elif intent["type"] == "procedure_guidance":
            # 程序指导
            return {
                "type": "procedure_guidance",
                "steps": self._get_procedure_steps(intent["procedure"]),
                "legal_basis": self.hybrid_search(intent["procedure"], top_k=5)
            }
        else:
            # 一般问答
            return {
                "type": "general_qa",
                "context": self.hybrid_search(message, top_k=3),
                "prompt": f"基于相关法律信息回答：{message}"
            }

    def _analyze_intent(self, message: str) -> dict:
        """分析用户意图"""
        message.lower()

        # 法律咨询关键词
        consult_keywords = ["如何", "怎样", "怎么办", "是否", "可以", "应该", "需要", "要求", "规定"]
        # 法律概念关键词
        concept_keywords = ["什么是", "定义", "含义", "解释", "概念"]
        # 程序指导关键词
        procedure_keywords = ["流程", "步骤", "程序", "办理", "申请", "起诉", "上诉", "执行"]

        if any(kw in message for kw in concept_keywords):
            # 提取概念
            for kw in concept_keywords:
                if kw in message:
                    concept = message.split(kw)[1].strip().split("？")[0].split("。")[0]
                    return {"type": "legal_concept", "concept": concept}

        elif any(kw in message for kw in procedure_keywords):
            # 提取程序
            for kw in procedure_keywords:
                if kw in message:
                    procedure = message.split(kw)[0].strip() + kw
                    return {"type": "procedure_guidance", "procedure": procedure}

        elif any(kw in message for kw in consult_keywords):
            return {"type": "legal_consultation"}

        return {"type": "general_qa"}

    def _generate_suggestions(self, query: str) -> list[str]:
        """生成建议问题"""
        suggestions = [
            f"关于{query}的详细法律规定是什么？",
            "如何申请相关的法律救济？",
            "有哪些需要注意的法律风险？",
            "相关的案例有哪些？"
        ]
        return suggestions[:3]

    def _get_legal_concept_definition(self, concept: str) -> str:
        """获取法律概念定义"""
        # 这里可以连接法律知识库获取定义
        # 暂时返回基本解释
        return f"关于'{concept}'的法律定义，请参考相关法律条文。"

    def _get_procedure_steps(self, procedure: str) -> list[dict]:
        """获取程序步骤"""
        # 这里可以查询具体的法律程序
        return [
            {"step": 1, "action": "准备相关材料", "description": "收集必要的证明文件"},
            {"step": 2, "action": "提交申请", "description": "向相关部门提交申请"},
            {"step": 3, "action": "等待审核", "description": "相关部门进行审核"},
            {"step": 4, "action": "获取结果", "description": "收到处理结果"}
        ]

    def close(self):
        """关闭连接"""
        if hasattr(self, 'vector_conn'):
            self.vector_conn.close()
        logger.info("✅ 法律知识图谱支持系统已关闭")


# 测试代码
if __name__ == "__main__":
    # 初始化系统
    lks = LegalKnowledgeGraphSupport()

    # 测试搜索功能
    query = "离婚财产如何分割？"

    print("\n=== 测试混合搜索 ===")
    results = lks.hybrid_search(query)
    for i, result in enumerate(results, 1):
        print(f"\n{i}. {result.get('title', 'N/A')}")
        print(f"   来源: {result.get('source', 'N/A')}")
        print(f"   分数: {result.get('score', 0):.3f}")
        if result.get('content'):
            print(f"   内容: {result['content'][:100]}...")

    print("\n=== 测试动态提示词生成 ===")
    prompt = lks.generate_dynamic_prompt(query)
    print(prompt[:500] + "..." if len(prompt) > 500 else prompt)

    print("\n=== 测试对话支持 ===")
    support = lks.get_conversation_support(query)
    print(f"支持类型: {support['type']}")
    print(f"参考数量: {len(support.get('references', []))}")

    # 关闭系统
    lks.close()
