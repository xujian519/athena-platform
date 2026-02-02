#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专利档案表更新分析工具
分析新的专利档案表并检查与数据库的重复情况
"""

import pandas as pd
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import sys
import logging

logger = logging.getLogger(__name__)


# 添加项目路径
sys.path.append(str(Path(__file__).parent))

try:
    import asyncpg
    import sqlalchemy
    from sqlalchemy import create_engine, Column, Integer, String, Date, Text, Boolean, DateTime, Numeric, ForeignKey
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.sql import func
    DB_AVAILABLE = True

    # 导入安全环境配置
    import sys
    from pathlib import Path
    sys.path.append(str(Path(__file__).parent.parent / "core"))
    from security.env_config import get_database_url
except ImportError:
    print("数据库模块未安装")
    DB_AVAILABLE = False

class PatentArchiveAnalyzer:
    """专利档案分析器"""

    def __init__(self, excel_path: str):
        self.excel_path = excel_path
        self.new_data = None
        self.existing_patents = set()
        self.existing_clients = set()

    def analyze_excel_structure(self):
        """分析Excel表格结构"""
        try:
            # 读取Excel文件
            print("🔍 正在分析Excel表格结构...")

            # 先读取前几行看结构
            df_header = pd.read_excel(self.excel_path, nrows=5)

            print("\n📋 Excel表格列结构:")
            for i, col in enumerate(df_header.columns):
                print(f"  {i+1:2d}. {col}")

            # 读取全部数据
            df = pd.read_excel(self.excel_path)

            # 清理列名
            df.columns = df.columns.str.strip()

            self.new_data = df

            print(f"\n📊 数据概览:")
            print(f"  总行数: {len(df)}")
            print(f"  总列数: {len(df.columns)}")

            # 显示示例数据
            print(f"\n📝 前3行数据示例:")
            for idx, row in df.head(3).iterrows():
                print(f"  行{idx+1}:")
                for col in df.columns[:5]:  # 只显示前5列
                    value = row[col]
                    if pd.isna(value):
                        value = "空"
                    elif isinstance(value, str) and len(value) > 20:
                        value = value[:20] + "..."
                    print(f"    {col}: {value}")
                print()

            return True

        except Exception as e:
            print(f"❌ 读取Excel失败: {str(e)}")
            return False

    def load_existing_data(self):
        """加载现有数据库数据用于去重检查"""
        if not DB_AVAILABLE:
            print("⚠️ 数据库不可用，跳过现有数据加载")
            return False

        try:
            print("\n🔗 正在连接数据库...")

            # 连接数据库（使用环境变量）
            database_url = get_database_url()
            engine = create_engine(database_url)

            Session = sessionmaker(bind=engine)
            session = Session()

            # 加载现有专利号
            try:
                result = session.execute("SELECT DISTINCT patent_number FROM patents WHERE patent_number IS NOT NULL")
                self.existing_patents = {row[0] for row in result if row[0]}
                print(f"  现有专利数量: {len(self.existing_patents)}")
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[patent_archive_updater] Exception: {e}")
                print("  ⚠️ patents表不存在，跳过专利号去重")

            # 加载现有客户
            try:
                result = session.execute("SELECT DISTINCT name FROM clients WHERE name IS NOT NULL")
                self.existing_clients = {row[0] for row in result if row[0]}
                print(f"  现有客户数量: {len(self.existing_clients)}")
            except Exception as e:
                # 记录异常但不中断流程
                logger.debug(f"[patent_archive_updater] Exception: {e}")
                print("  ⚠️ clients表不存在，跳过客户去重")

            session.close()
            return True

        except Exception as e:
            print(f"❌ 连接数据库失败: {str(e)}")
            return False

    def identify_columns(self) -> Dict[str, str]:
        """智能识别关键列"""
        columns = {}

        for col in self.new_data.columns:
            col_str = str(col).strip()

            # 精确匹配
            if '申请号' in col_str and '专利' not in col_str:
                columns['application_number'] = col
            elif '专利名称' in col_str:
                columns['patent_name'] = col
            elif '案源人' in col_str or '客户' in col_str:
                columns['client_name'] = col
            elif '代理人' in col_str:
                columns['agent'] = col
            elif '类型' in col_str:
                columns['patent_type'] = col
            elif '申请日' in col_str:
                columns['filing_date'] = col
            elif '授权日' in col_str:
                columns['grant_date'] = col
            elif '缴费联系人' in col_str or '联系人' in col_str:
                columns['contact'] = col
            elif '法律状态' in col_str:
                columns['status'] = col
            elif '档案号' in col_str:
                columns['archive_number'] = col
            elif '申请方式' in col_str:
                columns['application_method'] = col
            elif '审查意见' in col_str:
                columns['review_status'] = col
            elif '档案存放' in col_str:
                columns['archive_location'] = col

        return columns

    def extract_patent_data(self, row, columns: Dict) -> Dict | None:
        """提取单行专利数据"""
        # 获取申请号作为去重关键字段
        app_num_col = columns.get('application_number')
        if app_num_col and pd.notna(row[app_num_col]):
            app_num = str(row[app_num_col]).strip()
            # 过滤掉日期格式（明显不是专利号的数据）
            if app_num and not app_num.startswith('20'):
                patent_number = app_num
            else:
                patent_number = f"NEW_{hashlib.md5(str(row, usedforsecurity=False).encode(), usedforsecurity=False).hexdigest()[:8]}"
        else:
            # 生成唯一标识
            patent_number = f"NEW_{hashlib.md5(str(row, usedforsecurity=False).encode()).hexdigest()[:8]}"

        # 提取客户名称
        client_name = ""
        if 'client_name' in columns and pd.notna(row[columns['client_name']]):
            client_name = str(row[columns['client_name']]).strip()
        elif 'patent_name' in columns and pd.notna(row[columns['patent_name']]):
            # 尝试从专利名称中提取客户名称
            patent_name = str(row[columns['patent_name']])
            if '公司' in patent_name:
                parts = patent_name.split('公司')
                if len(parts) > 1:
                    client_name = parts[0] + '公司'
            elif '有限' in patent_name:
                parts = patent_name.split('有限')
                if len(parts) > 1:
                    client_name = ''.join(parts[:2]) + '有限'
            elif '大学' in patent_name:
                parts = patent_name.split('大学')
                if len(parts) > 1:
                    client_name = parts[0] + '大学'
            elif '学院' in patent_name:
                parts = patent_name.split('学院')
                if len(parts) > 1:
                    client_name = parts[0] + '学院'

        # 推断专利类型
        patent_type = "实用新型"  # 默认
        if 'patent_type' in columns and pd.notna(row[columns['patent_type']]):
            type_str = str(row[columns['patent_type']]).lower()
            if '发明' in type_str:
                patent_type = "发明专利"
            elif '实用' in type_str:
                patent_type = "实用新型"
            elif '外观' in type_str:
                patent_type = "外观设计"

        return {
            'patent_number': patent_number,
            'patent_name': str(row.get(columns.get('patent_name', ''), "")).strip(),
            'client_name': client_name,
            'patent_type': patent_type,
            'filing_date': self._parse_date(row.get(columns.get('filing_date', ""), "")),
            'grant_date': self._parse_date(row.get(columns.get('grant_date', ""), "")),
            'status': str(row.get(columns.get('status', ""), "")).strip(),
            'contact': str(row.get(columns.get('contact', ""), "")).strip(),
            'agent': str(row.get(columns.get('agent', ""), "")).strip(),
            'archive_number': str(row.get(columns.get('archive_number', ""), "")).strip(),
            'application_method': str(row.get(columns.get('application_method', ""), "")).strip(),
            'review_status': str(row.get(columns.get('review_status', ""), "")).strip(),
            'archive_location': str(row.get(columns.get('archive_location', ""), "")).strip(),
            'source_file': str(self.excel_path),
            'import_time': datetime.now().isoformat()
        }

    def _parse_date(self, date_value) -> str | None:
        """解析日期"""
        if pd.isna(date_value):
            return None

        try:
            if isinstance(date_value, datetime):
                return date_value.strftime("%Y-%m-%d")
            elif isinstance(date_value, str):
                for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d"]:
                    try:
                        dt = datetime.strptime(date_value, fmt)
                        return dt.strftime("%Y-%m-%d")
                    except Exception as e:
                        # 记录异常但不中断流程
                        logger.debug(f"[patent_archive_updater] Exception: {e}")
                        continue
        except Exception as e:

            # 记录异常但不中断流程

            logger.debug(f"[patent_archive_updater] Exception: {e}")
        return str(date_value)

    def analyze_duplicates(self) -> Dict:
        """分析重复数据"""
        if self.new_data is None:
            return {"error": "Excel数据未加载"}

        print("\n🔍 正在分析重复数据...")

        # 识别列
        columns = self.identify_columns()
        print(f"  识别的列映射: {columns}")

        # 提取新数据
        new_patents = []
        duplicate_count = 0
        new_client_count = 0

        for idx, row in self.new_data.iterrows():
            try:
                patent_data = self.extract_patent_data(row, columns)
                if patent_data:
                    # 检查专利号重复
                    patent_num = patent_data['patent_number']
                    if patent_num in self.existing_patents:
                        duplicate_count += 1
                        patent_data['duplicate_status'] = 'patent_number_exists'
                    else:
                        patent_data['duplicate_status'] = 'new'

                        # 检查客户是否为新客户
                        client_name = patent_data['client_name']
                        if client_name and client_name not in self.existing_clients:
                            new_client_count += 1
                            patent_data['new_client'] = True
                        else:
                            patent_data['new_client'] = False

                    new_patents.append(patent_data)

            except Exception as e:
                print(f"  ⚠️ 处理第{idx+1}行出错: {str(e)}")
                continue

        # 统计分析
        total_new = len([p for p in new_patents if p['duplicate_status'] == 'new'])

        analysis_result = {
            "excel_file": str(self.excel_path),
            "analysis_time": datetime.now().isoformat(),
            "total_rows": len(self.new_data),
            "processed_rows": len(new_patents),
            "duplicates_found": duplicate_count,
            "new_patents": total_new,
            "new_clients": new_client_count,
            "column_mapping": columns,
            "patent_data": new_patents,
            "summary": {
                "existing_patents_in_db": len(self.existing_patents),
                "existing_clients_in_db": len(self.existing_clients),
                "duplicate_rate": f"{duplicate_count/len(new_patents)*100:.1f}%" if new_patents else "0%"
            }
        }

        print(f"\n📊 分析结果:")
        print(f"  总行数: {analysis_result['total_rows']}")
        print(f"  处理行数: {analysis_result['processed_rows']}")
        print(f"  重复专利: {duplicate_count}")
        print(f"  新专利: {total_new}")
        print(f"  新客户: {new_client_count}")
        print(f"  重复率: {analysis_result['summary']['duplicate_rate']}")

        return analysis_result

    def save_analysis(self, analysis_result: Dict):
        """保存分析结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"patent_archive_analysis_{timestamp}.json"

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)

        print(f"\n💾 分析结果已保存到: {filename}")
        return filename


def main():
    """主函数"""
    excel_path = "/Users/xujian/工作/10_归档文件/专利档案表（2016---) .xlsx"

    print("🚀 专利档案表更新分析工具")
    print("=" * 50)

    # 检查文件
    if not Path(excel_path).exists():
        print(f"❌ 文件不存在: {excel_path}")
        return False

    # 创建分析器
    analyzer = PatentArchiveAnalyzer(excel_path)

    # 1. 分析Excel结构
    if not analyzer.analyze_excel_structure():
        return False

    # 2. 加载现有数据
    analyzer.load_existing_data()

    # 3. 分析重复数据
    analysis_result = analyzer.analyze_duplicates()

    # 4. 保存分析结果
    analyzer.save_analysis(analysis_result)

    print("\n✅ 分析完成！")
    return True


if __name__ == "__main__":
    main()