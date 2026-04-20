#!/usr/bin/env python3
from __future__ import annotations
"""
AI推理引擎模块
AI Reasoning Engine Module for Patent Invalidity System

集成大模型API,提供智能专利分析和推理能力,包括RAG问答系统
"""

import hashlib
import json
import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# API客户端导入
try:
    import openai

    OPENAI_AVAILABLE = True
except ImportError:
    logging.warning("OpenAI库未安装")

try:

    REQUESTS_AVAILABLE = True
except ImportError:
    logging.warning("requests库未安装")

# 向量数据库导入
try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    logging.warning("FAISS库未安装")

# 导入NLP处理器
try:
    from chinese_nlp_processor import ChineseNLPProcessor, ProcessResult

    CHINESE_NLP_AVAILABLE = True
except ImportError:
    logging.warning("中文NLP处理器不可用")

try:
    from enhanced_entity_recognizer import EnhancedEntityRecognizer, RecognitionResult

    ENHANCED_ENTITY_RECOGNIZER_AVAILABLE = True
except ImportError:
    logging.warning("增强实体识别器不可用")

# 配置日志
try:
    from loguru import logger

    logger.remove()
    logger.add("ai_reasoning_engine.log", rotation="10 MB", level="INFO")
    logger.add(lambda msg: print(msg, end=""), level="INFO")
except ImportError:
    pass  # loguru不可用,使用默认logging


@dataclass
class QueryResult:
    """查询结果"""

    query: str
    answer: str
    confidence: float
    sources: list[str]
    processing_time: float
    method_used: str
    metadata: dict[str, Any]
@dataclass
class ReasoningTask:
    """推理任务"""

    task_id: str
    task_type: str
    input_data: dict[str, Any]
    context: str
    priority: int
    created_at: float
    status: str = "pending"


class AIReasoningEngine:
    """AI推理引擎"""

    def __init__(
        self,
        openai_api_key: str | None = None,
        model_name: str = "gpt-3.5-turbo",
        use_mock: bool = True,
        cache_dir: str = "./ai_reasoning_cache",
    ):
        """
        初始化AI推理引擎

        Args:
            openai_api_key: OpenAI API密钥
            model_name: 模型名称
            use_mock: 是否使用模拟模式
            cache_dir: 缓存目录
        """
        self.openai_api_key = openai_api_key
        self.model_name = model_name
        self.use_mock = use_mock
        self.cache_dir = Path(cache_dir)

        # 创建缓存目录
        self.cache_dir.mkdir(exist_ok=True)

        # 初始化NLP组件
        self.nlp_processor = None
        if CHINESE_NLP_AVAILABLE:
            self.nlp_processor = ChineseNLPProcessor(use_bert=False)

        self.entity_recognizer = None
        if ENHANCED_ENTITY_RECOGNIZER_AVAILABLE:
            self.entity_recognizer = EnhancedEntityRecognizer()

        # 向量数据库
        self.vector_db = None
        self.vector_index = None
        self.document_store = []

        # 任务队列
        self.task_queue = []
        self.processing_tasks = defaultdict(list)

        # 统计信息
        self.stats = {
            "total_queries": 0,
            "total_processing_time": 0.0,
            "avg_response_time": 0.0,
            "cache_hits": 0,
            "cache_misses": 0,
        }

        # 初始化向量数据库
        self._init_vector_db()

        logger.info(f"AI推理引擎初始化完成,模型: {model_name},模拟模式: {use_mock}")

    def _init_vector_db(self) -> Any:
        """初始化向量数据库"""
        if FAISS_AVAILABLE:
            try:
                # 创建FAISS索引
                self.vector_index = faiss.IndexFlatIP(1024)  # BGE-M3标准维度为1024维
                logger.info("向量数据库初始化完成")
            except Exception:
                self.vector_index = None
        else:
            logger.warning("FAISS不可用,将使用基础检索")

    def _get_cache_key(self, content: str) -> str:
        """生成缓存键"""
        return hashlib.md5(content.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()

    def _load_from_cache(self, cache_key: str) -> Any | None:
        """从缓存加载结果"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass  # TODO: 处理异常
        return None

    def _save_to_cache(self, cache_key: str, data: Any) -> Any:
        """保存结果到缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"⚠️ 保存缓存失败: {e}")

    def _mock_openai_response(self, prompt: str, context: str = "") -> str:
        """模拟OpenAI响应"""
        # 简单的基于规则的响应生成
        patent_keywords = [
            "专利号",
            "申请号",
            "权利要求",
            "无效",
            "有效",
            "新颖性",
            "创造性",
            "专利法",
        ]
        question_lower = prompt.lower()

        if any(keyword in question_lower for keyword in patent_keywords):
            if "无效" in question_lower or "有效" in question_lower:
                return "根据专利法的规定,专利权的无效宣告需要满足法定条件。通常包括:缺乏新颖性、创造性或实用性,或者专利保护范围不清楚等。具体分析需要结合具体的证据和法律条文。"
            elif "新颖性" in question_lower:
                return "新颖性是指发明在申请日以前未被国内外出版物公开过、未被公开使用过或者以其他方式为公众所知。在专利无效宣告程序中,如果现有技术已经公开了相同的发明创造,则该专利不具备新颖性。"
            elif "创造性" in question_lower:
                return "创造性是指与现有技术相比,该发明具有突出的实质性特点和显著的进步。判断创造性需要考虑:发明的技术方案、技术效果、解决的技术问题等,以及本领域技术人员的水平。"
            elif "权利要求" in question_lower:
                return "权利要求书是专利文件的核心部分,界定了专利保护的范围。在无效宣告程序中,通常会对权利要求进行解释,分析其保护范围是否清楚,是否得到说明书的支持等。"
            else:
                return "这是一个专利相关的问题。专利无效宣告是指根据专利法的规定,对已经授予的专利权宣告其自始无效的程序。通常由利害关系人向专利复审委员会提出请求。"
        else:
            return "我是专利无效宣告知识图谱系统的AI助手,可以帮助您分析专利文件、识别实体、提取关键信息,并提供专利法律相关的分析。请问您有什么具体的专利问题需要咨询?"

    def _call_openai_api(self, prompt: str, context: str = "") -> tuple[str, float]:
        """调用OpenAI API"""
        if self.use_mock:
            return self._mock_openai_response(prompt, context), 0.8

        try:
            if not OPENAI_AVAILABLE or not self.openai_api_key:
                logger.warning("OpenAI API不可用,使用模拟响应")
                return self._mock_openai_response(prompt, context), 0.8

            # 设置API密钥
            openai.api_key = self.openai_api_key

            # 构建完整提示
            full_prompt = f"""
            你是一个专业的专利分析师,专门处理专利无效宣告相关的问题。请基于以下上下文和问题,提供专业、准确的回答。

            上下文信息:
            {context}

            用户问题:
            {prompt}

            请用中文回答,并提供详细的分析和建议。
            """

            start_time = time.time()

            # 调用API
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业的专利分析师,专门处理专利无效宣告相关的问题。",
                    },
                    {"role": "user", "content": full_prompt},
                ],
                max_tokens=1500,
                temperature=0.7,
            )

            processing_time = time.time() - start_time
            answer = response.choices.get(0).message.content.strip()

            return answer, processing_time

        except Exception:
            pass  # TODO: 处理异常
            return self._mock_openai_response(prompt, context), 0.5

    def _enhance_context_with_entities(self, text: str) -> str:
        """用实体信息增强上下文"""
        if not self.entity_recognizer:
            return text

        try:
            # 识别实体
            result = self.entity_recognizer.recognize_entities(text)
            entities = result.entities

            # 构建增强的上下文
            enhanced_context = text + "\n\n识别到的关键实体信息:\n"
            for entity in entities[:10]:  # 限制前10个实体
                enhanced_context += (
                    f"- {entity.entity_type}: {entity.text} (置信度: {entity.confidence:.2f})\n"
                )

            return enhanced_context

        except Exception:
            pass  # TODO: 处理异常
            return text

    def _search_relevant_documents(self, query: str, top_k: int = 5) -> list[str]:
        """搜索相关文档"""
        if not self.document_store:
            return []

        try:
            # 简单的关键词匹配搜索
            query_terms = query.split()
            relevant_docs = []

            for doc in self.document_store:
                doc_text = doc["text"]
                score = 0

                for term in query_terms:
                    if term in doc_text:
                        score += doc_text.count(term)

                if score > 0:
                    relevant_docs.append((doc["text"], score))

            # 按相关性排序
            relevant_docs.sort(key=lambda x: x[1], reverse=True)
            return [doc[0] for doc in relevant_docs[:top_k]]

        except Exception:
            pass  # TODO: 处理异常
            return []

    def add_document_to_store(
        self, doc_id: str, text: str, metadata: dict[str, Any] | None = None
    ) -> None:
        """添加文档到存储"""
        document = {"id": doc_id, "text": text, "metadata": metadata or {}, "added_at": time.time()}
        self.document_store.append(document)
        logger.info(f"文档已添加到存储: {doc_id}")

    def analyze_patent_document(self, document_text: str) -> dict[str, Any]:
        """分析专利文档"""
        start_time = time.time()

        try:
            # 1. NLP处理
            nlp_result = None
            if self.nlp_processor:
                nlp_result = self.nlp_processor.process_text(document_text)

            # 2. 实体识别
            entity_result = None
            if self.entity_recognizer:
                entity_result = self.entity_recognizer.recognize_entities(document_text)

            # 3. 生成分析报告
            analysis_prompt = f"""
            请分析以下专利文档,并提供专业的分析报告:

            文档内容:
            {document_text[:2000]}...

            请从以下角度进行分析:
            1. 专利类型和技术领域
            2. 关键技术特征
            3. 潜在的法律风险点
            4. 无效宣告的可能性评估
            5. 建议的应对策略
            """

            context = ""
            if nlp_result:
                context += f"摘要: {nlp_result.summary}\n"
                context += f"关键词: {', '.join(nlp_result.keywords[:10])}\n"

            if entity_result:
                context += f"识别实体数: {len(entity_result.entities)}\n"
                entity_types = ", ".join(
                    {entity.entity_type for entity in entity_result.entities}
                )
                context += f"实体类型: {entity_types}\n"

            # 调用AI分析
            ai_response, _ai_time = self._call_openai_api(analysis_prompt, context)

            processing_time = time.time() - start_time

            analysis_result = {
                "document_id": f"doc_{int(time.time())}",
                "analysis_report": ai_response,
                "nlp_result": nlp_result,
                "entity_result": entity_result,
                "processing_time": processing_time,
                "confidence": 0.8,
                "timestamp": time.time(),
            }

            return analysis_result

        except Exception as e:
            pass  # TODO: 处理异常
            return {"error": str(e), "timestamp": time.time()}

    def answer_question(self, question: str, context: str = "") -> QueryResult:
        """回答问题"""
        time.time()

        # 检查缓存
        cache_key = self._get_cache_key(f"{question}_{context}")
        cached_result = self._load_from_cache(cache_key)
        if cached_result:
            self.stats["cache_hits"] += 1
            return QueryResult(**cached_result)

        self.stats["cache_misses"] += 1

        # 增强上下文
        enhanced_context = self._enhance_context_with_entities(context)

        # 搜索相关文档
        relevant_docs = self._search_relevant_documents(question)
        if relevant_docs:
            enhanced_context += "\n\n相关文档信息:\n"
            for i, doc in enumerate(relevant_docs[:3], 1):
                enhanced_context += f"文档{i}: {doc[:500]}...\n"

        # 调用AI回答
        answer, processing_time = self._call_openai_api(question, enhanced_context)

        # 提取信息来源
        sources = []
        if relevant_docs:
            sources = [f"相关文档_{i+1}" for i in range(len(relevant_docs))]

        result = QueryResult(
            query=question,
            answer=answer,
            confidence=0.8,
            sources=sources,
            processing_time=processing_time,
            method_used="openai_api",
            metadata={"context_length": len(enhanced_context), "sources_count": len(sources)},
        )

        # 保存到缓存
        self._save_to_cache(cache_key, asdict(result))

        # 更新统计
        self.stats["total_queries"] += 1
        self.stats["total_processing_time"] += result.processing_time
        self.stats["avg_response_time"] = (
            self.stats["total_processing_time"] / self.stats["total_queries"]
        )

        return result

    def batch_analyze_documents(self, documents: list[tuple[str, str]]) -> list[dict[str, Any]]:
        """批量分析文档"""
        results = []
        total = len(documents)

        logger.info(f"开始批量分析 {total} 个文档")

        for i, (doc_id, doc_text) in enumerate(documents, 1):
            logger.info(f"分析进度: {i}/{total}")
            result = self.analyze_patent_document(doc_text)
            result["document_id"] = doc_id
            results.append(result)

        logger.info(f"批量分析完成,共处理 {total} 个文档")
        return results

    def generate_patent_summary(self, patent_info: dict[str, Any]) -> dict[str, Any]:
        """生成专利摘要"""
        try:
            summary_prompt = f"""
            请基于以下专利信息生成专业的专利摘要:

            专利信息:
            {json.dumps(patent_info, ensure_ascii=False, indent=2)}

            请生成以下内容:
            1. 专利基本信息
            2. 技术方案概述
            3. 关键创新点
            4. 保护范围分析
            5. 法律风险评估
            """

            answer, processing_time = self._call_openai_api(summary_prompt)

            return {
                "patent_info": patent_info,
                "summary": answer,
                "processing_time": processing_time,
                "timestamp": time.time(),
            }

        except Exception as e:
            pass  # TODO: 处理异常
            return {"error": str(e)}

    def validate_patent_claim(self, claim_text: str) -> dict[str, Any]:
        """验证权利要求"""
        try:
            validation_prompt = f"""
            请从专利法律角度分析以下权利要求的有效性:

            权利要求内容:
            {claim_text}

            请分析:
            1. 权利要求的清晰度
            2. 保护范围的合理性
            3. 技术特征的完整性
            4. 是否符合专利法的要求
            5. 潜在的无效风险点
            6. 改进建议
            """

            answer, processing_time = self._call_openai_api(validation_prompt)

            return {
                "claim_text": claim_text,
                "validation_result": answer,
                "processing_time": processing_time,
                "timestamp": time.time(),
            }

        except Exception as e:
            pass  # TODO: 处理异常
            return {"error": str(e)}

    def compare_patents(self, patent1_info: dict, patent2_info: dict) -> dict[str, Any]:
        """比较两个专利"""
        try:
            comparison_prompt = f"""
            请比较以下两个专利的异同点:

            专利1信息:
            {json.dumps(patent1_info, ensure_ascii=False, indent=2)}

            专利2信息:
            {json.dumps(patent2_info, ensure_ascii=False, indent=2)}

            请从以下角度进行比较:
            1. 技术方案对比
            2. 保护范围差异
            3. 创新点分析
            4. 新颖性评估
            5. 侵权可能性分析
            6. 法律风险对比
            """

            answer, processing_time = self._call_openai_api(comparison_prompt)

            return {
                "patent1_info": patent1_info,
                "patent2_info": patent2_info,
                "comparison_result": answer,
                "processing_time": processing_time,
                "timestamp": time.time(),
            }

        except Exception as e:
            pass  # TODO: 处理异常
            return {"error": str(e)}

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = self.stats.copy()
        stats["document_store_size"] = len(self.document_store)
        stats["vector_db_available"] = self.vector_index is not None
        stats["nlp_processor_available"] = self.nlp_processor is not None
        stats["entity_recognizer_available"] = self.entity_recognizer is not None
        stats["cache_hit_rate"] = (
            (stats["cache_hits"] / (stats["cache_hits"] + stats["cache_misses"]))
            if (stats["cache_hits"] + stats["cache_misses"]) > 0
            else 0
        )
        return stats

    def save_state(self, save_path: str) -> None:
        """保存状态"""
        try:
            save_dir = Path(save_path)
            save_dir.mkdir(exist_ok=True)

            state = {
                "stats": self.stats,
                "document_store": self.document_store,
                "model_config": {"model_name": self.model_name, "use_mock": self.use_mock},
            }

            with open(save_dir / "ai_reasoning_state.json", "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)

            logger.info(f"AI推理引擎状态已保存到: {save_path}")

        except Exception as e:
            logger.error(f"❌ 保存状态失败: {e}")

    def load_state(self, load_path: str) -> Any | None:
        """加载状态"""
        try:
            load_dir = Path(load_path)
            state_file = load_dir / "ai_reasoning_state.json"

            if state_file.exists():
                with open(state_file, encoding="utf-8") as f:
                    state = json.load(f)

                self.stats = state.get("stats", self.stats)
                self.document_store = state.get("document_store", [])

                model_config = state.get("model_config", {})
                self.model_name = model_config.get("model_name", self.model_name)
                self.use_mock = model_config.get("use_mock", self.use_mock)

                logger.info(f"AI推理引擎状态已从 {load_path} 加载")

        except Exception as e:
            logger.error(f"❌ 加载状态失败: {e}")
            return None


def main() -> None:
    """测试函数"""
    print("=== AI推理引擎演示 ===")

    # 初始化AI推理引擎(使用模拟模式)
    engine = AIReasoningEngine(model_name="gpt-3.5-turbo", use_mock=True)  # 使用模拟模式进行演示

    # 添加示例文档
    sample_document = """
    专利号:CN202110123456.7
    发明名称:一种人工智能专利分析方法
    技术领域:本发明涉及专利分析技术领域,特别是一种基于人工智能的专利无效宣告分析方法。

    背景技术:现有的专利分析方法主要依赖人工审查,效率低下且容易产生主观偏差。

    发明内容:本发明提供了一种人工智能专利分析方法,包括:
    1. 文档自动处理模块,用于解析专利文档;
    2. 实体识别模块,用于提取关键实体信息;
    3. 法律规则匹配模块,用于评估专利有效性;
    4. 智能分析模块,用于生成分析报告。
    """

    doc_id = "sample_patent_001"
    engine.add_document_to_store(doc_id, sample_document, {"type": "patent"})

    # 测试问题回答
    questions = [
        "这个专利的发明点是什么?",
        "分析该专利的新颖性和创造性",
        "专利权利要求应该如何撰写?",
        "什么情况下专利会被宣告无效?",
    ]

    print("\n=== 问题回答测试 ===")
    for i, question in enumerate(questions, 1):
        print(f"\n问题 {i}: {question}")
        result = engine.answer_question(question, sample_document)
        print(f"回答: {result.answer}")
        print(f"置信度: {result.confidence:.2f}")
        print(f"处理时间: {result.processing_time:.2f}秒")

    # 测试专利文档分析
    print("\n=== 专利文档分析测试 ===")
    analysis = engine.analyze_patent_document(sample_document)
    if "analysis_report" in analysis:
        print(f"分析报告:\n{analysis['analysis_report']}")
        print(f"处理时间: {analysis['processing_time']:.2f}秒")

    # 测试统计信息
    print("\n=== 统计信息 ===")
    stats = engine.get_statistics()
    print(f"总查询数: {stats['total_queries']}")
    print(f"平均响应时间: {stats['avg_response_time']:.2f}秒")
    print(f"缓存命中率: {stats['cache_hit_rate']:.2%}")
    print(f"文档存储数量: {stats['document_store_size']}")


if __name__ == "__main__":
    main()
