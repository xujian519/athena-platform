"""
情节记忆
Episodic Memory
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path


class EpisodicMemory:
    """情节记忆 - 存储事件序列"""

    def __init__(self, storage_path: Path | None = None, max_episodes: int = 1000):
        """
        初始化情节记忆

        Args:
            storage_path: 存储路径
            max_episodes: 最大情节数量(内存泄漏修复: 添加边界限制)
        """
        self.storage_path = storage_path or Path("/tmp/athena_episodic_memory")
        self.storage_path.mkdir(parents=True, exist_ok=True)

        # 内存泄漏修复: 配置化最大限制，默认1000条
        self.max_episodes = max_episodes

        self.episodes = []
        self._load_episodes()

        # 内存泄漏修复: 加载后立即检查并裁剪
        self._trim_episodes()

    def _load_episodes(self):
        """加载情节"""
        episodes_file = self.storage_path / "episodes.json"
        if episodes_file.exists():
            try:
                with open(episodes_file, encoding="utf-8") as f:
                    loaded_episodes = json.load(f)
                # 内存泄漏修复: 确保加载的数据不会超过限制
                self.episodes = loaded_episodes[-self.max_episodes:] if len(loaded_episodes) > self.max_episodes else loaded_episodes
            except (OSError, json.JSONDecodeError) as e:
                # 内存泄漏修复: 加载失败时初始化为空列表，不传播异常
                print(f"加载情节文件失败: {e}")
                self.episodes = []

    def _trim_episodes(self):
        """内存泄漏修复: 裁剪情节到最大限制"""
        if len(self.episodes) > self.max_episodes:
            removed_count = len(self.episodes) - self.max_episodes
            self.episodes = self.episodes[-self.max_episodes:]
            print(f"⚠️ 裁剪了 {removed_count} 条旧情节以维持内存限制")

    async def add_episode(self, event: str, context: dict | None = None) -> bool:
        """添加情节"""
        try:
            episode = {
                "event": event,
                "context": context or {},
                "timestamp": datetime.now().isoformat(),
                "embeddings": None,  # 可以后续添加向量嵌入
            }

            # 内存泄漏修复: 在添加前检查边界
            if len(self.episodes) >= self.max_episodes:
                # 移除最旧的一条
                self.episodes.pop(0)

            self.episodes.append(episode)

            self._save_episodes()
            return True
        except Exception as e:
            print(f"添加情节失败: {e}")
            raise

    async def recall_episodes(self, query: str, limit: int = 10) -> list[dict]:
        """回忆相关情节"""
        query_lower = query.lower()
        results = []

        for episode in reversed(self.episodes):
            if query_lower in episode["event"].lower():
                results.append(episode)
                if len(results) >= limit:
                    break

        return results

    def _save_episodes(self):
        """保存情节"""
        episodes_file = self.storage_path / "episodes.json"
        with open(episodes_file, "w", encoding="utf-8") as f:
            json.dump(self.episodes, f, ensure_ascii=False, indent=2)
