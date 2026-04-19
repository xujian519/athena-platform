#!/usr/bin/env python3
"""
增强型专利检索模块 v2.0 - 修正版

修正说明:
- authorization_number 字段实际存储的是授权日期
- 公开号 (publication_number) 是唯一可用于下载的编号
- 对于实用新型专利,公开号就是授权公告号

作者: Athena Platform Team
版本: 2.0.0
创建时间: 2026-01-07
"""

from __future__ import annotations
import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any

import psycopg2

from core.logging_config import setup_logging

# 配置日志
# setup_logging()  # 日志配置已移至模块导入
logger = setup_logging()


@dataclass
class PatentInfo:
    """专利信息数据类 v2.0"""

    # 基本信息
    patent_name: str
    application_number: str
    patent_type: str

    # 编号信息(重要:用于下载)
    publication_number: str | None = None  # 公开号(实用新型的授权公告号)
    # 注意:数据库中的authorization_number字段实际是授权日期,不是编号

    # 日期信息
    application_date: str | None = None
    publication_date: str | None = None
    grant_date: str | None = None  # 授权日期(从authorization_number字段获取)

    # 申请人信息
    applicant: str | None = None
    inventor: str | None = None

    # IPC分类
    ipc_main_class: str | None = None
    ipc_classification: str | None = None

    # 内容
    abstract: str | None = None
    claims_content: str | None = None

    # PDF信息
    pdf_path: str | None = None
    pdf_downloaded: bool = False

    def get_best_number_for_download(self) -> str | None:
        """
        获取最适合用于下载的专利号

        优先级:
        1. publication_number (公开号) - 实用新型的授权公告号
        2. application_number (申请号) - 兜底

        Returns:
            最适合下载的专利号
        """
        if self.publication_number:
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

    def get_cnipa_download_params(self) -> dict[str, str]:
        """
        获取CNIPA下载参数

        Returns:
            包含申请号、公开号等信息的字典
        """
        return {
            "application_number": self.application_number,
            "publication_number": self.publication_number or "",
            "patent_type": self.patent_type,
            "patent_name": self.patent_name,
        }

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
  注: 实用新型的公开号即授权公告号
  最佳下载号: {self.get_best_number_for_download()}

[日期信息]
  申请日: {self.application_date or '无'}
  公开日/授权日: {self.publication_date or '无'}

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
    """增强型专利检索器 v2.0"""

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
                application_date,
                publication_date,
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

            # 处理授权日期(从authorization_number字段获取,但这里我们不查这个字段)
            # 如果需要授权日期,单独查询

            return PatentInfo(**patent_dict)

        return None

    def search_by_keywords(
        self, keywords: list[str], limit: int = 20, require_publication_number: bool = True
    ) -> list[PatentInfo]:
        """
        根据关键词检索专利

        Args:
            keywords: 关键词列表
            limit: 返回数量限制
            require_publication_number: 是否要求有公开号

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

        # 如果要求有公开号
        if require_publication_number:
            where_clause += " AND publication_number IS NOT NULL"

        query = f"""
            SELECT
                patent_name,
                application_number,
                patent_type,
                publication_number,
                application_date,
                publication_date,
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
        self, applicant: str, limit: int = 30, require_publication_number: bool = True
    ) -> list[PatentInfo]:
        """
        根据申请人检索专利

        Args:
            applicant: 申请人名称
            limit: 返回数量限制
            require_publication_number: 是否要求有公开号

        Returns:
            PatentInfo对象列表
        """
        query = """
            SELECT
                patent_name,
                application_number,
                patent_type,
                publication_number,
                application_date,
                publication_date,
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

        if require_publication_number:
            query += " AND publication_number IS NOT NULL"

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
        获取准备好下载的专利列表(有公开号但未下载PDF)

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
                application_date,
                publication_date,
                applicant,
                inventor,
                ipc_main_class,
                ipc_classification,
                abstract,
                claims_content,
                pdf_path,
                pdf_downloaded_at IS NOT NULL as pdf_downloaded
            FROM patents
            WHERE publication_number IS NOT NULL
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
        self,
        output_file: str,
        patent_list: list[PatentInfo] | None = None,
        format: str = "both",  # 'csv', 'json', or 'both'
    ):
        """
        导出专利下载清单

        Args:
            output_file: 输出文件路径(不含扩展名)
            patent_list: 专利列表,如果为None则自动获取
            format: 导出格式 ('csv', 'json', or 'both')
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
                    "best_number": patent.get_best_number_for_download(),
                    "download_url": patent.get_download_url(),
                    "applicant": patent.applicant or "",
                    "application_date": (
                        str(patent.application_date) if patent.application_date else ""
                    ),
                    "publication_date": (
                        str(patent.publication_date) if patent.publication_date else ""
                    ),
                    "patent_type": patent.patent_type,
                    "pdf_downloaded": patent.pdf_downloaded,
                }
            )

        if format in ["csv", "both"]:
            # 保存为CSV
            csv_file = f"{output_file}.csv"
            with open(csv_file, "w", newline="", encoding="utf-8") as f:
                if export_data:
                    writer = csv.DictWriter(f, fieldnames=export_data[0].keys())
                    writer.writeheader()
                    writer.writerows(export_data)
            logger.info(f"已导出 {len(export_data)} 条专利到 {csv_file}")

        if format in ["json", "both"]:
            # 保存为JSON
            json_file = f"{output_file}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            logger.info(f"已导出 JSON 到 {json_file}")

    def generate_mcp_download_commands(
        self, output_file: str, patent_list: list[PatentInfo] | None = None
    ):
        """
        生成MCP下载命令脚本

        Args:
            output_file: 输出脚本文件路径
            patent_list: 专利列表,如果为None则自动获取
        """
        if patent_list is None:
            patent_list = self.get_patents_ready_for_download(limit=50)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write("#!/bin/bash\n")
            f.write("# 专利PDF批量下载脚本\n")
            f.write(f"# 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"# 专利数量: {len(patent_list)}\n\n")

            f.write('echo "开始下载专利PDF文件..."\n\n')

            for i, patent in enumerate(patent_list, 1):
                best_number = patent.get_best_number_for_download()
                f.write(f"# {i}. {patent.patent_name}\n")
                f.write(f"#    申请号: {patent.application_number}\n")
                f.write(f"#    公开号: {patent.publication_number or '无'}\n")
                f.write(f'echo "正在下载 [{i}/{len(patent_list)}] {best_number}..."\n')
                f.write("# 使用MCP工具下载\n")
                f.write(f'# 调用: download_patent(patent_number="{best_number}")\n\n')

            f.write('echo "下载完成!"\n')

        # 设置执行权限
        import os

        os.chmod(output_file, 0o755)

        logger.info(f"已生成MCP下载脚本: {output_file}")


def main() -> None:
    """主函数 - 示例用法"""

    print("=" * 80)
    print("🔍 增强型专利检索模块 v2.0 - 示例用法")
    print("=" * 80)

    # 使用上下文管理器自动处理连接
    with EnhancedPatentRetriever() as retriever:

        # 示例1: 根据申请号检索
        print("\n[示例1]根据申请号检索专利\n")
        patent = retriever.search_by_application_number("CN97207103.2")

        if patent:
            print(patent.to_summary())

            # 保存详细信息
            output_file = "/tmp/CN97207103.2_完整信息_v2.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(patent.to_dict(), f, ensure_ascii=False, indent=2, default=str)
            print(f"\n💾 完整信息已保存至: {output_file}")
        else:
            print("未找到专利")

        # 示例2: 根据关键词检索(要求有公开号)
        print("\n" + "=" * 80)
        print("[示例2]根据关键词检索专利(要求有公开号)\n")

        patents = retriever.search_by_keywords(
            keywords=["色带盒", "隔离"],
            limit=10,
            require_publication_number=True,  # 只返回有公开号的专利
        )

        print(f"找到 {len(patents)} 条有公开号的专利:\n")
        for i, p in enumerate(patents[:5], 1):
            print(f"{i}. {p.patent_name}")
            print(f"   申请号: {p.application_number}")
            print(f"   公开号: {p.publication_number}")
            print(f"   最佳下载号: {p.get_best_number_for_download()}")
            print(f"   下载URL: {p.get_download_url()}")
            print()

        # 示例3: 导出下载清单
        print("=" * 80)
        print("[示例3]导出专利下载清单\n")

        base_file = "/tmp/patent_download_list_v2"
        retriever.export_download_list(base_file, format="both")

        # 示例4: 生成MCP下载脚本
        print("\n" + "=" * 80)
        print("[示例4]生成MCP下载命令脚本\n")

        script_file = "/tmp/download_patents_mcp.sh"
        retriever.generate_mcp_download_commands(script_file)

        print(f"✅ MCP下载脚本已生成: {script_file}")
        print("   可以使用此脚本配合MCP服务器批量下载专利")

    print("\n" + "=" * 80)
    print("✅ 示例完成")
    print("=" * 80)


if __name__ == "__main__":
    main()
