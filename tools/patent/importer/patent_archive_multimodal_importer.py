#!/usr/bin/env python3
"""
多模态+Dolphin+Ollama专利档案导入工具
结合多模态文件系统、Dolphin解析和Ollama大模型进行智能导入
"""

import json
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
import psycopg2
import requests
from psycopg2.extras import execute_values

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MultimodalPatentImporter:
    """多模态专利导入器"""

    def __init__(self):
        # 服务配置
        self.multimodal_url = "http://localhost:8001"
        self.dolphin_url = "http://localhost:8013"
        self.ollama_url = "http://127.0.0.1:8765/v1"
        self.ollama_model = "qwen:7b"

        # 数据库配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "athena_business",
            "user": "postgres",
            "password": "xj781102"
        }

        # 认证信息
        self.multimodal_token = None
        self.dolphin_session = None

        # 缓存数据
        self.existing_patents = set()
        self.existing_clients = set()
        self.client_map = {}

    async def initialize(self):
        """初始化服务连接"""
        logger.info("🔧 初始化多模态服务连接...")

        # 1. 连接多模态文件系统
        await self._connect_multimodal()

        # 2. 连接Dolphin解析服务
        await self._connect_dolphin()

        # 3. 加载数据库现有数据
        self._load_existing_data()

        logger.info("✅ 所有服务初始化完成")

    async def _connect_multimodal(self):
        """连接多模态文件系统"""
        try:
            # 认证获取token
            auth_response = requests.post(f"{self.multimodal_url}/auth/login", data={
                "username": "athena_platform",
                "password": "athena_integration_2024"
            }, timeout=10)

            if auth_response.status_code == 200:
                self.multimodal_token = auth_response.json()["token"]
                logger.info("✅ 多模态文件系统连接成功")
            else:
                logger.warning("⚠️ 多模态文件系统连接失败，将使用本地解析")
                self.multimodal_token = None

        except Exception as e:
            logger.warning(f"⚠️ 多模态文件系统不可用: {str(e)}")
            self.multimodal_token = None

    async def _connect_dolphin(self):
        """连接Dolphin解析服务"""
        try:
            # 检查Dolphin服务状态
            health_response = requests.get(f"{self.dolphin_url}/health", timeout=5)
            if health_response.status_code == 200:
                logger.info("✅ Dolphin解析服务连接成功")
                self.dolphin_available = True
            else:
                self.dolphin_available = False
        except Exception as e:
            # 记录异常但不中断流程
            logger.debug(f"[patent_archive_multimodal_importer] Exception: {e}")
            logger.warning("⚠️ Dolphin解析服务不可用，将使用基础解析")
            self.dolphin_available = False

    def _load_existing_data(self):
        """加载现有数据库数据"""
        logger.info("🔗 加载现有数据库数据...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 加载现有客户
            cursor.execute("SELECT id, name FROM clients WHERE name IS NOT NULL")
            for row in cursor.fetchall():
                name = row[1].strip()
                self.existing_clients.add(name)
                self.client_map[name] = row[0]

            logger.info(f"  现有客户: {len(self.existing_clients)}")

        except Exception as e:
            logger.error(f"加载数据失败: {str(e)}")
        finally:
            if conn:
                conn.close()

    async def upload_and_analyze_excel(self, excel_path: str) -> dict:
        """上传Excel到多模态系统并分析"""
        logger.info("📤 上传Excel到多模态系统...")

        try:
            if not self.multimodal_token:
                return await self._local_excel_analysis(excel_path)

            # 上传文件
            with open(excel_path, 'rb') as f:
                files = {'file': (Path(excel_path).name, f, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')}
                data = {
                    'token': self.multimodal_token,
                    'description': '专利档案表',
                    'doc_type': 'patent_archive'
                }

                upload_response = requests.post(
                    f"{self.multimodal_url}/upload",
                    files=files,
                    data=data,
                    timeout=30
                )

            if upload_response.status_code == 200:
                file_info = upload_response.json()["file_info"]
                file_id = file_info["file_id"]
                logger.info(f"✅ 文件上传成功，ID: {file_id}")

                # 获取文件分析结果
                analysis_result = await self._get_file_analysis(file_id)
                return analysis_result
            else:
                logger.warning("⚠️ 多模态上传失败，使用本地分析")
                return await self._local_excel_analysis(excel_path)

        except Exception as e:
            logger.warning(f"⚠️ 多模态处理失败: {str(e)}，使用本地分析")
            return await self._local_excel_analysis(excel_path)

    async def _get_file_analysis(self, file_id: str) -> dict:
        """获取多模态系统的文件分析结果"""
        try:
            headers = {"Authorization": f"Bearer {self.multimodal_token}"}

            # 获取文件信息
            info_response = requests.get(
                f"{self.multimodal_url}/files/{file_id}",
                headers=headers,
                timeout=10
            )

            if info_response.status_code == 200:
                file_info = info_response.json()

                # 获取元数据
                metadata = file_info.get("metadata", {})

                analysis_result = {
                    "file_id": file_id,
                    "file_info": file_info,
                    "analysis_method": "multimodal",
                    "structure_detected": metadata.get("structure_detected", False),
                    "columns": metadata.get("columns", []),
                    "data_summary": metadata.get("data_summary", {}),
                    "processing_time": datetime.now().isoformat()
                }

                logger.info("✅ 多模态分析完成")
                return analysis_result

        except Exception as e:
            logger.warning(f"⚠️ 获取分析结果失败: {str(e)}")

        return None

    async def _local_excel_analysis(self, excel_path: str) -> dict:
        """本地Excel分析（备用方案）"""
        logger.info("📊 使用本地方式分析Excel...")

        try:
            # 读取Excel
            df = pd.read_excel(excel_path)

            # 分析结构
            columns = df.columns.tolist()
            sample_data = df.head(3).to_dict('records')

            # 使用Ollama分析数据结构
            structure_analysis = await self._analyze_structure_with_ollama(columns, sample_data)

            analysis_result = {
                "excel_path": excel_path,
                "total_rows": len(df),
                "total_columns": len(columns),
                "columns": columns,
                "sample_data": sample_data,
                "structure_analysis": structure_analysis,
                "analysis_method": "local_ollama",
                "processing_time": datetime.now().isoformat()
            }

            logger.info("✅ 本地分析完成")
            return analysis_result

        except Exception as e:
            logger.error(f"❌ 本地分析失败: {str(e)}")
            return None

    async def _analyze_structure_with_ollama(self, columns: list, sample_data: list[dict]) -> dict:
        """使用Ollama分析Excel结构"""
        try:
            columns_text = "\n".join([f"{i+1}. {col}" for i, col in enumerate(columns)])
            sample_text = json.dumps(sample_data[:2], ensure_ascii=False, indent=2)

            prompt = f"""
作为专利数据专家，请分析以下Excel表格结构：

列名：
{columns_text}

示例数据：
{sample_text}

请识别每个列的用途，并以JSON格式返回映射关系：
{{
    "column_mapping": {{
        "档案号": "archive_number",
        "申请号": "application_number",
        "专利名称": "patent_title",
        "案源人": "client_name",
        "代理人": "agent",
        "类型": "patent_type",
        "申请日": "filing_date",
        "法律状态": "legal_status"
    }},
    "data_insights": {{
        "total_records": "总记录数",
        "data_quality": "数据质量评估",
        "special_notes": "特殊说明"
    }}
}}

注意：
1. 案源人通常是客户名称
2. 专利名称可能是客户名称或真实的专利标题
3. 只返回JSON格式
"""

            payload = {
                "model": self.ollama_model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            }

            response = requests.post(f"{self.ollama_url}/chat/completions", json=payload, timeout=30)

            if response.status_code == 200:
                result = response.json()
                ai_response = result.get("choices", [{}])[0].get("message", {}).get("content", "")

                # 解析JSON
                if "```json" in ai_response:
                    json_part = ai_response.split("```json")[1].split("```")[0].strip()
                elif "{" in ai_response and "}" in ai_response:
                    start = ai_response.find("{")
                    end = ai_response.rfind("}") + 1
                    json_part = ai_response[start:end]
                else:
                    json_part = ai_response.strip()

                try:
                    analysis = json.loads(json_part)
                    logger.info("✅ Ollama结构分析成功")
                    return analysis
                except json.JSONDecodeError:
                    logger.warning("⚠️ Ollama响应解析失败，使用默认映射")
                    return self._get_default_mapping(columns)

            else:
                logger.warning("⚠️ Ollama请求失败，使用默认映射")
                return self._get_default_mapping(columns)

        except Exception as e:
            logger.warning(f"⚠️ Ollama分析失败: {str(e)}")
            return self._get_default_mapping(columns)

    def _get_default_mapping(self, columns: list) -> dict:
        """获取默认列映射"""
        mapping = {}
        for col in columns:
            col_str = str(col).strip().lower()
            if '申请号' in col_str and not col_str.startswith('专利'):
                mapping[col] = 'application_number'
            elif '专利名称' in col_str:
                mapping[col] = 'patent_title'
            elif '案源人' in col_str or '客户' in col_str:
                mapping[col] = 'client_name'
            elif '代理人' in col_str:
                mapping[col] = 'agent'
            elif '类型' in col_str:
                mapping[col] = 'patent_type'
            elif '申请日' in col_str:
                mapping[col] = 'filing_date'
            elif '法律状态' in col_str:
                mapping[col] = 'legal_status'
            elif '档案号' in col_str:
                mapping[col] = 'archive_number'

        return {
            "column_mapping": mapping,
            "data_insights": {
                "total_records": len(columns),
                "data_quality": "待评估",
                "special_notes": "使用默认映射"
            }
        }

    async def process_patent_data(self, excel_path: str, analysis_result: dict) -> dict:
        """处理专利数据"""
        logger.info("🔄 开始处理专利数据...")

        # 读取Excel
        df = pd.read_excel(excel_path)
        total_rows = len(df)

        # 获取列映射
        if "structure_analysis" in analysis_result:
            column_mapping = analysis_result["structure_analysis"].get("column_mapping", {})
        else:
            column_mapping = analysis_result.get("column_mapping", {})

        logger.info(f"  使用列映射: {column_mapping}")

        # 处理数据
        processed_data = []
        new_clients = set()

        # 获取列引用
        col_refs = {}
        for col, mapped in column_mapping.items():
            col_refs[mapped] = col

        for idx, row in df.iterrows():
            try:
                # 提取申请号
                app_number = None
                if 'application_number' in col_refs and pd.notna(row[col_refs['application_number']]):
                    app_num = str(row[col_refs['application_number']]).strip()
                    # 过滤掉日期格式的数据
                    if not (app_num.startswith('20') and len(app_num) in [8, 10] and app_num.replace('-', '').isdigit()):
                        app_number = app_num

                # 提取客户名称
                client_name = ""
                if 'client_name' in col_refs and pd.notna(row[col_refs['client_name']]):
                    client_name = str(row[col_refs['client_name']]).strip()

                # 如果没有客户名，尝试从专利标题提取
                if not client_name and 'patent_title' in col_refs:
                    patent_title = str(row[col_refs['patent_title']])
                    client_name = self._extract_client_name(patent_title)

                # 检查新客户
                if client_name and client_name not in self.existing_clients:
                    new_clients.add(client_name)

                # 提取专利类型
                patent_type = "UTILITY_MODEL"
                if 'patent_type' in col_refs and pd.notna(row[col_refs['patent_type']]):
                    type_str = str(row[col_refs['patent_type']]).lower()
                    if '发明' in type_str:
                        patent_type = "INVENTION"
                    elif '外观' in type_str:
                        patent_type = "DESIGN"

                # 提取专利标题
                patent_title = ""
                if 'patent_title' in col_refs and pd.notna(row[col_refs['patent_title']]):
                    patent_title = self._extract_patent_title(
                        str(row[col_refs['patent_title']]),
                        client_name
                    )

                # 构建记录
                record = {
                    "row_index": idx,
                    "application_number": app_number,
                    "client_name": client_name,
                    "patent_title": patent_title or f"专利-{app_number or '未知'}",
                    "patent_type": patent_type,
                    "filing_date": str(row[col_refs['filing_date']]) if 'filing_date' in col_refs and pd.notna(row[col_refs['filing_date']]) else None,
                    "agent": str(row[col_refs['agent']]) if 'agent' in col_refs and pd.notna(row[col_refs['agent']]) else "",
                    "legal_status": str(row[col_refs['legal_status']]) if 'legal_status' in col_refs and pd.notna(row[col_refs['legal_status']]) else "",
                    "archive_number": str(row[col_refs['archive_number']]) if 'archive_number' in col_refs and pd.notna(row[col_refs['archive_number']]) else "",
                    "new_client": client_name in new_clients if client_name else False
                }

                processed_data.append(record)

            except Exception as e:
                logger.warning(f"处理第{idx+1}行出错: {str(e)}")
                continue

        result = {
            "excel_path": excel_path,
            "analysis": analysis_result,
            "total_rows": total_rows,
            "processed_rows": len(processed_data),
            "new_patents": len(processed_data),
            "new_clients": len(new_clients),
            "processed_data": processed_data,
            "processing_time": datetime.now().isoformat()
        }

        logger.info("\n📈 处理结果:")
        logger.info(f"  新专利: {result['new_patents']}")
        logger.info(f"  新客户: {result['new_clients']}")

        return result

    def _extract_client_name(self, text: str) -> str:
        """提取客户名称"""
        text = str(text).strip()

        # 简单规则提取
        if '公司' in text:
            parts = text.split('公司')
            if len(parts) > 1:
                return parts[0] + '公司'
        if '有限' in text:
            parts = text.split('有限')
            if len(parts) > 1:
                return parts[:2] + '有限'
        if '大学' in text:
            parts = text.split('大学')
            if len(parts) > 1:
                return parts[0] + '大学'

        return text

    def _extract_patent_title(self, title: str, client_name: str) -> str:
        """提取专利发明名称"""
        if not client_name:
            return title

        # 如果标题包含客户名，说明可能是客户名称
        if client_name in title:
            return ""  # 无法分离

        return title

    async def save_to_database(self, processed_data: list[dict]):
        """保存到数据库"""
        logger.info("💾 保存数据到数据库...")

        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()

            # 准备客户数据
            clients_to_add = {}
            client_code_counter = 1001

            # 获取现有最大客户代码
            cursor.execute("SELECT client_code FROM clients WHERE client_code LIKE 'C%' ORDER BY client_code DESC LIMIT 1")
            result = cursor.fetchone()
            if result:
                try:
                    existing_num = int(result[0][1:])
                    client_code_counter = existing_num + 1
                except Exception as e:
                    # 记录异常但不中断流程
                    logger.debug(f"[patent_archive_multimodal_importer] Exception: {e}")

            for record in processed_data:
                client_name = record.get('client_name', '').strip()
                if client_name and client_name not in self.existing_clients and client_name not in clients_to_add:
                    clients_to_add[client_name] = {
                        'id': str(uuid.uuid4()),
                        'name': client_name,
                        'client_code': f"C{client_code_counter:04d}",
                        'client_type': 'COMPANY' if '公司' in client_name else 'INDIVIDUAL',
                        'created_at': datetime.now(),
                        'updated_at': datetime.now(),
                        'tenant_id': 'baochen-main',
                        'source': 'multimodal_import'
                    }
                    client_code_counter += 1

            # 插入新客户
            for client_name, client_data in clients_to_add.items():
                cursor.execute("""
                    INSERT INTO clients (id, name, client_code, client_type, created_at, updated_at, tenant_id, source)
                    VALUES (%(id)s, %(name)s, %(client_code)s, %(client_type)s, %(created_at)s, %(updated_at)s, %(tenant_id)s, %(source)s)
                """, client_data)
                self.client_map[client_name] = client_data['id']

            conn.commit()

            # 准备专利数据
            patent_records = []
            for record in processed_data:
                client_name = record.get('client_name', '').strip()
                self.client_map.get(client_name)

                patent_record = {
                    'patent_id': str(uuid.uuid4()),
                    'application_number': record.get('application_number'),
                    'title': record.get('patent_title'),
                    'applicant': client_name,
                    'inventor': client_name,
                    'legal_status': record.get('legal_status', 'PENDING'),
                    'metadata': json.dumps({
                        'source': 'multimodal_dolphin_ollama',
                        'client_name': client_name,
                        'agent': record.get('agent', ''),
                        'archive_number': record.get('archive_number', ''),
                        'import_method': '多模态+Ollama',
                        'import_time': datetime.now().isoformat()
                    }, ensure_ascii=False),
                    'created_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'created_by': 'multimodal_importer'
                }
                patent_records.append(patent_record)

            # 批量插入专利
            if patent_records:
                columns = patent_records[0].keys()
                values = [[record[col] for col in columns] for record in patent_records]

                insert_query = f"""
                    INSERT INTO patents ({', '.join(columns)})
                    VALUES %s
                """

                execute_values(cursor, insert_query, values)

            conn.commit()
            logger.info(f"✅ 成功保存 {len(patent_records)} 条专利记录")

        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"保存失败: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()

    async def export_results(self, result: dict):
        """导出结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # 导出JSON
        export_file = f"patent_multimodal_import_result_{timestamp}.json"

        export_data = result.copy()
        export_data['processed_data'] = export_data['processed_data'][:100]  # 限制大小

        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)

        logger.info(f"📋 结果已导出到: {export_file}")

        # 导出Excel
        if result['new_patents'] > 0:
            df = pd.DataFrame([
                {
                    '申请号': record.get('application_number', ''),
                    '客户名称': record.get('client_name', ''),
                    '专利名称': record.get('patent_title', ''),
                    '专利类型': record.get('patent_type', ''),
                    '申请日': record.get('filing_date', ''),
                    '代理人': record.get('agent', ''),
                    '法律状态': record.get('legal_status', ''),
                    '新客户': '是' if record.get('new_client') else '否'
                }
                for record in result['processed_data']
            ])

            excel_file = f"多模态导入数据_{timestamp}.xlsx"
            df.to_excel(excel_file, index=False)
            logger.info(f"📊 数据已导出到: {excel_file}")

        return export_file


async def main():
    """主函数"""
    excel_path = "/Users/xujian/工作/10_归档文件/专利档案表（2016---) .xlsx"

    print("🚀 多模态+Dolphin+Ollama专利档案导入工具")
    print("=" * 60)

    # 检查文件
    if not Path(excel_path).exists():
        logger.error(f"❌ 文件不存在: {excel_path}")
        return False

    # 创建导入器
    importer = MultimodalPatentImporter()

    try:
        # 1. 初始化
        await importer.initialize()

        # 2. 上传并分析Excel
        analysis_result = await importer.upload_and_analyze_excel(excel_path)

        if not analysis_result:
            logger.error("❌ 文件分析失败")
            return False

        # 3. 处理数据
        process_result = await importer.process_patent_data(excel_path, analysis_result)

        # 4. 保存到数据库
        if process_result['new_patents'] > 0:
            await importer.save_to_database(process_result['processed_data'])
            logger.info(f"✅ 成功导入 {process_result['new_patents']} 条新专利")
        else:
            logger.info("ℹ️ 没有新的专利需要导入")

        # 5. 导出结果
        await importer.export_results(process_result)

        print("\n✨ 导入完成！")
        print(f"  处理总数: {process_result['processed_rows']}")
        print(f"  新增专利: {process_result['new_patents']}")
        print(f"  新增客户: {process_result['new_clients']}")
        print(f"  分析方法: {analysis_result.get('analysis_method', '未知')}")

        return True

    except Exception as e:
        logger.error(f"❌ 导入失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
