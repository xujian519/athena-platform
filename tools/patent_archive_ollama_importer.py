#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Ollama大模型的专利档案表智能导入工具
Intelligent Patent Archive Importer with Ollama AI

1. 使用AI智能分析Excel表格结构
2. 智能识别和提取客户信息
3. 自动去重处理
4. 智能数据清洗和标准化
"""

import json
import pandas as pd
import requests
import hashlib
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import os
import sys
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OllamaPatentImporter:
    """使用Ollama的专利导入器"""

    def __init__(self):
        # Ollama配置
        self.ollama_url = "http://localhost:11434/api"
        self.model_name = "qwen:7b"  # 使用qwen模型
        self.embedding_model = "nomic-embed-text:latest"  # 用于相似度比较

        # 数据库配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_archive",  # 使用专利档案数据库
            "user": "xujian",
            "password": ""
        }

        # 缓存现有数据
        self.existing_patents = set()
        self.existing_patent_names = set()
        self.existing_clients = set()

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

    def get_embedding(self, text: str) -> List[float | None]:
        """获取文本的向量嵌入"""
        try:
            payload = {
                "model": self.embedding_model,
                "prompt": text
            }

            response = requests.post(f"{self.ollama_url}/embeddings", json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                return result.get("embedding", [])
            else:
                logger.warning(f"嵌入生成失败: {response.status_code}")
                return None

        except Exception as e:
            logger.warning(f"获取嵌入出错: {str(e)}")
            return None

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦相似度"""
        if not vec1 or not vec2:
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        if magnitude1 == 0 or magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def load_existing_data(self):
        """加载现有数据库数据"""
        logger.info("🔗 正在加载现有数据...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 加载现有专利信息
            cursor.execute("""
                SELECT patent_number, patent_name
                FROM patents
                WHERE patent_number IS NOT NULL
            """)
            for row in cursor.fetchall():
                self.existing_patents.add(row[0])
                if row[1]:
                    self.existing_patent_names.add(row[1].strip())

            # 加载现有客户
            cursor.execute("""
                SELECT DISTINCT client_name
                FROM patent_clients
                WHERE client_name IS NOT NULL
            """)
            for row in cursor.fetchall():
                self.existing_clients.add(row[0].strip())

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

1. 申请号/专利号列
2. 客户/申请人名称列（通常在公司名称前）
3. 专利名称/发明名称列
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
- 专利名称字段有时实际存储的是客户名称
- 要准确区分客户名称和专利发明名称
- 申请号通常是数字，不会是日期格式"""

            prompt = f"""
请分析以下专利档案Excel样本数据，识别各个列的含义：

{sample_text}

请以JSON格式返回分析结果，包含每个列的作用和数据类型：
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
                # 提取JSON部分
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
                logger.error(f"响应内容: {response[:500]}...")
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
            if '申请号' in col_str:
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

    def extract_client_name_with_ai(self, patent_title: str, fallback_client: str = "") -> str:
        """使用AI提取客户名称"""
        if not patent_title or pd.isna(patent_title):
            return fallback_client

        prompt = f"""
从以下文本中提取客户/申请人名称。规则：
1. 通常是公司名称（包含"公司"、"有限"、"科技"等词）
2. 如果是个人，通常是全名
3. 不要提取专利的技术描述部分

文本：{patent_title}

请只返回客户名称，不要其他解释：
"""

        response = self.query_ollama(prompt,
            "你是一个专业的文本提取专家，专门从专利标题中提取客户名称。")

        client_name = response.strip()

        # 如果AI没有返回合理结果，使用简单规则
        if len(client_name) < 2 or '无法' in client_name or '没有' in client_name:
            # 简单提取规则
            title_str = str(patent_title)
            if '公司' in title_str:
                parts = title_str.split('公司')
                if len(parts) > 1:
                    return parts[0] + '公司'
            if '有限' in title_str:
                parts = title_str.split('有限')
                if len(parts) > 1:
                    return parts[:2] + '有限'
            if '大学' in title_str:
                parts = title_str.split('大学')
                if len(parts) > 1:
                    return parts[0] + '大学'
            return fallback_client

        return client_name

    def extract_patent_title_with_ai(self, patent_title: str) -> str:
        """使用AI提取真实的专利发明名称"""
        if not patent_title or pd.isna(patent_title):
            return ""

        prompt = f"""
从以下文本中提取专利的发明名称（不是客户名称）：
1. 发明名称应该描述技术或产品
2. 不应该包含公司名称
3. 应该简洁明确

文本：{patent_title}

请只返回发明名称，如果无法确定请返回空字符串：
"""

        response = self.query_ollama(prompt,
            "你是一个专利专家，能够准确区分客户名称和专利发明名称。")

        patent_name = response.strip()

        # 如果返回的是客户名称，则说明无法提取发明名称
        if any(word in patent_name for word in ['公司', '有限', '科技', '集团', '企业']):
            return ""

        return patent_name

    def check_similarity_with_ai(self, new_title: str, existing_titles: List[str]) -> Tuple[bool, float]:
        """使用AI检查相似度"""
        if not new_title or not existing_titles:
            return False, 0.0

        # 获取新标题的嵌入
        new_embedding = self.get_embedding(new_title)
        if not new_embedding:
            return False, 0.0

        max_similarity = 0.0
        for existing_title in existing_titles[:10]:  # 只比较前10个
            existing_embedding = self.get_embedding(existing_title)
            if existing_embedding:
                similarity = self.cosine_similarity(new_embedding, existing_embedding)
                max_similarity = max(max_similarity, similarity)

        return max_similarity > 0.8, max_similarity  # 0.8作为相似度阈值

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
                    # 过滤掉日期格式的数据
                    if not app_num.startswith('20') and len(app_num) > 5:
                        app_number = app_num

                # 检查专利号重复
                is_duplicate = False
                duplicate_type = None

                if app_number and app_number in self.existing_patents:
                    is_duplicate = True
                    duplicate_type = "申请号重复"
                else:
                    # 检查专利名称相似度
                    title_col = None
                    for col, mapped in column_mapping.items():
                        if mapped == 'patent_title':
                            title_col = col
                            break

                    if title_col and pd.notna(row[title_col]):
                        patent_title = str(row[title_col]).strip()
                        if patent_title in self.existing_patent_names:
                            is_duplicate = True
                            duplicate_type = "专利名称重复"

                # 提取客户名称
                client_name = ""
                if 'client_name' in column_mapping.values():
                    for col, mapped in column_mapping.items():
                        if mapped == 'client_name' and pd.notna(row[col]):
                            client_name = str(row[col]).strip()
                            break

                # 如果没有明确的客户列，从专利标题中提取
                if not client_name:
                    title_col = None
                    for col, mapped in column_mapping.items():
                        if mapped == 'patent_title':
                            title_col = col
                            break
                    if title_col and pd.notna(row[title_col]):
                        client_name = self.extract_client_name_with_ai(str(row[title_col]))

                # 检查是否为新客户
                if client_name and client_name not in self.existing_clients:
                    new_clients.add(client_name)

                # 提取专利类型
                patent_type = "实用新型"
                if 'patent_type' in column_mapping.values():
                    for col, mapped in column_mapping.items():
                        if mapped == 'patent_type' and pd.notna(row[col]):
                            type_str = str(row[col]).lower()
                            if '发明' in type_str:
                                patent_type = "发明专利"
                            elif '外观' in type_str:
                                patent_type = "外观设计"
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
            clients = {}
            for record in processed_data:
                client_name = record.get('client_name', '').strip()
                if client_name and client_name not in clients:
                    clients[client_name] = {
                        'client_name': client_name,
                        'patent_count': 0,
                        'created_at': datetime.now()
                    }

            # 插入新客户
            for client_name, client_data in clients.items():
                if client_name not in self.existing_clients:
                    cursor.execute("""
                        INSERT INTO patent_clients (client_name, patent_count, created_at)
                        VALUES (%(client_name)s, %(patent_count)s, %(created_at)s)
                    """, client_data)

            # 获取客户ID映射
            cursor.execute("SELECT id, client_name FROM patent_clients")
            client_id_map = {name: id for id, name in cursor.fetchall()}

            # 准备专利数据
            patent_records = []
            for record in processed_data:
                client_name = record.get('client_name', '').strip()
                client_id = client_id_map.get(client_name)

                patent_record = {
                    'patent_number': record.get('application_number'),
                    'patent_title': record.get('patent_title'),
                    'client_id': client_id,
                    'client_name': client_name,
                    'patent_type': record.get('patent_type', '实用新型'),
                    'filing_date': record.get('filing_date'),
                    'agent': record.get('agent'),
                    'legal_status': record.get('legal_status'),
                    'archive_number': record.get('archive_number'),
                    'application_method': record.get('application_method'),
                    'contact_info': record.get('contact'),
                    'source': 'ollama_import',
                    'created_at': datetime.now()
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

            # 更新客户专利计数
            for client_name in clients.keys():
                cursor.execute("""
                    UPDATE patent_clients
                    SET patent_count = (
                        SELECT COUNT(*)
                        FROM patents
                        WHERE client_name = %s
                    )
                    WHERE client_name = %s
                """, (client_name, client_name))

            conn.commit()
            logger.info(f"✅ 成功保存 {len(patent_records)} 条专利记录")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"保存数据失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

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
        if result['new_patent_data'] > 0:
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

        return export_file


def main():
    """主函数"""
    excel_path = "/Users/xujian/工作/10_归档文件/专利档案表（2016---) .xlsx"

    print("🚀 使用Ollama大模型的专利档案智能导入工具")
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