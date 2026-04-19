#!/usr/bin/env python3
"""
知识图谱构建模块
将专利数据构建为知识图谱并存储到NebulaGraph

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from core.config.secure_config import get_config

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

config = get_config()


# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

# 导入安全配置
try:
    from production.config import get_nebula_config
except ImportError:
    def get_nebula_config():
        return {
            'host': '127.0.0.1',
            'port': 9669,
            'user': 'root',
            "password": config.get("NEBULA_PASSWORD", required=True),
            'space': 'patent_full_text'
        }

# 导入配置管理
try:
    from .config import get_config
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入NebulaGraph客户端
try:
    from nebula3.Config import Config
    from nebula3.gclient.net import ConnectionPool
    NEBULA_AVAILABLE = True
except ImportError:
    NEBULA_AVAILABLE = False
    logger.warning("⚠️ nebula3未安装")


@dataclass
class KGBuildResult:
    """知识图谱构建结果"""
    patent_number: str
    success: bool
    vertex_id: str | None = None
    error_message: str | None = None
    vertices_created: int = 0
    edges_created: int = 0


class PatentKGBuilder:
    """专利知识图谱构建器"""

    def __init__(
        self,
        hosts: str = None,
        username: str = None,
        password: str = None,
        space_name: str = None,
        config=None  # 配置对象（可选）
    ):
        """
        初始化知识图谱构建器

        Args:
            hosts: NebulaGraph地址 (如果为None,从配置读取)
            username: 用户名 (如果为None,从配置读取)
            password: 密码 (如果为None,从配置读取)
            space_name: 空间名称 (如果为None,从配置读取)
            config: 配置对象（可选，优先级高于其他参数）
        """
        # 从环境变量配置获取默认值
        nebula_config = get_nebula_config()
        hosts = hosts or f"{nebula_config.get('host', '127.0.0.1')}:{nebula_config.get('port', 9669)}"
        username = username or nebula_config.get('user', 'root')
        password = password or nebula_config.get("password", config.get("NEBULA_PASSWORD", required=True))
        space_name = space_name or nebula_config.get('space', 'patent_full_text')

        # 使用配置对象（如果提供）
        if config is not None and CONFIG_AVAILABLE:
            hosts = config.nebula.hosts
            username = config.nebula.username
            password = config.nebula.password
            space_name = config.nebula.space_name

        self.hosts = hosts
        self.username = username
        self.password = password
        self.space_name = space_name

        self.pool = None
        self.session = None

        if NEBULA_AVAILABLE:
            self._connect()

    def _connect(self):
        """连接NebulaGraph"""
        try:
            config = Config()
            config.max_connection_pool_size = 2

            # 解析主机地址（支持 "host:port" 格式）
            host_addresses = []
            for host in self.hosts.split(','):
                host = host.strip()
                if ':' in host:
                    host_part, port_part = host.rsplit(':', 1)
                    host_addresses.append((host_part, int(port_part)))
                else:
                    host_addresses.append((host, 9669))  # 默认端口

            self.pool = ConnectionPool()
            self.pool.init(host_addresses, config)

            self.session = self.pool.get_session(self.username, self.password)

            # 使用空间
            result = self.session.execute(f"USE {self.space_name};")
            logger.info(f"✅ 连接NebulaGraph成功: {self.space_name}")

        except Exception as e:
            logger.error(f"❌ 连接NebulaGraph失败: {e}")
            self.pool = None
            self.session = None

    def _generate_vertex_id(self, prefix: str, identifier: str) -> str:
        """生成顶点ID"""
        data = f"{prefix}_{identifier}"
        return short_hash(data.encode())[:32]

    def build_patent_kg(
        self,
        patent_number: str,
        patent_name: str,
        application_number: str,
        applicant: str,
        inventor: str,
        ipc_main_class: str,
        abstract: str,
        claims_text: str
    ) -> KGBuildResult:
        """
        构建专利知识图谱

        Args:
            patent_number: 专利号
            patent_name: 专利名称
            application_number: 申请号
            applicant: 申请人
            inventor: 发明人
            ipc_main_class: IPC主分类
            abstract: 摘要
            claims_text: 权利要求书

        Returns:
            KGBuildResult: 构建结果
        """
        if not self.session:
            return KGBuildResult(
                patent_number=patent_number,
                success=False,
                error_message="NebulaGraph未连接"
            )

        logger.info(f"🔄 构建知识图谱: {patent_number}")

        try:
            vertices_created = 0
            edges_created = 0

            # 1. 创建专利顶点
            patent_id = self._generate_vertex_id("patent", patent_number)
            self._create_patent_vertex(
                patent_id, patent_number, patent_name,
                application_number, ipc_main_class, abstract
            )
            vertices_created += 1

            # 2. 创建申请人顶点和边
            if applicant:
                applicant_id = self._generate_vertex_id("applicant", applicant)
                self._create_applicant_vertex(applicant_id, applicant)
                vertices_created += 1
                self._create_has_applicant_edge(patent_id, applicant_id)
                edges_created += 1

            # 3. 创建IPC分类顶点和边
            if ipc_main_class:
                ipc_id = self._generate_vertex_id("ipc", ipc_main_class)
                self._create_ipc_vertex(ipc_id, ipc_main_class)
                vertices_created += 1
                self._create_has_ipc_edge(patent_id, ipc_id)
                edges_created += 1

            # 4. 解析并创建权利要求顶点和边
            if claims_text:
                claim_vertices, claim_edges = self._create_claim_vertices(
                    patent_id, claims_text
                )
                vertices_created += claim_vertices
                edges_created += claim_edges

            logger.info(
                f"✅ 知识图谱构建成功: "
                f"{vertices_created}个顶点, {edges_created}条边"
            )

            return KGBuildResult(
                patent_number=patent_number,
                success=True,
                vertex_id=patent_id,
                vertices_created=vertices_created,
                edges_created=edges_created
            )

        except Exception as e:
            logger.error(f"❌ 知识图谱构建失败: {e}")
            return KGBuildResult(
                patent_number=patent_number,
                success=False,
                error_message=str(e)
            )

    def _create_patent_vertex(
        self,
        vertex_id: str,
        patent_number: str,
        patent_name: str,
        application_number: str,
        ipc_class: str,
        abstract: str
    ):
        """创建专利顶点"""
        # 截断摘要以避免超过限制
        abstract_short = abstract[:500] if abstract else ""

        nGQL = f"""
        INSERT VERTEX patent(
            id, patent_number, patent_name, application_number,
            ipc_class, abstract, created_at
        ) VALUES "{vertex_id}": (
            "{vertex_id}",
            "{patent_number}",
            "{patent_name.replace(chr(34), '')}",
            "{application_number}",
            "{ipc_class}",
            "{abstract_short.replace(chr(34), '').replace(chr(10), ' ')}",
            datetime("{datetime.now().isoformat()}")
        );
        """

        result = self.session.execute(nGQL)
        if not result.is_succeeded():
            logger.warning(f"⚠️ 创建专利顶点失败: {result.error_msg()}")

    def _create_applicant_vertex(self, vertex_id: str, name: str):
        """创建申请人顶点"""
        nGQL = f"""
        INSERT VERTEX applicant(id, name, created_at) VALUES "{vertex_id}": (
            "{vertex_id}",
            "{name.replace(chr(34), '')}",
            datetime("{datetime.now().isoformat()}")
        );
        """

        result = self.session.execute(nGQL)
        # 忽略已存在的错误
        if not result.is_succeeded() and "duplicate" not in str(result.error_msg()).lower():
            logger.warning(f"⚠️ 创建申请人顶点失败: {result.error_msg()}")

    def _create_has_applicant_edge(self, patent_id: str, applicant_id: str):
        """创建专利-申请人边"""
        nGQL = f"""
        INSERT EDGE HAS_APPLICANT(created_at) VALUES "{patent_id}"->"{applicant_id}": (
            datetime("{datetime.now().isoformat()}")
        );
        """

        result = self.session.execute(nGQL)
        if not result.is_succeeded():
            logger.warning(f"⚠️ 创建HAS_APPLICANT边失败: {result.error_msg()}")

    def _create_ipc_vertex(self, vertex_id: str, ipc_code: str):
        """创建IPC分类顶点"""
        # 提取IPC级别信息
        section = ipc_code[0] if ipc_code else ""
        subclass = ipc_code[:4] if len(ipc_code) >= 4 else ""

        nGQL = f"""
        INSERT VERTEX ipc_class(id, code, section, subclass, created_at) VALUES "{vertex_id}": (
            "{vertex_id}",
            "{ipc_code}",
            "{section}",
            "{subclass}",
            datetime("{datetime.now().isoformat()}")
        );
        """

        result = self.session.execute(nGQL)
        # 忽略已存在的错误
        if not result.is_succeeded() and "duplicate" not in str(result.error_msg()).lower():
            logger.warning(f"⚠️ 创建IPC顶点失败: {result.error_msg()}")

    def _create_has_ipc_edge(self, patent_id: str, ipc_id: str):
        """创建专利-IPC边"""
        nGQL = f"""
        INSERT EDGE HAS_CLAIM(sequence) VALUES "{patent_id}"->"{ipc_id}": (0);
        """

        result = self.session.execute(nGQL)
        if not result.is_succeeded():
            logger.warning(f"⚠️ 创建HAS_CLAIM边失败: {result.error_msg()}")

    def _create_claim_vertices(
        self,
        patent_id: str,
        claims_text: str
    ) -> tuple[int, int]:
        """创建权利要求顶点和边"""
        vertices = 0
        edges = 0

        # 简单解析权利要求（按数字分割）
        import re
        claim_pattern = re.compile(r'(\d+)\.\s*(.+?)(?=\n\s*\d+\.|$)', re.DOTALL)
        matches = claim_pattern.finditer(claims_text)

        for match in matches:
            claim_num = match.group(1)
            claim_text = match.group(2).strip()

            if len(claim_text) < 10:
                continue

            # 创建权利要求顶点
            claim_id = self._generate_vertex_id(f"claim_{patent_id}", claim_num)
            claim_text_short = claim_text[:500].replace('"', '').replace('\n', ' ')

            nGQL = f"""
            INSERT VERTEX claim(id, patent_id, claim_number, text, created_at) VALUES "{claim_id}": (
                "{claim_id}",
                "{patent_id}",
                {claim_num},
                "{claim_text_short}",
                datetime("{datetime.now().isoformat()}")
            );
            """

            result = self.session.execute(nGQL)
            if result.is_succeeded():
                vertices += 1

                # 创建专利-权利要求边
                edge_nGQL = f"""
                INSERT EDGE HAS_CLAIM(sequence) VALUES "{patent_id}"->"{claim_id}": ({claim_num});
                """

                edge_result = self.session.execute(edge_nGQL)
                if edge_result.is_succeeded():
                    edges += 1

        return vertices, edges

    def create_citation_edge(
        self,
        citing_patent: str,
        cited_patent: str,
        citation_type: str = "forward"
    ) -> bool:
        """
        创建专利引用关系

        Args:
            citing_patent: 引用专利
            cited_patent: 被引用专利
            citation_type: 引用类型 (forward/backward)

        Returns:
            bool: 是否成功
        """
        if not self.session:
            return False

        citing_id = self._generate_vertex_id("patent", citing_patent)
        cited_id = self._generate_vertex_id("patent", cited_patent)

        nGQL = f"""
        INSERT EDGE CITES(citation_type, created_at) VALUES "{citing_id}"->"{cited_id}": (
            "{citation_type}",
            datetime("{datetime.now().isoformat()}")
        );
        """

        result = self.session.execute(nGQL)
        return result.is_succeeded()

    def close(self):
        """关闭连接"""
        if self.session:
            self.session.release()
        if self.pool:
            self.pool.close()
        logger.info("🔌 NebulaGraph连接已关闭")


# ==================== 示例使用 ====================

def main():
    """示例使用"""
    builder = PatentKGBuilder()

    if not builder.session:
        logger.error("❌ 无法连接NebulaGraph，跳过示例")
        return

    print("=" * 70)
    print("知识图谱构建示例")
    print("=" * 70)

    # 示例1: 构建专利知识图谱
    result = builder.build_patent_kg(
        patent_number="CN112233445A",
        patent_name="一种基于人工智能的图像识别方法",
        application_number="CN202110001234",
        applicant="北京某某科技有限公司",
        inventor="张三;李四",
        ipc_main_class="G06F",
        abstract="本发明公开了一种图像识别方法，通过深度学习模型实现高精度识别。",
        claims_text="1. 一种图像识别方法，其特征在于，包括：获取图像；提取特征；分类识别。2. 根据权利要求1所述的方法，所述模型为卷积神经网络。"
    )

    print("\n📋 构建结果:")
    print(f"   专利号: {result.patent_number}")
    print(f"   成功: {result.success}")
    print(f"   顶点ID: {result.vertex_id}")
    print(f"   创建顶点: {result.vertices_created}")
    print(f"   创建边: {result.edges_created}")

    if not result.success:
        print(f"   错误: {result.error_message}")

    builder.close()


if __name__ == "__main__":
    main()
