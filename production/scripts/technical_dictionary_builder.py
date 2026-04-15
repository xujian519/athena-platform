#!/usr/bin/env python3
"""
技术词典知识图谱构建器
Technical Dictionary Knowledge Graph Builder

利用本地NLP系统和大模型构建技术词典知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v3.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import aiohttp

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TechTermEntity:
    """技术术语实体"""
    entity_id: str
    entity_type: str
    term_name: str
    term_english: str
    definition: str
    category: str
    domain: str
    attributes: dict
    confidence: float
    source_chunk: str

@dataclass
class TechTermRelation:
    """技术术语关系"""
    relation_id: str
    subject_id: str
    object_id: str
    relation_type: str
    attributes: dict
    confidence: float
    source_chunk: str

class TechnicalDictionaryBuilder:
    """技术词典知识图谱构建器"""

    def __init__(self):
        # NLP服务配置
        self.nlp_url = "http://localhost:8001"
        self.nlp_model = "technical_terminology"
        self.llm_url = "http://localhost:8002"

        # 实体类型定义
        self.entity_types = {
            "TECH_TERM": "技术术语",
            "CONCEPT": "概念",
            "PROCESS": "工艺流程",
            "MATERIAL": "材料",
            "EQUIPMENT": "设备",
            "STANDARD": "标准",
            "PARAMETER": "参数",
            "FORMULA": "公式",
            "METHOD": "方法",
            "TECHNOLOGY": "技术",
            "APPLICATION": "应用",
            "INDUSTRY": "行业",
            "DOMAIN": "领域",
            "CATEGORY": "类别",
            "PROPERTY": "属性",
            "UNIT": "单位"
        }

        # 关系类型定义
        self.relation_types = {
            "IS_A": "是一种",
            "HAS_PROPERTY": "具有属性",
            "BELONGS_TO": "属于",
            "RELATED_TO": "相关于",
            "SIMILAR_TO": "类似于",
            "OPPOSITE_OF": "相反于",
            "CAUSES": "导致",
            "USED_IN": "用于",
            "REQUIRES": "需要",
            "PRODUCES": "产生",
            "MEASURES": "测量",
            "DEFINED_AS": "定义为",
            "EXAMPLE_OF": "是...的例子",
            "APPLIES_TO": "适用于",
            "DEPENDS_ON": "依赖于",
            "IMPROVES": "改进",
            "REPLACES": "替代"
        }

        # 技术领域分类
        self.technical_domains = {
            "人工智能": ["机器学习", "深度学习", "神经网络", "自然语言处理", "计算机视觉"],
            "机械工程": ["力学", "热力学", "流体力学", "材料力学", "机械设计"],
            "电子信息": ["电路", "信号处理", "通信", "控制", "半导体"],
            "化学工程": ["反应工程", "分离工程", "传质", "传热", "化工原理"],
            "生物医学": ["生物化学", "分子生物学", "遗传学", "药理学", "医学工程"],
            "材料科学": ["金属材料", "非金属材料", "复合材料", "纳米材料", "功能材料"],
            "能源工程": ["传统能源", "新能源", "储能", "节能", "能源转换"],
            "环境工程": ["水处理", "大气污染", "固废处理", "噪声控制", "环境监测"]
        }

        # 正则表达式模式
        self.patterns = {
            # 英文术语
            "english_term": r"\b([A-Z][a-zA-Z\s\-]+)\b",
            # 中文术语
            "chinese_term": r"[\u4e00-\u9fa5]+[^\s，。；：！？]*",
            # 定义模式
            "definition": r"是指|定义为|指的是|即|也就是",
            # 单位
            "unit": r"([°℃℉%‰mmcmkg])",
            # 数字
            "number": r"(\d+\.?\d*)",
            # 参数范围
            "range": r"(\d+\.?\d*)\s*[-~至到]\s*(\d+\.?\d*)",
            # 公式
            "formula": r"([A-Z]+[a-z]*\s*=\s*[^。；\n]+)"
        }

    async def extract_entities_with_nlp(self, text: str, chunk_id: str) -> list[TechTermEntity]:
        """使用NLP服务提取技术术语实体"""
        entities = []

        try:
            # 调用NLP服务进行实体识别
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": text,
                    "task": "extract_technical_terms",
                    "domain": "technical_dictionary",
                    "model": self.nlp_model
                }

                async with session.post(
                    f"{self.nlp_url}/extract_technical_terms",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        nlp_entities = data.get("entities", [])

                        # 转换为TechTermEntity格式
                        for nlp_entity in nlp_entities:
                            entity = TechTermEntity(
                                entity_id=self._generate_entity_id(
                                    nlp_entity.get("term", ""), chunk_id
                                ),
                                entity_type=nlp_entity.get("type", "TECH_TERM"),
                                term_name=nlp_entity.get("term", ""),
                                term_english=nlp_entity.get("english", ""),
                                definition=nlp_entity.get("definition", ""),
                                category=nlp_entity.get("category", ""),
                                domain=self._identify_domain(text, nlp_entity.get("term", "")),
                                attributes={
                                    "position": nlp_entity.get("position", 0),
                                    "context": nlp_entity.get("context", ""),
                                    "synonyms": nlp_entity.get("synonyms", []),
                                    "dev/examples": nlp_entity.get("dev/examples", []),
                                    "confidence_nlp": nlp_entity.get("confidence", 0.8)
                                },
                                confidence=nlp_entity.get("confidence", 0.8),
                                source_chunk=chunk_id
                            )
                            entities.append(entity)
                    else:
                        logger.warning(f"NLP实体提取失败: {response.status}")

        except Exception as e:
            logger.error(f"NLP调用失败: {e}")
            # 使用规则提取作为后备
            entities = self._extract_entities_with_rules(text, chunk_id)

        return entities

    def _extract_entities_with_rules(self, text: str, chunk_id: str) -> list[TechTermEntity]:
        """使用规则提取技术术语实体（后备方案）"""
        entities = []

        # 查找定义模式
        sentences = text.split('。')
        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            # 查找"术语是指..."的模式
            for def_pattern in self.patterns["definition"].split('|'):
                if def_pattern in sentence:
                    parts = sentence.split(def_pattern)
                    if len(parts) >= 2:
                        term = parts[0].strip()
                        definition = parts[1].strip()

                        # 提取英文术语
                        english_terms = re.findall(self.patterns["english_term"], sentence)
                        english = english_terms[0] if english_terms else ""

                        entity = TechTermEntity(
                            entity_id=self._generate_entity_id(term, chunk_id),
                            entity_type=self._classify_term_type(term, definition),
                            term_name=term,
                            term_english=english,
                            definition=definition,
                            category=self._extract_category(sentence),
                            domain=self._identify_domain(sentence, term),
                            attributes={
                                "source_pattern": "rule_based",
                                "sentence_context": sentence
                            },
                            confidence=0.7,
                            source_chunk=chunk_id
                        )
                        entities.append(entity)

        return entities

    async def extract_relations_with_llm(self, text: str, entities: list[TechTermEntity], chunk_id: str) -> list[TechTermRelation]:
        """使用本地大模型提取术语关系"""
        relations = []

        try:
            # 准备实体信息
            entity_list = [
                {
                    "term": e.term_name,
                    "english": e.term_english,
                    "definition": e.definition,
                    "type": e.entity_type,
                    "domain": e.domain
                }
                for e in entities
            ]

            # 调用本地大模型进行关系提取
            async with aiohttp.ClientSession() as session:
                prompt = self._build_relation_extraction_prompt(text, entity_list)
                payload = {
                    "model": "qwen2.5:14b",
                    "prompt": prompt,
                    "max_tokens": 2048,
                    "temperature": 0.1
                }

                async with session.post(
                    f"{self.llm_url}/api/generate",
                    json=payload,
                    timeout=60
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        llm_response = data.get("response", "")

                        # 解析LLM响应中的关系
                        relations = self._parse_llm_relations(llm_response, entities, chunk_id)
                    else:
                        logger.warning(f"LLM关系提取失败: {response.status}")

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 使用规则提取作为后备
            relations = self._extract_relations_with_rules(text, entities, chunk_id)

        return relations

    def _build_relation_extraction_prompt(self, text: str, entities: list[dict]) -> str:
        """构建关系提取提示词"""
        prompt = f"""你是一个专业的技术领域专家。请分析以下文本，识别技术术语之间的关系。

文本内容：
{text}

已识别的技术术语：
{json.dumps(entities, ensure_ascii=False, indent=2)}

请识别以下类型的关系：
1. 继承关系（is_a）：一个术语是另一个术语的子类
2. 属性关系（has_property）：术语具有的属性或特征
3. 应用关系（used_in）：术语在哪些场景或领域应用
4. 因果关系（causes）：术语之间的因果联系
5. 相似关系（similar_to）：术语之间的相似性
6. 依赖关系（depends_on）：术语之间的依赖关系

以JSON格式返回关系列表：
{{
    "relations": [
        {{
            "subject": "术语1",
            "object": "术语2",
            "type": "关系类型",
            "confidence": 0.9,
            "reason": "判断依据"
        }}
    ]
}}
"""
        return prompt

    def _parse_llm_relations(self, llm_response: str, entities: list[TechTermEntity], chunk_id: str) -> list[TechTermRelation]:
        """解析LLM响应中的关系"""
        relations = []
        entity_map = {e.term_name: e for e in entities}

        try:
            # 尝试解析JSON响应
            response_data = json.loads(llm_response)
            llm_relations = response_data.get("relations", [])

            for rel in llm_relations:
                subject_term = rel.get("subject", "")
                object_term = rel.get("object", "")

                if subject_term in entity_map and object_term in entity_map:
                    relation = TechTermRelation(
                        relation_id=self._generate_relation_id(
                            entity_map[subject_term].entity_id,
                            entity_map[object_term].entity_id,
                            rel.get("type", "RELATED_TO")
                        ),
                        subject_id=entity_map[subject_term].entity_id,
                        object_id=entity_map[object_term].entity_id,
                        relation_type=rel.get("type", "RELATED_TO"),
                        attributes={
                            "reason": rel.get("reason", ""),
                            "confidence_llm": rel.get("confidence", 0.7),
                            "domain": entity_map[subject_term].domain,
                            "relation_context": f"{subject_term} -> {rel.get('type', 'RELATED_TO')} -> {object_term}"
                        },
                        confidence=rel.get("confidence", 0.7),
                        source_chunk=chunk_id
                    )
                    relations.append(relation)

        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            # 使用规则提取作为后备
            relations = self._extract_relations_with_rules("", entities, chunk_id)

        return relations

    def _extract_relations_with_rules(self, text: str, entities: list[TechTermEntity], chunk_id: str) -> list[TechTermRelation]:
        """使用规则提取术语关系（后备方案）"""
        relations = []

        # 基于同域实体生成关系
        domain_groups = defaultdict(list)
        for entity in entities:
            domain_groups[entity.domain].append(entity)

        for domain, domain_entities in domain_groups.items():
            # 在同一领域内生成关系
            for i, entity1 in enumerate(domain_entities):
                for j, entity2 in enumerate(domain_entities):
                    if i >= j:
                        continue

                    # 检查是否是包含关系
                    if entity1.term_name in entity2.definition or entity2.term_name in entity1.definition:
                        # 确定父子关系
                        if len(entity1.definition) > len(entity2.definition):
                            parent, child = entity1, entity2
                        else:
                            parent, child = entity2, entity1

                        relation = TechTermRelation(
                            relation_id=self._generate_relation_id(
                                parent.entity_id, child.entity_id, "IS_A"
                            ),
                            subject_id=child.entity_id,
                            object_id=parent.entity_id,
                            relation_type="IS_A",
                            attributes={
                                "rule_type": "definition_containment",
                                "domain": domain
                            },
                            confidence=0.8,
                            source_chunk=chunk_id
                        )
                        relations.append(relation)

                    # 检查是否是相关关系
                    elif self._terms_are_related(entity1, entity2):
                        relation = TechTermRelation(
                            relation_id=self._generate_relation_id(
                                entity1.entity_id, entity2.entity_id, "RELATED_TO"
                            ),
                            subject_id=entity1.entity_id,
                            object_id=entity2.entity_id,
                            relation_type="RELATED_TO",
                            attributes={
                                "rule_type": "domain_similarity",
                                "domain": domain,
                                "similarity_score": self._calculate_similarity(entity1, entity2)
                            },
                            confidence=0.6,
                            source_chunk=chunk_id
                        )
                        relations.append(relation)

        return relations

    def _classify_term_type(self, term: str, definition: str) -> str:
        """分类术语类型"""
        type_keywords = {
            "MATERIAL": ["材料", "物质", "合金", "塑料", "陶瓷", "复合材料"],
            "EQUIPMENT": ["设备", "机器", "仪器", "装置", "系统", "工具"],
            "PROCESS": ["工艺", "流程", "方法", "技术", "步骤", "程序"],
            "PARAMETER": ["参数", "指标", "数值", "系数", "率", "度"],
            "STANDARD": ["标准", "规范", "规定", "要求", "条件"],
            "CONCEPT": ["概念", "定义", "原理", "理论", "思想"]
        }

        text = f"{term} {definition}".lower()

        for term_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return term_type

        return "TECH_TERM"

    def _extract_category(self, text: str) -> str:
        """提取术语类别"""
        category_patterns = [
            r"([^\s，。；：]{1,10})(类|类型|种类)",
            r"分为([^\s，。；：]{1,10})",
            r"属于([^\s，。；：]{1,10})"
        ]

        for pattern in category_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return "未分类"

    def _identify_domain(self, text: str, term: str) -> str:
        """识别技术领域"""
        for domain, keywords in self.technical_domains.items():
            for keyword in keywords:
                if keyword in text or keyword in term:
                    return domain

        # 基于文本特征判断
        if "专利" in text or "发明" in text:
            return "专利技术"
        elif "医学" in text or "医疗" in text:
            return "生物医学"
        elif "计算机" in text or "软件" in text:
            return "信息技术"
        elif "化学" in text or "化工" in text:
            return "化学工程"

        return "通用技术"

    def _terms_are_related(self, entity1: TechTermEntity, entity2: TechTermEntity) -> bool:
        """判断两个术语是否相关"""
        # 检查共享关键词
        words1 = set(entity1.definition.split())
        words2 = set(entity2.definition.split())

        common_words = words1 & words2
        if len(common_words) > 2:
            return True

        # 检查类别相同
        if entity1.category == entity2.category and entity1.category != "未分类":
            return True

        # 检查英文术语相似
        if entity1.term_english and entity2.term_english:
            words_en1 = entity1.term_english.lower().split()
            words_en2 = entity2.term_english.lower().split()
            common_en = words_en1 & words_en2
            if common_en:
                return True

        return False

    def _calculate_similarity(self, entity1: TechTermEntity, entity2: TechTermEntity) -> float:
        """计算术语相似度"""
        # 简单的基于共同词的相似度计算
        words1 = set(entity1.definition.split())
        words2 = set(entity2.definition.split())

        if not words1 or not words2:
            return 0.0

        common_words = words1 & words2
        total_words = words1 | words2

        similarity = len(common_words) / len(total_words)

        # 调整因子
        if entity1.category == entity2.category:
            similarity += 0.1

        if entity1.domain == entity2.domain:
            similarity += 0.1

        return min(similarity, 1.0)

    def _generate_entity_id(self, term: str, chunk_id: str) -> str:
        """生成实体ID"""
        content = f"{term}_{chunk_id}"
        return short_hash(content.encode())[:16]

    def _generate_relation_id(self, subject_id: str, object_id: str, relation_type: str) -> str:
        """生成关系ID"""
        content = f"{subject_id}_{object_id}_{relation_type}"
        return short_hash(content.encode())[:16]

    async def process_dictionary_data(self, data_dir: Path, output_dir: Path):
        """处理技术词典数据"""
        logger.info("开始处理技术词典数据")

        all_entities = []
        all_relations = []

        # 查找技术词典文件
        dict_files = list(data_dir.rglob("*dict*"))
        dict_files.extend(data_dir.rglob("*lexicon*"))
        dict_files.extend(data_dir.rglob("*术语*"))
        dict_files.extend(data_dir.rglob("*技术*"))
        dict_files.extend(data_dir.rglob("*词汇*"))

        if not dict_files:
            logger.warning(f"在 {data_dir} 中未找到技术词典文件")
            # 使用模拟数据
            await self._process_sample_data(output_dir)
            return

        # 处理每个词典文件
        for file_path in dict_files[:50]:  # 限制处理数量
            logger.info(f"处理文件: {file_path.name}")

            try:
                # 读取文件内容
                content = file_path.read_text(encoding='utf-8')

                # 分块处理
                chunks = self._split_content(content)
                chunk_id_prefix = file_path.stem

                # 处理每个块
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{chunk_id_prefix}_chunk_{i}"

                    # 提取实体
                    entities = await self.extract_entities_with_nlp(chunk, chunk_id)
                    all_entities.extend(entities)

                    # 提取关系
                    relations = await self.extract_relations_with_llm(chunk, entities, chunk_id)
                    all_relations.extend(relations)

            except Exception as e:
                logger.error(f"处理文件 {file_path} 失败: {e}")

        # 统计信息
        entity_stats = Counter(e.entity_type for e in all_entities)
        relation_stats = Counter(r.relation_type for r in all_relations)

        logger.info("\n📊 处理统计:")
        logger.info(f"  总术语数: {len(all_entities)}")
        logger.info(f"  总关系数: {len(all_relations)}")

        # 保存结果
        self._save_results(all_entities, all_relations, entity_stats, relation_stats, output_dir)

    async def _process_sample_data(self, output_dir: Path):
        """处理示例数据（当没有真实数据时）"""
        logger.info("使用示例技术词典数据进行演示")

        sample_terms = [
            {
                "term": "神经网络",
                "english": "Neural Network",
                "definition": "一种模仿生物神经网络结构和功能的数学模型或计算模型",
                "category": "计算模型",
                "domain": "人工智能"
            },
            {
                "term": "深度学习",
                "english": "Deep Learning",
                "definition": "机器学习的分支，使用多层神经网络学习数据的表示",
                "category": "学习方法",
                "domain": "人工智能"
            },
            {
                "term": "机器学习",
                "english": "Machine Learning",
                "definition": "计算机系统利用数据自动改善性能的科学",
                "category": "计算科学",
                "domain": "人工智能"
            },
            {
                "term": "纳米材料",
                "english": "Nanomaterial",
                "definition": "至少在一维尺寸上处于纳米尺度范围的材料",
                "category": "材料",
                "domain": "材料科学"
            },
            {
                "term": "复合材料",
                "english": "Composite Material",
                "definition": "由两种或两种以上不同性质的材料组合而成的材料",
                "category": "材料",
                "domain": "材料科学"
            }
        ]

        all_entities = []
        all_relations = []

        # 创建实体
        for i, data in enumerate(sample_terms):
            entity = TechTermEntity(
                entity_id=f"sample_entity_{i}",
                entity_type=self._classify_term_type(data["term"], data["definition"]),
                term_name=data["term"],
                term_english=data["english"],
                definition=data["definition"],
                category=data["category"],
                domain=data["domain"],
                attributes={
                    "source": "sample_data",
                    "language": "zh-en"
                },
                confidence=1.0,
                source_chunk="sample"
            )
            all_entities.append(entity)

        # 创建关系
        # 神经网络 is_a 机器学习
        relation1 = TechTermRelation(
            relation_id="sample_rel_0",
            subject_id="sample_entity_0",  # 神经网络
            object_id="sample_entity_2",  # 机器学习
            relation_type="IS_A",
            attributes={"type": "hierarchical"},
            confidence=0.9,
            source_chunk="sample"
        )
        all_relations.append(relation1)

        # 深度学习 is_a 机器学习
        relation2 = TechTermRelation(
            relation_id="sample_rel_1",
            subject_id="sample_entity_1",  # 深度学习
            object_id="sample_entity_2",  # 机器学习
            relation_type="IS_A",
            attributes={"type": "hierarchical"},
            confidence=0.9,
            source_chunk="sample"
        )
        all_relations.append(relation2)

        # 神经网络 related_to 深度学习
        relation3 = TechTermRelation(
            relation_id="sample_rel_2",
            subject_id="sample_entity_0",  # 神经网络
            object_id="sample_entity_1",  # 深度学习
            relation_type="RELATED_TO",
            attributes={"type": "technical_correlation"},
            confidence=0.8,
            source_chunk="sample"
        )
        all_relations.append(relation3)

        # 保存结果
        entity_stats = Counter(e.entity_type for e in all_entities)
        relation_stats = Counter(r.relation_type for r in all_relations)

        self._save_results(all_entities, all_relations, entity_stats, relation_stats, output_dir)

    def _split_content(self, content: str, chunk_size: int = 800) -> list[str]:
        """内容分块"""
        chunks = []
        paragraphs = content.split('\n')
        current_chunk = ""
        current_size = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # 检查是否需要分块
            if current_size + len(paragraph) > chunk_size and current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = paragraph
                current_size = len(paragraph)
            else:
                if current_chunk:
                    current_chunk += "\n" + paragraph
                else:
                    current_chunk = paragraph
                current_size += len(paragraph)

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def _save_results(self, entities: list[TechTermEntity], relations: list[TechTermRelation],
                      entity_stats: Counter, relation_stats: Counter, output_dir: Path):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建输出目录
        output_dir = output_dir / "technical_dictionary_kg"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存实体
        entities_file = output_dir / f"tech_entities_{timestamp}.json"
        entities_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "技术词典知识图谱实体",
                "total_entities": len(entities),
                "entity_types": dict(entity_stats),
                "nlp_integration": True
            },
            "entities": [asdict(e) for e in entities]
        }
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = output_dir / f"tech_relations_{timestamp}.json"
        relations_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "技术词典知识图谱关系",
                "total_relations": len(relations),
                "relation_types": dict(relation_stats),
                "llm_integration": True
            },
            "relations": [asdict(r) for r in relations]
        }
        with open(relations_file, 'w', encoding='utf-8') as f:
            json.dump(relations_data, f, ensure_ascii=False, indent=2)

        # 生成NebulaGraph导入脚本
        self._generate_nebula_scripts(entities, relations, output_dir, timestamp)

        # 保存统计
        stats_file = output_dir / f"tech_stats_{timestamp}.json"
        stats = {
            "timestamp": datetime.now().isoformat(),
            "entity_types": self.entity_types,
            "relation_types": self.relation_types,
            "entity_statistics": dict(entity_stats),
            "relation_statistics": dict(relation_stats),
            "technical_domains": self.technical_domains,
            "processing_summary": {
                "total_entities": len(entities),
                "total_relations": len(relations),
                "unique_terms": len({e.term_name for e in entities}),
                "domains_covered": len({e.domain for e in entities})
            }
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info("💾 技术词典知识图谱已保存:")
        logger.info(f"  实体文件: {entities_file}")
        logger.info(f"  关系文件: {relations_file}")
        logger.info(f"  统计文件: {stats_file}")

    def _generate_nebula_scripts(self, entities: list[TechTermEntity], relations: list[TechTermRelation],
                                 output_dir: Path, timestamp: str):
        """生成NebulaGraph导入脚本"""
        # 创建tags
        tags_dir = output_dir / "nebula_tags"
        tags_dir.mkdir(exist_ok=True)

        # 为每种实体类型创建tag文件
        for entity_type, _type_name in self.entity_types.items():
            type_entities = [e for e in entities if e.entity_type == entity_type]
            if type_entities:
                tag_file = tags_dir / f"{entity_type.lower()}.ngql"
                with open(tag_file, 'w', encoding='utf-8') as f:
                    f.write(f"CREATE TAG IF NOT EXISTS {entity_type} (\n")
                    f.write("  entity_id string,\n")
                    f.write("  term_name string,\n")
                    f.write("  term_english string,\n")
                    f.write("  definition string,\n")
                    f.write("  category string,\n")
                    f.write("  domain string,\n")
                    f.write("  confidence double,\n")
                    f.write("  created_at timestamp\n")
                    f.write(");\n\n")

                    f.write(f"INSERT VERTEX {entity_type} (\n")
                    f.write("  entity_id, term_name, term_english, definition, ")
                    f.write("  category, domain, confidence, created_at\n")
                    f.write(") VALUES\n")

                    for i, entity in enumerate(type_entities):
                        f.write(f"  '{entity.entity_id}': ('{entity.entity_id}', '{entity.term_name}', ")
                        f.write(f"'{entity.term_english}', '{entity.definition[:200]}', ")
                        f.write(f"'{entity.category}', '{entity.domain}', {entity.confidence}, ")
                        f.write(f"datetime('{datetime.now().isoformat()}')")
                        f.write(")\n")
                        if i < len(type_entities) - 1:
                            f.write(",")

        # 创建edges
        edges_dir = output_dir / "nebula_edges"
        edges_dir.mkdir(exist_ok=True)

        # 为每种关系类型创建edge文件
        for relation_type, _type_name in self.relation_types.items():
            type_relations = [r for r in relations if r.relation_type == relation_type]
            if type_relations:
                edge_file = edges_dir / f"{relation_type.lower()}.ngql"
                with open(edge_file, 'w', encoding='utf-8') as f:
                    f.write(f"CREATE EDGE IF NOT EXISTS {relation_type} (\n")
                    f.write("  relation_id string,\n")
                    f.write("  confidence double,\n")
                    f.write("  created_at timestamp\n")
                    f.write(");\n\n")

                    f.write(f"INSERT EDGE {relation_type} (\n")
                    f.write("  relation_id, confidence, created_at\n")
                    f.write(") VALUES\n")

                    for i, relation in enumerate(type_relations):
                        f.write(f"  '{relation.subject_id}' -> '{relation.object_id}': (")
                        f.write(f"'{relation.relation_id}', {relation.confidence}, ")
                        f.write(f"datetime('{datetime.now().isoformat()}')")
                        f.write(")\n")
                        if i < len(type_relations) - 1:
                            f.write(",")

        logger.info(f"  📦 NebulaGraph脚本已生成在: {output_dir}/nebula_*/")

async def main():
    """主函数"""
    print("="*100)
    print("📚 技术词典知识图谱构建器 📚")
    print("="*100)

    builder = TechnicalDictionaryBuilder()

    # 数据目录
    data_dir = Path("/Users/xujian/Athena工作平台/dev/tools/technical_dict")
    if not data_dir.exists():
        data_dir = Path("/Users/xujian/Athena工作平台/dev/tools")

    output_dir = Path("/Users/xujian/Athena工作平台/production/data")

    # 处理技术词典数据
    await builder.process_dictionary_data(data_dir, output_dir)

    print("\n✅ 技术词典知识图谱构建完成！")

if __name__ == "__main__":
    asyncio.run(main())
