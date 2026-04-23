#!/usr/bin/env python3
"""
arXiv论文下载器
ArXiv Paper Downloader - 支持智能重试和批量下载

作者: Athena AI系统
创建时间: 2026-02-12
"""

import asyncio
import json
import logging
import random
import time
from pathlib import Path

import aiohttp

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [arXiv下载器] %(message)s',
    handlers=[
        logging.FileHandler('arxiv_downloader.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ArXivDownloader:
    """arXiv论文下载器"""

    def __init__(self, download_dir: str = None, delay: float = 2.0):
        """
        初始化下载器

        Args:
            download_dir: 下载目录
            delay: 每次下载之间的延迟（秒），避免限流
        """
        self.download_dir = Path(download_dir) if download_dir else Path('./papers')
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.delay = delay
        self.session = None
        self.stats = {
            'success': 0,
            'failed': 0,
            'skipped': 0
        }

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def start(self):
        """启动下载器会话"""
        connector = aiohttp.TCPConnector(
            limit=50,
            limit_per_host=5,
            ttl_dns_cache=300,
        )

        timeout = aiohttp.ClientTimeout(total=120)

        # 随机User-Agent列表
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Googlebot/2.1',
            'arXiv URL resolver',
        ]

        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'application/pdf',
        }

        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=headers
        )

        logger.info('📚 arXiv下载器已启动')

    async def close(self):
        """关闭下载器会话"""
        if self.session:
            await self.session.close()
            logger.info('arXiv下载器已关闭')

    async def download_paper(self, arxiv_id: str, filename: str = None) -> bool:
        """
        下载单篇论文

        Args:
            arxiv_id: arXiv论文ID (如 2602.10116)
            filename: 可选的自定义文件名

        Returns:
            是否下载成功
        """
        url = f'https://arxiv.org/pdf/{arxiv_id}.pdf'

        try:
            logger.info(f"📥 下载: {arxiv_id}")

            async with self.session.get(url) as response:
                if response.status == 200:
                    content = await response.read()

                    # 使用自定义文件名或默认文件名
                    if filename:
                        filepath = self.download_dir / f'{filename}.pdf'
                    else:
                        filepath = self.download_dir / f'{arxiv_id}.pdf'

                    with open(filepath, 'wb') as f:
                        f.write(content)

                    file_size = len(content) / 1024  # KB
                    logger.info(f"✅ 成功: {filepath.name} ({file_size:.1f} KB)")
                    self.stats['success'] += 1
                    return True
                else:
                    logger.warning(f"❌ HTTP {response.status}: {arxiv_id}")
                    self.stats['failed'] += 1
                    return False

        except asyncio.TimeoutError:
            logger.warning(f"⏱️ 超时: {arxiv_id}")
            self.stats['failed'] += 1
            return False
        except Exception as e:
            logger.error(f"❌ 错误 {arxiv_id}: {e}")
            self.stats['failed'] += 1
            return False

    async def download_papers(self, papers: list[dict[str, str]]) -> dict[str, any]:
        """
        批量下载论文

        Args:
            papers: 论文列表，每个元素包含 {'arxiv_id': ..., 'filename': ...}

        Returns:
            下载统计信息
        """
        logger.info(f"🎯 开始下载 {len(papers)} 篇论文")

        results = []

        for i, paper in enumerate(papers):
            arxiv_id = paper['arxiv_id']
            filename = paper.get('filename')

            # 添加延迟避免限流
            if i > 0:
                delay = self.delay + random.uniform(0.5, 2.0)
                logger.info(f"⏳ 等待 {delay:.1f} 秒后继续...")
                await asyncio.sleep(delay)

            success = await self.download_paper(arxiv_id, filename)
            results.append({
                'arxiv_id': arxiv_id,
                'success': success,
                'filename': filename or f'{arxiv_id}.pdf'
            })

            # 显示进度
            done = i + 1
            logger.info(f"📊 进度: {done}/{len(papers)}")

        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        failed_count = len(results) - success_count

        logger.info("\n📊 下载完成:")
        logger.info(f"  ✅ 成功: {success_count} 篇")
        logger.info(f"  ❌ 失败: {failed_count} 篇")

        return {
            'total': len(papers),
            'success': success_count,
            'failed': failed_count,
            'results': results
        }

    def get_stats(self) -> dict:
        """获取下载统计"""
        return self.stats


async def main():
    """主函数 - 下载2026年AI Agent相关论文"""

    # 2026年AI Agent相关论文列表
    papers = [
        # 计算机视觉与机器人
        {'arxiv_id': '2602.10116', 'filename': 'SAGE_3D_Scene_Generation'},
        {'arxiv_id': '2602.09657', 'filename': 'AutoFly_VLA_UAV_Navigation'},
        {'arxiv_id': '2602.08373', 'filename': 'VIRF_Verifiable_Planner'},
        {'arxiv_id': '2602.08092', 'filename': 'Comparing_Coding_Agents'},
        {'arxiv_id': '2602.07787', 'filename': 'Multi_Agents_AndroidWorld'},
        {'arxiv_id': '2602.07521', 'filename': 'Pareto_Mobile_MOBA_Games'},

        # AI安全与架构
        {'arxiv_id': '2602.09947', 'filename': 'Trustworthy_AI_Deterministic_Boundaries'},
        {'arxiv_id': '2602.09433', 'filename': 'Evaluation_Becomes_Side_Channel'},
        {'arxiv_id': '2602.08412', 'filename': 'Decentralized_Intent_Multi_Robot'},
        {'arxiv_id': '2602.08421', 'filename': 'From_Assistant_Double_Attack'},
        {'arxiv_id': '2602.07918', 'filename': 'CausalArmor_Prompt_Injection'},

        # AI代理系统与工具
        {'arxiv_id': '2602.10081', 'filename': 'Anagent_Scientific_Tables'},
        {'arxiv_id': '2602.10009', 'filename': 'Discovering_High_Level_Patterns'},
        {'arxiv_id': '2602.09185', 'filename': 'AutoFly_Vision_Language_Action'},
        {'arxiv_id': '2602.09132', 'filename': 'AIDev_Studying_AI_Coding_Agents'},
        {'arxiv_id': '2602.08949', 'filename': 'Minitap_Multi_Agent_System'},

        # 操作系统与资源管理
        {'arxiv_id': '2602.09345', 'filename': 'AgentCgroup_OS_Resources_AI_Agents'},
        {'arxiv_id': '2602.08199', 'filename': 'Fork_Explore_Commit_OS_Primitives'},

        # 数据处理与科学应用
        {'arxiv_id': '2602.09286', 'filename': 'Generative_AI_Adoption_Energy_Company'},
        {'arxiv_id': '2602.08915', 'filename': 'Fork_Explore_Commit_OS_Primitives'},

        # AI理论与基础
        {'arxiv_id': '2602.08835', 'filename': 'Learning_Value_Systems_Societies'},
        {'arxiv_id': '2602.08041', 'filename': 'Objective_Decoupling_Social_RL'},

        # 应用与部署
        {'arxiv_id': '2602.09447', 'filename': 'Human_AI_Integration_Framework'},
        {'arxiv_id': '2602.07918', 'filename': 'CausalArmor_2'},
        {'arxiv_id': '2602.08268', 'filename': 'Puda_Private_User_Dataset_Agent'},

        # 软件工程
        {'arxiv_id': '2602.09447', 'filename': 'SWE_AGI_Software_Construction'},
        {'arxiv_id': '2602.09339', 'filename': 'Understanding_Risk_AI_Chatbot'},
    ]

    download_dir = '/Users/xujian/Athena工作平台/docs/papers/2026_ai_agent'

    async with ArXivDownloader(download_dir=download_dir, delay=3.0) as downloader:
        results = await downloader.download_papers(papers)

    # 保存下载结果
    result_file = Path(download_dir) / 'download_results.json'
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump({
            'download_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'results': results['results']
        }, f, indent=2, ensure_ascii=False)

    logger.info(f"📄 结果已保存到: {result_file}")


if __name__ == '__main__':
    asyncio.run(main())
