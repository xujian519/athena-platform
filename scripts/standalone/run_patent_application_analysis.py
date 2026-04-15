#!/usr/bin/env python3
"""
使用小娜专利智能分析系统分析技术交底书的可专利性
"""

import asyncio
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, "/Users/xujian/Athena工作平台")

from core.cognition.xiaona_patent_analyzer import (
    PatentAnalysisRequest,
    XiaonaPatentAnalyzer,
)


def extract_text_from_doc(file_path: str) -> str:
    """从.doc或.docx文件中提取文本"""
    try:
        # 尝试使用python-docx读取docx文件
        try:
            from docx import Document
            doc = Document(file_path)
            paragraphs = []
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append(para.text.strip())
            return "\n".join(paragraphs)
        except Exception:
            # 如果是.doc文件，使用antiword工具提取
            import subprocess
            cmd = ['antiword', file_path]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                text = result.stdout
                # 清理提取的文本
                lines = text.split('\n')
                paragraphs = []
                for line in lines:
                    stripped_line = line.strip()
                    if stripped_line:
                        paragraphs.append(stripped_line)
                return "\n".join(paragraphs)
            else:
                raise Exception(f"antiword command failed with code {result.returncode}") from None
    except Exception as e:
        print(f"❌ 提取文本失败: {e}")
        return ""


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("🚀 使用方法: python3 run_patent_application_analysis.py <文件路径>")
        print("📝 示例: python3 run_patent_application_analysis.py temp_converted.docx")
        return

    file_path = sys.argv[1]

    # 检查文件是否存在
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return

    print("🚀 开始分析技术交底书的可专利性...")

    # 1. 提取文档内容
    print("📄 步骤1: 提取文档内容")
    content = extract_text_from_doc(file_path)
    if not content:
        return

    print(f"✅ 提取成功，共 {len(content)} 字符")

    # 2. 创建分析器实例
    print("🤖 步骤2: 初始化小娜专利智能分析系统")
    analyzer = XiaonaPatentAnalyzer()
    await analyzer.initialize()

    # 3. 准备分析请求
    print("📋 步骤3: 准备分析请求")
    request = PatentAnalysisRequest(
        patent_type="application_analysis",
        technology_field="医疗器械",
        invention_description=content,
        priority="high",
        user_requirements=[
            "评估技术交底书的可专利性",
            "分析技术创新性和创造性",
            "提供申请策略建议",
            "识别潜在风险和改进方向"
        ]
    )

    # 4. 执行分析
    print("🔍 步骤4: 执行专利申请分析")
    try:
        result = await analyzer.analyze_patent(request)

        # 5. 显示分析结果
        print("📊 步骤5: 显示分析结果")
        print("=" * 80)
        print(f"🎯 分析类型: {result.analysis_type}")
        print(f"📄 专利号: {result.patent_number}")
        print(f"🏷️  标题: {result.title}")
        print(f"📝 摘要: {result.abstract}")
        print(f"📋 权利要求: {result.claims}")
        print(f"📈 置信度: {result.confidence_score:.1%}")
        print("=" * 80)

        print("📝 结论:")
        for i, conclusion in enumerate(result.conclusions, 1):
            print(f"  {i}. {conclusion}")

        print("💡 建议:")
        for i, recommendation in enumerate(result.recommendations, 1):
            print(f"  {i}. {recommendation}")

        print("⚠️  风险:")
        for i, risk in enumerate(result.risks, 1):
            print(f"  {i}. {risk}")

        print("🚶 下一步:")
        for i, step in enumerate(result.next_steps, 1):
            print(f"  {i}. {step}")

        print("=" * 80)
        print("✅ 分析完成！")

    except Exception as e:
        print(f"❌ 分析失败: {e}")
        import traceback
        print(f"📄 错误详情:\n{traceback.format_exc()}")


if __name__ == "__main__":
    asyncio.run(main())
