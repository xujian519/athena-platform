#!/usr/bin/env python3
"""
IPC分类知识图谱构建器
IPC Classification Knowledge Graph Builder

利用本地NLP系统和大模型构建IPC分类知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v3.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import aiohttp

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class IPCEntity:
    """IPC分类实体"""
    entity_id: str
    entity_type: str
    ipc_code: str
    ipc_title: str
    ipc_description: str
    parent_code: str
    level: int
    attributes: dict
    confidence: float
    source_chunk: str

@dataclass
class IPCRelation:
    """IPC关系"""
    relation_id: str
    subject_id: str
    object_id: str
    relation_type: str
    attributes: dict
    confidence: float
    source_chunk: str

class IPCKnowledgeGraphBuilder:
    """IPC分类知识图谱构建器"""

    def __init__(self):
        # NLP服务配置
        self.nlp_url = "http://localhost:8001"
        self.nlp_model = "patent_classification"  # 使用专利分类模型
        self.llm_url = "http://localhost:8002"  # 本地大模型

        # 实体类型定义
        self.entity_types = {
            "IPC_SECTION": "IPC部",
            "IPC_CLASS": "IPC大类",
            "IPC_SUBCLASS": "IPC小类",
            "IPC_GROUP": "IPC大组",
            "IPC_SUBGROUP": "IPC小组",
            "TECHNOLOGY_AREA": "技术领域",
            "APPLICATION_FIELD": "应用领域",
            "KEYWORD": "关键词",
            "REFERENCE": "参考文献",
            "EXAMPLE": "实例"
        }

        # 关系类型定义
        self.relation_types = {
            "HAS_PARENT": "属于",
            "HAS_CHILD": "包含",
            "RELATED_TO": "相关于",
            "APPLIES_TO": "应用于",
            "EXAMPLE_OF": "是...的实例",
            "REFERENCES": "参考",
            "KEYWORD_OF": "是...的关键词",
            "CROSS_REFERENCE": "交叉引用",
            "HIERARCHICAL": "层级关系",
            "FUNCTIONAL": "功能关系",
            "TECHNICAL": "技术关系",
            "SEMANTIC": "语义关系"
        }

        # IPC正则表达式模式
        self.patterns = {
            # A01B 1/00
            "ipc_full": r"([A-H])(\d{2})([A-Z])\s*(\d{1,3})/(\d{2})",
            # A01
            "ipc_subclass": r"([A-H])(\d{2})([A-Z])",
            # A
            "ipc_section": r"([A-H])",
            # A01B
            "ipc_class": r"([A-H])(\d{2})([A-Z])",
            # 1/00
            "ipc_group": r"(\d{1,3})/(\d{2})",
            # 版本号
            "ipc_version": r"IPC\s+(\d{4})\.(\d{2})"
        }

        # IPC技术领域映射
        self.technology_areas = {
            "A": "人类生活必需",
            "B": "作业；运输",
            "C": "化学；冶金",
            "D": "纺织；造纸",
            "E": "固定建筑物",
            "F": "机械工程；照明；加热；武器；爆破",
            "G": "物理",
            "H": "电学"
        }

    async def extract_entities_with_nlp(self, text: str, chunk_id: str) -> list[IPCEntity]:
        """使用NLP服务提取IPC实体"""
        entities = []

        try:
            # 调用NLP服务进行实体识别
            async with aiohttp.ClientSession() as session:
                payload = {
                    "text": text,
                    "task": "extract_ipc_entities",
                    "domain": "patent_classification",
                    "model": self.nlp_model
                }

                async with session.post(
                    f"{self.nlp_url}/extract_ipc_entities",
                    json=payload,
                    timeout=30
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        nlp_entities = data.get("entities", [])

                        # 转换为IPCEntity格式
                        for nlp_entity in nlp_entities:
                            entity = IPCEntity(
                                entity_id=self._generate_entity_id(
                                    nlp_entity.get("ipc_code", ""), chunk_id
                                ),
                                entity_type=self._classify_ipc_level(nlp_entity.get("ipc_code", "")),
                                ipc_code=nlp_entity.get("ipc_code", ""),
                                ipc_title=nlp_entity.get("title", ""),
                                ipc_description=nlp_entity.get("description", ""),
                                parent_code=nlp_entity.get("parent", ""),
                                level=self._calculate_ipc_level(nlp_entity.get("ipc_code", "")),
                                attributes={
                                    "position": nlp_entity.get("position", 0),
                                    "context": nlp_entity.get("context", ""),
                                    "technology_area": self._get_technology_area(
                                        nlp_entity.get("ipc_code", "")
                                    ),
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

    def _extract_entities_with_rules(self, text: str, chunk_id: str) -> list[IPCEntity]:
        """使用规则提取IPC实体（后备方案）"""
        entities = []

        # 提取完整的IPC分类号 (如 A01B 1/00)
        for match in re.finditer(self.patterns["ipc_full"], text):
            ipc_code = f"{match.group(1)}{match.group(2)}{match.group(3)} {match.group(4)}/{match.group(5)}"
            title = self._extract_ipc_title(text, match.start())
            description = self._extract_ipc_description(text, match.end())

            entity = IPCEntity(
                entity_id=self._generate_entity_id(ipc_code, chunk_id),
                entity_type=self._classify_ipc_level(ipc_code),
                ipc_code=ipc_code,
                ipc_title=title,
                ipc_description=description,
                parent_code=self._get_parent_code(ipc_code),
                level=self._calculate_ipc_level(ipc_code),
                attributes={
                    "section": match.group(1),
                    "class": match.group(1) + match.group(2),
                    "subclass": ipc_code[:4],
                    "group": match.group(4),
                    "subgroup": match.group(5),
                    "technology_area": self.technology_areas.get(match.group(1), "未知")
                },
                confidence=0.95,
                source_chunk=chunk_id
            )
            entities.append(entity)

        # 提取IPC小类 (如 A01B)
        for match in re.finditer(self.patterns["ipc_subclass"], text):
            ipc_code = match.group()
            if not any(e.ipc_code == ipc_code for e in entities):
                title = self._extract_ipc_title(text, match.start())
                description = self._extract_ipc_description(text, match.end())

                entity = IPCEntity(
                    entity_id=self._generate_entity_id(ipc_code, chunk_id),
                    entity_type="IPC_SUBCLASS",
                    ipc_code=ipc_code,
                    ipc_title=title,
                    ipc_description=description,
                    parent_code=self._get_parent_code(ipc_code),
                    level=3,
                    attributes={
                        "section": match.group(1),
                        "class_num": match.group(2),
                        "subclass_letter": match.group(3),
                        "technology_area": self.technology_areas.get(match.group(1), "未知")
                    },
                    confidence=0.9,
                    source_chunk=chunk_id
                )
                entities.append(entity)

        return entities

    async def extract_relations_with_llm(self, text: str, entities: list[IPCEntity], chunk_id: str) -> list[IPCRelation]:
        """使用本地大模型提取IPC关系"""
        relations = []

        try:
            # 准备实体信息
            entity_list = [
                {
                    "code": e.ipc_code,
                    "title": e.ipc_title,
                    "type": e.entity_type,
                    "level": e.level
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
        prompt = f"""你是一个专业的IPC分类专家。请分析以下文本，识别IPC分类号之间的关系。

文本内容：
{text}

已识别的IPC分类实体：
{json.dumps(entities, ensure_ascii=False, indent=2)}

请识别以下类型的关系：
1. 层级关系（父子关系）
2. 技术相关性
3. 应用领域关系
4. 交叉引用关系

以JSON格式返回关系列表：
{{
    "relations": [
        {{
            "subject": "IPC代码1",
            "object": "IPC代码2",
            "type": "关系类型",
            "confidence": 0.9,
            "reason": "判断依据"
        }}
    ]
}}
"""
        return prompt

    def _parse_llm_relations(self, llm_response: str, entities: list[IPCEntity], chunk_id: str) -> list[IPCRelation]:
        """解析LLM响应中的关系"""
        relations = []
        entity_map = {e.ipc_code: e for e in entities}

        try:
            # 尝试解析JSON响应
            response_data = json.loads(llm_response)
            llm_relations = response_data.get("relations", [])

            for rel in llm_relations:
                subject_code = rel.get("subject", "")
                object_code = rel.get("object", "")

                if subject_code in entity_map and object_code in entity_map:
                    relation = IPCRelation(
                        relation_id=self._generate_relation_id(
                            entity_map[subject_code].entity_id,
                            entity_map[object_code].entity_id,
                            rel.get("type", "RELATED_TO")
                        ),
                        subject_id=entity_map[subject_code].entity_id,
                        object_id=entity_map[object_code].entity_id,
                        relation_type=rel.get("type", "RELATED_TO"),
                        attributes={
                            "reason": rel.get("reason", ""),
                            "confidence_llm": rel.get("confidence", 0.7),
                            "relation_strength": self._calculate_relation_strength(
                                entity_map[subject_code], entity_map[object_code]
                            )
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

    def _extract_relations_with_rules(self, text: str, entities: list[IPCEntity], chunk_id: str) -> list[IPCRelation]:
        """使用规则提取IPC关系（后备方案）"""
        relations = []

        # 按层级排序
        sorted_entities = sorted(entities, key=lambda x: x.level)

        # 生成层级关系
        for i, entity1 in enumerate(sorted_entities):
            for entity2 in sorted_entities[i+1:]:
                if entity2.level == entity1.level + 1:
                    # 检查是否是父子关系
                    if self._is_parent_child(entity1, entity2):
                        relation = IPCRelation(
                            relation_id=self._generate_relation_id(
                                entity1.entity_id, entity2.entity_id, "HAS_CHILD"
                            ),
                            subject_id=entity1.entity_id,
                            object_id=entity2.entity_id,
                            relation_type="HAS_CHILD",
                            attributes={
                                "hierarchy_level": entity1.level,
                                "inheritance_type": "direct"
                            },
                            confidence=0.9,
                            source_chunk=chunk_id
                        )
                        relations.append(relation)

                        # 同时生成HAS_PARENT关系
                        relation_rev = IPCRelation(
                            relation_id=self._generate_relation_id(
                                entity2.entity_id, entity1.entity_id, "HAS_PARENT"
                            ),
                            subject_id=entity2.entity_id,
                            object_id=entity1.entity_id,
                            relation_type="HAS_PARENT",
                            attributes={
                                "hierarchy_level": entity2.level,
                                "inheritance_type": "direct"
                            },
                            confidence=0.9,
                            source_chunk=chunk_id
                        )
                        relations.append(relation_rev)

        # 生成技术领域关系
        for entity1 in entities:
            for entity2 in entities:
                if entity1.level == entity2.level and entity1.entity_id != entity2.entity_id:
                    # 同层级的IPC可能有技术相关性
                    similarity = self._calculate_technical_similarity(entity1, entity2)
                    if similarity > 0.6:
                        relation = IPCRelation(
                            relation_id=self._generate_relation_id(
                                entity1.entity_id, entity2.entity_id, "RELATED_TO"
                            ),
                            subject_id=entity1.entity_id,
                            object_id=entity2.entity_id,
                            relation_type="RELATED_TO",
                            attributes={
                                "similarity_score": similarity,
                                "relation_type": "technical_correlation"
                            },
                            confidence=similarity,
                            source_chunk=chunk_id
                        )
                        relations.append(relation)

        return relations

    def _classify_ipc_level(self, ipc_code: str) -> str:
        """分类IPC层级"""
        if len(ipc_code) == 1:  # A
            return "IPC_SECTION"
        elif len(ipc_code) <= 4:  # A01B
            return "IPC_SUBCLASS"
        elif "/" in ipc_code and len(ipc_code.split(" ")) > 1:  # A01B 1/00
            return "IPC_SUBGROUP"
        elif len(ipc_code) == 3:  # A01
            return "IPC_CLASS"
        else:
            return "UNKNOWN"

    def _calculate_ipc_level(self, ipc_code: str) -> int:
        """计算IPC层级"""
        if len(ipc_code) == 1:  # A
            return 1
        elif len(ipc_code) == 3:  # A01
            return 2
        elif len(ipc_code) == 4:  # A01B
            return 3
        elif "/" in ipc_code:  # A01B 1/00
            return 4 if "/" in ipc_code.split(" ")[-1] else 5
        else:
            return 0

    def _get_technology_area(self, ipc_code: str) -> str:
        """获取技术领域"""
        if ipc_code:
            section = ipc_code[0]
            return self.technology_areas.get(section, "未知")
        return "未知"

    def _get_parent_code(self, ipc_code: str) -> str:
        """获取父级IPC代码"""
        if not ipc_code:
            return ""

        if "/" in ipc_code:  # A01B 1/00
            parts = ipc_code.split()
            if len(parts) > 1:
                return parts[0]  # A01B
        elif len(ipc_code) == 4:  # A01B
            return ipc_code[:3]  # A01
        elif len(ipc_code) == 3:  # A01
            return ipc_code[0]  # A

        return ""

    def _extract_ipc_title(self, text: str, start_pos: int) -> str:
        """提取IPC标题"""
        # 查找IPC代码后的第一个句号或换行
        text_after = text[start_pos:]
        for delim in ["。", "\n", "\r"]:
            if delim in text_after:
                return text_after.split(delim)[0].strip()
        return text_after[:100].strip()

    def _extract_ipc_description(self, text: str, end_pos: int) -> str:
        """提取IPC描述"""
        # 查找IPC代码后的描述文本
        text_after = text[end_pos:end_pos+200]
        # 移除IPC代码
        cleaned = re.sub(r'[A-H]\d{2}[A-Z]\s*\d{1,3}/\d{2}', '', text_after)
        # 移除特殊字符
        cleaned = re.sub(r'[^\u4e00-\u9fa5a-zA-Z0-9\s，。、；：]', '', cleaned)
        return cleaned.strip()

    def _is_parent_child(self, parent: IPCEntity, child: IPCEntity) -> bool:
        """判断是否是父子关系"""
        # 简单判断：子代码以父代码开头
        return child.ipc_code.startswith(parent.ipc_code)

    def _calculate_technical_similarity(self, entity1: IPCEntity, entity2: IPCEntity) -> float:
        """计算技术相似度"""
        # 基于技术领域和标题计算相似度
        if entity1.attributes.get("technology_area") != entity2.attributes.get("technology_area"):
            return 0.0

        # 简单的标题相似度计算
        title1 = entity1.ipc_title.lower()
        title2 = entity2.ipc_title.lower()

        common_words = set(title1.split()) & set(title2.split())
        total_words = set(title1.split()) | set(title2.split())

        if total_words:
            return len(common_words) / len(total_words)
        return 0.0

    def _calculate_relation_strength(self, entity1: IPCEntity, entity2: IPCEntity) -> float:
        """计算关系强度"""
        # 基于层级距离计算关系强度
        level_diff = abs(entity1.level - entity2.level)
        if level_diff == 0:
            return 0.5  # 同级
        elif level_diff == 1:
            return 0.9  # 直接父子
        else:
            return 0.3  # 远亲

    def _generate_entity_id(self, ipc_code: str, chunk_id: str) -> str:
        """生成实体ID"""
        content = f"{ipc_code}_{chunk_id}"
        return short_hash(content.encode())[:16]

    def _generate_relation_id(self, subject_id: str, object_id: str, relation_type: str) -> str:
        """生成关系ID"""
        content = f"{subject_id}_{object_id}_{relation_type}"
        return short_hash(content.encode())[:16]

    async def process_ipc_data(self, data_dir: Path, output_dir: Path):
        """处理IPC数据"""
        logger.info("开始处理IPC分类数据")

        all_entities = []
        all_relations = []

        # 查找IPC数据文件
        ipc_files = list(data_dir.rglob("*ipc*"))
        ipc_files.extend(data_dir.rglob("*classification*"))
        ipc_files.extend(data_dir.rglob("*分类*"))

        if not ipc_files:
            logger.warning(f"在 {data_dir} 中未找到IPC数据文件")
            # 使用模拟数据
            await self._process_sample_data(output_dir)
            return

        # 处理每个IPC文件
        for file_path in ipc_files[:50]:  # 限制处理数量
            logger.info(f"处理文件: {file_path.name}")

            try:
                # 读取文件内容
                content = file_path.read_text(encoding='utf-8')

                # 分块处理
                chunks = self._split_ipc_content(content)
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
        logger.info(f"  总实体数: {len(all_entities)}")
        logger.info(f"  总关系数: {len(all_relations)}")

        # 保存结果
        self._save_results(all_entities, all_relations, entity_stats, relation_stats, output_dir)

    async def _process_sample_data(self, output_dir: Path):
        """处理示例数据（当没有真实数据时）"""
        logger.info("使用示例IPC数据进行演示")

        sample_ipc_data = [
            {
                "code": "A01",
                "title": "农业；林业；畜牧业；打猎；诱捕；捕鱼",
                "description": "涉及农业和相关部门的技术",
                "level": 2
            },
            {
                "code": "A01B",
                "title": "农业或林业的整地；一般农业机械或农具的附件",
                "description": "农业整地机械和相关工具",
                "level": 3
            },
            {
                "code": "A01B 1/00",
                "title": "手工工具",
                "description": "用于农业的手工操作工具",
                "level": 4
            },
            {
                "code": "G06",
                "title": "计算；推算；计数",
                "description": "数据处理和计算技术",
                "level": 2
            },
            {
                "code": "G06F",
                "title": "电数字数据处理",
                "description": "电子数字计算机和相关设备",
                "level": 3
            }
        ]

        all_entities = []
        all_relations = []

        # 创建实体
        for i, data in enumerate(sample_ipc_data):
            entity = IPCEntity(
                entity_id=f"sample_entity_{i}",
                entity_type=self._classify_ipc_level(data["code"]),
                ipc_code=data["code"],
                ipc_title=data["title"],
                ipc_description=data["description"],
                parent_code=self._get_parent_code(data["code"]),
                level=data["level"],
                attributes={
                    "technology_area": self._get_technology_area(data["code"]),
                    "source": "sample_data"
                },
                confidence=1.0,
                source_chunk="sample"
            )
            all_entities.append(entity)

        # 创建关系
        for i, entity1 in enumerate(all_entities):
            for j, entity2 in enumerate(all_entities):
                if i < j:
                    if self._is_parent_child(entity1, entity2):
                        # 父子关系
                        relation = IPCRelation(
                            relation_id=f"sample_rel_{i}_{j}_child",
                            subject_id=entity1.entity_id,
                            object_id=entity2.entity_id,
                            relation_type="HAS_CHILD",
                            attributes={"type": "hierarchical"},
                            confidence=1.0,
                            source_chunk="sample"
                        )
                        all_relations.append(relation)
                    elif entity1.level == entity2.level:
                        # 同级相关关系
                        relation = IPCRelation(
                            relation_id=f"sample_rel_{i}_{j}_related",
                            subject_id=entity1.entity_id,
                            object_id=entity2.entity_id,
                            relation_type="RELATED_TO",
                            attributes={"type": "same_level"},
                            confidence=0.5,
                            source_chunk="sample"
                        )
                        all_relations.append(relation)

        # 保存结果
        entity_stats = Counter(e.entity_type for e in all_entities)
        relation_stats = Counter(r.relation_type for r in all_relations)

        self._save_results(all_entities, all_relations, entity_stats, relation_stats, output_dir)

    def _split_ipc_content(self, content: str, chunk_size: int = 1000) -> list[str]:
        """IPC内容分块"""
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

    def _save_results(self, entities: list[IPCEntity], relations: list[IPCRelation],
                      entity_stats: Counter, relation_stats: Counter, output_dir: Path):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 创建输出目录
        output_dir = output_dir / "ipc_knowledge_graph"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 保存实体
        entities_file = output_dir / f"ipc_entities_{timestamp}.json"
        entities_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "IPC分类知识图谱实体",
                "total_entities": len(entities),
                "entity_types": dict(entity_stats),
                "nlp_integration": True
            },
            "entities": [asdict(e) for e in entities]
        }
        with open(entities_file, 'w', encoding='utf-8') as f:
            json.dump(entities_data, f, ensure_ascii=False, indent=2)

        # 保存关系
        relations_file = output_dir / f"ipc_relations_{timestamp}.json"
        relations_data = {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "description": "IPC分类知识图谱关系",
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
        stats_file = output_dir / f"ipc_stats_{timestamp}.json"
        stats = {
            "timestamp": datetime.now().isoformat(),
            "entity_types": self.entity_types,
            "relation_types": self.relation_types,
            "entity_statistics": dict(entity_stats),
            "relation_statistics": dict(relation_stats),
            "technology_areas": self.technology_areas,
            "processing_summary": {
                "total_entities": len(entities),
                "total_relations": len(relations),
                "unique_ipc_codes": len({e.ipc_code for e in entities}),
                "max_level": max(e.level for e in entities) if entities else 0
            }
        }
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        logger.info("💾 IPC知识图谱已保存:")
        logger.info(f"  实体文件: {entities_file}")
        logger.info(f"  关系文件: {relations_file}")
        logger.info(f"  统计文件: {stats_file}")

    def _generate_nebula_scripts(self, entities: list[IPCEntity], relations: list[IPCRelation],
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
                    f.write("  ipc_code string,\n")
                    f.write("  ipc_title string,\n")
                    f.write("  ipc_description string,\n")
                    f.write("  parent_code string,\n")
                    f.write("  level int,\n")
                    f.write("  confidence double,\n")
                    f.write("  technology_area string,\n")
                    f.write("  created_at timestamp\n")
                    f.write(");\n\n")

                    f.write(f"INSERT VERTEX {entity_type} (\n")
                    f.write("  entity_id, ipc_code, ipc_title, ipc_description, ")
                    f.write("  parent_code, level, confidence, technology_area, created_at\n")
                    f.write(") VALUES\n")

                    for i, entity in enumerate(type_entities):
                        tech_area = entity.attributes.get("technology_area", "")
                        f.write(f"  '{entity.entity_id}': ('{entity.entity_id}', '{entity.ipc_code}', ")
                        f.write(f"'{entity.ipc_title}', '{entity.ipc_description[:100]}', ")
                        f.write(f"'{entity.parent_code}', {entity.level}, {entity.confidence}, ")
                        f.write(f"'{tech_area}', datetime('{datetime.now().isoformat()}')")
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
                    f.write("  relation_strength double,\n")
                    f.write("  created_at timestamp\n")
                    f.write(");\n\n")

                    f.write(f"INSERT EDGE {relation_type} (\n")
                    f.write("  relation_id, confidence, relation_strength, created_at\n")
                    f.write(") VALUES\n")

                    for i, relation in enumerate(type_relations):
                        strength = relation.attributes.get("relation_strength", 0.5)
                        f.write(f"  '{relation.subject_id}' -> '{relation.object_id}': (")
                        f.write(f"'{relation.relation_id}', {relation.confidence}, {strength}, ")
                        f.write(f"datetime('{datetime.now().isoformat()}')")
                        f.write(")\n")
                        if i < len(type_relations) - 1:
                            f.write(",")

        logger.info(f"  📦 NebulaGraph脚本已生成在: {output_dir}/nebula_*/")

async def main():
    """主函数"""
    print("="*100)
    print("🏗️ IPC分类知识图谱构建器 🏗️")
    print("="*100)

    builder = IPCKnowledgeGraphBuilder()

    # 数据目录
    data_dir = Path("/Users/xujian/Athena工作平台/dev/tools/ipc_data")
    if not data_dir.exists():
        data_dir = Path("/Users/xujian/Athena工作平台/dev/tools")

    output_dir = Path("/Users/xujian/Athena工作平台/production/data")

    # 处理IPC数据
    await builder.process_ipc_data(data_dir, output_dir)

    print("\n✅ IPC分类知识图谱构建完成！")

if __name__ == "__main__":
    asyncio.run(main())
