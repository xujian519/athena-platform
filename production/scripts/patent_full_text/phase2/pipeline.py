#!/usr/bin/env python3
"""
专利全文处理管道
整合PDF提取、权利要求解析、向量化、知识图谱构建和数据库更新

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
from core.config.secure_config import get_config

config = get_config()

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# 导入安全配置
try:
    from production.config import get_nebula_config, get_postgres_config
except ImportError:
    def get_postgres_config() -> Any | None:
        return {'host': 'localhost', 'port': 5432, 'user': 'athena', "password": config.get("POSTGRES_PASSWORD", required=True), 'database': 'patent_db'}
    def get_nebula_config() -> Any | None:
        return {'host': '127.0.0.1', 'port': 9669, 'user': 'root', "password": config.get("NEBULA_PASSWORD", required=True), 'space': 'patent_full_text'}

# 导入配置管理
try:
    from config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# 导入各处理模块
from claim_parser import ClaimParser
from kg_builder import PatentKGBuilder
from pdf_extractor import PDFExtractor
from postgresql_updater import PostgreSQLUpdater
from vector_processor import BGEVectorizer

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    """管道处理结果"""
    patent_number: str
    success: bool

    # 各模块处理结果
    pdf_extracted: bool = False
    claims_parsed: bool = False
    vectorized: bool = False
    kg_built: bool = False
    db_updated: bool = False

    # 生成的ID
    vector_ids: dict[str, str] = None
    kg_vertex_id: str = None
    postgres_id: str = None

    # 错误信息
    error_message: str | None = None

    def __post_init__(self):
        if self.vector_ids is None:
            self.vector_ids = {}

    @property
    def completion_rate(self) -> float:
        """完成率"""
        steps = [self.pdf_extracted, self.claims_parsed, self.vectorized,
                 self.kg_built, self.db_updated]
        return sum(steps) / len(steps) * 100


class PatentFullTextPipeline:
    """专利全文处理管道"""

    def __init__(
        self,
        qdrant_host: str = "localhost",
        qdrant_port: int = 6333,
        nebula_hosts: str = None,
        postgres_host: str = None,
        postgres_port: int = None,
        postgres_db: str = None,
        postgres_user: str = None,
        postgres_password: str = None,
        config=None  # 配置对象（可选）
    ):
        """
        初始化处理管道

        Args:
            qdrant_host: Qdrant主机
            qdrant_port: Qdrant端口
            nebula_hosts: NebulaGraph地址 (如果为None,从配置读取)
            postgres_host: PostgreSQL主机 (如果为None,从配置读取)
            postgres_port: PostgreSQL端口 (如果为None,从配置读取)
            postgres_db: 数据库名
            postgres_user: 用户名
            postgres_password: 密码
            config: 配置对象（可选，优先级高于其他参数）
        """
        # 从配置获取默认值
        if postgres_host is None:
            pg_config = get_postgres_config()
            postgres_host = pg_config.get('host', 'localhost')
            postgres_port = pg_config.get('port', 5432)
            postgres_db = pg_config.get('database', 'patent_db')
            postgres_user = pg_config.get('user', 'athena')
            postgres_password = pg_config.get("password", config.get("POSTGRES_PASSWORD", required=True))

        if nebula_hosts is None:
            nebula_config = get_nebula_config()
            nebula_hosts = f"{nebula_config.get('host', '127.0.0.1')}:{nebula_config.get('port', 9669)}"

        # 使用配置对象（如果提供）
        if config is not None and CONFIG_AVAILABLE:
            qdrant_host = config.qdrant.host
            qdrant_port = config.qdrant.port
            nebula_hosts = config.nebula.hosts
            postgres_host = config.postgresql.host
            postgres_port = config.postgresql.port
            postgres_db = config.postgresql.database
            postgres_user = config.postgresql.user
            postgres_password = config.postgresql.password

        # 初始化各模块
        self.pdf_extractor = PDFExtractor()
        self.claim_parser = ClaimParser()
        self.vectorizer = BGEVectorizer(
            collection_name="patent_full_text",
            qdrant_host=qdrant_host,
            qdrant_port=qdrant_port,
            config=config
        )
        self.kg_builder = PatentKGBuilder(
            hosts=nebula_hosts,
            space_name="patent_full_text",
            config=config
        )
        self.db_updater = PostgreSQLUpdater(
            host=postgres_host,
            port=postgres_port,
            database=postgres_db,
            user=postgres_user,
            password=postgres_password
        )

    def process_pdf(
        self,
        pdf_path: str,
        metadata: dict[str, Any] | None = None
    ) -> PipelineResult:
        """
        处理单个PDF文件（完整流程）

        Args:
            pdf_path: PDF文件路径
            metadata: 专利元数据（从patent-search等获取）

        Returns:
            PipelineResult: 处理结果
        """
        pdf_path = Path(pdf_path)
        patent_number = pdf_path.stem

        logger.info("=" * 70)
        logger.info(f"开始处理专利: {patent_number}")
        logger.info("=" * 70)

        result = PipelineResult(patent_number=patent_number, success=False)

        try:
            # 步骤1: 提取PDF内容
            logger.info("\n[1/5] 📄 提取PDF内容")
            pdf_content = self.pdf_extractor.extract(str(pdf_path))
            result.pdf_extracted = True
            logger.info(f"   ✅ PDF提取成功: {pdf_content.pages_count}页")

            # 步骤2: 解析权利要求
            logger.info("\n[2/5] ⚖️  解析权利要求")
            if pdf_content.claims:
                parsed_claims = self.claim_parser.parse(pdf_content.claims)
                result.claims_parsed = True
                logger.info(f"   ✅ 权利要求解析成功: {len(parsed_claims.claims)}条")
            else:
                parsed_claims = None
                logger.warning("   ⚠️  未找到权利要求书")

            # 步骤3: 向量化
            logger.info("\n[3/5] 🔄 向量化处理")
            vector_results = self.vectorizer.vectorize_patent(
                patent_number=patent_number,
                title=pdf_content.title,
                abstract=pdf_content.abstract,
                claims=pdf_content.claims,
                description=pdf_content.description
            )

            # 提取成功的向量ID
            for section, vr in vector_results.items():
                if vr.success:
                    result.vector_ids[section] = vr.vector_id

            if result.vector_ids:
                result.vectorized = True
                logger.info(f"   ✅ 向量化成功: {len(result.vector_ids)}个部分")
            else:
                logger.warning("   ⚠️  向量化失败")

            # 步骤4: 构建知识图谱
            logger.info("\n[4/5] 🕸️  构建知识图谱")

            # 获取元数据
            patent_name = metadata.get("patent_name") if metadata else pdf_content.title
            applicant = metadata.get("applicant") if metadata else ""
            ipc_class = metadata.get("ipc_main_class") if metadata else ""

            kg_result = self.kg_builder.build_patent_kg(
                patent_number=patent_number,
                patent_name=patent_name or pdf_content.title,
                application_number=metadata.get("application_number") if metadata else "",
                applicant=applicant,
                inventor=metadata.get("inventor") if metadata else "",
                ipc_main_class=ipc_class,
                abstract=pdf_content.abstract,
                claims_text=pdf_content.claims
            )

            if kg_result.success:
                result.kg_built = True
                result.kg_vertex_id = kg_result.vertex_id
                logger.info(f"   ✅ 知识图谱构建成功: {kg_result.vertices_created}顶点, {kg_result.edges_created}边")
            else:
                logger.warning(f"   ⚠️  知识图谱构建失败: {kg_result.error_message}")

            # 步骤5: 更新数据库
            logger.info("\n[5/5] 💾 更新数据库")

            # 尝试从PostgreSQL查找记录
            postgres_record = None
            if metadata and metadata.get("postgres_id"):
                postgres_record = self.db_updater.get_patent_by_publication_number(patent_number)

            update_results = self.db_updater.update_all(
                patent_number=patent_number,
                pdf_path=str(pdf_path),
                vector_ids=result.vector_ids if result.vector_ids else None,
                kg_vertex_id=result.kg_vertex_id if result.kg_built else None
            )

            if any(r.success for r in update_results.values()):
                result.db_updated = True

                # 获取PostgreSQL ID
                for r in update_results.values():
                    if r.postgres_id:
                        result.postgres_id = r.postgres_id
                        break

                logger.info("   ✅ 数据库更新成功")
            else:
                logger.warning("   ⚠️  数据库更新失败")

            # 判断整体成功
            result.success = (
                result.pdf_extracted and
                (result.vectorized or result.kg_built or result.db_updated)
            )

            # 输出总结
            logger.info("\n" + "=" * 70)
            logger.info("处理结果总结")
            logger.info("=" * 70)
            logger.info(f"   专利号: {result.patent_number}")
            logger.info(f"   PDF提取: {'✅' if result.pdf_extracted else '❌'}")
            logger.info(f"   权利要求解析: {'✅' if result.claims_parsed else '❌'}")
            logger.info(f"   向量化: {'✅' if result.vectorized else '❌'}")
            logger.info(f"   知识图谱: {'✅' if result.kg_built else '❌'}")
            logger.info(f"   数据库更新: {'✅' if result.db_updated else '❌'}")
            logger.info(f"   完成率: {result.completion_rate:.1f}%")
            logger.info("=" * 70)

            return result

        except Exception as e:
            logger.error(f"❌ 处理失败: {e}")
            result.error_message = str(e)
            return result

    def process_batch(
        self,
        pdf_files: list[str],
        metadata_list: list[dict[str, Any]] | None = None
    ) -> list[PipelineResult]:
        """
        批量处理PDF文件

        Args:
            pdf_files: PDF文件路径列表
            metadata_list: 对应的元数据列表

        Returns:
            List[PipelineResult]: 处理结果列表
        """
        logger.info(f"📦 批量处理: {len(pdf_files)}个PDF文件")

        results = []
        successful = 0
        failed = 0

        for i, pdf_file in enumerate(pdf_files, 1):
            logger.info(f"\n{'=' * 70}")
            logger.info(f"[{i}/{len(pdf_files)}] {Path(pdf_file).name}")
            logger.info('=' * 70)

            # 获取对应的元数据
            metadata = None
            if metadata_list and i <= len(metadata_list):
                metadata = metadata_list[i - 1]

            result = self.process_pdf(pdf_file, metadata)
            results.append(result)

            if result.success:
                successful += 1
            else:
                failed += 1

        # 输出批量统计
        logger.info("\n" + "=" * 70)
        logger.info("批量处理统计")
        logger.info("=" * 70)
        logger.info(f"总计: {len(pdf_files)}")
        logger.info(f"成功: {successful}")
        logger.info(f"失败: {failed}")
        logger.info(f"成功率: {successful/len(pdf_files)*100:.1f}%")

        # 各步骤统计
        pdf_ok = sum(1 for r in results if r.pdf_extracted)
        claims_ok = sum(1 for r in results if r.claims_parsed)
        vec_ok = sum(1 for r in results if r.vectorized)
        kg_ok = sum(1 for r in results if r.kg_built)
        db_ok = sum(1 for r in results if r.db_updated)

        logger.info("\n各步骤成功数:")
        logger.info(f"  PDF提取: {pdf_ok}/{len(pdf_files)}")
        logger.info(f"  权利要求解析: {claims_ok}/{len(pdf_files)}")
        logger.info(f"  向量化: {vec_ok}/{len(pdf_files)}")
        logger.info(f"  知识图谱: {kg_ok}/{len(pdf_files)}")
        logger.info(f"  数据库更新: {db_ok}/{len(pdf_files)}")

        return results

    def close(self) -> Any:
        """关闭所有连接"""
        self.kg_builder.close()
        self.db_updater.close()
        logger.info("🔌 管道已关闭")


# ==================== 示例使用 ====================

def main() -> None:
    """示例使用"""
    pipeline = PatentFullTextPipeline()

    # 示例1: 处理单个PDF
    print("=" * 70)
    print("专利全文处理管道 - 单个PDF处理示例")
    print("=" * 70)

    # 查找测试PDF
    test_pdfs = list(Path("/Users/xujian/apps/apps/patents/PDF/CN").glob("*.pdf"))
    if test_pdfs:
        test_pdf = test_pdfs[0]

        # 模拟元数据
        metadata = {
            "postgres_id": "test-uuid-001",
            "patent_name": "测试专利名称",
            "application_number": "CN202110001234",
            "applicant": "测试申请人",
            "inventor": "张三",
            "ipc_main_class": "G06F"
        }

        result = pipeline.process_pdf(str(test_pdf), metadata)

        print("\n📋 处理结果:")
        print(f"   成功: {result.success}")
        print(f"   完成率: {result.completion_rate:.1f}%")
        print(f"   向量ID: {len(result.vector_ids)}个")
        print(f"   KG顶点ID: {result.kg_vertex_id}")
        print(f"   PostgreSQL ID: {result.postgres_id}")

    pipeline.close()


if __name__ == "__main__":
    main()
