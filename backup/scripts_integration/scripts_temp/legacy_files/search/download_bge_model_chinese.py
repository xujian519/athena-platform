#!/usr/bin/env python3
"""
使用国内镜像下载BGE模型
Download BGE Model from Chinese Mirrors

支持多个国内镜像源的模型下载工具
"""

import logging
import os
import sys
import tarfile
import time
import zipfile
from pathlib import Path
from typing import List, Optional
from urllib.parse import urljoin

import requests

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 模型信息
BGE_MODEL_INFO = {
    'name': 'BAAI/bge-base-zh-v1.5',
    'files': [
        'config.json',
        'pytorch_model.bin',
        'tokenizer.json',
        'tokenizer_config.json',
        'vocab.txt',
        'special_tokens_map.json',
        'config_sentence_transformers.json',
        'sentence_bert_config.json',
        'modules.json'
    ],
    'total_size': '410MB'  # 大约总大小
}

# 国内镜像源列表
CHINESE_MIRRORS = [
    {
        'name': 'ModelScope',
        'base_url': 'https://modelscope.cn/api/v1/models',
        'model_path': 'Xorbits/bge-base-zh-v1.5/repo/files',
        'download_url': 'https://modelscope.cn/api/v1/models/Xorbits/bge-base-zh-v1.5/repo/files'
    },
    {
        'name': 'PaddleHub',
        'base_url': 'https://paddlehub.bj.bcebos.com',
        'model_path': '/community_models/bge-base-zh-v1.5'
    },
    {
        'name': 'FastNLP',
        'base_url': 'https://hf-mirror.com',
        'model_path': '/BAAI/bge-base-zh-v1.5'
    },
    {
        'name': 'Aliyun OSS',
        'base_url': 'https://hf-mirror.com',
        'model_path': '/BAAI/bge-base-zh-v1.5'
    }
]

class BGEModelDownloader:
    """BGE模型下载器"""

    def __init__(self, target_dir: str = None):
        """初始化下载器

        Args:
            target_dir: 目标保存目录，默认为huggingface缓存目录
        """
        if target_dir is None:
            # 使用标准的huggingface缓存目录
            cache_home = Path.home() / '.cache' / 'huggingface' / 'hub'
            self.target_dir = cache_home / f'models--{BGE_MODEL_INFO['name'].replace('/', '--')}'
        else:
            self.target_dir = Path(target_dir)

        self.target_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 目标目录: {self.target_dir}")

    def try_modelscope_download(self) -> bool:
        """尝试从ModelScope下载"""
        logger.info('🔄 尝试从ModelScope下载...')

        try:
            # 设置ModelScope镜像环境变量
            os.environ['MODELSCOPE_CACHE'] = str(Path.home() / '.cache' / 'modelscope')

            # 使用ModelScope SDK下载
            try:
                from modelscope import snapshot_download

                # 下载模型到目标目录
                model_dir = snapshot_download(
                    'Xorbits/bge-base-zh-v1.5',
                    cache_dir=str(Path.home() / '.cache' / 'modelscope'),
                    revision='master'
                )

                # 复制文件到目标目录
                import shutil
                if os.path.exists(model_dir):
                    for item in os.listdir(model_dir):
                        s = os.path.join(model_dir, item)
                        d = os.path.join(self.target_dir, item)
                        if os.path.isdir(s):
                            shutil.copytree(s, d, dirs_exist_ok=True)
                        else:
                            shutil.copy2(s, d)

                    logger.info('✅ ModelScope下载成功！')
                    return True

            except ImportError:
                logger.warning('⚠️ ModelScope SDK未安装，尝试手动下载...')

            # 手动下载
            return self.manual_download_from_modelscope()

        except Exception as e:
            logger.error(f"❌ ModelScope下载失败: {e}")
            return False

    def manual_download_from_modelscope(self) -> bool:
        """从ModelScope手动下载"""
        try:
            # 创建快照目录
            snapshot_dir = self.target_dir / 'snapshots' / 'main'
            snapshot_dir.mkdir(parents=True, exist_ok=True)

            # ModelScope文件URL模板
            base_url = 'https://modelscope.cn/api/v1/models/Xorbits/bge-base-zh-v1.5/repo/files'

            # 下载每个文件
            for file_name in BGE_MODEL_INFO['files']:
                url = f"{base_url}/{file_name}"
                target_path = snapshot_dir / file_name

                if self.download_file(url, target_path, file_name):
                    logger.info(f"✅ {file_name} 下载成功")
                else:
                    logger.error(f"❌ {file_name} 下载失败")
                    return False

            # 创建refs
            refs_dir = self.target_dir / 'refs' / 'main'
            refs_dir.mkdir(parents=True, exist_ok=True)

            return True

        except Exception as e:
            logger.error(f"❌ 手动下载失败: {e}")
            return False

    def try_hf_mirror_download(self) -> bool:
        """尝试从HF镜像下载"""
        logger.info('🔄 尝试从HF镜像下载...')

        try:
            # 设置镜像环境变量
            os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'

            # 使用huggingface-hub下载
            try:
                from huggingface_hub import snapshot_download

                model_dir = snapshot_download(
                    repo_id='BAAI/bge-base-zh-v1.5',
                    cache_dir=str(Path.home() / '.cache' / 'huggingface'),
                    local_files_only=False,
                    resume_download=True
                )

                logger.info('✅ HF镜像下载成功！')
                return True

            except ImportError:
                logger.warning('⚠️ huggingface-hub未安装')

            return False

        except Exception as e:
            logger.error(f"❌ HF镜像下载失败: {e}")
            return False

    def download_file(self, url: str, target_path: Path, file_name: str,
                     max_retries: int = 3) -> bool:
        """下载单个文件

        Args:
            url: 下载URL
            target_path: 目标路径
            file_name: 文件名
            max_retries: 最大重试次数

        Returns:
            是否下载成功
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"📥 下载 {file_name} (尝试 {attempt + 1}/{max_retries})")

                # 添加请求头
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                    'Accept': 'application/octet-stream'
                }

                # 流式下载
                response = requests.get(url, headers=headers, stream=True, timeout=30)
                response.raise_for_status()

                # 获取文件大小
                total_size = int(response.headers.get('content-length', 0))
                downloaded_size = 0

                # 写入文件
                with open(target_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded_size += len(chunk)

                            # 显示进度
                            if total_size > 0:
                                progress = (downloaded_size / total_size) * 100
                                print(f"\r   进度: {progress:.1f}%", end='', flush=True)

                print()  # 换行
                return True

            except Exception as e:
                logger.warning(f"⚠️ 下载失败 (尝试 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避

        return False

    def create_blobs_dir(self) -> bool:
        """创建blobs目录并移动文件"""
        try:
            blobs_dir = self.target_dir / 'blobs'
            blobs_dir.mkdir(exist_ok=True)

            snapshot_dir = self.target_dir / 'snapshots' / 'main'
            if not snapshot_dir.exists():
                logger.error('❌ 快照目录不存在')
                return False

            # 移动文件到blobs目录并创建符号链接
            import hashlib
            import shutil

            for file_name in BGE_MODEL_INFO['files']:
                source_path = snapshot_dir / file_name

                if source_path.exists():
                    # 计算文件hash作为blob名称
                    with open(source_path, 'rb') as f:
                        content = f.read()
                        file_hash = hashlib.sha256(content).hexdigest()

                    # 移动到blobs
                    blob_path = blobs_dir / file_hash
                    shutil.move(str(source_path), str(blob_path))

                    # 创建符号链接
                    link_path = snapshot_dir / file_name
                    link_path.symlink_to(f'../../blobs/{file_hash}')

                    logger.info(f"✅ {file_name} 已移动到blobs目录")

            return True

        except Exception as e:
            logger.error(f"❌ 创建blobs目录失败: {e}")
            return False

    def verify_download(self) -> bool:
        """验证下载完整性"""
        try:
            snapshot_dir = self.target_dir / 'snapshots' / 'main'

            missing_files = []
            for file_name in BGE_MODEL_INFO['files']:
                file_path = snapshot_dir / file_name
                if not file_path.exists():
                    missing_files.append(file_name)

            if missing_files:
                logger.error(f"❌ 缺少文件: {missing_files}")
                return False

            # 检查pytorch_model.bin大小
            model_bin = snapshot_dir / 'pytorch_model.bin'
            if model_bin.exists():
                size_mb = model_bin.stat().st_size / (1024 * 1024)
                if size_mb < 100:  # 应该大于100MB
                    logger.error(f"❌ pytorch_model.bin大小异常: {size_mb:.1f}MB")
                    return False
                else:
                    logger.info(f"✅ pytorch_model.bin大小正常: {size_mb:.1f}MB")

            logger.info('✅ 文件完整性验证通过')
            return True

        except Exception as e:
            logger.error(f"❌ 验证失败: {e}")
            return False

    def download(self) -> bool:
        """执行下载流程"""
        logger.info('🚀 开始下载BGE模型...')
        logger.info(f"📊 模型: {BGE_MODEL_INFO['name']}")
        logger.info(f"📦 预计大小: {BGE_MODEL_INFO['total_size']}")
        logger.info(f"📁 保存位置: {self.target_dir}")

        # 尝试不同的下载方式
        download_methods = [
            self.try_modelscope_download,
            self.try_hf_mirror_download
        ]

        for method in download_methods:
            try:
                if method():
                    # 下载成功，创建blobs目录
                    if self.create_blobs_dir():
                        # 验证下载
                        if self.verify_download():
                            logger.info('🎉 BGE模型下载完成！')
                            return True
                    else:
                        logger.warning('⚠️ blobs目录创建失败')

            except Exception as e:
                logger.error(f"❌ 下载方法失败: {e}")
                continue

        logger.error('❌ 所有下载方法都失败了')
        return False

def main():
    """主函数"""
    logger.info('🧠 BGE模型下载器 (国内镜像版)')
    logger.info(str('=' * 60))
    logger.info(f"📦 模型: {BGE_MODEL_INFO['name']}")
    logger.info(f"📊 大小: {BGE_MODEL_INFO['total_size']}")
    logger.info(f"🌐 镜像: ModelScope, HF-Mirror")
    logger.info(str('=' * 60))

    # 检查网络连接
    try:
        response = requests.get('https://modelscope.cn', timeout=5)
        logger.info('✅ 网络连接正常')
    except Exception as e:
        logger.error(f"❌ 网络连接失败: {e}")
        return False

    # 创建下载器并开始下载
    downloader = BGEModelDownloader()
    success = downloader.download()

    if success:
        logger.info("\n✅ 下载成功！")
        logger.info("\n📍 模型位置:")
        logger.info(f"   {downloader.target_dir}")
        logger.info("\n🚀 下一步:")
        logger.info('   1. 运行向量化测试')
        logger.info('   2. 开始专利数据向量化')
        logger.info('   3. 创建向量索引')
    else:
        logger.info("\n❌ 下载失败")
        logger.info("\n💡 建议:")
        logger.info('   1. 检查网络连接')
        logger.info('   2. 手动安装ModelScope: pip install modelscope')
        logger.info('   3. 稍后重试')

    return success

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)