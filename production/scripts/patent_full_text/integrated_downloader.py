#!/usr/bin/env python3
"""
专利检索与下载集成中间层
解决patent-downloader只接受专利号的问题，维护元数据关联

作者: Athena平台团队
创建时间: 2025-12-24
"""

from __future__ import annotations
import json
import logging
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

# 使用安全哈希函数替代不安全的MD5/SHA1
from production.utils.security_helpers import short_hash

# 添加项目路径 - patent_downloader在dev/tools/patent_downloader/src
project_root = Path(__file__).parent.parent.parent.parent
patent_downloader_src = project_root / "dev/tools" / "patent_downloader" / "src"

sys.path.insert(0, str(patent_downloader_src))

# 导入patent_downloader
try:
    from patent_downloader import PatentDownloader
except ImportError:
    PatentDownloader = None

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler(f'/Users/xujian/Athena工作平台/logs/integrated_download_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class PatentDownloadRequest:
    """专利下载请求 - 包含完整元数据"""
    # 核心标识
    patent_number: str
    application_number: str | None = None

    # PostgreSQL关联
    postgres_id: str | None = None  # UUID in patents table

    # 元数据（用于分类和验证）
    patent_name: str | None = None
    patent_type: str | None = None  # 发明/实用新型/外观设计
    applicant: str | None = None
    inventor: str | None = None
    ipc_main_class: str | None = None

    # 来源信息
    source: str = "patent_search"  # patent_search, google_patents, manual
    search_query: str | None = None

    # 下载配置
    output_dir: str | None = None

    def get_cache_key(self) -> str:
        """生成缓存键"""
        data = f"{self.patent_number}_{self.application_number or ''}"
        return short_hash(data.encode())[:16]


@dataclass
class PatentDownloadResult:
    """专利下载结果"""
    request: PatentDownloadRequest
    success: bool
    file_path: str | None = None
    file_size: int | None = None
    error_message: str | None = None
    downloaded_at: str = None

    def __post_init__(self):
        if self.downloaded_at is None:
            self.downloaded_at = datetime.now().isoformat()


class MetadataTracker:
    """元数据追踪器 - 维护下载与数据库记录的关联"""

    def __init__(self, tracking_dir: str = "/Users/xujian/apps/apps/patents/checkpoints"):
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(parents=True, exist_ok=True)
        self.mapping_file = self.tracking_dir / "download_mapping.json"
        self.mapping = self._load_mapping()

    def _load_mapping(self) -> dict[str, dict[str, Any]]:
        """加载映射关系"""
        if self.mapping_file.exists():
            try:
                with open(self.mapping_file, encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载映射文件失败: {e}")
        return {}

    def _save_mapping(self) -> Any:
        """保存映射关系"""
        try:
            with open(self.mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapping, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存映射文件失败: {e}")

    def record_download(self, request: PatentDownloadRequest, result: PatentDownloadResult) -> Any:
        """记录下载结果"""
        key = request.get_cache_key()

        self.mapping[key] = {
            "patent_number": request.patent_number,
            "application_number": request.application_number,
            "postgres_id": request.postgres_id,
            "file_path": result.file_path,
            "file_size": result.file_size,
            "downloaded_at": result.downloaded_at,
            "success": result.success,
            "metadata": {
                "patent_name": request.patent_name,
                "patent_type": request.patent_type,
                "applicant": request.applicant,
                "inventor": request.inventor,
                "ipc_main_class": request.ipc_main_class,
                "source": request.source,
                "search_query": request.search_query,
            }
        }

        self._save_mapping()
        logger.info(f"✅ 记录下载映射: {request.patent_number} -> {result.file_path}")

    def get_by_postgres_id(self, postgres_id: str) -> dict[str, Any | None]:
        """根据PostgreSQL ID查询下载记录"""
        for record in self.mapping.values():
            if record.get("postgres_id") == postgres_id:
                return record
        return None

    def get_by_patent_number(self, patent_number: str) -> dict[str, Any | None]:
        """根据专利号查询下载记录"""
        for record in self.mapping.values():
            if record.get("patent_number") == patent_number:
                return record
        return None


class IntegratedPatentDownloader:
    """集成专利下载器 - 中间层"""

    def __init__(self, default_output_dir: str = "/Users/xujian/apps/apps/patents/PDF"):
        self.default_output_dir = default_output_dir
        self.tracker = MetadataTracker()

        # 初始化patent_downloader
        if PatentDownloader:
            self.downloader = PatentDownloader()
            logger.info("✅ patent_downloader初始化成功")
        else:
            self.downloader = None
            logger.warning("⚠️ patent_downloader未安装，部分功能不可用")

    def determine_output_dir(self, request: PatentDownloadRequest) -> str:
        """根据专利号确定输出目录"""
        if request.output_dir:
            return request.output_dir

        # 按国家/地区分类
        patent_number = request.patent_number.upper()

        if patent_number.startswith("CN"):
            return f"{self.default_output_dir}/CN"
        elif patent_number.startswith("US"):
            return f"{self.default_output_dir}/US"
        elif patent_number.startswith("EP"):
            return f"{self.default_output_dir}/EP"
        elif patent_number.startswith("WO") or patent_number.startswith("PCT"):
            return f"{self.default_output_dir}/WO"
        else:
            return self.default_output_dir

    def download_single(self, request: PatentDownloadRequest) -> PatentDownloadResult:
        """下载单个专利"""
        output_dir = self.determine_output_dir(request)
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        logger.info(f"📥 下载专利: {request.patent_number}")
        logger.info(f"   输出目录: {output_dir}")
        logger.info(f"   PostgreSQL ID: {request.postgres_id}")
        logger.info(f"   申请人: {request.applicant}")

        try:
            if self.downloader:
                # 使用patent_downloader下载
                success = self.downloader.download_patent(request.patent_number, output_dir)

                if success:
                    file_path = f"{output_dir}/{request.patent_number}.pdf"
                    file_size = Path(file_path).stat().st_size

                    result = PatentDownloadResult(
                        request=request,
                        success=True,
                        file_path=file_path,
                        file_size=file_size
                    )

                    # 记录映射
                    self.tracker.record_download(request, result)

                    logger.info(f"✅ 下载成功: {file_path} ({file_size:,} bytes)")
                    return result
                else:
                    result = PatentDownloadResult(
                        request=request,
                        success=False,
                        error_message="下载失败（未知原因）"
                    )
                    logger.error(f"❌ 下载失败: {request.patent_number}")
                    return result
            else:
                # 模拟下载（用于测试）
                logger.warning("⚠️ patent_downloader未安装，使用模拟下载")
                result = PatentDownloadResult(
                    request=request,
                    success=False,
                    error_message="patent_downloader未安装"
                )
                return result

        except Exception as e:
            result = PatentDownloadResult(
                request=request,
                success=False,
                error_message=str(e)
            )
            logger.error(f"❌ 下载异常: {e}")
            return result

    def download_batch(self, requests: list[PatentDownloadRequest]) -> list[PatentDownloadResult]:
        """批量下载"""
        logger.info(f"📦 批量下载 {len(requests)} 个专利")

        results = []
        successful = 0
        failed = 0

        for i, request in enumerate(requests, 1):
            logger.info(f"\n[{i}/{len(requests)}]")

            result = self.download_single(request)
            results.append(result)

            if result.success:
                successful += 1
            else:
                failed += 1

        # 输出统计
        logger.info("\n" + "=" * 70)
        logger.info("批量下载统计")
        logger.info("=" * 70)
        logger.info(f"总计: {len(requests)}")
        logger.info(f"成功: {successful}")
        logger.info(f"失败: {failed}")
        logger.info(f"成功率: {successful/len(requests)*100:.1f}%")

        return results

    def create_requests_from_patent_search(
        self,
        patents_data: list[dict[str, Any]],
        source: str = "patent_search"
    ) -> list[PatentDownloadRequest]:
        """从patent-search结果创建下载请求"""
        requests = []

        for patent in patents_data:
            request = PatentDownloadRequest(
                patent_number=patent.get("publication_number", patent.get("application_number", "")),
                application_number=patent.get("application_number"),
                postgres_id=patent.get("id"),  # PostgreSQL UUID
                patent_name=patent.get("patent_name"),
                patent_type=patent.get("patent_type"),
                applicant=patent.get("applicant"),
                inventor=patent.get("inventor"),
                ipc_main_class=patent.get("ipc_main_class"),
                source=source,
                output_dir=None  # 自动确定
            )
            requests.append(request)

        logger.info(f"✅ 从patent-search创建 {len(requests)} 个下载请求")
        return requests

    def create_requests_from_patent_numbers(
        self,
        patent_numbers: list[str],
        metadata: dict[str, Any] | None = None
    ) -> list[PatentDownloadRequest]:
        """从专利号列表创建下载请求"""
        requests = []

        for pn in patent_numbers:
            request = PatentDownloadRequest(
                patent_number=pn,
                source=metadata.get("source", "manual") if metadata else "manual",
                search_query=metadata.get("search_query") if metadata else None,
                output_dir=None
            )
            requests.append(request)

        logger.info(f"✅ 从专利号列表创建 {len(requests)} 个下载请求")
        return requests


# ==================== 示例使用 ====================

def example_usage() -> Any:
    """示例使用"""
    downloader = IntegratedPatentDownloader()

    # 示例1: 从patent-search结果下载
    patent_search_results = [
        {
            "id": "uuid-1",
            "patent_name": "一种人工智能算法",
            "application_number": "CN202110000001",
            "publication_number": "CN112233445A",
            "patent_type": "发明",
            "applicant": "某某公司",
            "inventor": "张三",
            "ipc_main_class": "G06F"
        }
    ]

    requests = downloader.create_requests_from_patent_search(patent_search_results)
    results = downloader.download_batch(requests)

    # 示例2: 从专利号列表下载
    patent_numbers = ["CN112233445A", "US20231234567A1"]
    requests = downloader.create_requests_from_patent_numbers(
        patent_numbers,
        metadata={"source": "google_patents", "search_query": "人工智能"}
    )
    results = downloader.download_batch(requests)

    # 示例3: 查询下载记录
    record = downloader.tracker.get_by_postgres_id("uuid-1")
    if record:
        logger.info(f"📋 找到记录: {record}")


if __name__ == "__main__":
    example_usage()
