#!/usr/bin/env python3
"""
简化的专利AI分析器
Simplified Patent AI Analyzer

直接查询数据并使用Ollama分析
"""


import psycopg2
import requests


class PatentAIAnalyzerSimple:
    """简化的专利AI分析器"""

    def __init__(self):
        # PostgreSQL配置
        self.db_config = {
            "host": "localhost",
            "port": 5432,
            "database": "patent_archive",
            "user": "xujian",
            "password": ""
        }

        # Ollama配置
        self.ollama_url = "http://127.0.0.1:8765/v1"
        self.model_name = "qwen:7b"

    def query_ollama(self, prompt: str, system_prompt: str = None) -> str:
        """查询Ollama模型"""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload = {
                "model": self.model_name,
                "messages": messages,
                "stream": False
            }

            response = requests.post(f"{self.ollama_url}/chat/completions", json=payload, timeout=60)

            if response.status_code == 200:
                result = response.json()
                return result.get("choices", [{}])[0].get("message", {}).get("content", "")
            else:
                print(f"Ollama请求失败: {response.status_code}")
                return ""

        except Exception as e:
            print(f"查询Ollama出错: {str(e)}")
            return ""

    def analyze_customer_names(self):
        """分析客户名称"""
        print("🤖 使用AI分析专利客户名称...")

        # 连接数据库
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        # 获取客户名称样本
        cursor.execute("""
            SELECT DISTINCT patent_name, COUNT(*) as count
            FROM patents
            WHERE patent_name IS NOT NULL
            AND patent_name != ''
            AND patent_name != 'nan'
            AND (patent_name LIKE '%公司%' OR patent_name LIKE '%学院%' OR patent_name LIKE '%大学%'
                 OR patent_name LIKE '%科技%' OR patent_name LIKE '%有限公司%')
            GROUP BY patent_name
            ORDER BY count DESC
            LIMIT 50
        """)

        customers = cursor.fetchall()
        customer_text = "\n".join([f"{c[1]}x: {c[0]}" for c in customers])

        # AI分析提示
        system_prompt = """你是一个专业的企业名称分析专家。请分析以下专利申请人名称，识别出真正的客户名称。

分析要点：
1. 专利名称字段实际存储的是申请人（客户）名称
2. 识别公司、学校、机构等不同类型的申请人
3. 注意名称变更（如"变更为"）
4. 统一相似名称
5. 识别核心主体名称

输出格式：
1. 每个标准化的客户名称
2. 对应的专利数量
3. 客户类型（公司/学校/机构等）
4. 名称变更情况"""

        prompt = f"""
请分析以下专利申请人名称，识别并整理真正的客户：

{customer_text}

请以清晰的格式输出分析结果，包括：
1. 主要客户列表（按专利数量排序）
2. 客户类型分布
3. 需要合并的相似名称
4. 有名称变更的客户
"""

        response = self.query_ollama(prompt, system_prompt)

        # 保存结果
        with open("ai_customer_analysis.txt", "w", encoding="utf-8") as f:
            f.write("AI客户分析结果\n")
            f.write("="*60 + "\n\n")
            f.write("原始数据：\n")
            f.write(customer_text)
            f.write("\n\nAI分析结果：\n")
            f.write("="*60 + "\n\n")
            f.write(response)

        print("\n✅ AI分析完成！")
        print("结果已保存到：ai_customer_analysis.txt")
        print("\n📋 AI分析结果摘要：")
        print("-" * 60)
        print(response[:1000] + "..." if len(response) > 1000 else response)

        cursor.close()
        conn.close()

    def analyze_structure(self):
        """分析数据结构"""
        print("\n🔍 分析专利数据结构...")

        # 连接数据库
        conn = psycopg2.connect(**self.db_config)
        cursor = conn.cursor()

        # 获取表结构信息
        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'patents'
            AND table_schema = 'public'
            ORDER BY ordinal_position
        """)

        columns_info = cursor.fetchall()

        # 获取样本数据
        cursor.execute("""
            SELECT patent_number, patent_name, patent_type,
                   application_date, legal_status, contact_info
            FROM patents
            LIMIT 10
        """)

        sample_data = cursor.fetchall()

        # 构建分析文本
        structure_text = "\n数据表结构：\n"
        for col in columns_info:
            structure_text += f"- {col[0]} ({col[1]})\n"

        structure_text += "\n样本数据：\n"
        for i, row in enumerate(sample_data):
            structure_text += f"\n记录{i+1}：\n"
            structure_text += f"  专利号: {row[0]}\n"
            structure_text += f"  申请人: {row[1]}\n"
            structure_text += f"  类型: {row[2]}\n"
            structure_text += f"  申请日: {row[3]}\n"
            structure_text += f"  状态: {row[4]}\n"
            structure_text += f"  联系人: {row[5]}\n"

        # AI分析
        system_prompt = """你是一个数据结构分析专家。请分析专利数据库的结构，特别关注：
1. 每个字段的实际含义
2. patent_name字段存储的是申请人名称而不是专利发明名称
3. 识别真正的关系（客户、案源人、代理人等）
4. 数据质量问题
5. 改进建议"""

        prompt = f"""
请分析以下专利数据库结构：

{structure_text}

请特别说明：
1. patent_name字段的实际含义
2. 客户信息存储在哪里
3. 案源人和客户的关系
4. 如何优化数据结构
"""

        response = self.query_ollama(prompt, system_prompt)

        # 保存结果
        with open("ai_structure_analysis.txt", "w", encoding="utf-8") as f:
            f.write("AI数据结构分析\n")
            f.write("="*60 + "\n\n")
            f.write(response)

        print("\n📋 AI结构分析：")
        print("-" * 60)
        print(response[:1000] + "..." if len(response) > 1000 else response)

        cursor.close()
        conn.close()

    def run_analysis(self):
        """运行分析"""
        print("🚀 开始AI专利数据分析")
        print("="*60)

        # 分析数据结构
        self.analyze_structure()

        # 分析客户名称
        self.analyze_customer_names()

        print("\n✅ 分析完成！")
        print("\n生成的文件：")
        print("- ai_structure_analysis.txt - 数据结构分析")
        print("- ai_customer_analysis.txt - 客户分析")


def main():
    """主函数"""
    analyzer = PatentAIAnalyzerSimple()
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
