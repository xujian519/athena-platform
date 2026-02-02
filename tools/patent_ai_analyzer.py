#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使用Ollama大模型分析专利数据
Patent Data Analysis with Ollama AI

使用大模型识别和提取专利数据库中的客户信息
"""

import json
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
import time
from datetime import datetime, date
import os
from pathlib import Path

class PatentAIAnalyzer:
    """专利AI分析器"""

    def __init__(self):
        # 检查PostgreSQL路径
        postgres_path = "/opt/homebrew/opt/postgresql@17/bin"
        if postgres_path not in os.environ.get("PATH", ""):
            os.environ["PATH"] = postgres_path + ":" + os.environ.get("PATH", "")

        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_archive",
            "user": "xujian",
            "password": ""
        }

        # Ollama配置
        self.ollama_url = "http://localhost:11434/api"
        self.model_name = "qwen:7b"  # 使用qwen模型

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
                print(f"Ollama请求失败: {response.status_code}")
                return ""

        except Exception as e:
            print(f"查询Ollama出错: {str(e)}")
            return ""

    def get_db_connection(self):
        """获取数据库连接"""
        try:
            conn = psycopg2.connect(
                host=self.db_config["host"],
                port=self.db_config["port"],
                database=self.db_config["database"],
                user=self.db_config["user"]
            )
            return conn
        except Exception as e:
            print(f"❌ 数据库连接失败: {str(e)}")
            return None

    def extract_patent_data_sample(self, limit=50):
        """提取专利数据样本"""
        conn = self.get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("""
                SELECT
                    id,
                    patent_number,
                    patent_name,
                    patent_type,
                    application_date,
                    legal_status,
                    contact_info,
                    sequence_number
                FROM patents
                WHERE patent_name IS NOT NULL AND patent_name != ''
                ORDER BY id
                LIMIT %s
            """, (limit,))

            records = cursor.fetchall()
            return [dict(record) for record in records]

        except Exception as e:
            print(f"提取数据失败: {str(e)}")
            return []
        finally:
            conn.close()

    def analyze_patent_structure_with_ai(self, sample_data):
        """使用AI分析专利数据结构"""
        print("\n🤖 使用AI分析专利数据结构...")

        # 准备样本数据（处理日期序列化）
        def json_serialize(obj):
            if isinstance(obj, datetime.date):
                return obj.isoformat()
            raise TypeError(f'Object of type {obj.__class__.__name__} is not JSON serializable')

        sample_text = json.dumps(sample_data[:10], ensure_ascii=False, indent=2, default=json_serialize)

        system_prompt = """你是一个专利数据分析师。请分析以下专利数据，识别出：
1. 专利申请号
2. 申请人/客户名称（注意：专利名称字段实际存储的是申请人名称）
3. 发明名称（如果有的话）
4. 专利类型
5. 案源人（代理人）
6. 其他重要信息

请特别注意：专利名称字段实际上是申请人名称，不是发明名称。"""

        prompt = f"""
请分析以下专利数据样本，识别各个字段的含义和数据特点：

{sample_text}

请以JSON格式返回分析结果：
{{
    "字段说明": {{
        "patent_number": "字段含义",
        "patent_name": "字段含义（实际是申请人名称）",
        "patent_type": "字段含义",
        "application_date": "字段含义",
        "legal_status": "字段含义",
        "contact_info": "字段含义",
        "sequence_number": "字段含义"
    }},
    "客户名称提取规则": "如何从patent_name字段提取标准化的客户名称",
    "需要处理的问题": ["问题1", "问题2", "问题3"],
    "建议的数据结构改进": ["改进建议1", "改进建议2"]
}}
"""

        response = self.query_ollama(prompt, system_prompt)

        print("\n📋 AI分析结果：")
        print("=" * 60)
        print(response)
        print("=" * 60)

        # 保存分析结果
        with open("patent_ai_analysis.json", "w", encoding="utf-8") as f:
            json.dump({"analysis": response, "sample_data": sample_data}, f, ensure_ascii=False, indent=2)

        return response

    def extract_and_standardize_customers(self):
        """提取并标准化客户名称"""
        print("\n🏢 提取并标准化客户名称...")

        conn = self.get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # 获取所有专利名称
            cursor.execute("""
                SELECT DISTINCT patent_name, COUNT(*) as count
                FROM patents
                WHERE patent_name IS NOT NULL
                AND patent_name != ''
                AND patent_name != 'nan'
                GROUP BY patent_name
                ORDER BY count DESC
            """)

            raw_customers = cursor.fetchall()
            print(f"\n找到 {len(raw_customers)} 个不同的客户名称")

            # 分批处理（每次处理20个）
            batch_size = 20
            for i in range(0, len(raw_customers), batch_size):
                batch = raw_customers[i:i+batch_size]
                print(f"\n处理批次 {i//batch_size + 1}/{(len(raw_customers)-1)//batch_size + 1}")

                # 准备批处理数据
                batch_text = "\n".join([f"{row[1]}x: {row[0]}" for row in batch])

                # 使用AI分析客户名称
                system_prompt = """你是一个企业名称标准化专家。请将专利申请人名称进行标准化处理。

规则：
1. 去除法人类型后缀（有限公司、股份有限公司等）
2. 识别名称变更（如"变更为："）
3. 合并相似名称（如"山东艾迈泰克"和"山东艾迈泰克机械科技有限公司"）
4. 保留核心名称以便识别
5. 统一地域标识

输出格式：每个原始名称对应一个标准化名称"""

                prompt = f"""
请标准化以下专利申请人名称：

{batch_text}

请以JSON格式返回结果：
{{
    "标准化结果": [
        {{
            "原始名称": "原始名称1",
            "标准化名称": "标准化名称1",
            "核心名称": "核心名称1",
            "地域": "地域1",
            "法人类型": "有限公司/股份有限公司/学院/大学等",
            "是否为名称变更": true/false
        }},
        ...
    ]
}}
"""

                response = self.query_ollama(prompt, system_prompt)

                # 保存批处理结果
                with open(f"customer_batch_{i//batch_size + 1}.json", "w", encoding="utf-8") as f:
                    f.write(response)

                print(f"批次 {i//batch_size + 1} 处理完成")

                # 避免请求过快
                time.sleep(2)

            return True

        except Exception as e:
            print(f"处理失败: {str(e)}")
            return False
        finally:
            conn.close()

    def create_customer_table(self):
        """创建客户表"""
        sql_statements = [
            # 创建标准客户表
            """
            CREATE TABLE IF NOT EXISTS patent_customers_standard (
                id SERIAL PRIMARY KEY,
                customer_name VARCHAR(500) NOT NULL,  -- 原始名称
                standard_name VARCHAR(200) NOT NULL,  -- 标准化名称
                core_name VARCHAR(100),               -- 核心名称
                region VARCHAR(50),                   -- 地域
                entity_type VARCHAR(50),              -- 法人类型
                is_name_change BOOLEAN DEFAULT FALSE, -- 是否为名称变更
                patent_count INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(customer_name)
            );
            """,

            # 创建索引
            "CREATE INDEX IF NOT EXISTS idx_customers_standard_name ON patent_customers_standard(standard_name);",
            "CREATE INDEX IF NOT EXISTS idx_customers_core_name ON patent_customers_standard(core_name);",
            "CREATE INDEX IF NOT EXISTS idx_customers_region ON patent_customers_standard(region);",
        ]

        conn = self.get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            for sql in sql_statements:
                cursor.execute(sql)
            conn.commit()
            print("✅ 客户表创建成功！")
            return True
        except Exception as e:
            print(f"❌ 创建表失败: {str(e)}")
            conn.rollback()
            return False
        finally:
            conn.close()

    def analyze_agent_performance(self):
        """分析案源人业绩"""
        print("\n📊 分析案源人业绩...")

        conn = self.get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor(cursor_factory=RealDictCursor)

            # 获取案源人数据
            cursor.execute("""
                SELECT
                    a.client_name as 案源人,
                    a.patent_count as 总专利数,
                    COUNT(p.id) as 实际专利数,
                    COUNT(CASE WHEN p.legal_status = '已拿证' THEN 1 END) as 已授权数,
                    COUNT(CASE WHEN p.legal_status LIKE '%驳回%' THEN 1 END) as 驳回数,
                    COUNT(CASE WHEN p.patent_type = '发明' THEN 1 END) as 发明专利数,
                    COUNT(CASE WHEN p.patent_type = '实用新型' THEN 1 END) as 实用新型数,
                    COUNT(CASE WHEN p.patent_type LIKE '%外观%' THEN 1 END) as 外观数,
                    MIN(p.application_date) as 最早申请日,
                    MAX(p.application_date) as 最新申请日
                FROM patent_agents a
                LEFT JOIN patents p ON a.id = p.agent_id
                GROUP BY a.id, a.client_name, a.patent_count
                ORDER BY 实际专利数 DESC
            """)

            agent_data = cursor.fetchall()

            print("\n案源人业绩报告：")
            print("-" * 100)
            print(f"{'案源人':<15} {'总专利':<8} {'实际专利':<10} {'已授权':<8} {'驳回':<8} {'发明':<8} {'实用新型':<10} {'外观':<8}")
            print("-" * 100)

            for row in agent_data:
                print(f"{row['案源人']:<15} {row['总专利数']:<8} {row['实际专利数']:<10} "
                      f"{row['已授权数']:<8} {row['驳回数']:<8} {row['发明专利数']:<8} "
                      f"{row['实用新型数']:<10} {row['外观数']:<8}")

            # 使用AI分析案源人业绩
            agent_json = json.dumps([dict(row) for row in agent_data], ensure_ascii=False, indent=2)

            system_prompt = """你是一个专利业务分析专家。请分析以下案源人的业绩数据，
            识别出业绩优秀的案源人、业绩特点，并提出改进建议。"""

            prompt = f"""
请分析以下案源人业绩数据：

{agent_json}

请从以下角度进行分析：
1. 业绩排名（专利数量、授权率）
2. 专利类型分布（发明/实用新型/外观）
3. 成功率分析
4. 案源人特长领域
5. 改进建议
"""

            ai_analysis = self.query_ollama(prompt, system_prompt)

            print("\n🤖 AI业绩分析：")
            print("=" * 60)
            print(ai_analysis)
            print("=" * 60)

            # 保存分析结果
            with open("agent_performance_analysis.json", "w", encoding="utf-8") as f:
                json.dump({
                    "raw_data": [dict(row) for row in agent_data],
                    "ai_analysis": ai_analysis,
                    "analysis_time": datetime.now().isoformat()
                }, f, ensure_ascii=False, indent=2)

            return True

        except Exception as e:
            print(f"分析失败: {str(e)}")
            return False
        finally:
            conn.close()

    def run_analysis(self):
        """运行完整分析"""
        print("🚀 开始使用AI分析专利数据库")
        print("=" * 60)

        # 1. 提取样本数据
        print("\n1. 提取专利数据样本...")
        sample_data = self.extract_patent_data_sample(50)

        # 2. AI分析数据结构
        self.analyze_patent_structure_with_ai(sample_data)

        # 3. 创建客户表
        print("\n2. 创建标准化客户表...")
        self.create_customer_table()

        # 4. 提取并标准化客户名称
        self.extract_and_standardize_customers()

        # 5. 分析案源人业绩
        self.analyze_agent_performance()

        print("\n✅ AI分析完成！")
        print("生成的文件：")
        print("- patent_ai_analysis.json - AI数据结构分析")
        print("- customer_batch_*.json - 客户名称标准化结果")
        print("- agent_performance_analysis.json - 案源人业绩分析")


def main():
    """主函数"""
    analyzer = PatentAIAnalyzer()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()