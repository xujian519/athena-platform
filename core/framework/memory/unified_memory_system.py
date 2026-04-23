"""
Athena统一记忆系统

参考优秀开源项目的记忆系统设计：
- AutoGen: RAG模式 + Zep长期记忆
- LangGraph: Checkpoint持久化 + 故障恢复
- CrewAI: 统一Memory类 + Markdown持久化

核心特性：
1. 两层架构（全局+项目）
2. 自动持久化
3. 向量检索（TODO）
4. 智能体共享
5. 版本控制友好
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)


class MemoryType(Enum):
    """记忆类型"""
    GLOBAL = "global"  # 全局记忆
    PROJECT = "project"  # 项目记忆


class MemoryCategory(Enum):
    """记忆分类"""
    USER_PREFERENCE = "user_preference"
    AGENT_LEARNING = "agent_learning"
    PROJECT_CONTEXT = "project_context"
    WORK_HISTORY = "work_history"
    AGENT_COLLABORATION = "agent_collaboration"
    TECHNICAL_FINDINGS = "technical_findings"
    LEGAL_ANALYSIS = "legal_analysis"


@dataclass
class MemoryEntry:
    """记忆条目

    Attributes:
        type: 记忆类型（全局/项目）
        category: 记忆分类
        key: 唯一键
        content: Markdown内容
        metadata: 元数据
        created_at: 创建时间
        updated_at: 更新时间
        embedding: 向量嵌入（可选）
    """
    type: MemoryType
    category: MemoryCategory
    key: str
    content: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    embedding: Optional[list[float]] = None


class UnifiedMemorySystem:
    """统一记忆系统

    核心功能：
    - 两层记忆架构（全局+项目）
    - 自动持久化到Markdown文件
    - 记忆索引管理
    - 工作历史记录
    - 简单关键词搜索（TODO: 向量检索）

    Example:
        >>> from core.framework.memory.unified_memory_system import get_global_memory
        >>> memory = get_global_memory()
        >>> memory.write(
        ...     type=MemoryType.GLOBAL,
        ...     category=MemoryCategory.USER_PREFERENCE,
        ...     key="user_preferences",
        ...     content="# 用户偏好\\n\\n代码风格：简体中文注释"
        ... )
    """

    def __init__(
        self,
        global_memory_path: str = "~/.athena/memory",
        current_project_path: Optional[str] = None
    ) -> None:
        """初始化记忆系统

        Args:
            global_memory_path: 全局记忆路径
            current_project_path: 当前项目路径（可选）
        """
        # 路径初始化
        self.global_memory_path = Path(global_memory_path).expanduser()
        self.current_project_path = (
            Path(current_project_path).expanduser()
            if current_project_path
            else None
        )

        # 创建目录
        self._create_directories()

        # 加载记忆索引
        self.memory_index: dict[str, dict] = self._load_memory_index()

        # 搜索缓存（优化性能）
        self._search_cache: dict[str, tuple[list[MemoryEntry], float]] = {}
        self._cache_ttl = 60.0  # 缓存60秒

        logger.info(
            f"记忆系统初始化完成 - 全局: {self.global_memory_path}, "
            f"项目: {self.current_project_path}"
        )

    def _create_directories(self) -> None:
        """创建必要的目录结构"""
        # 全局记忆目录
        self.global_memory_path.mkdir(parents=True, exist_ok=True)

        # 全局记忆子目录
        subdirs = [
            "agent_learning",
            "cross_project_knowledge",
        ]
        for subdir in subdirs:
            (self.global_memory_path / subdir).mkdir(exist_ok=True)

        # 项目记忆目录
        if self.current_project_path:
            project_athena_dir = self.current_project_path / ".athena"
            project_athena_dir.mkdir(parents=True, exist_ok=True)

            # 项目记忆子目录
            project_subdirs = [
                "project_knowledge",
                "checkpoints",
            ]
            for subdir in project_subdirs:
                (project_athena_dir / subdir).mkdir(exist_ok=True)

    def write(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str,
        content: str,
        metadata: Optional[dict[str, Any]] = None
    ) -> MemoryEntry:
        """写入记忆

        Args:
            type: 记忆类型（全局/项目）
            category: 记忆分类
            key: 唯一键
            content: Markdown内容
            metadata: 元数据

        Returns:
            创建的记忆条目

        Raises:
            ValueError: 项目记忆需要指定项目路径
            IOError: 文件写入失败
        """
        try:
            # 确定存储路径
            base_path = self._get_base_path(type)

            # 根据分类确定子目录
            subdirectory = self._get_subdirectory(category)
            target_path = base_path / subdirectory
            target_path.mkdir(parents=True, exist_ok=True)

            # 创建文件路径
            file_path = target_path / f"{key}.md"

            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # 创建记忆条目
            entry = MemoryEntry(
                type=type,
                category=category,
                key=key,
                content=content,
                metadata=metadata or {},
                created_at=datetime.now(),
                updated_at=datetime.now()
            )

            # 更新索引
            self._update_memory_index(entry)

            logger.info(
                f"记忆写入成功 - {type.value}/{category.value}/{key}"
            )

            return entry

        except Exception as e:
            logger.error(f"记忆写入失败: {e}")
            raise OSError(f"无法写入记忆: {e}") from e

    def read(
        self,
        type: MemoryType,
        category: MemoryCategory,
        key: str
    ) -> Optional[str]:
        """读取记忆

        Args:
            type: 记忆类型
            category: 记忆分类
            key: 唯一键

        Returns:
            Markdown内容，如果不存在则返回None
        """
        try:
            # 确定文件路径
            base_path = self._get_base_path(type)
            subdirectory = self._get_subdirectory(category)
            file_path = base_path / subdirectory / f"{key}.md"

            # 检查文件是否存在
            if not file_path.exists():
                logger.warning(
                    f"记忆文件不存在: {file_path}"
                )
                return None

            # 读取文件
            with open(file_path, encoding='utf-8') as f:
                content = f.read()

            logger.debug(
                f"记忆读取成功 - {type.value}/{category.value}/{key}"
            )

            return content

        except Exception as e:
            logger.error(f"记忆读取失败: {e}")
            return None

    def search(
        self,
        query: str,
        type: Optional[MemoryType] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 10,
        use_cache: bool = True
    ) -> list[MemoryEntry]:
        """搜索记忆

        Args:
            query: 搜索查询
            type: 记忆类型过滤（可选）
            category: 记忆分类过滤（可选）
            limit: 返回数量限制
            use_cache: 是否使用缓存（默认True）

        Returns:
            匹配的记忆条目列表

        Note:
            当前使用简单的关键词匹配
            TODO: 实现向量检索
        """
        import time

        # 生成缓存键
        cache_key = f"{query}:{type}:{category}:{limit}"

        # 检查缓存
        if use_cache:
            cached_result, cache_time = self._search_cache.get(cache_key, ([], 0))
            if time.time() - cache_time < self._cache_ttl:
                logger.debug(f"搜索命中缓存 - 查询: {query}")
                return cached_result

        results: list[MemoryEntry] = []

        try:
            # 遍历索引
            for _, entry_data in self.memory_index.items():
                # 应用过滤器
                if type and entry_data.get('type') != type.value:
                    continue
                if category and entry_data.get('category') != category.value:
                    continue

                # 关键词匹配（不区分大小写）
                content = entry_data.get('content', '')
                if query.lower() in content.lower():
                    # 重建MemoryEntry对象
                    entry = MemoryEntry(
                        type=MemoryType(entry_data['type']),
                        category=MemoryCategory(entry_data['category']),
                        key=entry_data['key'],
                        content=entry_data['content'],
                        metadata=entry_data.get('metadata', {}),
                        created_at=datetime.fromisoformat(
                            entry_data['created_at']
                        ),
                        updated_at=datetime.fromisoformat(
                            entry_data['updated_at']
                        )
                    )
                    results.append(entry)

            # 限制结果数量
            results = results[:limit]

            # 更新缓存
            if use_cache:
                self._search_cache[cache_key] = (results, time.time())

            logger.info(
                f"搜索完成 - 查询: {query}, 结果数: {len(results)}"
            )

            return results

        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []

    def append_work_history(
        self,
        agent_name: str,
        task: str,
        result: str,
        status: str = "success"
    ) -> None:
        """追加工作历史

        Args:
            agent_name: 智能体名称
            task: 任务描述
            result: 任务结果
            status: 任务状态（success/failed/pending）

        Raises:
            ValueError: 项目记忆需要指定项目路径
        """
        if not self.current_project_path:
            raise ValueError("工作历史需要指定项目路径")

        try:
            # 读取现有工作历史
            history_content = self.read(
                MemoryType.PROJECT,
                MemoryCategory.WORK_HISTORY,
                "work_history"
            )

            # 如果不存在，初始化
            if not history_content:
                project_name = self.current_project_path.name
                today = datetime.now().strftime('%Y-%m-%d')
                history_content = (
                    f"# 工作历史\n\n"
                    f"> **项目**: {project_name}\n"
                    f"> **时间范围**: {today} 至今\n\n"
                )

            # 追加新条目
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
            today_str = datetime.now().strftime('%Y-%m-%d')

            # 检查是否已经有今天的日期标题
            if f"## {today_str}" not in history_content:
                new_entry = f"\n## {today_str}\n\n### {timestamp} - {task}\n"
            else:
                new_entry = f"\n### {timestamp} - {task}\n"

            new_entry += (
                f"- **智能体**: {agent_name}\n"
                f"- **任务**: {task}\n"
                f"- **状态**: {status}\n"
                f"- **结果**: {result}\n"
            )

            # 写入
            self.write(
                MemoryType.PROJECT,
                MemoryCategory.WORK_HISTORY,
                "work_history",
                history_content + new_entry,
                metadata={
                    "agent_name": agent_name,
                    "timestamp": timestamp,
                    "status": status
                }
            )

            logger.info(
                f"工作历史追加成功 - {agent_name}: {task}"
            )

        except Exception as e:
            logger.error(f"工作历史追加失败: {e}")
            raise

    def _get_base_path(self, type: MemoryType) -> Path:
        """获取基础路径

        Args:
            type: 记忆类型

        Returns:
            基础路径

        Raises:
            ValueError: 项目记忆需要指定项目路径
        """
        if type == MemoryType.GLOBAL:
            return self.global_memory_path
        else:
            if not self.current_project_path:
                raise ValueError("项目记忆需要指定项目路径")
            return self.current_project_path / ".athena"

    def _get_subdirectory(self, category: MemoryCategory) -> str:
        """获取子目录名称

        Args:
            category: 记忆分类

        Returns:
            子目录名称
        """
        # 全局记忆分类
        global_categories = {
            MemoryCategory.USER_PREFERENCE: "",
            MemoryCategory.AGENT_LEARNING: "agent_learning",
        }

        # 项目记忆分类
        project_categories = {
            MemoryCategory.PROJECT_CONTEXT: "",
            MemoryCategory.WORK_HISTORY: "",
            MemoryCategory.AGENT_COLLABORATION: "",
            MemoryCategory.TECHNICAL_FINDINGS: "project_knowledge",
            MemoryCategory.LEGAL_ANALYSIS: "project_knowledge",
        }

        # 合并分类映射
        category_map = {**global_categories, **project_categories}

        return category_map.get(
            category,
            category.value
        )

    def _load_memory_index(self) -> dict[str, dict]:
        """加载记忆索引

        Returns:
            记忆索引字典
        """
        index_file = self.global_memory_path / "memory_index.json"

        if not index_file.exists():
            logger.info("记忆索引不存在，创建新索引")
            return {}

        try:
            with open(index_file, encoding='utf-8') as f:
                index = json.load(f)

            logger.info(f"记忆索引加载成功 - {len(index)} 条记录")

            return index

        except Exception as e:
            logger.error(f"记忆索引加载失败: {e}")
            return {}

    def _update_memory_index(self, entry: MemoryEntry) -> None:
        """更新记忆索引

        Args:
            entry: 记忆条目
        """
        try:
            # 转换为字典（索引只保存前500字符）
            entry_dict = {
                'type': entry.type.value,
                'category': entry.category.value,
                'key': entry.key,
                'content': entry.content[:500],
                'metadata': entry.metadata,
                'created_at': entry.created_at.isoformat(),
                'updated_at': entry.updated_at.isoformat()
            }

            # 生成唯一键
            unique_key = (
                f"{entry.type.value}/"
                f"{entry.category.value}/"
                f"{entry.key}"
            )

            # 更新索引
            self.memory_index[unique_key] = entry_dict

            # 保存索引
            index_file = self.global_memory_path / "memory_index.json"
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(
                    self.memory_index,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            logger.debug(f"记忆索引更新成功 - {unique_key}")

        except Exception as e:
            logger.error(f"记忆索引更新失败: {e}")


# 便捷函数
def get_global_memory(
    global_memory_path: str = "~/.athena/memory"
) -> UnifiedMemorySystem:
    """获取全局记忆系统

    Args:
        global_memory_path: 全局记忆路径

    Returns:
        统一记忆系统实例

    Example:
        >>> memory = get_global_memory()
        >>> content = memory.read(
        ...     MemoryType.GLOBAL,
        ...     MemoryCategory.USER_PREFERENCE,
        ...     "user_preferences"
        ... )
    """
    return UnifiedMemorySystem(global_memory_path=global_memory_path)


def get_project_memory(
    project_path: str,
    global_memory_path: str = "~/.athena/memory"
) -> UnifiedMemorySystem:
    """获取项目记忆系统

    Args:
        project_path: 项目路径
        global_memory_path: 全局记忆路径

    Returns:
        统一记忆系统实例

    Example:
        >>> memory = get_project_memory("/Users/xujian/Athena工作平台")
        >>> memory.append_work_history(
        ...     agent_name="xiaonuo",
        ...     task="分析专利",
        ...     result="完成分析",
        ...     status="success"
        ... )
    """
    return UnifiedMemorySystem(
        global_memory_path=global_memory_path,
        current_project_path=project_path
    )

