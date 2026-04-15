#!/usr/bin/env python3
"""
知识图谱构建器 V2
Patent Knowledge Graph Builder V2

负责将三元组数据写入NebulaGraph图数据库

作者: Athena平台团队
创建时间: 2025-12-25
"""

from __future__ import annotations
import logging
import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from core.config.secure_config import get_config

config = get_config()


# 添加项目路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent.parent
sys.path.insert(0, str(project_root))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config():
        return {
            'host': 'localhost',
            'port': 9669,
            'user': 'root',
            "password": config.get("NEBULA_PASSWORD", required=True),
            'space': 'patent_full_text_v2'
        }

logger = logging.getLogger(__name__)


class InsertStatus(Enum):
    """插入状态"""
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"  # 已存在跳过


@dataclass
class InsertResult:
    """插入结果"""
    status: InsertStatus
    entity_type: str  # vertex/edge
    entity_id: str
    message: str = ""
    execution_time: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status.value,
            "entity_type": self.entity_type,
            "entity_id": self.entity_id,
            "message": self.message,
            "execution_time": self.execution_time
        }


@dataclass
class KGBuildResult:
    """知识图谱构建结果"""
    patent_number: str
    success: bool

    # 插入结果
    vertex_results: list[InsertResult] = field(default_factory=list)
    edge_results: list[InsertResult] = field(default_factory=list)

    # 统计信息
    total_vertices: int = 0
    total_edges: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    processing_time: float = 0.0
    error_message: str | None = None

    @property
    def all_results(self) -> list[InsertResult]:
        """获取所有插入结果"""
        return self.vertex_results + self.edge_results

    def get_summary(self) -> dict[str, Any]:
        """获取构建摘要"""
        return {
            "patent_number": self.patent_number,
            "success": self.success,
            "total_vertices": self.total_vertices,
            "total_edges": self.total_edges,
            "failed_count": self.failed_count,
            "skipped_count": self.skipped_count,
            "processing_time": self.processing_time
        }


class PatentKGBuilderV2:
    """
    专利知识图谱构建器V2

    支持功能:
    1. 创建专利基础顶点
    2. 创建技术分析顶点（问题/特征/效果）
    3. 创建三元组边
    4. 批量插入优化
    """

    # NGQL模板
    INSERT_VERTEX_TEMPLATE = 'INSERT VERTEX `{tag_name}`({props}) VALUES "{vid}";'
    INSERT_EDGE_TEMPLATE = 'INSERT EDGE `{edge_name}`({props}) "{src_vid}" -> "{dst_vid}";'

    def __init__(self, nebula_client=None):
        """
        初始化构建器

        Args:
            nebula_client: NebulaGraph客户端（可选）
        """
        self.nebula_client = nebula_client
        self._connected = False

    def connect(
        self,
        host: str = None,
        port: int = None,
        space_name: str = None,
        username: str = None,
        password: str = None
    ):
        """
        连接到NebulaGraph

        Args:
            host: 主机地址 (如果为None,从配置读取)
            port: 端口 (如果为None,从配置读取)
            space_name: 空间名称 (如果为None,从配置读取)
            username: 用户名 (如果为None,从配置读取)
            password: 密码 (如果为None,从配置读取)
        """
        # 从配置获取默认值
        nebula_config = get_nebula_config()
        host = host or nebula_config.get('host', '127.0.0.1')
        port = port or nebula_config.get('port', 9669)
        space_name = space_name or nebula_config.get('space', 'patent_full_text_v2')
        username = username or nebula_config.get('user', 'root')
        password = password or nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))

        try:
            from nebula3.gclient.net import ConnectionPool

            # 创建连接池
            self.nebula_client = ConnectionPool()
            self.nebula_client.init(
                [(host, port)],
                space_name,
                username,
                password
            )

            self._connected = True
            logger.info(f"✅ 已连接到NebulaGraph: {host}:{port}/{space_name}")

        except ImportError:
            logger.warning("⚠️  nebula3未安装，将生成NGQL语句但不执行")
            self.nebula_client = None
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            raise

    def close(self):
        """关闭连接"""
        if self.nebula_client:
            try:
                self.nebula_client.close()
                logger.info("✅ 已关闭NebulaGraph连接")
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass
        self._connected = False

    def build_patent_kg(
        self,
        patent_number: str,
        patent_data: dict[str, Any],
        triple_result: Any | None = None
    ) -> KGBuildResult:
        """
        构建专利知识图谱

        Args:
            patent_number: 专利号
            patent_data: 专利基础数据
            triple_result: 三元组提取结果

        Returns:
            KGBuildResult 构建结果
        """
        start_time = time.time()

        try:
            result = KGBuildResult(
                patent_number=patent_number,
                success=True
            )

            # 1. 创建专利基础顶点
            self._create_patent_vertex(patent_number, patent_data, result)

            # 2. 如果有三元组，创建技术分析顶点和边
            if triple_result and hasattr(triple_result, 'problems'):
                self._create_technical_vertices(triple_result, result)
                self._create_triple_edges(triple_result, result)

            # 3. 统计结果
            self._summarize_results(result)
            result.processing_time = time.time() - start_time

            logger.info(f"✅ 知识图谱构建完成: {result.total_vertices}顶点, "
                       f"{result.total_edges}边")

            return result

        except Exception as e:
            logger.error(f"❌ 知识图谱构建失败: {e}")
            return KGBuildResult(
                patent_number=patent_number,
                success=False,
                error_message=str(e),
                processing_time=time.time() - start_time
            )

    def _create_patent_vertex(
        self,
        patent_number: str,
        patent_data: dict[str, Any],
        result: KGBuildResult
    ):
        """创建专利基础顶点"""
        # 属性
        props = {
            "patent_number": f'"{patent_number}"',
            "title": f'"{patent_data.get("title", "")}"',
            "abstract": f'"{patent_data.get("abstract", "")}"',
            "ipc_main_class": f'"{patent_data.get("ipc_main_class", "")}"',
            "ipc_subclass": f'"{patent_data.get("ipc_subclass", "")}"',
            "patent_type": f'"{patent_data.get("patent_type", "invention")}"',
            "publication_date": patent_data.get("publication_date", 0),
            "application_date": patent_data.get("application_date", 0),
        }

        # 移除空值
        props = {k: v for k, v in props.items() if v not in ['', '', 0, '']}

        # 生成NGQL
        ngql = self.INSERT_VERTEX_TEMPLATE.format(
            tag_name="patent",
            props=", ".join([f"{k}={v}" for k, v in props.items()]),
            vid=patent_number
        )

        # 执行或保存
        insert_result = self._execute_ngql(
            ngql,
            "vertex",
            patent_number
        )
        result.vertex_results.append(insert_result)

    def _create_technical_vertices(
        self,
        triple_result,
        kg_result: KGBuildResult
    ):
        """创建技术分析顶点（问题/特征/效果）"""
        # 1. 创建技术问题顶点
        for problem in triple_result.problems:
            props = {
                "description": f'"{problem.description}"',
                "problem_type": f'"{problem.problem_type}"',
                "source_section": f'"{problem.source_section}"',
                "severity": problem.severity
            }

            ngql = self.INSERT_VERTEX_TEMPLATE.format(
                tag_name="technical_problem",
                props=", ".join([f"{k}={v}" for k, v in props.items()]),
                vid=problem.id
            )

            insert_result = self._execute_ngql(ngql, "vertex", problem.id)
            kg_result.vertex_results.append(insert_result)

            # 创建patent -> problem边
            self._create_edge(
                kg_result,
                kg_result.patent_number,
                problem.id,
                "HAS_PROBLEM"
            )

        # 2. 创建技术特征顶点
        for feature in triple_result.features:
            props = {
                "description": f'"{feature.description}"',
                "feature_category": f'"{feature.feature_category}"',
                "feature_type": f'"{feature.feature_type}"',
                "source_claim": feature.source_claim,
                "importance": feature.importance
            }

            ngql = self.INSERT_VERTEX_TEMPLATE.format(
                tag_name="technical_feature",
                props=", ".join([f"{k}={v}" for k, v in props.items()]),
                vid=feature.id
            )

            insert_result = self._execute_ngql(ngql, "vertex", feature.id)
            kg_result.vertex_results.append(insert_result)

            # 创建patent -> feature边
            self._create_edge(
                kg_result,
                kg_result.patent_number,
                feature.id,
                "HAS_FEATURE"
            )

        # 3. 创建技术效果顶点
        for effect in triple_result.effects:
            props = {
                "description": f'"{effect.description}"',
                "effect_type": f'"{effect.effect_type}"',
                "quantifiable": str(effect.quantifiable).lower(),
                "metrics": f'"{effect.metrics}"'
            }

            ngql = self.INSERT_VERTEX_TEMPLATE.format(
                tag_name="technical_effect",
                props=", ".join([f"{k}={v}" for k, v in props.items()]),
                vid=effect.id
            )

            insert_result = self._execute_ngql(ngql, "vertex", effect.id)
            kg_result.vertex_results.append(insert_result)

            # 创建patent -> effect边
            self._create_edge(
                kg_result,
                kg_result.patent_number,
                effect.id,
                "HAS_EFFECT"
            )

    def _create_triple_edges(
        self,
        triple_result,
        kg_result: KGBuildResult
    ):
        """创建三元组边"""
        # 1. SOLVES边 (feature -> problem)
        # 2. ACHIEVES边 (feature -> effect)
        for triple in triple_result.triples:
            edge_type = triple.relation

            # 属性
            props = {
                "confidence": triple.confidence
            }

            ngql = self.INSERT_EDGE_TEMPLATE.format(
                edge_name=edge_type,
                props=", ".join([f"{k}={v}" for k, v in props.items()]),
                src_vid=triple.subject,
                dst_vid=triple.object
            )

            insert_result = self._execute_ngql(ngql, "edge", triple.subject)
            kg_result.edge_results.append(insert_result)

        # 3. RELATES_TO边 (feature -> feature)
        for relation in triple_result.feature_relations:
            props = {
                "relation_type": f'"{relation.relation_type}"',
                "strength": relation.strength,
                "description": f'"{relation.description}"'
            }

            ngql = self.INSERT_EDGE_TEMPLATE.format(
                edge_name="RELATES_TO",
                props=", ".join([f"{k}={v}" for k, v in props.items()]),
                src_vid=relation.from_feature,
                dst_vid=relation.to_feature
            )

            insert_result = self._execute_ngql(ngql, "edge", relation.from_feature)
            kg_result.edge_results.append(insert_result)

    def _create_edge(
        self,
        result: KGBuildResult,
        src_vid: str,
        dst_vid: str,
        edge_type: str,
        props: dict[str, Any] | None = None
    ):
        """创建边"""
        if props is None:
            props = {}

        # 转换属性
        prop_strs = []
        for k, v in props.items():
            if isinstance(v, str):
                prop_strs.append(f'{k}="{v}"')
            else:
                prop_strs.append(f'{k}={v}')

        ngql = self.INSERT_EDGE_TEMPLATE.format(
            edge_name=edge_type,
            props=", ".join(prop_strs) if prop_strs else "",
            src_vid=src_vid,
            dst_vid=dst_vid
        )

        insert_result = self._execute_ngql(ngql, "edge", src_vid)
        result.edge_results.append(insert_result)

    def _execute_ngql(
        self,
        ngql: str,
        entity_type: str,
        entity_id: str
    ) -> InsertResult:
        """
        执行NGQL语句

        Args:
            ngql: NGQL语句
            entity_type: 实体类型（vertex/edge）
            entity_id: 实体ID

        Returns:
            InsertResult
        """
        start_time = time.time()

        try:
            if self.nebula_client and self._connected:
                # 实际执行
                session = self.nebula_client.session_pool.get_session()
                try:
                    result = session.execute(ngql)
                    if result.is_succeeded():
                        return InsertResult(
                            status=InsertStatus.SUCCESS,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            execution_time=time.time() - start_time
                        )
                    else:
                        return InsertResult(
                            status=InsertStatus.FAILED,
                            entity_type=entity_type,
                            entity_id=entity_id,
                            message=result.error_msg(),
                            execution_time=time.time() - start_time
                        )
                finally:
                    session.release()
            else:
                # 无客户端，返回成功（仅生成NGQL）
                return InsertResult(
                    status=InsertStatus.SUCCESS,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    message="[NGQL生成] " + ngql[:100] + "...",
                    execution_time=time.time() - start_time
                )

        except Exception as e:
            return InsertResult(
                status=InsertStatus.FAILED,
                entity_type=entity_type,
                entity_id=entity_id,
                message=str(e),
                execution_time=time.time() - start_time
            )

    def _summarize_results(self, result: KGBuildResult):
        """统计结果"""
        result.total_vertices = len(result.vertex_results)
        result.total_edges = len(result.edge_results)

        for r in result.all_results:
            if r.status == InsertStatus.FAILED:
                result.failed_count += 1
            elif r.status == InsertStatus.SKIPPED:
                result.skipped_count += 1

        # 如果有失败，标记为失败
        if result.failed_count > 0:
            result.success = False

    def batch_build(
        self,
        patents: list[dict[str, Any]],
        triple_results: list[Any] | None = None
    ) -> list[KGBuildResult]:
        """
        批量构建知识图谱

        Args:
            patents: 专利数据列表
            triple_results: 三元组结果列表（可选）

        Returns:
            List[KGBuildResult]
        """
        results = []

        for i, patent_data in enumerate(patents):
            patent_number = patent_data.get("patent_number", f"patent_{i}")

            # 获取对应的三元组结果
            triple_result = None
            if triple_results and i < len(triple_results):
                triple_result = triple_results[i]

            result = self.build_patent_kg(
                patent_number,
                patent_data,
                triple_result
            )
            results.append(result)

        return results

    def get_ngql_script(
        self,
        patent_number: str,
        patent_data: dict[str, Any],
        triple_result: Any | None = None
    ) -> str:
        """
        获取完整的NGQL脚本（用于手动执行）

        Returns:
            str NGQL脚本
        """
        lines = []
        lines.append(f"-- Patent KG Building Script for {patent_number}")
        lines.append(f"-- Generated at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("")

        # USE space
        lines.append("USE patent_full_text_v2;")
        lines.append("")

        # 临时断开连接以生成NGQL
        original_client = self.nebula_client
        self.nebula_client = None

        # 构建图谱（会生成NGQL）
        result = self.build_patent_kg(patent_number, patent_data, triple_result)

        # 收集所有NGQL
        for r in result.all_results:
            if r.message and r.message.startswith("[NGQL生成]"):
                lines.append(r.message.replace("[NGQL生成] ", ""))
                lines.append("")

        # 恢复客户端
        self.nebula_client = original_client

        return "\n".join(lines)


# ========== 便捷函数 ==========

def build_patent_kg(
    patent_number: str,
    patent_data: dict[str, Any],
    triple_result: Any | None = None,
    nebula_host: str = "127.0.0.1",
    nebula_port: int = 9669
) -> KGBuildResult:
    """
    构建专利知识图谱

    Args:
        patent_number: 专利号
        patent_data: 专利数据
        triple_result: 三元组结果
        nebula_host: NebulaGraph主机
        nebula_port: NebulaGraph端口

    Returns:
        KGBuildResult
    """
    builder = PatentKGBuilderV2()
    try:
        builder.connect(nebula_host, nebula_port)
        return builder.build_patent_kg(patent_number, patent_data, triple_result)
    except Exception as e:
        logger.error(f"❌ 构建知识图谱失败: {e}")
        return KGBuildResult(
            patent_number=patent_number,
            success=False,
            error_message=str(e)
        )
    finally:
        builder.close()


# ========== 示例使用 ==========

def main():
    """示例使用"""
    print("=" * 70)
    print("知识图谱构建器V2 示例")
    print("=" * 70)

    # 示例专利数据
    patent_data = {
        "patent_number": "CN112233445A",
        "title": "一种基于人工智能的图像识别方法",
        "abstract": "本发明公开了一种基于人工智能的图像识别方法。",
        "ipc_main_class": "G06F",
        "ipc_subclass": "G06F40/00",
        "patent_type": "invention",
        "publication_date": 20210815,
        "application_date": 20201201
    }

    # 示例三元组结果
    from rule_extractor import (
        TechnicalEffect,
        TechnicalFeature,
        TechnicalProblem,
        Triple,
        TripleExtractionResult,
    )

    triple_result = TripleExtractionResult(
        patent_number="CN112233445A",
        success=True,
        problems=[
            TechnicalProblem(
                id="CN112233445A_p_0",
                description="现有图像识别方法精度较低",
                problem_type="technical"
            )
        ],
        features=[
            TechnicalFeature(
                id="CN112233445A_f_0",
                description="深度学习模型",
                feature_category="structural"
            )
        ],
        effects=[
            TechnicalEffect(
                id="CN112233445A_e_0",
                description="提高识别准确率",
                effect_type="direct"
            )
        ],
        triples=[
            Triple(
                subject="CN112233445A_f_0",
                relation="SOLVES",
                object="CN112233445A_p_0",
                confidence=0.8
            ),
            Triple(
                subject="CN112233445A_f_0",
                relation="ACHIEVES",
                object="CN112233445A_e_0",
                confidence=0.8
            )
        ]
    )

    # 构建图谱
    builder = PatentKGBuilderV2()

    # 生成NGQL脚本（不执行）
    print("\n📝 生成NGQL脚本:")
    ngql_script = builder.get_ngql_script(
        "CN112233445A",
        patent_data,
        triple_result
    )
    print(ngql_script[:500] + "...")
    print("\n✅ 脚本生成完成")


if __name__ == "__main__":
    main()
