#!/usr/bin/env python3
"""
专利申请信息管理系统
Patent Application Information Management System

统一管理专利申请的所有关键信息,包括申请人、发明人、费用明细等
支持自动提取、存储、查询和统计功能

作者: 小娜·天秤女神
创建时间: 2025-12-17
版本: v1.0.0
"""

from __future__ import annotations
import json
import sqlite3
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class ApplicantInfo:
    """申请人信息"""

    name: str  # 申请人名称
    id_type: str  # 身份证类型 (身份证/信用代码)
    id_number: str  # 身份证号码/信用代码
    address: str  # 申请地址
    postal_code: str  # 邮编
    phone: str  # 联系电话
    email: str | None = None  # 电子邮箱
    organization_type: str | None = None  # 机构类型 (个人/企业/科研机构)


@dataclass
class InventorInfo:
    """发明人信息"""

    name: str  # 发明人姓名
    id_number: str  # 身份证号码
    sequence: int  # 排序
    education: str | None = None  # 学历
    professional_title: str | None = None  # 职称
    workplace: str | None = None  # 工作单位
    contribution: str | None = None  # 主要贡献


@dataclass
class FeeDetails:
    """费用明细"""

    application_fee: float  # 申请费
    examination_fee: float  # 实质审查费 (发明专利)
    printing_fee: float  # 印刷费
    certificate_fee: float  # 证书费
    maintenance_fee: float | None = None  # 年费
    agency_fee: float | None = None  # 代理费
    other_fees: dict[str, float] | None = None  # 其他费用
    total_amount: float = 0.0  # 总费用
    payment_status: str = "未支付"  # 支付状态


@dataclass
class PatentApplication:
    """专利申请完整信息"""

    # 基本信息
    patent_id: str  # 专利申请ID (系统生成)
    patent_name: str  # 专利名称
    patent_type: str  # 专利类型 (发明/实用新型/外观设计)
    application_date: str  # 申请日期
    application_number: str | None = None  # 申请号

    # 联系信息
    contact_person: str  # 联系人姓名
    contact_phone: str  # 联系电话
    contact_email: str | None = None  # 联系邮箱

    # 申请人信息 (支持多个申请人)
    applicants: list[ApplicantInfo] | None = None

    # 发明人信息
    inventors: list[InventorInfo] | None = None

    # 费用信息
    fee_details: FeeDetails = None

    # 状态信息
    application_status: str = "准备中"  # 申请状态
    priority_date: str | None = None  # 优先权日期

    # 其他信息
    technical_field: str | None = None  # 技术领域
    abstract: str | None = None  # 摘要
    keywords: list[str] | None = None  # 关键词

    # 系统信息
    created_at: str = ""  # 创建时间
    updated_at: str = ""  # 更新时间
    created_by: str = ""  # 创建人
    notes: str | None = None  # 备注信息

    def __post_init__(self):
        if not self.patent_id:
            self.patent_id = f"PA{datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4())[:8].upper()}"
        if not self.applicants:
            self.applicants = []
        if not self.inventors:
            self.inventors = []
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = self.created_at
        if self.fee_details and self.fee_details.total_amount == 0.0:
            # 自动计算总费用
            total = (
                self.fee_details.application_fee
                + self.fee_details.examination_fee
                + self.fee_details.printing_fee
                + self.fee_details.certificate_fee
            )
            if self.fee_details.maintenance_fee:
                total += self.fee_details.maintenance_fee
            if self.fee_details.agency_fee:
                total += self.fee_details.agency_fee
            if self.fee_details.other_fees:
                total += sum(self.fee_details.other_fees.values())
            self.fee_details.total_amount = total


class PatentApplicationDatabase:
    """专利申请数据库管理"""

    def __init__(self, db_path: str | None = None):
        if db_path is None:
            db_path = Path(__file__).parent.parent.parent / "data" / "patent_applications.db"
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> Any:
        """初始化数据库"""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 专利申请主表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS patent_applications (
                    patent_id TEXT PRIMARY KEY,
                    patent_name TEXT NOT NULL,
                    patent_type TEXT NOT NULL,
                    application_date TEXT NOT NULL,
                    application_number TEXT,
                    contact_person TEXT NOT NULL,
                    contact_phone TEXT NOT NULL,
                    contact_email TEXT,
                    application_status TEXT DEFAULT '准备中',
                    priority_date TEXT,
                    technical_field TEXT,
                    abstract TEXT,
                    keywords TEXT,  -- JSON格式存储
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    created_by TEXT,
                    notes TEXT,
                    fee_details TEXT,  -- JSON格式存储
                    raw_data TEXT  -- 原始数据JSON存储
                )
            """)

            # 申请人表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applicants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    id_type TEXT NOT NULL,
                    id_number TEXT NOT NULL,
                    address TEXT NOT NULL,
                    postal_code TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT,
                    organization_type TEXT,
                    sequence INTEGER,
                    FOREIGN KEY (patent_id) REFERENCES patent_applications (patent_id)
                )
            """)

            # 发明人表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS inventors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    id_number TEXT NOT NULL,
                    sequence INTEGER NOT NULL,
                    education TEXT,
                    professional_title TEXT,
                    workplace TEXT,
                    contribution TEXT,
                    FOREIGN KEY (patent_id) REFERENCES patent_applications (patent_id)
                )
            """)

            # 费用明细表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fee_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT NOT NULL,
                    application_fee REAL NOT NULL,
                    examination_fee REAL NOT NULL,
                    printing_fee REAL NOT NULL,
                    certificate_fee REAL NOT NULL,
                    maintenance_fee REAL,
                    agency_fee REAL,
                    other_fees TEXT,  -- JSON格式
                    total_amount REAL NOT NULL,
                    payment_status TEXT DEFAULT '未支付',
                    FOREIGN KEY (patent_id) REFERENCES patent_applications (patent_id)
                )
            """)

            # 文档档案表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS application_documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT NOT NULL,
                    document_type TEXT NOT NULL,  -- 文档类型:确认书、技术交底书、说明书等
                    document_name TEXT NOT NULL,  -- 文档名称
                    file_path TEXT NOT NULL,      -- 文件路径
                    file_size INTEGER,            -- 文件大小
                    upload_time TEXT NOT NULL,    -- 上传时间
                    uploaded_by TEXT,             -- 上传人
                    notes TEXT,                   -- 备注
                    FOREIGN KEY (patent_id) REFERENCES patent_applications (patent_id)
                )
            """)

            # 创建索引
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_patent_applications_name ON patent_applications(patent_name)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_patent_applications_date ON patent_applications(application_date)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_applicants_patent_id ON applicants(patent_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_inventors_patent_id ON inventors(patent_id)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_fee_details_patent_id ON fee_details(patent_id)"
            )

            conn.commit()

    def save_patent_application(self, application: PatentApplication) -> str:
        """保存专利申请信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 保存主表信息
            cursor.execute(
                """
                INSERT OR REPLACE INTO patent_applications
                (patent_id, patent_name, patent_type, application_date, application_number,
                 contact_person, contact_phone, contact_email, application_status,
                 priority_date, technical_field, abstract, keywords,
                 created_at, updated_at, created_by, notes, fee_details, raw_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    application.patent_id,
                    application.patent_name,
                    application.patent_type,
                    application.application_date,
                    application.application_number,
                    application.contact_person,
                    application.contact_phone,
                    application.contact_email,
                    application.application_status,
                    application.priority_date,
                    application.technical_field,
                    application.abstract,
                    (
                        json.dumps(application.keywords, ensure_ascii=False)
                        if application.keywords
                        else None
                    ),
                    application.created_at,
                    application.updated_at,
                    application.created_by,
                    application.notes,
                    (
                        json.dumps(asdict(application.fee_details), ensure_ascii=False)
                        if application.fee_details
                        else None
                    ),
                    json.dumps(asdict(application), ensure_ascii=False, default=str),
                ),
            )

            # 删除旧的申请人信息
            cursor.execute("DELETE FROM applicants WHERE patent_id = ?", (application.patent_id,))

            # 保存申请人信息
            for i, applicant in enumerate(application.applicants):
                cursor.execute(
                    """
                    INSERT INTO applicants
                    (patent_id, name, id_type, id_number, address, postal_code, phone, email, organization_type, sequence)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        application.patent_id,
                        applicant.name,
                        applicant.id_type,
                        applicant.id_number,
                        applicant.address,
                        applicant.postal_code,
                        applicant.phone,
                        applicant.email,
                        applicant.organization_type,
                        i + 1,
                    ),
                )

            # 删除旧的发明人信息
            cursor.execute("DELETE FROM inventors WHERE patent_id = ?", (application.patent_id,))

            # 保存发明人信息
            for inventor in application.inventors:
                cursor.execute(
                    """
                    INSERT INTO inventors
                    (patent_id, name, id_number, sequence, education, professional_title, workplace, contribution)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        application.patent_id,
                        inventor.name,
                        inventor.id_number,
                        inventor.sequence,
                        inventor.education,
                        inventor.professional_title,
                        inventor.workplace,
                        inventor.contribution,
                    ),
                )

            # 保存费用信息
            if application.fee_details:
                cursor.execute(
                    "DELETE FROM fee_details WHERE patent_id = ?", (application.patent_id,)
                )
                cursor.execute(
                    """
                    INSERT INTO fee_details
                    (patent_id, application_fee, examination_fee, printing_fee, certificate_fee,
                     maintenance_fee, agency_fee, other_fees, total_amount, payment_status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        application.patent_id,
                        application.fee_details.application_fee,
                        application.fee_details.examination_fee,
                        application.fee_details.printing_fee,
                        application.fee_details.certificate_fee,
                        application.fee_details.maintenance_fee,
                        application.fee_details.agency_fee,
                        (
                            json.dumps(application.fee_details.other_fees, ensure_ascii=False)
                            if application.fee_details.other_fees
                            else None
                        ),
                        application.fee_details.total_amount,
                        application.fee_details.payment_status,
                    ),
                )

            conn.commit()
            return application.patent_id

    def get_patent_application(self, patent_id: str) -> PatentApplication | None:
        """获取专利申请信息"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            cursor.execute("SELECT * FROM patent_applications WHERE patent_id = ?", (patent_id,))
            app_row = cursor.fetchone()

            if not app_row:
                return None

            # 获取申请人信息
            cursor.execute(
                "SELECT * FROM applicants WHERE patent_id = ? ORDER BY sequence", (patent_id,)
            )
            applicant_rows = cursor.fetchall()

            # 获取发明人信息
            cursor.execute(
                "SELECT * FROM inventors WHERE patent_id = ? ORDER BY sequence", (patent_id,)
            )
            inventor_rows = cursor.fetchall()

            # 获取费用信息
            cursor.execute("SELECT * FROM fee_details WHERE patent_id = ?", (patent_id,))
            fee_row = cursor.fetchone()

            # 构建申请人信息
            applicants = []
            for row in applicant_rows:
                applicants.append(
                    ApplicantInfo(
                        name=row["name"],
                        id_type=row["id_type"],
                        id_number=row["id_number"],
                        address=row["address"],
                        postal_code=row["postal_code"],
                        phone=row["phone"],
                        email=row["email"],
                        organization_type=row["organization_type"],
                    )
                )

            # 构建发明人信息
            inventors = []
            for row in inventor_rows:
                inventors.append(
                    InventorInfo(
                        name=row["name"],
                        id_number=row["id_number"],
                        sequence=row["sequence"],
                        education=row["education"],
                        professional_title=row["professional_title"],
                        workplace=row["workplace"],
                        contribution=row["contribution"],
                    )
                )

            # 构建费用信息
            fee_details = None
            if fee_row:
                fee_details = FeeDetails(
                    application_fee=fee_row["application_fee"],
                    examination_fee=fee_row["examination_fee"],
                    printing_fee=fee_row["printing_fee"],
                    certificate_fee=fee_row["certificate_fee"],
                    maintenance_fee=fee_row["maintenance_fee"],
                    agency_fee=fee_row["agency_fee"],
                    other_fees=json.loads(fee_row["other_fees"]) if fee_row["other_fees"] else None,
                    total_amount=fee_row["total_amount"],
                    payment_status=fee_row["payment_status"],
                )

            # 构建完整申请信息
            application = PatentApplication(
                patent_id=app_row["patent_id"],
                patent_name=app_row["patent_name"],
                patent_type=app_row["patent_type"],
                application_date=app_row["application_date"],
                application_number=app_row["application_number"],
                contact_person=app_row["contact_person"],
                contact_phone=app_row["contact_phone"],
                contact_email=app_row["contact_email"],
                application_status=app_row["application_status"],
                priority_date=app_row["priority_date"],
                technical_field=app_row["technical_field"],
                abstract=app_row["abstract"],
                keywords=json.loads(app_row["keywords"]) if app_row["keywords"] else None,
                created_at=app_row["created_at"],
                updated_at=app_row["updated_at"],
                created_by=app_row["created_by"],
                notes=app_row["notes"],
                applicants=applicants,
                inventors=inventors,
                fee_details=fee_details,
            )

            return application

    def search_applications(self, **kwargs) -> list[PatentApplication]:
        """搜索专利申请"""
        # 定义允许的搜索字段(白名单验证,防止SQL注入)
        ALLOWED_SEARCH_FIELDS = {
            "patent_name",
            "patent_type",
            "application_status",
            "contact_person",
            "application_date_from",
            "application_date_to",
        }

        conditions = []
        params = []

        for key, value in kwargs.items():
            # 安全验证:只允许预定义的字段
            if key not in ALLOWED_SEARCH_FIELDS:
                continue

            if value is not None:
                if key in ["patent_name", "patent_type", "application_status", "contact_person"]:
                    # 安全:key来自白名单,字符串拼接安全
                    conditions.append(f"{key} LIKE ?")
                    params.append(f"%{value}%")
                elif key in ["application_date_from"]:
                    conditions.append("application_date >= ?")
                    params.append(value)
                elif key in ["application_date_to"]:
                    conditions.append("application_date <= ?")
                    params.append(value)

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 安全说明:where_clause只包含白名单验证过的字段
            cursor.execute(
                f"SELECT patent_id FROM patent_applications {where_clause} ORDER BY created_at DESC",
                params,
            )
            rows = cursor.fetchall()

            applications = []
            for row in rows:
                app = self.get_patent_application(row[0])
                if app:
                    applications.append(app)

            return applications

    def add_document(
        self,
        patent_id: str,
        document_type: str,
        document_name: str,
        file_path: str,
        uploaded_by: str | None = None,
        notes: str | None = None,
    ):
        """添加申请文档档案"""
        file_size = Path(file_path).stat().st_size if Path(file_path).exists() else 0

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO application_documents
                (patent_id, document_type, document_name, file_path, file_size, upload_time, uploaded_by, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    patent_id,
                    document_type,
                    document_name,
                    file_path,
                    file_size,
                    datetime.now().isoformat(),
                    uploaded_by,
                    notes,
                ),
            )
            conn.commit()

    def get_documents(self, patent_id: str) -> list[dict]:
        """获取申请文档列表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM application_documents WHERE patent_id = ? ORDER BY upload_time DESC",
                (patent_id,),
            )
            return [dict(row) for row in cursor.fetchall()]

    def generate_statistics(self) -> dict[str, Any]:
        """生成统计信息"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 基本统计
            cursor.execute("SELECT COUNT(*) FROM patent_applications")
            total_applications = cursor.fetchone()[0]

            cursor.execute(
                "SELECT patent_type, COUNT(*) FROM patent_applications GROUP BY patent_type"
            )
            type_stats = dict(cursor.fetchall())

            cursor.execute(
                "SELECT application_status, COUNT(*) FROM patent_applications GROUP BY application_status"
            )
            status_stats = dict(cursor.fetchall())

            # 费用统计
            cursor.execute("SELECT SUM(total_amount) FROM fee_details")
            total_fees = cursor.fetchone()[0] or 0

            return {
                "total_applications": total_applications,
                "type_distribution": type_stats,
                "status_distribution": status_stats,
                "total_fees": total_fees,
                "last_updated": datetime.now().isoformat(),
            }


class PatentApplicationExtractor:
    """专利申请信息提取器"""

    def __init__(self, database: PatentApplicationDatabase):
        self.database = database

    def extract_from_confirmation_form(
        self, file_path: str, customer_name: str | None = None
    ) -> PatentApplication:
        """从确认书提取信息 - 需要手动输入或OCR识别"""
        print(f"正在解析文件: {file_path}")
        print("由于文档格式限制,需要手动输入信息...")

        # 这里应该集成OCR或手动输入功能
        # 暂时返回一个示例结构
        application = PatentApplication(
            patent_name="农作物幼苗培育保护罩",
            patent_type="实用新型",
            application_date="2025-12-17",
            contact_person="孙俊霞",
            contact_phone="待输入",
            created_by="小娜系统",
        )

        return application

    def auto_fill_template(
        self, template_data: dict[str, Any], customer_info: dict[str, Any]
    ) -> PatentApplication:
        """根据模板和客户信息自动填充"""
        application = PatentApplication(
            patent_name=template_data.get("patent_name", ""),
            patent_type=template_data.get("patent_type", "实用新型"),
            application_date=datetime.now().strftime("%Y-%m-%d"),
            contact_person=customer_info.get("name", ""),
            contact_phone=customer_info.get("phone", ""),
            contact_email=customer_info.get("email", ""),
            created_by="小娜系统",
        )

        # 添加申请人信息
        applicant = ApplicantInfo(
            name=customer_info.get("name", ""),
            id_type="身份证",
            id_number=customer_info.get("id_number", ""),
            address=customer_info.get("address", ""),
            postal_code=customer_info.get("postal_code", ""),
            phone=customer_info.get("phone", ""),
            organization_type="个人",
        )
        application.applicants.append(applicant)

        # 添加发明人信息
        if "inventors" in template_data:
            for i, inventor_data in enumerate(template_data["inventors"]):
                inventor = InventorInfo(
                    name=inventor_data.get("name", ""),
                    id_number=inventor_data.get("id_number", ""),
                    sequence=i + 1,
                    professional_title=inventor_data.get("professional_title", ""),
                    workplace=inventor_data.get("workplace", ""),
                )
                application.inventors.append(inventor)

        # 设置费用信息
        fee_details = FeeDetails(
            application_fee=template_data.get("application_fee", 500.0),
            examination_fee=template_data.get("examination_fee", 0.0),
            printing_fee=template_data.get("printing_fee", 50.0),
            certificate_fee=template_data.get("certificate_fee", 200.0),
            agency_fee=template_data.get("agency_fee", 0.0),
        )
        application.fee_details = fee_details

        return application


# 使用示例
if __name__ == "__main__":
    # 初始化数据库
    db = PatentApplicationDatabase()

    # 创建提取器
    extractor = PatentApplicationExtractor(db)

    print("专利申请信息管理系统已启动")
    print(f"数据库路径: {db.db_path}")

    # 显示统计信息
    stats = db.generate_statistics()
    print(f"当前申请总数: {stats['total_applications']}")
    print(f"专利类型分布: {stats['type_distribution']}")
    print(f"申请状态分布: {stats['status_distribution']}")
