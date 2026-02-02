#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Ollama大模型的专利档案表智能导入工具 v2.0
适配现有的athena_business数据库结构
"""

import json
import pandas as pd
import requests
import hashlib
import psycopg2
from psycopg2.extras import execute_values, RealDictCursor
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import os
import sys
import logging
import uuid

# 导入安全配置
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "core"))
from security.env_config import get_env_var, get_database_url, get_jwt_secret

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaPatentImporter:
    """使用Ollama的专利导入器 v2.0"""

    def __init__(self):
        # Ollama配置
        self.ollama_url = "http://localhost:11434/api"
        self.model_name = "qwen:7b"  # 使用qwen模型

        # 数据库配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "athena_business",
            "user": "postgres",
            "password": "xj781102"
        }

        # 缓存现有数据
        self.existing_patents = set()
        self.existing_patent_names = set()
        self.existing_clients = set()
        self.client_map = {}  # 名称到ID的映射

    def query_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """查询Ollama模型"""
        try:
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            }

            if system_prompt:
                payload["system"] = system_prompt

            response = requests.post(f"{self.ollama_url}/generate", json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(f"Ollama请求失败: {response.status_code}")
                return ""

        except Exception as e:
            logger.error(f"查询Ollama出错: {str(e)}")
            return ""

    def load_existing_data(self):
        """加载现有数据库数据"""
        logger.info("🔗 正在加载现有数据...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 加载现有专利申请号
            cursor.execute("""
                SELECT patent_id, application_number, title
                FROM patents
                WHERE application_number IS NOT NULL
            """)
            for row in cursor.fetchall():
                if row[1]:
                    self.existing_patents.add(row[1].strip())
                if row[2]:
                    self.existing_patent_names.add(row[2].strip())

            # 加载现有客户
            cursor.execute("""
                SELECT id, name
                FROM clients
                WHERE name IS NOT NULL
            """)
            for row in cursor.fetchall():
                name = row[1].strip()
                self.existing_clients.add(name)
                self.client_map[name] = row[0]

            logger.info(f"  现有专利: {len(self.existing_patents)}")
            logger.info(f"  现有客户: {len(self.existing_clients)}")

        except Exception as e:
            logger.error(f"加载现有数据失败: {str(e)}")
        finally:
            if conn:
                conn.close()

    def analyze_excel_with_ai(self, excel_path: str) -> Dict:
        """使用AI分析Excel表格结构"""
        logger.info("🤖 使用AI分析Excel表格结构...")

        try:
            # 读取Excel样本
            df = pd.read_excel(excel_path, nrows=20)

            # 准备样本数据
            sample_data = []
            for idx, row in df.iterrows():
                row_data = {}
                for col in df.columns:
                    value = row[col]
                    if pd.isna(value):
                        row_data[col] = None
                    else:
                        row_data[col] = str(value)[:100]  # 限制长度
                sample_data.append(row_data)

            sample_text = json.dumps(sample_data[:5], ensure_ascii=False, indent=2)

            system_prompt = """你是一个专业的专利数据分析师。请分析提供的Excel表格数据，识别出以下关键信息：

1. 申请号/专利号列（通常是数字，如2025开头或包含年份）
2. 客户/申请人名称列（公司名称或个人姓名）
3. 专利名称/发明名称列（描述技术或产品的标题）
4. 专利类型列（发明/实用新型/外观设计）
5. 申请日列
6. 案源人/代理人列
7. 联系人/联系方式列
8. 法律状态列
9. 档案号列
10. 申请方式列
11. 审查意见列
12. 档案存放位置列

请特别注意：
- 专利名称字段可能实际存储的是客户名称，需要区分
- 申请号通常是专利号格式，不会是纯日期"""

            prompt = f"""
请分析以下专利档案Excel样本数据，识别各个列的含义：

{sample_text}

请以JSON格式返回分析结果：
{{
    "column_mapping": {{
        "原列名": "标准字段名",
        ...
    }},
    "data_characteristics": {{
        "total_columns": "总列数",
        "data_quality": "数据质量评估",
        "special_notes": "特殊说明"
    }}
}}
"""

            response = self.query_ollama(prompt, system_prompt)

            # 尝试解析JSON响应
            try:
                if "```json" in response:
                    json_part = response.split("```json")[1].split("```")[0].strip()
                elif "{" in response and "}" in response:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_part = response[start:end]
                else:
                    json_part = response.strip()

                analysis_result = json.loads(json_part)
                analysis_result["excel_file"] = excel_path
                analysis_result["total_rows"] = len(pd.read_excel(excel_path))
                return analysis_result

            except json.JSONDecodeError as e:
                logger.error(f"解析AI响应失败: {e}")
                return self._fallback_analysis(excel_path)

        except Exception as e:
            logger.error(f"AI分析失败: {e}")
            return self._fallback_analysis(excel_path)

    def _fallback_analysis(self, excel_path: str) -> Dict:
        """备用分析方法（不使用AI）"""
        logger.info("使用备用分析方法...")

        df = pd.read_excel(excel_path, nrows=5)
        columns = df.columns.tolist()

        # 简单的列映射
        mapping = {}
        for col in columns:
            col_str = str(col).strip().lower()
            if '申请号' in col_str and not col_str.startswith('专利'):
                mapping[col] = 'application_number'
            elif '专利名称' in col_str:
                mapping[col] = 'patent_title'
            elif '案源人' in col_str or '客户' in col_str:
                mapping[col] = 'client_name'
            elif '类型' in col_str:
                mapping[col] = 'patent_type'
            elif '申请日' in col_str:
                mapping[col] = 'filing_date'
            elif '代理人' in col_str:
                mapping[col] = 'agent'
            elif '状态' in col_str:
                mapping[col] = 'legal_status'
            elif '档案号' in col_str:
                mapping[col] = 'archive_number'

        return {
            "column_mapping": mapping,
            "data_characteristics": {
                "total_columns": len(columns),
                "data_quality": "待评估",
                "special_notes": "使用备用分析方法"
            },
            "excel_file": excel_path,
            "total_rows": len(pd.read_excel(excel_path))
        }

    def extract_client_name_with_ai(self, text: str, fallback: str = "") -> str:
        """使用AI提取客户名称"""
        if not text or pd.isna(text):
            return fallback

        prompt = f"""
从以下文本中提取客户/申请人名称：
1. 通常是公司名称（包含"公司"、"有限"、"科技"等词）
2. 如果是个人，通常是全名
3. 不要提取专利的技术描述部分

文本：{text}

请只返回客户名称，不要其他解释：
"""

        response = self.query_ollama(prompt,
            "你是一个专业的文本提取专家，专门从专利标题中提取客户名称。")

        client_name = response.strip()

        # 如果AI没有返回合理结果，使用简单规则
        if len(client_name) < 2 or '无法' in client_name or '没有' in client_name:
            # 简单提取规则
            text_str = str(text)
            if '公司' in text_str:
                parts = text_str.split('公司')
                if len(parts) > 1:
                    return parts[0] + '公司'
            if '有限' in text_str:
                parts = text_str.split('有限')
                if len(parts) > 1:
                    return parts[:2] + '有限'
            if '大学' in text_str:
                parts = text_str.split('大学')
                if len(parts) > 1:
                    return parts[0] + '大学'
            return fallback

        return client_name

    def extract_patent_title_with_ai(self, text: str) -> str:
        """使用AI提取真实的专利发明名称"""
        if not text or pd.isna(text):
            return ""

        prompt = f"""
从以下文本中提取专利的发明名称（不是客户名称）：
1. 发明名称应该描述技术或产品
2. 不应该包含公司名称
3. 应该简洁明确

文本：{text}

请只返回发明名称，如果无法确定请返回空字符串：
"""

        response = self.query_ollama(prompt,
            "你是一个专利专家，能够准确区分客户名称和专利发明名称。")

        patent_name = response.strip()

        # 如果返回的是客户名称，则说明无法提取发明名称
        if any(word in patent_name for word in ['公司', '有限', '科技', '集团', '企业']):
            return ""

        return patent_name

    def process_excel_data(self, excel_path: str) -> Dict:
        """处理Excel数据"""
        logger.info("📊 开始处理Excel数据...")

        # 1. 使用AI分析结构
        analysis = self.analyze_excel_with_ai(excel_path)
        column_mapping = analysis.get("column_mapping", {})

        # 2. 读取数据
        df = pd.read_excel(excel_path)
        total_rows = len(df)

        logger.info(f"  总行数: {total_rows}")
        logger.info(f"  列映射: {column_mapping}")

        # 3. 处理数据
        processed_data = []
        duplicates = []
        new_clients = set()

        for idx, row in df.iterrows():
            try:
                # 提取申请号
                app_number = None
                app_col = None
                for col, mapped in column_mapping.items():
                    if mapped == 'application_number':
                        app_col = col
                        break

                if app_col and pd.notna(row[app_col]):
                    app_num = str(row[app_col]).strip()
                    # 过滤掉日期格式的数据（申请号不会是纯日期）
                    if not (app_num.startswith('20') and len(app_num) in [8, 10] and app_num.replace('-', '').isdigit()):
                        app_number = app_num

                # 检查专利号重复
                is_duplicate = False
                duplicate_type = None

                if app_number and app_number in self.existing_patents:
                    is_duplicate = True
                    duplicate_type = "申请号重复"

                # 提取客户名称
                client_name = ""
                title_col = None

                # 先找到专利标题列
                for col, mapped in column_mapping.items():
                    if mapped == 'patent_title':
                        title_col = col
                        break

                if 'client_name' in column_mapping.values():
                    for col, mapped in column_mapping.items():
                        if mapped == 'client_name' and pd.notna(row[col]):
                            client_name = str(row[col]).strip()
                            break

                # 如果没有明确的客户列，从专利标题中提取
                if not client_name:
                    if title_col and pd.notna(row[title_col]):
                        client_name = self.extract_client_name_with_ai(str(row[title_col]))

                # 检查是否为新客户
                if client_name and client_name not in self.existing_clients:
                    new_clients.add(client_name)

                # 提取专利类型
                patent_type = "UTILITY_MODEL"  # 默认实用新型
                if 'patent_type' in column_mapping.values():
                    for col, mapped in column_mapping.items():
                        if mapped == 'patent_type' and pd.notna(row[col]):
                            type_str = str(row[col]).lower()
                            if '发明' in type_str:
                                patent_type = "INVENTION"
                            elif '外观' in type_str:
                                patent_type = "DESIGN"
                            break

                # 构建处理后的数据
                processed_record = {
                    "row_index": idx,
                    "application_number": app_number,
                    "client_name": client_name,
                    "patent_title": self.extract_patent_title_with_ai(
                        str(row.get(title_col, "")) if title_col else ""
                    ),
                    "patent_type": patent_type,
                    "is_duplicate": is_duplicate,
                    "duplicate_type": duplicate_type,
                    "new_client": client_name in new_clients if client_name else False,
                    "raw_data": dict(row)
                }

                # 添加其他字段
                field_mapping = {
                    'filing_date': 'filing_date',
                    'agent': 'agent',
                    'legal_status': 'legal_status',
                    'archive_number': 'archive_number',
                    'application_method': 'application_method',
                    'contact': 'contact'
                }

                for col, mapped in column_mapping.items():
                    if mapped in field_mapping and pd.notna(row[col]):
                        processed_record[field_mapping[mapped]] = str(row[col]).strip()

                if is_duplicate:
                    duplicates.append(processed_record)
                else:
                    processed_data.append(processed_record)

            except Exception as e:
                logger.warning(f"处理第{idx+1}行出错: {str(e)}")
                continue

        # 4. 统计结果
        result = {
            "excel_file": excel_path,
            "analysis": analysis,
            "total_rows": total_rows,
            "processed_rows": len(processed_data) + len(duplicates),
            "new_patents": len(processed_data),
            "duplicate_patents": len(duplicates),
            "new_clients": len(new_clients),
            "new_patent_data": processed_data,
            "duplicate_data": duplicates,
            "processing_time": datetime.now().isoformat()
        }

        logger.info(f"\n📈 处理结果:")
        logger.info(f"  新专利: {result['new_patents']}")
        logger.info(f"  重复专利: {result['duplicate_patents']}")
        logger.info(f"  新客户: {result['new_clients']}")

        return result

    def save_to_database(self, processed_data: List[Dict]):
        """保存数据到数据库"""
        logger.info("💾 正在保存数据到数据库...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 准备客户数据
            clients_to_add = {}
            for record in processed_data:
                client_name = record.get('client_name', '').strip()
                if client_name and client_name not in self.existing_clients:
                    clients_to_add[client_name] = {
                        'id': str(uuid.uuid4()),
                        'name': client_name,
                        'client_code': f"C{len(clients_to_add)+1001:04d}",
                        'client_type': 'COMPANY' if '公司' in client_name else 'INDIVIDUAL',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'tenant_id': 'baochen-main'
                    }

            # 插入新客户
            for client_name, client_data in clients_to_add.items():
                cursor.execute("""
                    INSERT INTO clients (id, name, client_code, client_type, created_at, updated_at, tenant_id)
                    VALUES (%(id)s, %(name)s, %(client_code)s, %(client_type)s, %(created_at)s, %(updated_at)s, %(tenant_id)s)
                """, client_data)
                self.client_map[client_name] = client_data['id']

            # 提取客户ID映射
            conn.commit()

            # 准备专利数据
            patent_records = []
            for record in processed_data:
                client_name = record.get('client_name', '').strip()
                client_id = self.client_map.get(client_name)

                # 生成专利ID
                patent_id = str(uuid.uuid4())

                patent_record = {
                    'patent_id': patent_id,
                    'application_number': record.get('application_number'),
                    'title': record.get('patent_title') or f"专利-{record.get('application_number', '未知')}",
                    'applicant': client_name,
                    'inventor': client_name,  # 暂时使用客户名作为发明人
                    'patent_type': record.get('patent_type', 'UTILITY_MODEL'),
                    'filing_date': self._parse_date(record.get('filing_date')),
                    'legal_status': record.get('legal_status', 'PENDING'),
                    'metadata': json.dumps({
                        'source': 'ollama_import',
                        'client_name': client_name,
                        'agent': record.get('agent', ''),
                        'archive_number': record.get('archive_number', ''),
                        'application_method': record.get('application_method', ''),
                        'contact': record.get('contact', ''),
                        'import_time': datetime.now().isoformat()
                    }, ensure_ascii=False),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'created_by': 'ollama_importer'
                }
                patent_records.append(patent_record)

            # 插入专利数据（使用批量插入提高效率）
            if patent_records:
                columns = patent_records[0].keys()
                values = [[record[col] for col in columns] for record in patent_records]

                insert_query = f"""
                    INSERT INTO patents ({', '.join(columns)})
                    VALUES %s
                """

                execute_values(cursor, insert_query, values)

                # 创建对应的案卷
                case_records = []
                for patent in patent_records:
                    case_record = {
                        'id': str(uuid.uuid4()),
                        'case_number': patent['application_number'] or f"CASE-{patent['patent_id'][:8]}",
                        'client_id': self.client_map.get(patent['metadata']['client_name']),
                        'client_name': patent['metadata']['client_name'],
                        'case_type': patent['patent_type'],
                        'title': patent['title'],
                        'status': patent['legal_status'],
                        'assignee': patent['metadata']['agent'],
                        'start_date': patent['filing_date'],
                        'project_name': f"{patent['metadata']['client_name']}项目",
                        'inventor': patent['inventor'],
                        'metadata': patent['metadata'],
                        'created_at': patent['created_at'],
                        'updated_at': patent['updated_at'],
                        'tenant_id': 'baochen-main'
                    }
                    case_records.append(case_record)

                if case_records:
                    case_columns = case_records[0].keys()
                    case_values = [[record[col] for col in case_columns] for record in case_records]

                    case_insert_query = f"""
                        INSERT INTO cases ({', '.join(case_columns)})
                        VALUES %s
                    """

                    execute_values(cursor, case_insert_query, case_values)

            conn.commit()
            logger.info(f"✅ 成功保存 {len(patent_records)} 条专利记录")
            logger.info(f"✅ 成功创建 {len(case_records)} 个案卷")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"保存数据失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    def _parse_date(self, date_str: str) -> datetime | None:
        """解析日期"""
        if not date_str or pd.isna(date_str):
            return None

        try:
            date_str = str(date_str).strip()
            # 尝试解析各种日期格式
            for fmt in ["%Y-%m-%d", "%Y/%m/%d", "%Y年%m月%d日", "%Y.%m.%d"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[patent_archive_ollama_importer_v2] Exception: {e}")
                    continue
        except Exception as e:

            # 记录异常但不中断流程

            logger.debug(f"[patent_archive_ollama_importer_v2] Exception: {e}")
        return None

    def export_results(self, result: Dict):
        """导出处理结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出完整结果
        export_file = f"patent_import_result_{timestamp}.json"

        # 准备导出数据（去掉原始数据以减少文件大小）
        export_data = result.copy()
        export_data['new_patent_data'] = [
            {k: v for k, v in record.items() if k != 'raw_data'}
            for record in export_data['new_patent_data'][:100]  # 只导出前100条
        ]
        export_data['duplicate_data'] = [
            {k: v for k, v in record.items() if k != 'raw_data'}
            for record in export_data['duplicate_data'][:100]
        ]

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📋 结果已导出到: {export_file}")

        # 导出新专利到Excel
        if result['new_patents'] > 0:
            new_patents_df = pd.DataFrame([
                {
                    '申请号': record.get('application_number', ''),
                    '客户名称': record.get('client_name', ''),
                    '专利名称': record.get('patent_title', ''),
                    '专利类型': record.get('patent_type', ''),
                    '申请日': record.get('filing_date', ''),
                    '代理人': record.get('agent', ''),
                    '法律状态': record.get('legal_status', ''),
                    '档案号': record.get('archive_number', '')
                }
                for record in result['new_patent_data']
            ])

            excel_file = f"新专利数据_{timestamp}.xlsx"
            new_patents_df.to_excel(excel_file, index=False)
            logger.info(f"📊 新专利数据已导出到: {excel_file}")

        # 导出重复数据到Excel
        if result['duplicate_patents'] > 0:
            duplicate_df = pd.DataFrame([
                {
                    '重复原因': record.get('duplicate_type', ''),
                    '申请号': record.get('application_number', ''),
                    '客户名称': record.get('client_name', ''),
                    '专利名称': record.get('patent_title', ''),
                    '原始行号': record.get('row_index', '') + 1
                }
                for record in result['duplicate_data']
            ])

            duplicate_file = f"重复专利数据_{timestamp}.xlsx"
            duplicate_df.to_excel(duplicate_file, index=False)
            logger.info(f"⚠️ 重复数据已导出到: {duplicate_file}")

        return export_file


def main():
    """主函数"""
    excel_path = "/Users/xujian/工作/10_归档文件/专利档案表（2016---) .xlsx"

    print("🚀 使用Ollama大模型的专利档案智能导入工具 v2.0")
    print("=" * 60)

    # 检查文件
    if not Path(excel_path).exists():
        logger.error(f"❌ 文件不存在: {excel_path}")
        return False

    # 创建导入器
    importer = OllamaPatentImporter()

    try:
        # 1. 加载现有数据
        importer.load_existing_data()

        # 2. 处理Excel数据
        result = importer.process_excel_data(excel_path)

        # 3. 保存新数据到数据库
        if result['new_patents'] > 0:
            importer.save_to_database(result['new_patent_data'])
            logger.info(f"✅ 成功导入 {result['new_patents']} 条新专利")
        else:
            logger.info("ℹ️ 没有新的专利需要导入")

        # 4. 导出结果
        importer.export_results(result)

        print("\n✨ 导入完成！")
        print(f"  处理总数: {result['processed_rows']}")
        print(f"  新增专利: {result['new_patents']}")
        print(f"  重复专利: {result['duplicate_patents']}")
        print(f"  新增客户: {result['new_clients']}")

        return True

    except Exception as e:
        logger.error(f"导入失败: {str(e)}")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)