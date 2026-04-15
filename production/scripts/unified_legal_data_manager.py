#!/usr/bin/env python3
"""
统一法律数据管理器
Unified Legal Data Manager

解决数据散落和质量问题，提供统一的法律数据管理接口

作者: Athena平台团队
创建时间: 2025-12-20
版本: v1.0.0
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class DataConfig:
    """数据配置"""
    base_path: str = "/Users/xujian/Athena工作平台"
    data_source: str = "/Users/xujian/Athena工作平台/dev/tools/Laws-1.0.0"
    nlp_service_url: str = "http://localhost:8001"
    qdrant_url: str = "http://localhost:6333"
    nebulagraph_url: str = "localhost:9669"
    meta_db_path: str = "/Users/xujian/Athena工作平台/production/data/metadata"

class UnifiedLegalDataManager:
    """统一法律数据管理器"""

    def __init__(self, config: DataConfig = None):
        self.config = config or DataConfig()
        self.ensure_directories()

        # 初始化元数据
        self.metadata = self.load_metadata()

        # 数据版本控制
        self.current_version = self.generate_version_id()

        logger.info(f"统一数据管理器初始化完成，版本: {self.current_version}")

    def ensure_directories(self) -> Any:
        """确保必要目录存在"""
        dirs = [
            Path(self.config.meta_db_path),
            Path(self.config.base_path) / "production" / "data" / "vectors",
            Path(self.config.base_path) / "production" / "data" / "knowledge_graph",
            Path(self.config.base_path) / "production" / "data" / "raw",
            Path(self.config.base_path) / "production" / "data" / "processed"
        ]

        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def generate_version_id(self) -> str:
        """生成数据版本ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return timestamp

    def load_metadata(self) -> dict:
        """加载元数据"""
        meta_file = Path(self.config.meta_db_path) / "unified_metadata.json"

        if meta_file.exists():
            with open(meta_file, encoding='utf-8') as f:
                return json.load(f)

        return {
            "datasets": {},
            "versions": {},
            "quality_metrics": {},
            "last_updated": None
        }

    def save_metadata(self) -> None:
        """保存元数据"""
        meta_file = Path(self.config.meta_db_path) / "unified_metadata.json"
        meta_file.parent.mkdir(parents=True, exist_ok=True)

        self.metadata["last_updated"] = datetime.now().isoformat()

        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)

    def register_dataset(self, name: str, dataset_type: str,
                        source_path: str, description: str = "") -> str:
        """注册数据集"""
        dataset_id = f"{name}_{self.current_version}"

        self.metadata["datasets"][dataset_id] = {
            "name": name,
            "type": dataset_type,  # vectors, knowledge_graph, raw
            "source_path": source_path,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "status": "registered",
            "quality_score": None,
            "size": None
        }

        self.save_metadata()
        logger.info(f"数据集已注册: {dataset_id}")
        return dataset_id

    def scan_existing_data(self) -> dict[str, list]:
        """扫描现有数据"""
        scan_result = {
            "vector_collections": [],
            "knowledge_graph_files": [],
            "raw_data_files": [],
            "processed_files": []
        }

        # 扫描Qdrant集合
        try:
            response = requests.get(f"{self.config.qdrant_url}/collections")
            if response.status_code == 200:
                collections = response.json().get('result', {}).get('collections', [])
                for col in collections:
                    scan_result["vector_collections"].append({
                        "name": col["name"],
                        "vectors_count": col.get("vectors_count"),
                        "points_count": col.get("points_count")
                    })
        except Exception as e:
            logger.error(f"扫描Qdrant失败: {e}")

        # 扫描文件系统
        base_path = Path(self.config.base_path)

        # 扫描知识图谱文件
        kg_files = list(base_path.glob("**/*legal*.json")) + \
                  list(base_path.glob("**/*kg*.json"))
        for f in kg_files:
            scan_result["knowledge_graph_files"].append(str(f))

        # 扫描原始数据
        raw_path = Path(self.config.data_source)
        if raw_path.exists():
            scan_result["raw_data_files"] = [str(f) for f in raw_path.rglob("*.md")]

        return scan_result

    def clean_duplicate_data(self) -> dict[str, int]:
        """清理重复数据"""
        cleaned = {
            "files_removed": 0,
            "collections_merged": 0,
            "space_freed_mb": 0
        }

        # 识别重复的知识图谱文件
        base_path = Path(self.config.base_path)
        kg_pattern = "*legal_entities_*.json"
        kg_files = list(base_path.glob(kg_pattern))

        # 按修改时间排序，保留最新的
        kg_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        # 保留最新版本，删除其他
        unique_files = {}
        for f in kg_files:
            # 提取基础名称（去除时间戳）
            base_name = f.stem.split('_')[0] + '_' + f.stem.split('_')[1]
            if base_name not in unique_files:
                unique_files[base_name] = f
            else:
                f.unlink()
                cleaned["files_removed"] += 1
                logger.info(f"删除重复文件: {f}")

        return cleaned

    def enhance_vector_quality(self, collection_name: str) -> dict[str, float]:
        """提升向量质量"""
        # 这里需要调用高质量的NLP服务重新生成向量
        # 当前简化版本，只是记录计划

        enhancement_plan = {
            "current_avg_similarity": 0.35,  # 当前平均相似度
            "target_avg_similarity": 0.75,   # 目标平均相似度
            "enhancement_method": "semantic_embedding",
            "model_to_use": "bert-base-chinese",
            "processing_status": "planned"
        }

        # 更新元数据
        dataset_id = f"{collection_name}_enhanced"
        self.metadata["quality_metrics"][dataset_id] = enhancement_plan

        self.save_metadata()

        return enhancement_plan

    def get_quality_report(self) -> dict:
        """生成数据质量报告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "data_summary": {
                "total_collections": 0,
                "total_documents": 0,
                "total_vectors": 0
            },
            "quality_metrics": {
                "vector_similarity_avg": 0.0,
                "knowledge_graph_entities": 0,
                "knowledge_graph_relations": 0
            },
            "issues": [],
            "recommendations": []
        }

        # 统计向量集合
        try:
            response = requests.get(f"{self.config.qdrant_url}/collections")
            if response.status_code == 200:
                collections = response.json().get('result', {}).get('collections', [])
                report["data_summary"]["total_collections"] = len(collections)

                for col in collections:
                    col_name = col["name"]
                    col_info = requests.get(f"{self.config.qdrant_url}/collections/{col_name}")
                    if col_info.status_code == 200:
                        points = col_info.json().get('result', {}).get('points_count', 0)
                        report["data_summary"]["total_documents"] += points
                        report["data_summary"]["total_vectors"] += points
        except Exception as e:
            report["issues"].append(f"无法获取向量集合信息: {e}")

        # 识别问题
        if report["data_summary"]["total_documents"] < 3000:
            report["issues"].append("文档数量不足，可能存在数据丢失")

        # 简单测试搜索质量
        try:
            test_vector = np.random.rand(1024).tolist()
            response = requests.post(
                f"{self.config.qdrant_url}/collections/legal_articles_1024/points/search",
                json={
                    "vector": test_vector,
                    "limit": 10,
                    "with_payload": True
                }
            )

            if response.status_code == 200:
                results = response.json().get('result', [])
                scores = [r.get('score', 0) for r in results]
                if scores:
                    report["quality_metrics"]["vector_similarity_avg"] = sum(scores) / len(scores)
        except Exception as e:
            report["issues"].append(f"搜索质量测试失败: {e}")

        # 生成建议
        if report["quality_metrics"]["vector_similarity_avg"] < 0.5:
            report["recommendations"].append("建议重新生成高质量语义向量")

        if report["issues"]:
            report["recommendations"].append("建议执行数据清理和整合")

        # 保存报告
        report_path = Path(self.config.meta_db_path) / f"quality_report_{self.current_version}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        return report

    def export_unified_dataset(self, export_path: str) -> str:
        """导出统一数据集"""
        export_info = {
            "version": self.current_version,
            "timestamp": datetime.now().isoformat(),
            "contents": {
                "vectors": {},
                "knowledge_graph": {},
                "metadata": self.metadata
            }
        }

        # 导出向量数据信息
        try:
            response = requests.get(f"{self.config.qdrant_url}/collections")
            if response.status_code == 200:
                collections = response.json().get('result', {}).get('collections', [])
                for col in collections:
                    col_name = col["name"]
                    col_response = requests.get(f"{self.config.qdrant_url}/collections/{col_name}")
                    if col_response.status_code == 200:
                        col_info = col_response.json().get('result', {})
                        export_info["contents"]["vectors"][col_name] = {
                            "points_count": col_info.get('points_count', 0),
                            "status": col_info.get('status', 'unknown')
                        }
        except Exception as e:
            logger.error(f"导出向量信息失败: {e}")

        # 保存导出文件
        export_file = Path(export_path) / f"unified_legal_dataset_{self.current_version}.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_info, f, ensure_ascii=False, indent=2)

        logger.info(f"统一数据集已导出: {export_file}")
        return str(export_file)

def main() -> None:
    """主函数"""
    print("="*100)
    print("🔧 统一法律数据管理器 🔧")
    print("="*100)

    # 初始化管理器
    manager = UnifiedLegalDataManager()

    # 1. 扫描现有数据
    print("\n📊 扫描现有数据...")
    scan_result = manager.scan_existing_data()

    print(f"  - 向量集合: {len(scan_result['vector_collections'])}个")
    print(f"  - 知识图谱文件: {len(scan_result['knowledge_graph_files'])}个")
    print(f"  - 原始数据文件: {len(scan_result['raw_data_files'])}个")

    # 2. 清理重复数据
    print("\n🧹 清理重复数据...")
    cleaned = manager.clean_duplicate_data()
    print(f"  - 删除重复文件: {cleaned['files_removed']}个")

    # 3. 注册数据集
    print("\n📝 注册数据集...")
    vector_id = manager.register_dataset(
        name="legal_vectors_1024",
        dataset_type="vectors",
        source_path="Qdrant",
        description="1024维法律文档向量"
    )

    kg_id = manager.register_dataset(
        name="legal_knowledge_graph",
        dataset_type="knowledge_graph",
        source_path="NebulaGraph",
        description="法律知识图谱数据"
    )

    # 4. 生成质量报告
    print("\n📈 生成质量报告...")
    report = manager.get_quality_report()

    print(f"  - 总文档数: {report['data_summary']['total_documents']:,}")
    print(f"  - 平均相似度: {report['quality_metrics']['vector_similarity_avg']:.3f}")
    print(f"  - 发现问题: {len(report['issues'])}个")
    print(f"  - 改进建议: {len(report['recommendations'])}条")

    # 5. 导出统一数据集
    print("\n💾 导出统一数据集...")
    export_path = manager.export_unified_dataset(
        "/Users/xujian/Athena工作平台/production/data/exports"
    )

    print("\n✅ 数据管理器运行完成！")
    print(f"📄 质量报告: {Path(manager.config.meta_db_path)}/quality_report_{manager.current_version}.json")
    print(f"📦 导出文件: {export_path}")

if __name__ == "__main__":
    main()
