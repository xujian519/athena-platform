#!/usr/bin/env python3
"""
⚠️  DEPRECATED - NebulaGraph同步工具已废弃
DEPRECATED - NebulaGraph sync tool deprecated

废弃日期: 2026-01-26
废弃原因: TD-001 - 系统已迁移到Neo4j
影响范围: 整个文件
建议操作: 使用Neo4j作为图数据库，无需此同步工具

原功能说明:
Qdrant向量库到NebulaGraph知识图谱数据同步工具
Vector to Knowledge Graph Data Synchronization Tool

将Qdrant向量库中的专利规则数据同步到NebulaGraph知识图谱

作者: 小诺·双鱼公主
创建时间: 2026-01-07
版本: v1.2.0 - 新增历史数据导入支持
更新时间: 2026-01-26 (TD-001: 标记废弃)
"""

from __future__ import annotations
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import requests
from nebula3.Config import SessionPoolConfig
from nebula3.gclient.net.ConnectionPool import ConnectionPool
from nebula3.gclient.net.SessionPool import SessionPool

from core.logging_config import setup_logging

# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


class SafeNebulaQueryBuilder:
    """
    安全的NebulaGraph查询构建器

    防止SQL注入的查询构建类,提供严格的输入验证和转义
    """

    # 允许的标识符格式:字母开头,只包含字母、数字、下划线
    IDENTIFIER_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
    # 最大字符串长度限制
    MAX_STRING_LENGTH = 1000

    @classmethod
    def validate_identifier(cls, identifier: str, field_name: str = "标识符") -> str:
        """
        验证标识符(表名、字段名、标签名等)

        Args:
            identifier: 要验证的标识符
            field_name: 字段名(用于错误消息)

        Returns:
            验证后的标识符

        Raises:
            ValueError: 如果标识符不符合安全要求
        """
        if not identifier:
            raise ValueError(f"{field_name}不能为空")

        if not isinstance(identifier, str):
            raise ValueError(f"{field_name}必须是字符串")

        if len(identifier) > 100:
            raise ValueError(f"{field_name}长度不能超过100个字符")

        if not cls.IDENTIFIER_PATTERN.match(identifier):
            raise ValueError(
                f"{field_name}格式无效: '{identifier}',只能包含字母、数字和下划线,且必须以字母或下划线开头"
            )

        return identifier

    @classmethod
    def escape_string_literal(cls, value: str) -> str:
        """
        转义字符串字面量,防止注入

        Args:
            value: 要转义的字符串

        Returns:
            转义后的字符串,可用在双引号内
        """
        if not isinstance(value, str):
            value = str(value)

        if len(value) > cls.MAX_STRING_LENGTH:
            logger.warning(f"字符串长度超过限制({len(value)} > {cls.MAX_STRING_LENGTH}),将截断")
            value = value[: cls.MAX_STRING_LENGTH]

        # 转义特殊字符:双引号和反斜杠
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')

        return escaped

    @classmethod
    def validate_vid(cls, vid: str) -> str:
        """
        验证顶点ID(VID)

        Args:
            vid: 顶点ID

        Returns:
            验证后的VID

        Raises:
            ValueError: 如果VID不符合安全要求
        """
        if not vid:
            raise ValueError("顶点ID不能为空")

        if not isinstance(vid, str):
            raise ValueError("顶点ID必须是字符串")

        # VID可以包含更多字符(如UUID、哈希等),但要控制长度
        if len(vid) > 200:
            raise ValueError(f"顶点ID长度不能超过200个字符: {vid[:50]}...")

        # 检查是否包含危险字符
        dangerous_chars = [";", "\n", "\r", "\x00"]
        if any(char in vid for char in dangerous_chars):
            raise ValueError("顶点ID包含非法字符")

        return vid

    @classmethod
    def build_use_space_query(cls, space_name: str) -> str:
        """
        构建USE SPACE查询

        Args:
            space_name: 空间名称

        Returns:
            安全的USE查询语句
        """
        safe_space = cls.validate_identifier(space_name, "空间名称")
        return f"USE {safe_space};"

    @classmethod
    def build_insert_vertex_query(cls, vid: str, tag: str, properties: dict[str, Any]) -> str:
        """
        构建安全的INSERT VERTEX查询

        Args:
            vid: 顶点ID
            tag: 标签名称
            properties: 属性字典

        Returns:
            安全的INSERT VERTEX语句
        """
        safe_vid = cls.validate_vid(vid)
        safe_tag = cls.validate_identifier(tag, "标签名")
        safe_props = cls._build_properties_string(properties)

        return f'INSERT VERTEX {safe_tag} ({safe_props}) VALUES "{safe_vid}";'

    @classmethod
    def build_match_vertex_query(cls, vid: str) -> str:
        """
        构建安全的MATCH查询

        Args:
            vid: 顶点ID

        Returns:
            安全的MATCH语句
        """
        safe_vid = cls.validate_vid(vid)
        return f'MATCH (v) WHERE id(v) == "{safe_vid}" RETURN v;'

    @classmethod
    def build_insert_edge_query(
        cls, src_vid: str, dst_vid: str, edge_type: str, properties: dict[str, Any]
    ) -> str:
        """
        构建安全的INSERT EDGE查询

        Args:
            src_vid: 源顶点ID
            dst_vid: 目标顶点ID
            edge_type: 边类型
            properties: 属性字典

        Returns:
            安全的INSERT EDGE语句
        """
        safe_src = cls.validate_vid(src_vid)
        safe_dst = cls.validate_vid(dst_vid)
        safe_type = cls.validate_identifier(edge_type, "边类型")
        safe_props = cls._build_properties_string(properties)

        if safe_props:
            return f'INSERT EDGE {safe_type} VALUES "{safe_src}"->"{safe_dst}" @{safe_props};'
        else:
            return f'INSERT EDGE {safe_type} VALUES "{safe_src}"->"{safe_dst}";'

    @classmethod
    def _build_properties_string(cls, properties: dict[str, Any]) -> str:
        """
        构建安全的属性字符串

        Args:
            properties: 属性字典

        Returns:
            安全的属性字符串
        """
        if not properties:
            return ""

        props = []
        for key, value in properties.items():
            # 验证属性名
            safe_key = cls.validate_identifier(key, f"属性名 '{key}'")

            if value is None:
                continue

            # 根据类型处理值
            if isinstance(value, str):
                # 转义字符串
                escaped_value = cls.escape_string_literal(value)
                props.append(f'{safe_key}: "{escaped_value}"')
            elif isinstance(value, bool):
                # 布尔值直接使用
                props.append(f"{safe_key}: {str(value).lower()}")
            elif isinstance(value, (int, float)):
                # 数字直接使用
                props.append(f"{safe_key}: {value}")
            elif isinstance(value, list):
                # 列表转JSON字符串
                list_str = json.dumps(value, ensure_ascii=False)
                escaped_list = cls.escape_string_literal(list_str)
                props.append(f'{safe_key}: "{escaped_list}"')
            else:
                # 其他类型转JSON字符串
                json_str = json.dumps(value, ensure_ascii=False, default=str)
                escaped_json = cls.escape_string_literal(json_str)
                props.append(f'{safe_key}: "{escaped_json}"')

        return ", ".join(props)


@dataclass
class VectorData:
    """向量数据"""

    id: str
    payload: dict[str, Any]
    vector: list[float] | None = None


@dataclass
class KGNode:
    """知识图谱节点"""

    vid: str
    tag: str
    properties: dict[str, Any]
@dataclass
class KGEdge:
    """知识图谱边"""

    src_vid: str
    dst_vid: str
    edge_type: str
    properties: dict[str, Any]
class VectorToKGSync:
    """向量到知识图谱同步器"""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        nebula_host: str = "127.0.0.1",
        nebula_port: int = 9669,
        nebula_space: str = "patent_rules",
    ):
        # Qdrant配置
        self.qdrant_url = f"http://{qdrant_host}:{qdrant_port}"
        self.qdrant_collections = [
            # 原有集合
            "patent_rules_complete",
            "patent_guidelines",
            "patent_legal_rules_enhanced",
            # 新增:历史数据导入集合
            "patent_invalidation_decisions",
            "legal_docs_chinese_laws",
            "legal_docs_patent_laws",
            "legal_docs_trademark_docs",
        ]

        # NebulaGraph配置
        self.nebula_config = {
            "host": nebula_host,
            "port": nebula_port,
            "username": "root",
            "password": "nebula",
            "space_name": nebula_space,
        }
        self.nebula_pool: ConnectionPool | None = None
        self.nebula_session = None

        # 同步统计
        self.sync_stats = {
            "total_vectors": 0,
            "processed_vectors": 0,
            "created_nodes": 0,
            "created_edges": 0,
            "skipped": 0,
            "errors": [],
        }

        # 概念词典(用于提取概念节点)
        self.patent_concepts = {
            "专利",
            "发明",
            "实用新型",
            "外观设计",
            "申请",
            "审查",
            "授权",
            "权利要求",
            "说明书",
            "摘要",
            "附图",
            "优先权",
            "新颖性",
            "创造性",
            "实用性",
            "公开",
            "公告",
            "异议",
            "无效",
            "撤销",
            "终止",
            "期限",
            "费用",
            "代理",
            "专利权",
            "侵权",
            "许可",
            "转让",
            "评估",
            "诉讼",
            "管辖",
            "当事人",
            "证据",
            "举证",
            "赔偿",
            "执行",
            "保全",
        }

    def sync_all_collections(self) -> Any:
        """同步所有集合"""
        logger.info("🚀 开始向量到知识图谱数据同步...")

        # 初始化NebulaGraph连接
        if not self._init_nebula():
            logger.error("❌ NebulaGraph初始化失败")
            return

        # 处理每个集合
        for collection_name in self.qdrant_collections:
            self._sync_collection(collection_name)

        # 显示统计
        self._print_statistics()

        # 关闭连接
        self._close_nebula()

    def _sync_collection(self, collection_name: str) -> Any:
        """同步单个集合"""
        logger.info(f"\n{'='*60}")
        logger.info(f"📦 处理集合: {collection_name}")
        logger.info(f"{'='*60}")

        # 获取集合信息
        collection_info = self._get_qdrant_collection_info(collection_name)
        if not collection_info:
            logger.warning(f"⚠️ 集合不存在或无法访问: {collection_name}")
            return

        total_points = collection_info.get("points_count", 0)
        logger.info(f"总向量数: {total_points:,}")

        if total_points == 0:
            logger.info("集合为空,跳过")
            return

        self.sync_stats["total_vectors"] += total_points

        # 批量获取数据
        batch_size = 100
        offset = None
        batch_num = 0

        while True:
            batch_num += 1
            logger.info(f"处理批次 {batch_num}...")

            # 获取一批数据
            vectors = self._scroll_qdrant_collection(
                collection_name, limit=batch_size, offset=offset
            )

            if not vectors:
                break

            # 处理这批数据
            for vector_data in vectors:
                self._process_vector_data(vector_data, collection_name)

            # 检查是否还有更多数据
            if len(vectors) < batch_size:
                break

            # 更新offset(使用最后一个点的ID)
            offset = vectors[-1].id

        logger.info(f"✅ 集合 {collection_name} 处理完成")

    def _process_vector_data(self, vector_data: VectorData, collection_name: str) -> Any:
        """处理单条向量数据"""
        try:
            payload = vector_data.payload

            # 提取关键信息
            law_name = payload.get("law_name", "")
            article_number = payload.get("article_number", "")
            content = payload.get("content", "")
            level = payload.get("level", "")
            source_file = payload.get("source_file", "")

            # 生成顶点ID
            law_id = payload.get("law_id", vector_data.id)
            vertex_id = f"law_{self._generate_hash(law_id)}"

            # 确定标签类型
            tag = self._determine_tag_type(level, collection_name)

            # 创建文档节点
            doc_vertex_id = f"doc_{self._generate_hash(source_file)}"
            self._ensure_document_node(doc_vertex_id, source_file, law_name)

            # 创建法条节点
            properties = {
                "law_id": law_id,
                "law_name": law_name,
                "article_number": article_number,
                "content": content[:500] if len(content) > 500 else content,  # 限制长度
                "level": level,
                "source_file": source_file,
                "effective_date": payload.get("effective_date", ""),
                "created_at": datetime.now().isoformat(),
            }

            # 创建法条节点
            self._create_vertex(vertex_id, tag, properties)
            self.sync_stats["created_nodes"] += 1

            # 创建文档-法条关系 (CONTAINS)
            self._create_edge(
                doc_vertex_id,
                vertex_id,
                "BELONGS_TO",
                {"relationship_type": "document_contains_article"},
            )
            self.sync_stats["created_edges"] += 1

            # 提取概念节点并创建关系
            self._extract_and_create_concepts(content, vertex_id)

            # 提取引用关系
            self._extract_and_create_references(content, vertex_id)

            self.sync_stats["processed_vectors"] += 1

        except Exception as e:
            logger.warning(f"⚠️ 处理向量失败 {vector_data.id}: {e}")
            self.sync_stats["errors"].append(str(e))

    def _determine_tag_type(self, level: str, collection_name: str) -> str:
        """确定节点标签类型"""
        level_lower = level.lower()
        collection_lower = collection_name.lower()

        # 新增:历史数据导入的集合类型判断
        if "invalidation_decisions" in collection_lower or "invalid" in collection_lower:
            return "InvalidationDecision"
        elif "chinese_laws" in collection_lower or "chinese_law" in collection_lower:
            return "ChineseLaw"
        elif "patent_laws" in collection_lower:
            return "PatentLaw"
        elif "trademark_docs" in collection_lower:
            return "TrademarkDocument"
        # 原有类型判断
        elif "司法解释" in level_lower or "解释" in level_lower:
            return "JudicialInterpretation"
        elif "审查指南" in collection_lower or "指南" in level_lower:
            return "GuidelineSection"
        elif "专利法" in level_lower or level_lower in ["法条", "条款", "法律"]:
            return "LawArticle"
        else:
            return "PatentDocument"

    def _extract_and_create_concepts(self, content: str, parent_vertex_id: str) -> Any:
        """提取概念并创建关系"""
        if not content:
            return

        # 查找内容中的概念
        found_concepts = []
        for concept in self.patent_concepts:
            if concept in content:
                found_concepts.append(concept)

        # 为每个概念创建节点和关系
        for concept in found_concepts:
            concept_vid = f"concept_{self._generate_hash(concept)}"

            # 创建概念节点
            properties = {
                "concept_name": concept,
                "category": self._classify_concept(concept),
                "definition": self._get_concept_definition(concept),
                "created_at": datetime.now().isoformat(),
            }

            self._create_vertex_if_not_exists(concept_vid, "Concept", properties)

            # 创建法条-概念关系 (DEFINES)
            self._create_edge(
                parent_vertex_id, concept_vid, "DISCUSSES_CONCEPT", {"confidence": 1.0}
            )
            self.sync_stats["created_edges"] += 1

    def _extract_and_create_references(self, content: str, parent_vertex_id: str) -> Any:
        """提取引用关系"""
        if not content:
            return

        # 查找"第X条"模式
        pattern = r"第([一二三四五六七八九十百千0-9]+)条"
        matches = re.findall(pattern, content)

        for match in matches:
            # 创建引用节点
            ref_id = f"ref_{parent_vertex_id}_{match}"
            properties = {
                "reference_type": "article_reference",
                "reference_text": f"第{match}条",
                "created_at": datetime.now().isoformat(),
            }

            self._create_vertex(ref_id, "LawReference", properties)
            self.sync_stats["created_nodes"] += 1

            # 创建引用关系
            self._create_edge(
                parent_vertex_id, ref_id, "REFERS_TO", {"reference_context": "internal_reference"}
            )
            self.sync_stats["created_edges"] += 1

    def _classify_concept(self, concept: str) -> str:
        """分类概念"""
        if concept in ["发明", "实用新型", "外观设计"]:
            return "专利类型"
        elif concept in ["申请", "审查", "授权", "公开", "公告"]:
            return "程序性概念"
        elif concept in ["侵权", "诉讼", "管辖", "证据", "赔偿"]:
            return "法律概念"
        else:
            return "通用概念"

    def _get_concept_definition(self, concept: str) -> str:
        """获取概念定义"""
        definitions = {
            "专利": "国家授予发明创造者在一定期限内的独占权",
            "发明": "对产品、方法或者其改进所提出的新的技术方案",
            "实用新型": "对产品的形状、构造或者其结合所提出的适于实用的新的技术方案",
            "新颖性": "不属于现有技术",
            "创造性": "与现有技术相比,具有突出的实质性特点和显著的进步",
            "权利要求": "专利申请人要求专利保护的范围",
        }
        return definitions.get(concept, f"{concept}相关的专业概念")

    def _ensure_document_node(self, doc_vertex_id: str, source_file: str, law_name: str) -> Any:
        """确保文档节点存在"""
        properties = {
            "source_file": source_file,
            "law_name": law_name,
            "document_type": self._classify_document_type(law_name),
            "created_at": datetime.now().isoformat(),
        }
        self._create_vertex_if_not_exists(doc_vertex_id, "DecisionDocument", properties)

    def _classify_document_type(self, law_name: str) -> str:
        """分类文档类型"""
        if "专利法" in law_name:
            return "专利法"
        elif "无效" in law_name or "复审" in law_name:
            return "无效复审决定"
        elif "经济" in law_name:
            return "经济法"
        elif "商标" in law_name:
            return "商标文档"
        elif "司法解释" in law_name:
            return "司法解释"
        elif "审查指南" in law_name:
            return "审查指南"
        else:
            return "其他法律文件"

    def _generate_hash(self, text: str) -> str:
        """生成哈希ID"""

        return hashlib.md5(text.encode("utf-8", usedforsecurity=False), usedforsecurity=False).hexdigest()[:16]

    def _get_qdrant_collection_info(self, collection_name: str) -> dict | None:
        """获取Qdrant集合信息 - 添加超时防止无限等待"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}"
            # 添加5秒超时防止无限等待
            response = requests.get(url, timeout=5)
            data = response.json()
            return data.get("result", {})
        except (requests.TimeoutException, requests.ConnectionError) as e:
            logger.error(f"获取集合信息超时或连接失败: {e}")
            return None
        except Exception as e:
            logger.error(f"获取集合信息失败: {e}")
            return None

    def _scroll_qdrant_collection(
        self, collection_name: str, limit: int = 100, offset: str | None = None
    ) -> list[VectorData]:
        """滚动获取Qdrant集合数据 - 添加超时防止无限等待"""
        try:
            url = f"{self.qdrant_url}/collections/{collection_name}/points/scroll"
            data = {"limit": limit, "with_payload": True, "with_vector": False}

            if offset:
                data["offset"] = offset

            # 添加10秒超时防止无限等待
            response = requests.post(url, json=data, timeout=10)
            result = response.json()

            vectors = []
            for point in result.get("result", {}).get("points", []):
                vector_data = VectorData(id=str(point["id"]), payload=point.get("payload", {}))
                vectors.append(vector_data)

            return vectors

        except (requests.TimeoutException, requests.ConnectionError) as e:
            logger.error(f"滚动获取集合数据超时或连接失败: {e}")
            return []
        except Exception as e:
            logger.error(f"滚动获取集合数据失败: {e}")
            return []

    def _init_nebula(self) -> bool:
        """初始化NebulaGraph连接"""
        try:
            # 创建SessionPool配置
            config = SessionPoolConfig()
            config.max_connection_pool_size = 10

            # 初始化SessionPool
            self.nebula_pool = SessionPool(
                self.nebula_config["username"],
                self.nebula_config["password"],
                self.nebula_config["space_name"],
                [(self.nebula_config["host"], self.nebula_config["port"])],
            )

            init_result = self.nebula_pool.init(config)

            if not init_result:
                logger.error("❌ NebulaGraph SessionPool初始化失败")
                return False

            # 使用空间 - 使用安全查询构建器防止SQL注入
            try:
                use_query = SafeNebulaQueryBuilder.build_use_space_query(
                    self.nebula_config["space_name"]
                )
                result = self.nebula_pool.execute(use_query)
            except ValueError as e:
                logger.error(f"❌ 空间名称验证失败: {e}")
                return False

            if result.is_succeeded():
                logger.info(f"✅ NebulaGraph连接成功: {self.nebula_config['space_name']}")
                return True
            else:
                logger.error(f"❌ 使用空间失败: {result.error_msg()}")
                return False

        except Exception as e:
            logger.error(f"❌ NebulaGraph连接失败: {e}")
            import traceback

            traceback.print_exc()
            return False

    def _close_nebula(self) -> Any:
        """关闭NebulaGraph连接"""
        if self.nebula_pool:
            self.nebula_pool.close()
        logger.info("🔌 NebulaGraph连接已关闭")

    def _create_vertex(self, vid: str, tag: str, properties: dict[str, Any]) -> Any:
        """创建顶点 - 使用安全查询构建器防止SQL注入"""
        try:
            # 使用安全查询构建器
            query = SafeNebulaQueryBuilder.build_insert_vertex_query(vid, tag, properties)
            result = self.nebula_pool.execute(query)

            if not result.is_succeeded():
                logger.debug(f"顶点可能已存在 {vid}: {result.error_msg()}")

        except ValueError as e:
            logger.warning(f"创建顶点失败 - 参数验证错误 {vid}: {e}")
        except Exception as e:
            logger.warning(f"创建顶点失败 {vid}: {e}")

    def _create_vertex_if_not_exists(self, vid: str, tag: str, properties: dict[str, Any]) -> Any:
        """如果顶点不存在则创建 - 使用安全查询构建器防止SQL注入"""
        try:
            # 先检查是否存在 - 使用安全查询
            check_query = SafeNebulaQueryBuilder.build_match_vertex_query(vid)
            result = self.nebula_pool.execute(check_query)

            if not result.is_succeeded() or result.row_size() == 0:
                # 不存在,创建
                self._create_vertex(vid, tag, properties)

        except ValueError as e:
            logger.warning(f"检查顶点存在性失败 - 参数验证错误 {vid}: {e}")
        except Exception as e:
            logger.warning(f"检查顶点存在性失败 {vid}: {e}")

    def _create_edge(
        self, src_vid: str, dst_vid: str, edge_type: str, properties: dict[str, Any]
    ) -> Any:
        """创建边 - 使用安全查询构建器防止SQL注入"""
        try:
            # 使用安全查询构建器
            query = SafeNebulaQueryBuilder.build_insert_edge_query(
                src_vid, dst_vid, edge_type, properties
            )
            result = self.nebula_pool.execute(query)

            if not result.is_succeeded():
                logger.debug(f"边可能已存在 {src_vid}->{dst_vid}: {result.error_msg()}")

        except ValueError as e:
            logger.warning(f"创建边失败 - 参数验证错误 {src_vid}->{dst_vid}: {e}")
        except Exception as e:
            logger.warning(f"创建边失败 {src_vid}->{dst_vid}: {e}")

    def _print_statistics(self) -> Any:
        """打印统计信息"""
        logger.info(f"\n{'='*60}")
        logger.info("📊 同步统计报告")
        logger.info(f"{'='*60}")
        logger.info(f"总向量数: {self.sync_stats['total_vectors']:,}")
        logger.info(f"已处理: {self.sync_stats['processed_vectors']:,}")
        logger.info(f"创建节点: {self.sync_stats['created_nodes']:,}")
        logger.info(f"创建边: {self.sync_stats['created_edges']:,}")
        logger.info(f"跳过: {self.sync_stats['skipped']:,}")
        logger.info(f"错误: {len(self.sync_stats['errors'])}")

        if self.sync_stats["errors"]:
            logger.info("\n错误详情:")
            for error in self.sync_stats["errors"][:10]:
                logger.info(f"  - {error}")

        logger.info(f"{'='*60}")


def main() -> None:
    """主函数"""
    sync = VectorToKGSync()

    # 执行同步
    sync.sync_all_collections()

    logger.info("\n✅ 向量到知识图谱同步完成!")


if __name__ == "__main__":
    main()
