#!/usr/bin/env python3
"""
专利法律法规向量和知识图谱构建执行脚本
Patent Legal Vector and Knowledge Graph Construction Execution Script

作者: 小诺·双鱼公主
创建时间: 2024年12月14日
"""

import os
import sys
import asyncio
import logging
import subprocess
from pathlib import Path

# 添加项目路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class PatentLegalPipeline:
    """专利法律法规处理流水线"""

    def __init__(self):
        """初始化"""
        self.base_path = "/Users/xujian/Athena工作平台"
        self.legal_folder = "/Users/xujian/学习资料/专利/专利法律法规"

    async def run_vectorization(self):
        """运行向量化处理"""
        logger.info("=== 步骤1: 专利法律法规向量化处理 ===")

        # 检查必要的库
        try:
            import sentence_transformers
            import numpy
        except ImportError:
            logger.error("请安装必要的库: pip install sentence-transformers numpy")
            return False

        # 执行向量化
        script_path = os.path.join(self.base_path, "patent_legal_vectorization_design.py")
        cmd = f"cd {self.base_path} && python3 {script_path}"

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("向量化处理完成！")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"向量化处理失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"执行向量化脚本出错: {e}")
            return False

    async def run_kg_construction(self):
        """运行知识图谱构建"""
        logger.info("=== 步骤2: 专利法律法规知识图谱构建 ===")

        # 执行知识图谱构建
        script_path = os.path.join(self.base_path, "patent_legal_knowledge_graph_design.py")
        cmd = f"cd {self.base_path} && python3 {script_path}"

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("知识图谱构建完成！")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"知识图谱构建失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"执行知识图谱脚本出错: {e}")
            return False

    async def check_services(self):
        """检查服务状态"""
        logger.info("=== 步骤0: 检查服务状态 ===")

        # 检查Qdrant
        try:
            import requests
            response = requests.get("http://localhost:6333/collections")
            if response.status_code == 200:
                logger.info("✅ Qdrant服务正常运行")
            else:
                logger.warning("⚠️ Qdrant服务可能未正常运行")
        except:
            logger.warning("⚠️ 无法连接到Qdrant服务")

        # 检查JanusGraph
        try:
            from gremlin_python.driver.driver_remote_connection import DriverRemoteConnection
            from gremlin_python.process.anonymous_traversal import traversal
            g = traversal().withRemote(
                DriverRemoteConnection('ws://localhost:8182/gremlin', 'g')
            )
            g.V().limit(1).next()
            logger.info("✅ JanusGraph服务正常运行")
        except:
            logger.warning("⚠️ 无法连接到JanusGraph服务")

    async def import_to_qdrant(self):
        """导入到Qdrant"""
        logger.info("=== 步骤3: 导入向量到Qdrant ===")

        script_path = os.path.join(self.base_path, "scripts", "patent_legal", "import_to_qdrant.py")
        cmd = f"cd {self.base_path} && python3 {script_path}"

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("向量导入Qdrant成功！")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"向量导入Qdrant失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"执行Qdrant导入脚本出错: {e}")
            return False

    async def import_to_janusgraph(self):
        """导入到JanusGraph"""
        logger.info("=== 步骤4: 导入知识图谱到JanusGraph ===")

        script_path = os.path.join(self.base_path, "scripts", "patent_legal", "import_to_janusgraph.py")
        cmd = f"cd {self.base_path} && python3 {script_path}"

        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("知识图谱导入JanusGraph成功！")
                logger.info(result.stdout)
                return True
            else:
                logger.error(f"知识图谱导入JanusGraph失败: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"执行JanusGraph导入脚本出错: {e}")
            return False

    async def run_full_pipeline(self):
        """运行完整流水线"""
        logger.info("开始专利法律法规向量和知识图谱构建流水线...")

        # 检查源文件
        if not os.path.exists(self.legal_folder):
            logger.error(f"源文件夹不存在: {self.legal_folder}")
            return False

        # 检查服务状态
        await self.check_services()

        # 运行向量化
        if not await self.run_vectorization():
            logger.error("向量化处理失败，流水线终止")
            return False

        # 运行知识图谱构建
        if not await self.run_kg_construction():
            logger.error("知识图谱构建失败，流水线终止")
            return False

        # 导入到Qdrant
        if not await self.import_to_qdrant():
            logger.error("导入Qdrant失败")
            return False

        # 导入到JanusGraph
        if not await self.import_to_janusgraph():
            logger.error("导入JanusGraph失败")
            return False

        logger.info("🎉 专利法律法规向量和知识图谱构建流水线完成！")
        return True

async def main():
    """主函数"""
    pipeline = PatentLegalPipeline()
    success = await pipeline.run_full_pipeline()

    if success:
        logger.info("\n✅ 所有任务完成！")
        logger.info("\n数据位置：")
        logger.info("- 向量数据: /Users/xujian/Athena工作平台/data/patent_legal_vectors/patent_legal_vectors.json")
        logger.info("- 知识图谱: /Users/xujian/Athena工作平台/data/patent_legal_kg/patent_legal_kg.json")
        logger.info("\n可访问：")
        logger.info("- Qdrant: http://localhost:6333")
        logger.info("- JanusGraph: http://localhost:8182")
    else:
        logger.error("\n❌ 流水线执行失败，请查看日志")

if __name__ == "__main__":
    asyncio.run(main())