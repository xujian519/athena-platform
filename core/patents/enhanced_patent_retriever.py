#!/usr/bin/env python3
from __future__ import annotations
"""
增强型专利检索模块 - 返回完整专利信息(包括公开号、公告号等)

作者: Athena Platform Team
版本: 1.0.0
创建时间: 2026-01-07
"""

import json
from dataclasses import asdict, dataclass
from typing import Any

import psycopg2

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class PatentInfo:
    """专利信息数据类"""

    # 基本信息
    patent_name: str
    application_number: str
    patent_type: str

    # 编号信息(重要:用于下载)
    publication_number: Optional[str] = None
    authorization_number: Optional[str] = None

    # 日期信息
    application_date: Optional[str] = None
    publication_date: Optional[str] = None
    authorization_date: Optional[str] = None

    # 申请人信息
    applicant: Optional[str] = None
    inventor: Optional[str] = None

    # IPC分类
    ipc_main_class: Optional[str] = None
    ipc_classification: Optional[str] = None

    # 内容
    abstract: Optional[str] = None
    claims_content: Optional[str] = None

    # PDF信息
    pdf_path: Optional[str] = None
    pdf_downloaded: bool = False

    def get_best_number_for_download(self) -> Optional[str]:
        """
        获取最适合用于下载的专利号

        优先级:
        1. authorization_number (授权公告号) - 最稳定
        2. publication_number (公开号) - 次选
        3. application_number (申请号) - 兜底

        Returns:
            最适合下载的专利号
        """
        if self.authorization_number:
            return self.authorization_number
        elif self.publication_number:
            return self.publication_number
        else:
            return self.application_number

    def get_download_url(self, base_url: str = "https://patents.google.com/patent/") -> str:
        """
        获取Google Patents下载URL

        Args:
            base_url: 基础URL

        Returns:
            完整的下载URL
        """
        best_number = self.get_best_number_for_download()
        # 确保号码包含CN前缀
        if not best_number.startswith("CN"):
            best_number = f"CN{best_number}"
        return f"{base_url}{best_number}/zh"

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    def to_summary(self) -> str:
        """生成摘要信息"""
        summary = f"""
[专利基本信息]
  专利名称: {self.patent_name}
  申请号: {self.application_number}
  专利类型: {self.patent_type}

[编号信息](用于下载)
  公开号: {self.publication_number or '无'}
  授权公告号: {self.authorization_number or '无'}
  最佳下载号: {self.get_best_number_for_download()}

[日期信息]
  申请日: {self.application_date or '无'}
  公开日: {self.publication_date or '无'}
  授权日: {self.authorization_date or '无'}

[申请人信息]
  申请人: {self.applicant or '无'}
  发明人: {self.inventor or '无'}

[分类信息]
  IPC主分类: {self.ipc_main_class or '无'}

[PDF状态]
  已下载: {'是' if self.pdf_downloaded else '否'}
  路径: {self.pdf_path or '无'}

[下载链接]
  Google Patents: {self.get_download_url()}
"""
        return summary.strip()


class EnhancedPatentRetriever:
    """增强型专利检索器"""

    def __init__(self, db_config: dict | None = None):
        """
        初始化专利检索器

        Args:
            db_config: 数据库配置,默认使用本地patent_db
        """
        if db_config is None:
            db_config = {
                "host": "localhost",
                "port": 5432,
                "database": "patent_db",
                "user": "postgres",
                "password": "postgres",
            }

        self.db_config = db_config
        self.conn = None
        self.cursor = None

    def connect(self) -> Any:
        """连接数据库"""
        try:
            self.conn = psycopg2.connect(**self.db_config)
            self.cursor = self.conn.cursor()
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            raise

    def close(self) -> Any:
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("数据库连接已关闭")

    def __enter__(self):
        """上下文管理器入口"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器出口"""
        self.close()

    def search_by_application_number(self, application_number: str) -> PatentInfo | None:
        """
        根据申请号检索专利

        Args:
            application_number: 申请号

        Returns:
            PatentInfo对象或None
        """
        query = """
            SELECT
                patent_name,
                application_number,
                patent_type,
                publication_number,
                authorization_number,
                application_date,
                publication_date,
                authorization_date,
                applicant,
                inventor,
                ipc_main_class,
                ipc_classification,
                abstract,
                claims_content,
                pdf_path,
                pdf_downloaded_at IS NOT NULL as pdf_downloaded
            FROM patents
            WHERE application_number = %s
            LIMIT 1
        """

        self.cursor.execute(query, (application_number,))
        result = self.cursor.fetchone()

        if result:
            col_names = [desc[0] for desc in self.cursor.description]
            patent_dict = dict(zip(col_names, result, strict=False))
            return PatentInfo(**patent_dict)

        return None

    def search_by_keywords(
        self, keywords: list[str], limit: int = 20, require_full_numbers: bool = True
    ) -> list[PatentInfo]:
        """
        根据关键词检索专利

        Args:
            keywords: 关键词列表
            limit: 返回数量限制
            require_full_numbers: 是否要求有完整的编号信息(公开号或授权公告号)

        Returns:
            PatentInfo对象列表
        """
        # 构建WHERE条件
        conditions = []
        params = []

        for keyword in keywords:
            conditions.append("patent_name ILIKE %s")
            params.append(f"%{keyword}%")

        where_clause = " OR ".join(conditions)

        # 如果要求完整编号
        if require_full_numbers:
            where_clause += (
                " AND (publication_number IS NOT NULL OR authorization_number IS NOT NULL)"
            )

        query = f"""
            SELECT
                patent_name,
                application_number,
                patent_type,
                publication_number,
                authorization_number,
                application_date,
                publication_date,
                authorization_date,
                applicant,
                inventor,
                ipc_main_class,
                ipc_classification,
                abstract,
                claims_content,
                pdf_path,
                pdf_downloaded_at IS NOT NULL as pdf_downloaded
            FROM patents
            WHERE {where_clause}
            ORDER BY application_date DESC
            LIMIT %s
        """

        params.append(limit)

        self.cursor.execute(query, params)
        results = self.cursor.fetchall()

        col_names = [desc[0] for desc in self.cursor.description]
        patents = []

        for result in results:
            patent_dict = dict(zip(col_names, result, strict=False))
            patents.append(PatentInfo(**patent_dict))

        return patents

    def search_by_applicant(
        self, applicant: str, limit: int = 30, require_full_numbers: bool = True
    ) -> list[PatentInfo]:
        """
        根据申请人检索专利

        Args:
            applicant: 申请人名称
            limit: 返回数量限制
            require_full_numbers: 是否要求有完整的编号信息

        Returns:
            PatentInfo对象列表
        """
        query = """
            SELECT
                patent_name,
                application_number,
                patent_type,
                publication_number,
                authorization_number,
                application_date,
                publication_date,
                authorization_date,
                applicant,
                inventor,
                ipc_main_class,
                ipc_classification,
                abstract,
                claims_content,
                pdf_path,
                pdf_downloaded_at IS NOT NULL as pdf_downloaded
            FROM patents
            WHERE applicant ILIKE %s
        """

        if require_full_numbers:
            query += " AND (publication_number IS NOT NULL OR authorization_number IS NOT NULL)"

        query += " ORDER BY application_date DESC LIMIT %s"

        self.cursor.execute(query, (f"%{applicant}%", limit))
        results = self.cursor.fetchall()

        col_names = [desc[0] for desc in self.cursor.description]
        patents = []

        for result in results:
            patent_dict = dict(zip(col_names, result, strict=False))
            patents.append(PatentInfo(**patent_dict))

        return patents

    def get_patents_ready_for_download(self, limit: int = 100) -> list[PatentInfo]:
        """
        获取准备好下载的专利列表(有公开号或授权公告号但未下载PDF)

        Args:
            limit: 返回数量限制

        Returns:
            PatentInfo对象列表
        """
        query = """
            SELECT
                patent_name,
                application_number,
                patent_type,
                publication_number,
                authorization_number,
                application_date,
                publication_date,
                authorization_date,
                applicant,
                inventor,
                ipc_main_class,
                ipc_classification,
                abstract,
                claims_content,
                pdf_path,
                pdf_downloaded_at IS NOT NULL as pdf_downloaded
            FROM patents
            WHERE
                (publication_number IS NOT NULL OR authorization_number IS NOT NULL)
                AND pdf_path IS NULL
            ORDER BY application_date DESC
            LIMIT %s
        """

        self.cursor.execute(query, (limit,))
        results = self.cursor.fetchall()

        col_names = [desc[0] for desc in self.cursor.description]
        patents = []

        for result in results:
            patent_dict = dict(zip(col_names, result, strict=False))
            patents.append(PatentInfo(**patent_dict))

        return patents

    def export_download_list(
        self, output_file: str, patent_list: list[PatentInfo] | None = None
    ):
        """
        导出专利下载清单

        Args:
            output_file: 输出文件路径
            patent_list: 专利列表,如果为None则自动获取
        """
        if patent_list is None:
            patent_list = self.get_patents_ready_for_download()

        # 准备导出数据
        export_data = []
        for patent in patent_list:
            export_data.append(
                {
                    "patent_name": patent.patent_name,
                    "application_number": patent.application_number,
                    "publication_number": patent.publication_number or "",
                    "authorization_number": patent.authorization_number or "",
                    "best_number": patent.get_best_number_for_download(),
                    "download_url": patent.get_download_url(),
                    "applicant": patent.applicant or "",
                    "application_date": (
                        str(patent.application_date) if patent.application_date else ""
                    ),
                    "pdf_downloaded": patent.pdf_downloaded,
                }
            )

        # 保存为CSV
        import csv

        with open(output_file, "w", newline="", encoding="utf-8") as f:
            if export_data:
                writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
                writer.writeheader()
                writer.writerows(export_data)

        logger.info(f"已导出 {len(export_data)} 条专利到 {output_file}")

        # 同时保存为JSON
        json_file = output_file.replace(".csv", ".json")
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(
                [p.to_dict() for p in patent_list], f, ensure_ascii=False, indent=2, default=str
            )

        logger.info(f"已导出 JSON 到 {json_file}")


def main() -> None:
    """主函数 - 示例用法"""

    print("=" * 80)
    print("🔍 增强型专利检索模块 - 示例用法")
    print("=" * 80)

    # 使用上下文管理器自动处理连接
    with EnhancedPatentRetriever() as retriever:

        # 示例1: 根据申请号检索
        print("\n[示例1]根据申请号检索专利\n")
        patent = retriever.search_by_application_number("CN97207103.2")

        if patent:
            print(patent.to_summary())

            # 保存详细信息
            output_file = "/tmp/CN97207103.2_完整信息.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(patent.to_dict(), f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 完整信息已保存至: {output_file}")
        else:
            print("未找到专利")

        # 示例2: 根据关键词检索
        print("\n" + "=" * 80)
        print("[示例2]根据关键词检索专利(要求有完整编号)\n")

        patents = retriever.search_by_keywords(
            keywords=["色带盒", "打印头"],
            limit=10,
            require_full_numbers=True,  # 只返回有公开号或授权公告号的专利
        )

        print(f"找到 {len(patents)} 条专利:\n")
        for i, p in enumerate(patents[:5], 1):
            print(f"{i}. {p.patent_name}")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number or '无'}")
            print(f"   授权公告号: {p.authorization_number or '无'}")
            print(f"   最佳下载号: {p.get_best_number_for_download()}")
            print(f"   下载URL: {p.get_download_url()}")
            print()

        # 示例3: 导出下载清单
        print("=" * 80)
        print("[示例3]导出专利下载清单\n")

        csv_file = "/tmp/patent_download_list.csv"
        retriever.export_download_list(csv_file)

        print(f"✅ 下载清单已导出至: {csv_file}")

    print("\n" + "=" * 80)
    print("✅ 示例完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
