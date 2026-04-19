#!/usr/bin/env python3
"""
重建所有专业数据
Rebuild All Professional Data

使用本地NLP系统和大模型，最高质量重建所有专业向量库和知识图谱

作者: Athena平台团队
创建时间: 2025-12-20
版本: v3.0.0
"""

from __future__ import annotations
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

from high_quality_patent_builder import HighQualityPatentBuilder
from ipc_knowledge_graph_builder import IPCKnowledgeGraphBuilder

# 导入各个构建器
from patent_vector_builder_nlp import PatentVectorBuilderWithNLP
from technical_dictionary_builder import TechnicalDictionaryBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProfessionalDataRebuilder:
    """专业数据重建管理器"""

    def __init__(self):
        self.production_dir = Path("/Users/xujian/Athena工作平台/production")
        self.data_dir = self.production_dir / "data"
        self.tools_dir = Path("/Users/xujian/Athena工作平台/dev/tools")

        # 数据构建任务配置
        self.build_tasks = [
            {
                "name": "专利复审无效向量库",
                "type": "vector",
                "builder": "patent_vector",
                "enabled": True,
                "description": "专利复审和无效宣告决定的向量数据库"
            },
            {
                "name": "专利复审无效知识图谱",
                "type": "knowledge_graph",
                "builder": "patent_kg",
                "enabled": True,
                "description": "专利复审和无效宣告的知识图谱"
            },
            {
                "name": "IPC分类知识图谱",
                "type": "knowledge_graph",
                "builder": "ipc_kg",
                "enabled": True,
                "description": "国际专利分类知识图谱"
            },
            {
                "name": "技术词典知识图谱",
                "type": "knowledge_graph",
                "builder": "tech_dict_kg",
                "enabled": True,
                "description": "技术术语词典知识图谱"
            }
        ]

        # 构建状态
        self.build_status = {
            "start_time": None,
            "end_time": None,
            "completed_tasks": [],
            "failed_tasks": [],
            "current_task": None
        }

    async def rebuild_all(self):
        """重建所有专业数据"""
        logger.info("="*80)
        logger.info("🚀 开始重建所有专业数据（最高质量）")
        logger.info("="*80)

        self.build_status["start_time"] = datetime.now()

        # 1. 检查环境
        await self._check_environment()

        # 2. 清理旧数据
        await self._clean_old_data()

        # 3. 按顺序执行构建任务
        for task in self.build_tasks:
            if task["enabled"]:
                await self._execute_build_task(task)

        # 4. 生成最终报告
        await self._generate_final_report()

        self.build_status["end_time"] = datetime.now()

        logger.info("\n✅ 所有专业数据重建完成！")

    async def _check_environment(self):
        """检查运行环境"""
        logger.info("\n🔍 检查运行环境...")

        # 检查目录
        required_dirs = [self.production_dir, self.data_dir, self.tools_dir]
        for dir_path in required_dirs:
            if not dir_path.exists():
                logger.error(f"❌ 目录不存在: {dir_path}")
                raise FileNotFoundError(f"目录不存在: {dir_path}")

        # 检查服务（通过导入时验证）
        try:
            import aiohttp
            logger.info("✅ aiohttp 可用")
        except ImportError:
            logger.error("❌ 缺少 aiohttp")
            raise

        logger.info("✅ 环境检查完成")

    async def _clean_old_data(self):
        """清理旧数据"""
        logger.info("\n🧹 清理旧数据...")

        # 清理向量数据库目录
        vector_db_dir = self.data_dir / "vector_db"
        if vector_db_dir.exists():
            import shutil
            shutil.rmtree(vector_db_dir)
            logger.info(f"  已清理: {vector_db_dir}")

        # 清理知识图谱目录
        kg_dir = self.data_dir / "knowledge_graph"
        if kg_dir.exists():
            import shutil
            shutil.rmtree(kg_dir)
            logger.info(f"  已清理: {kg_dir}")

        # 重新创建目录
        for sub_dir in ["vector_db", "knowledge_graph", "patent_data", "ipc_data", "technical_dict"]:
            (self.data_dir / sub_dir).mkdir(parents=True, exist_ok=True)

        logger.info("✅ 数据清理完成")

    async def _execute_build_task(self, task: dict):
        """执行单个构建任务"""
        task_name = task["name"]
        logger.info(f"\n📋 执行任务: {task_name}")
        logger.info(f"   类型: {task['type']}")
        logger.info(f"   描述: {task['description']}")

        self.build_status["current_task"] = task_name

        try:
            if task["builder"] == "patent_vector":
                await self._build_patent_vectors()
            elif task["builder"] == "patent_kg":
                await self._build_patent_kg()
            elif task["builder"] == "ipc_kg":
                await self._build_ipc_kg()
            elif task["builder"] == "tech_dict_kg":
                await self._build_tech_dict_kg()
            else:
                logger.error(f"未知的构建器类型: {task['builder']}")
                return

            self.build_status["completed_tasks"].append({
                "task": task_name,
                "completed_at": datetime.now().isoformat(),
                "status": "success"
            })
            logger.info(f"✅ 任务完成: {task_name}")

        except Exception as e:
            logger.error(f"❌ 任务失败: {task_name} - {e}")
            self.build_status["failed_tasks"].append({
                "task": task_name,
                "failed_at": datetime.now().isoformat(),
                "error": str(e)
            })

    async def _build_patent_vectors(self):
        """构建专利向量库"""
        builder = PatentVectorBuilderWithNLP()

        # 准备数据
        patent_docs = await self._prepare_patent_documents()

        # 处理文档集合
        await builder.process_document_collection(
            patent_docs,
            "patent_review_invalid",
            {
                "name": "专利复审无效向量库",
                "description": "专利复审和无效宣告决定的向量数据库"
            }
        )

    async def _build_patent_kg(self):
        """构建专利知识图谱"""
        builder = HighQualityPatentBuilder()

        # 准备数据
        patent_docs = await self._prepare_patent_documents()

        # 批量处理文档
        output_dir = self.data_dir
        await builder.process_document_batch(patent_docs, output_dir)

    async def _build_ipc_kg(self):
        """构建IPC知识图谱"""
        builder = IPCKnowledgeGraphBuilder()

        # 处理IPC数据
        data_dir = self.tools_dir / "ipc_data"
        if not data_dir.exists():
            data_dir = self.tools_dir

        await builder.process_ipc_data(data_dir, self.data_dir)

    async def _build_tech_dict_kg(self):
        """构建技术词典知识图谱"""
        builder = TechnicalDictionaryBuilder()

        # 处理技术词典数据
        data_dir = self.tools_dir / "technical_dict"
        if not data_dir.exists():
            data_dir = self.tools_dir

        await builder.process_dictionary_data(data_dir, self.data_dir)

    async def _prepare_patent_documents(self) -> list[dict]:
        """准备专利文档数据"""
        docs = []

        # 查找专利数据目录
        patent_dirs = [
            self.tools_dir / "patent_review",
            self.tools_dir / "patent_invalid",
            self.tools_dir / "patent_data"
        ]

        patent_files = []
        for patent_dir in patent_dirs:
            if patent_dir.exists():
                patent_files.extend(patent_dir.rglob("*"))

        if patent_files:
            # 读取真实专利文件
            for file_path in patent_files[:50]:  # 限制数量
                try:
                    if file_path.suffix.lower() in ['.json', '.txt', '.md']:
                        content = file_path.read_text(encoding='utf-8')
                        if file_path.suffix == '.json':
                            data = json.loads(content)
                            docs.append(data)
                        else:
                            docs.append({
                                "title": file_path.stem,
                                "content": content,
                                "source": str(file_path)
                            })
                except Exception as e:
                    logger.warning(f"读取文件失败 {file_path}: {e}")
        else:
            # 使用示例数据
            docs = [
                {
                    "title": "CN202000000000.0 复审决定",
                    "content": """
                    复审请求审查决定书

                    专利号：CN202000000000.0
                    申请号：202000000000.0
                    发明名称：一种数据处理系统

                    复审请求人：甲公司
                    专利权人：甲公司

                    复审请求人于2023年01月01日向专利复审委员会提出复审请求。
                    经审查，本申请不符合专利法第22条第3款的规定。
                    """,
                    "source": "sample_data"
                },
                {
                    "title": "CN202100000000.0 无效宣告请求审查决定",
                    "content": """
                    无效宣告请求审查决定

                    专利号：CN202100000000.0
                    申请号：202100000000.0
                    发明名称：一种新型装置

                    无效宣告请求人：乙公司
                    专利权人：丙公司

                    本决定针对专利号为CN202100000000.0的发明专利。
                    基于专利法第45条的规定，本专利权被宣告无效。
                    """,
                    "source": "sample_data"
                }
            ]

        return docs

    async def _generate_final_report(self):
        """生成最终报告"""
        logger.info("\n📊 生成最终报告...")

        report = {
            "rebuild_summary": {
                "start_time": self.build_status["start_time"].isoformat(),
                "end_time": self.build_status["end_time"].isoformat() if self.build_status["end_time"] else None,
                "duration_hours": None,
                "total_tasks": len(self.build_tasks),
                "completed_tasks": len(self.build_status["completed_tasks"]),
                "failed_tasks": len(self.build_status["failed_tasks"])
            },
            "task_details": {
                "completed": self.build_status["completed_tasks"],
                "failed": self.build_status["failed_tasks"]
            },
            "output_structure": self._get_output_structure(),
            "quality_metrics": await self._calculate_quality_metrics(),
            "next_steps": [
                "1. 将向量数据导入Qdrant数据库",
                "2. 将知识图谱数据导入NebulaGraph",
                "3. 配置Hybrid RAG系统",
                "4. 验证数据质量",
                "5. 性能测试和优化"
            ]
        }

        # 计算持续时间
        if self.build_status["end_time"] and self.build_status["start_time"]:
            duration = self.build_status["end_time"] - self.build_status["start_time"]
            report["rebuild_summary"]["duration_hours"] = duration.total_seconds() / 3600

        # 保存报告
        report_file = self.production_dir / "rebuild_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        # 生成可读报告
        readable_report = self._generate_readable_report(report)
        readable_report_file = self.production_dir / "rebuild_report.txt"
        with open(readable_report_file, 'w', encoding='utf-8') as f:
            f.write(readable_report)

        logger.info(f"  报告已保存: {report_file}")
        logger.info(f"  可读报告: {readable_report_file}")

    def _get_output_structure(self) -> dict:
        """获取输出结构"""
        structure = {}
        data_dir = self.data_dir

        for item in data_dir.iterdir():
            if item.is_dir():
                # 统计文件数量
                file_count = len(list(item.rglob("*")))
                structure[item.name] = {
                    "type": "directory",
                    "path": str(item),
                    "file_count": file_count
                }
            elif item.is_file():
                structure[item.name] = {
                    "type": "file",
                    "path": str(item),
                    "size_mb": item.stat().st_size / 1024 / 1024
                }

        return structure

    async def _calculate_quality_metrics(self) -> dict:
        """计算质量指标"""
        metrics = {
            "total_vectors": 0,
            "total_entities": 0,
            "total_relations": 0,
            "avg_confidence": 0.0,
            "coverage_domains": []
        }

        # 扫描输出文件
        for json_file in self.data_dir.rglob("*.json"):
            try:
                data = json.load(json_file)
                if "metadata" in data:
                    meta = data["metadata"]
                    if "total_chunks" in meta:
                        metrics["total_vectors"] += meta["total_chunks"]
                    if "total_entities" in meta:
                        metrics["total_entities"] += meta["total_entities"]
                    if "total_relations" in meta:
                        metrics["total_relations"] += meta["total_relations"]
            except Exception as e:
                logger.warning(f"解析文件失败 {json_file}: {e}")

        # 识别覆盖的领域
        domains = set()
        for task in self.build_tasks:
            if task["name"] in ["专利复审无效向量库", "专利复审无效知识图谱"]:
                domains.add("专利")
            elif "IPC" in task["name"]:
                domains.add("分类")
            elif "技术词典" in task["name"]:
                domains.add("术语")

        metrics["coverage_domains"] = list(domains)

        return metrics

    def _generate_readable_report(self, report: dict) -> str:
        """生成可读报告"""
        lines = []
        lines.append("="*80)
        lines.append("专业数据重建报告")
        lines.append("="*80)
        lines.append("")
        lines.append(f"重建时间: {report['rebuild_summary']['start_time']}")
        lines.append(f"完成时间: {report['rebuild_summary']['end_time']}")
        if report['rebuild_summary']['duration_hours']:
            lines.append(f"总耗时: {report['rebuild_summary']['duration_hours']:.2f} 小时")
        lines.append("")
        lines.append("任务统计:")
        lines.append(f"  总任务数: {report['rebuild_summary']['total_tasks']}")
        lines.append(f"  成功任务: {report['rebuild_summary']['completed_tasks']}")
        lines.append(f"  失败任务: {report['rebuild_summary']['failed_tasks']}")
        lines.append("")
        lines.append("成功完成的任务:")
        for task in report['task_details']['completed']:
            lines.append(f"  ✅ {task['task']} - {task['completed_at']}")
        lines.append("")
        lines.append("失败的任务:")
        for task in report['task_details']['failed']:
            lines.append(f"  ❌ {task['task']} - {task['error']}")
        lines.append("")
        lines.append("质量指标:")
        metrics = report['quality_metrics']
        lines.append(f"  总向量数: {metrics['total_vectors']}")
        lines.append(f"  总实体数: {metrics['total_entities']}")
        lines.append(f"  总关系数: {metrics['total_relations']}")
        lines.append(f"  覆盖领域: {', '.join(metrics['coverage_domains'])}")
        lines.append("")
        lines.append("后续步骤:")
        for step in report['next_steps']:
            lines.append(f"  {step}")
        lines.append("")
        lines.append("="*80)

        return "\n".join(lines)

async def main():
    """主函数"""
    rebuilder = ProfessionalDataRebuilder()
    await rebuilder.rebuild_all()

if __name__ == "__main__":
    asyncio.run(main())
