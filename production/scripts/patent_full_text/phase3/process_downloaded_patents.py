#!/usr/bin/env python3
"""
处理已下载的专利PDF
Process Downloaded Patent PDFs

从PDF目录读取专利全文，通过Phase3 Pipeline进行处理
"""

from __future__ import annotations
import logging
import re
import sys
from pathlib import Path

import numpy as np

# 添加当前路径到sys.path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_patent_txt(txt_path: Path) -> dict:
    """解析专利TXT文件，提取结构化信息"""
    content = txt_path.read_text(encoding='utf-8', errors='ignore')

    patent_data = {
        'patent_number': '',
        'title': '',
        'abstract': '',
        'ipc_classification': '',
        'claims': '',
        'invention_content': '',
        'publication_date': '',
        'application_date': '',
        'patent_type': 'invention'
    }

    # 提取专利号（从文件名）
    match = re.search(r'CN(\d+[A-Z])', txt_path.name)
    if match:
        patent_data['patent_number'] = match.group(0)

    # 提取申请号
    app_match = re.search(r'\(21\)\s*申请号\s*([\d.]+)', content)
    if app_match:
        patent_data['application_number'] = app_match.group(1)

    # 提取申请日
    date_match = re.search(r'\(22\)\s*申请日\s*([\d.]+)', content)
    if date_match:
        patent_data['application_date'] = date_match.group(1).replace('.', '-')

    # 提取IPC分类
    ipc_match = re.search(r'\(51\)Int\.Cl\.\s*\n((?:[A-Z]\d+[A-Z]\s*\d+/\d+.*\n)+)', content)
    if ipc_match:
        patent_data['ipc_classification'] = ipc_match.group(1).strip()

    # 提取发明名称
    title_match = re.search(r'\(54\)\s*发明名称\s*\n(.+?)\n', content)
    if title_match:
        patent_data['title'] = title_match.group(1).strip()

    # 提取摘要
    abstract_match = re.search(r'\(57\)\s*摘要\s*\n((?:.+\n)+?)(?=\n权利要求书|CN\s)', content)
    if abstract_match:
        patent_data['abstract'] = abstract_match.group(1).strip()

    # 提取权利要求书
    claims_match = re.search(r'权利要求书.*?\n((?:.+\n)+?)(?=说明书|CN\s)', content, re.DOTALL)
    if claims_match:
        patent_data['claims'] = claims_match.group(1).strip()

    # 提取发明内容/说明书
    invention_match = re.search(r'发明内容.*?\n((?:.+\n)+)', content, re.DOTALL)
    if invention_match:
        patent_data['invention_content'] = invention_match.group(1).strip()[:2000]

    # 如果没有找到说明书，尝试整个内容
    if not patent_data['invention_content']:
        # 从"技术领域"开始提取
        tech_match = re.search(r'技术领域.*?\n((?:.+\n)+)', content, re.DOTALL)
        if tech_match:
            patent_data['invention_content'] = tech_match.group(1).strip()[:2000]

    return patent_data


def main() -> None:
    """主处理流程"""
    print("=" * 70)
    print("处理已下载的专利PDF")
    print("=" * 70)

    # 1. 导入模块
    print("\n📦 1. 导入模块...")

    from pipeline_v2 import PatentFullTextPipelineV2, PipelineInput
    print("   ✅ Pipeline导入成功")

    # 2. 创建模拟模型加载器
    print("\n🔧 2. 创建模型加载器...")

    class MockModel:
        def encode(self, text) -> None:
            return np.random.rand(768).tolist()

    class MockModelLoader:
        def load_model(self, name) -> None:
            return MockModel()

    model_loader = MockModelLoader()
    print("   ✅ 模型加载器已创建")

    # 3. 查找专利文件
    print("\n📁 3. 查找专利文件...")

    patent_dir = Path("/Users/xujian/apps/apps/patents/PDF/王玉荣_便携式电动果树修剪采摘一体机/CN")

    txt_files = list(patent_dir.glob("*.txt"))

    if not txt_files:
        print("   ❌ 未找到专利TXT文件")
        return 1

    print(f"   ✅ 找到 {len(txt_files)} 个专利文件")

    # 4. 创建Pipeline
    print("\n🏗️  4. 创建Pipeline...")

    pipeline = PatentFullTextPipelineV2(
        model_loader=model_loader,
        enable_vectorization=True,
        enable_triple_extraction=True,
        enable_kg_build=False,
        save_qdrant=False,
        save_nebula=False
    )
    print("   ✅ Pipeline已创建")

    # 5. 处理每个专利
    print("\n⚙️  5. 处理专利...")

    all_results = []

    for txt_file in txt_files:
        print(f"\n--- 处理: {txt_file.name} ---")

        # 解析专利数据
        patent_data = parse_patent_txt(txt_file)

        if not patent_data.get('patent_number'):
            print("   ⚠️  跳过: 无法解析专利号")
            continue

        print(f"   专利号: {patent_data['patent_number']}")
        print(f"   标题: {patent_data.get('title', 'N/A')[:50]}...")

        # 创建Pipeline输入
        input_data = PipelineInput(
            patent_number=patent_data['patent_number'],
            title=patent_data.get('title', ''),
            abstract=patent_data.get('abstract', ''),
            ipc_classification=patent_data.get('ipc_classification', ''),
            claims=patent_data.get('claims', ''),
            invention_content=patent_data.get('invention_content', ''),
            publication_date=patent_data.get('publication_date', ''),
            application_date=patent_data.get('application_date', ''),
            ipc_main_class=patent_data.get('ipc_main_class', ''),
            ipc_subclass=patent_data.get('ipc_subclass', ''),
            ipc_full_path=patent_data.get('ipc_full_path', ''),
            patent_type=patent_data.get('patent_type', 'invention')
        )

        # 处理
        result = pipeline.process(input_data)

        all_results.append(result)

        if result.success:
            print("   ✅ 处理成功")
            print(f"   向量: {result.total_vectors}个")
            print(f"   三元组: {result.total_triples}个")
        else:
            print(f"   ❌ 处理失败: {result.error_message}")

    # 6. 汇总结果
    print("\n" + "=" * 70)
    print("处理结果汇总")
    print("=" * 70)

    success_count = sum(1 for r in all_results if r.success)
    total_vectors = sum(r.total_vectors for r in all_results)
    total_triples = sum(r.total_triples for r in all_results)

    print(f"处理专利数: {len(all_results)}")
    print(f"成功: {success_count}")
    print(f"失败: {len(all_results) - success_count}")
    print(f"总向量数: {total_vectors}")
    print(f"总三元组: {total_triples}")

    # 7. 详细结果
    print("\n详细结果:")
    for result in all_results:
        status = "✅" if result.success else "❌"
        print(f"  {status} {result.patent_number}: "
              f"{result.total_vectors}向量, {result.total_triples}三元组")

    print("\n" + "=" * 70)
    print("✅ 处理完成!")
    print("=" * 70)

    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
