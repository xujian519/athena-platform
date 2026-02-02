#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利档案Excel解析工具
Patent Archive Excel Parser Tool

解析专利档案Excel表格，提取关键信息到数据库
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import asyncio
import logging

logger = logging.getLogger(__name__)


# 添加项目路径
sys.path.append(str(Path(__file__).parent.parent))

# 数据库连接
try:
    import asyncpg
    import sqlalchemy
    from sqlalchemy import create_engine, Column, Integer, String, Date, Text, Boolean, DateTime, Numeric, ForeignKey
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker, relationship
    from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
    from sqlalchemy.sql import func

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_env_var, get_database_url, get_jwt_secret
    DB_AVAILABLE = True
except ImportError:
    print("数据库模块未安装，将输出到JSON文件")
    DB_AVAILABLE = False

class PatentDataExtractor:
    """专利数据提取器"""

    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.patents = []
        self.clients = {}
        self.cases = {}

    def clean_patent_number(self, patent_str: str) -> str | None:
        """清理专利申请号"""
        if pd.isna(patent_str):
            return None

        # 移除空格和其他字符
        patent_clean = str(patent_str).strip()

        # 匹配专利申请号格式
        pattern = r'(\d{12,13})([\.\-Xx]?\d*)'
        match = re.search(pattern, patent_clean)

        if match:
            base_num = match.group(1)
            suffix = match.group(2).replace('.', '').replace('-', '')
            return f"{base_num}.{suffix}" if suffix else base_num

        return patent_clean

    def normalize_client_name(self, client_name: str) -> str:
        """标准化客户名称"""
        if pd.isna(client_name):
            return "未知客户"

        # 移除常见的公司后缀
        name = str(client_name).strip()
        suffixes = ["有限公司", "股份有限公司", "有限责任公司", "科技", "集团", "公司"]

        for suffix in suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)]

        return name

    def extract_patent_type(self, patent_str: str) -> str:
        """从申请号推断专利类型"""
        if pd.isna(patent_str):
            return "未知"

        patent_str = str(patent_str).lower()

        if "发明" in patent_str:
            return "发明专利"
        elif "实用新型" in patent_str:
            return "实用新型"
        elif "外观" in patent_str:
            return "外观设计"
        else:
            # 从申请号推断
            if len(patent_str) >= 12:
                # 中国专利申请号规则
                # 第5位：1=发明，2=实用新型，3=外观设计
                if len(patent_str) > 5:
                    type_code = patent_str[4]
                    if type_code == '1':
                        return "发明专利"
                    elif type_code == '2':
                        return "实用新型"
                    elif type_code == '3':
                        return "外观设计"

        return "未知"

    def parse_excel(self) -> Dict:
        """解析Excel文件"""
        try:
            # 读取Excel文件
            df = pd.read_excel(self.excel_file_path)

            # 显示列名
            print("Excel表格列名：")
            for i, col in enumerate(df.columns):
                print(f"{i+1}. {col}")

            # 提取数据
            extracted_data = {
                "patents": [],
                "clients": {},
                "summary": {
                    "total_rows": len(df),
                    "processed_rows": 0,
                    "unique_clients": set(),
                    "patent_types": {}
                }
            }

            # 智能识别列
            column_mapping = self.identify_columns(df.columns)
            print("\n列映射：", column_mapping)

            for idx, row in df.iterrows():
                try:
                    patent_data = self.extract_patent_data(row, column_mapping)
                    if patent_data:
                        extracted_data["patents"].append(patent_data)
                        extracted_data["summary"]["processed_rows"] += 1

                        # 统计客户
                        client_name = patent_data.get("client_name", "")
                        if client_name:
                            extracted_data["summary"]["unique_clients"].add(client_name)

                        # 统计专利类型
                        patent_type = patent_data.get("patent_type", "")
                        if patent_type:
                            extracted_data["summary"]["patent_types"][patent_type] = \
                                extracted_data["summary"]["patent_types"].get(patent_type, 0) + 1

                except Exception as e:
                    print(f"处理第{idx+2}行出错: {str(e)}")
                    continue

            # 处理客户信息
            extracted_data["clients"] = self.process_clients(extracted_data["patents"])

            # 转换set为list
            extracted_data["summary"]["unique_clients"] = list(extracted_data["summary"]["unique_clients"])

            return extracted_data

        except Exception as e:
            print(f"解析Excel失败: {str(e)}")
            return {"error": str(e)}

    def identify_columns(self, columns) -> Dict:
        """智能识别列的用途"""
        mapping = {}

        for col in columns:
            col_str = str(col).strip()

            # 精确匹配
            if col_str == "申请号":
                mapping["patent_number"] = col
            elif col_str == "专利名称":
                mapping["patent_name"] = col
            elif col_str == "案源人":
                mapping["client_name"] = col
            elif col_str == "代理人":
                mapping["agency"] = col
            elif col_str == "类型":
                mapping["patent_type"] = col
            elif col_str == "申请日":
                mapping["application_date"] = col
            elif col_str == "缴费联系人及电话":
                mapping["contact"] = col
            elif col_str == "法律状态":
                mapping["status"] = col
            elif col_str == "授权日":
                mapping["grant_date"] = col
            elif col_str == "审查意见":
                mapping["review_status"] = col
            elif col_str == "档案存放":
                mapping["archive_location"] = col
            elif col_str == "申请方式":
                mapping["application_method"] = col
            elif col_str == "序号":
                mapping["sequence_number"] = col
            elif col_str == "档案号":
                mapping["archive_number"] = col

        return mapping

    def extract_patent_data(self, row, column_mapping: Dict) -> Dict | None:
        """提取单行专利数据"""
        patent_number_col = column_mapping.get("patent_number")

        if not patent_number_col:
            return None

        patent_number = self.clean_patent_number(row[patent_number_col])
        if not patent_number:
            return None

        # 从类型列获取专利类型，如果不存在则从申请号推断
        patent_type_col = column_mapping.get("patent_type")
        patent_type = str(row.get(patent_type_col, "")).strip()
        if not patent_type:
            patent_type = self.extract_patent_type(patent_number)

        patent_data = {
            "patent_number": patent_number,
            "patent_name": str(row.get(column_mapping.get("patent_name", ""), "")).strip(),
            "client_name": self.normalize_client_name(row.get(column_mapping.get("client_name", ""), "")),
            "patent_type": patent_type,
            "application_date": self.parse_date(row.get(column_mapping.get("application_date", ""), "")),
            "status": str(row.get(column_mapping.get("status", ""), "")).strip(),
            "contact": str(row.get(column_mapping.get("contact", ""), "")).strip(),
            "agency": str(row.get(column_mapping.get("agency", ""), "")).strip(),
            "grant_date": self.parse_date(row.get(column_mapping.get("grant_date", ""), "")),
            "review_status": str(row.get(column_mapping.get("review_status", ""), "")).strip(),
            "archive_location": str(row.get(column_mapping.get("archive_location", ""), "")).strip(),
            "application_method": str(row.get(column_mapping.get("application_method", ""), "")).strip(),
            "sequence_number": str(row.get(column_mapping.get("sequence_number", ""), "")).strip(),
            "archive_number": str(row.get(column_mapping.get("archive_number", ""), "")).strip(),
        }

        return patent_data

    def parse_date(self, date_value) -> str | None:
        """解析日期"""
        if pd.isna(date_value):
            return None

        try:
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d")
            elif isinstance(date_value, str):
                # 尝试解析各种日期格式
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d"]:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except Exception as e:
                        # 记录异常但不中断流程
                        logger.debug(f"[patent_excel_parser] Exception: {e}")
                        continue
        except Exception as e:

            # 记录异常但不中断流程

            logger.debug(f"[patent_excel_parser] Exception: {e}")
        return str(date_value)

    def parse_number(self, number_value) -> float | None:
        """解析数字"""
        if pd.isna(number_value):
            return None

        try:
            # 移除货币符号和逗号
            if isinstance(number_value, str):
                num_str = re.sub(r'[^\d.]', '', number_value)
                return float(num_str) if num_str else None
            else:
                return float(number_value)
        except Exception as e:
            # 记录异常但不中断流程
            logger.debug(f"[patent_excel_parser] Exception: {e}")
            return None

    def process_clients(self, patents: List[Dict]) -> Dict:
        """处理客户信息，合并相同客户"""
        clients = {}

        for patent in patents:
            client_name = patent.get("client_name", "")
            if not client_name or client_name == "未知客户":
                continue

            if client_name not in clients:
                clients[client_name] = {
                    "client_name": client_name,
                    "patent_count": 0,
                    "total_fee": 0.0,
                    "patents": [],
                    "first_patent_date": None,
                    "last_patent_date": None
                }

            # 更新客户信息
            client = clients[client_name]
            client["patent_count"] += 1

            patent_number = patent.get("patent_number", "")
            if patent_number:
                client["patents"].append(patent_number)

            # 累计费用
            fee = patent.get("fee", 0)
            if fee:
                client["total_fee"] += fee

            # 记录日期范围
            app_date = patent.get("application_date")
            if app_date:
                if not client["first_patent_date"] or app_date < client["first_patent_date"]:
                    client["first_patent_date"] = app_date
                if not client["last_patent_date"] or app_date > client["last_patent_date"]:
                    client["last_patent_date"] = app_date

        return clients

    def save_to_json(self, data: Dict, output_file: str = None):
        """保存到JSON文件"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"patent_data_extracted_{timestamp}.json"

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"数据已保存到: {output_file}")
        return output_file


class PatentDatabaseImporter:
    """专利数据库导入器"""

    def __init__(self, db_config: Dict = None):
        self.db_config = db_config or {
            "host": "localhost",
            "port": 5432,
            "database": "athena_business",
            "username": "postgres",
            "password": "xj781102"
        }

        if DB_AVAILABLE:
            self.engine = create_engine(
                fget_database_url()username']}:{self.db_config['password']}"
                f"@{self.db_config['host']}:{self.db_config['port']}/{self.db_config['database']}"
            )
            self.Base = declarative_base()
            self.create_models()

    def create_models(self):
        """创建数据库模型"""

        class Client(self.Base):
            """客户表"""
            __tablename__ = 'patent_clients'

            id = Column(Integer, primary_key=True)
            client_name = Column(String(200), nullable=False, unique=True)
            client_alias = Column(JSONB)  # 存储客户别名
            contact_info = Column(JSONB)  # 联系信息
            patent_count = Column(Integer, default=0)
            total_fee = Column(Numeric(12, 2), default=0)
            first_patent_date = Column(Date)
            last_patent_date = Column(Date)
            created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
            updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

            # 关系
            patents = relationship("Patent", back_populates="client")

        class Patent(self.Base):
            """专利表"""
            __tablename__ = 'patents'

            id = Column(Integer, primary_key=True)
            patent_number = Column(String(50), nullable=False, unique=True)
            patent_name = Column(String(500))
            patent_type = Column(String(50))
            application_date = Column(Date)
            client_id = Column(Integer, ForeignKey('patent_clients.id'))
            status = Column(String(50))
            fee = Column(Numeric(12, 2))
            contact_info = Column(JSONB)
            agency = Column(String(200))
            notes = Column(Text)
            related_files = Column(JSONB)  # 相关文件路径
            created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
            updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

            # 关系
            client = relationship("Client", back_populates="patents")
            review_records = relationship("PatentReview", back_populates="patent")

        class PatentReview(self.Base):
            """专利审查记录表"""
            __tablename__ = 'patent_reviews'

            id = Column(Integer, primary_key=True)
            patent_id = Column(Integer, ForeignKey('patents.id'))
            review_type = Column(String(50))  # 审查类型
            review_date = Column(Date)
            review_deadline = Column(Date)
            status = Column(String(50))
            content = Column(Text)  # 审查内容
            response = Column(Text)  # 答复内容
            created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

            # 关系
            patent = relationship("Patent", back_populates="review_records")

        self.Client = Client
        self.Patent = Patent
        self.PatentReview = PatentReview

    def import_data(self, extracted_data: Dict):
        """导入数据到数据库"""
        if not DB_AVAILABLE:
            print("数据库不可用，跳过导入")
            return False

        try:
            # 创建表
            self.Base.metadata.create_all(self.engine)

            Session = sessionmaker(bind=self.engine)
            session = Session()

            try:
                # 导入客户数据
                client_map = {}
                for client_name, client_data in extracted_data["clients"].items():
                    # 检查客户是否已存在
                    existing = session.query(self.Client).filter_by(client_name=client_name).first()

                    if existing:
                        # 更新现有客户
                        existing.patent_count += client_data["patent_count"]
                        existing.total_fee += client_data["total_fee"]
                        client_map[client_name] = existing.id
                    else:
                        # 创建新客户
                        new_client = self.Client(
                            client_name=client_name,
                            patent_count=client_data["patent_count"],
                            total_fee=client_data["total_fee"]
                        )
                        session.add(new_client)
                        session.flush()  # 获取ID
                        client_map[client_name] = new_client.id

                # 导入专利数据
                for patent in extracted_data["patents"]:
                    client_name = patent.get("client_name", "")
                    client_id = client_map.get(client_name)

                    # 检查专利是否已存在
                    existing = session.query(self.Patent).filter_by(
                        patent_number=patent["patent_number"]
                    ).first()

                    if not existing:
                        new_patent = self.Patent(
                            patent_number=patent["patent_number"],
                            patent_name=patent.get("patent_name"),
                            patent_type=patent.get("patent_type"),
                            application_date=self.parse_date_to_obj(patent.get("application_date")),
                            client_id=client_id,
                            status=patent.get("status"),
                            fee=patent.get("fee"),
                            agency=patent.get("agency")
                        )
                        session.add(new_patent)

                session.commit()
                print(f"成功导入数据: {len(extracted_data['clients'])}个客户, {len(extracted_data['patents'])}个专利")
                return True

            except Exception as e:
                session.rollback()
                print(f"导入数据失败: {str(e)}")
                return False
            finally:
                session.close()

        except Exception as e:
            print(f"数据库连接失败: {str(e)}")
            return False

    def parse_date_to_obj(self, date_str: str):
        """将日期字符串转换为日期对象"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except Exception as e:
            # 记录异常但不中断流程
            logger.debug(f"[patent_excel_parser] Exception: {e}")
            return None


async def main():
    """主函数"""
    excel_file = "/Users/xujian/工作/06_财务档案/专利档案表_2016.xlsx"

    if not os.path.exists(excel_file):
        print(f"文件不存在: {excel_file}")
        return

    # 解析Excel
    print("开始解析专利档案Excel表格...")
    extractor = PatentDataExtractor(excel_file)
    extracted_data = extractor.parse_excel()

    if "error" in extracted_data:
        print("解析失败:", extracted_data["error"])
        return

    # 保存到JSON
    json_file = extractor.save_to_json(extracted_data)

    # 打印摘要
    summary = extracted_data.get("summary", {})
    print("\n解析摘要:")
    print(f"- 总行数: {summary.get('total_rows', 0)}")
    print(f"- 处理行数: {summary.get('processed_rows', 0)}")
    print(f"- 唯一客户数: {len(summary.get('unique_clients', []))}")
    print(f"- 专利类型分布: {summary.get('patent_types', {})}")

    # 导入数据库
    print("\n开始导入数据库...")
    importer = PatentDatabaseImporter()
    success = importer.import_data(extracted_data)

    if success:
        print("✅ 数据导入成功！")
    else:
        print("❌ 数据导入失败，请检查数据库配置")
        print(f"数据已保存到: {json_file}")


if __name__ == "__main__":
    asyncio.run(main())