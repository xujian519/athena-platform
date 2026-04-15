#!/usr/bin/env python3
"""
统一提示词加载器 - 生产环境 v2.5.0
支持多智能体、版本管理、智能缓存、精细化加载
"""

from __future__ import annotations
import hashlib
import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from threading import RLock
from typing import Any


@dataclass
class PromptMetadata:
    """提示词元数据"""
    name: str
    path: str
    size: int = 0
    hash: str = ""
    last_modified: float = 0
    load_count: int = 0
    total_load_time: float = 0

    @property
    def avg_load_time(self) -> float:
        """平均加载时间"""
        return self.total_load_time / self.load_count if self.load_count > 0 else 0


@dataclass
class CacheEntry:
    """缓存条目"""
    content: str
    metadata: PromptMetadata
    created_at: float
    ttl: int = 3600

    def is_expired(self) -> bool:
        """是否过期"""
        return time.time() - self.created_at > self.ttl

    def update_ttl(self, new_ttl: int) -> None:
        """更新TTL"""
        self.ttl = new_ttl


class PromptValidator:
    """提示词质量验证器"""

    @staticmethod
    def validate_format(content: str) -> tuple[bool, list[str]]:
        """
        验证提示词格式

        Returns:
            (是否有效, 错误列表)
        """
        errors = []

        # 检查是否为空
        if not content or not content.strip():
            errors.append("内容为空")
            return False, errors

        # 检查Markdown格式
        lines = content.split('\n')
        if lines and not lines[0].startswith('#'):
            errors.append("缺少标题（应以#开头）")

        # 检查字符长度
        if len(content) < 100:
            errors.append(f"内容过短（{len(content)}字符），建议至少100字符")

        # 检查编码问题
        try:
            content.encode('utf-8')
        except UnicodeEncodeError:
            errors.append("包含非UTF-8字符")

        return len(errors) == 0, errors

    @staticmethod
    def validate_consistency(l1: str, l2: str, l3: str, l4: str) -> list[str]:
        """
        验证跨层一致性

        Returns:
            问题列表
        """
        issues = []

        # 检查版本一致性
        def extract_version(content: str) -> str | None:
            for line in content.split('\n')[:10]:
                if 'version' in line.lower() or '版本' in line:
                    return line.strip()
            return None

        versions = []
        for name, content in [("L1", l1), ("L2", l2), ("L3", l3), ("L4", l4)]:
            ver = extract_version(content)
            if ver:
                versions.append(f"{name}:{ver}")

        if len(set(versions)) > 1:
            issues.append(f"版本不一致: {versions}")

        return issues

    @staticmethod
    def estimate_tokens(content: str) -> int:
        """
        估算Token数量（粗略估算：1 Token ≈ 3 字符）
        """
        return len(content) // 3


class PromptUsageMonitor:
    """提示词使用监控器"""

    def __init__(self, max_records: int = 1000):
        self.max_records = max_records
        self.records: list[dict] = []
        self._lock = RLock()

    def record_usage(self,
                    agent: str,
                    prompt_key: str,
                    tokens: int,
                    duration: float,
                    success: bool = True):
        """
        记录使用情况

        Args:
            agent: 智能体名称
            prompt_key: 提示词键
            tokens: Token数量
            duration: 加载耗时（秒）
            success: 是否成功
        """
        with self._lock:
            record = {
                "timestamp": time.time(),
                "agent": agent,
                "prompt_key": prompt_key,
                "tokens": tokens,
                "duration": duration,
                "success": success
            }
            self.records.append(record)

            # 限制记录数量
            if len(self.records) > self.max_records:
                self.records = self.records[-self.max_records:]

    def get_statistics(self, agent: str = None, hours: int = 24) -> dict:
        """
        获取使用统计

        Args:
            agent: 智能体名称（None表示全部）
            hours: 统计时间窗口（小时）

        Returns:
            统计信息字典
        """
        with self._lock:
            cutoff = time.time() - hours * 3600
            filtered = [r for r in self.records if r["timestamp"] > cutoff]

            if agent:
                filtered = [r for r in filtered if r["agent"] == agent]

            if not filtered:
                return {
                    "total_calls": 0,
                    "total_tokens": 0,
                    "avg_duration": 0,
                    "success_rate": 0,
                    "top_prompts": []
                }

            total_calls = len(filtered)
            total_tokens = sum(r["tokens"] for r in filtered)
            avg_duration = sum(r["duration"] for r in filtered) / total_calls
            success_count = sum(1 for r in filtered if r["success"])
            success_rate = success_count / total_calls

            # Top提示词统计
            prompt_counts = {}
            for r in filtered:
                key = r["prompt_key"]
                prompt_counts[key] = prompt_counts.get(key, 0) + 1

            top_prompts = sorted(prompt_counts.items(),
                               key=lambda x: x[1],
                               reverse=True)[:5]

            return {
                "total_calls": total_calls,
                "total_tokens": total_tokens,
                "avg_duration": avg_duration,
                "success_rate": success_rate,
                "top_prompts": top_prompts
            }

    def generate_report(self, agent: str = None) -> str:
        """生成使用报告"""
        stats = self.get_statistics(agent)

        lines = [
            "=" * 60,
            "📊 提示词使用监控报告",
            f"智能体: {agent or '全部'}",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
            "📈 调用统计:",
            f"  - 总调用次数: {stats['total_calls']:,}",
            f"  - 总Token数: {stats['total_tokens']:,}",
            f"  - 平均耗时: {stats['avg_duration']*1000:.2f}ms",
            f"  - 成功率: {stats['success_rate']*100:.1f}%",
            "",
            "🔥 热门提示词 TOP5:",
        ]

        for i, (prompt_key, count) in enumerate(stats['top_prompts'], 1):
            lines.append(f"  {i}. {prompt_key}: {count}次")

        lines.append("=" * 60)

        return "\n".join(lines)


class PromptCacheManager:
    """提示词缓存管理器"""

    def __init__(self, ttl: int = 3600, max_size: int = 100):
        """
        Args:
            ttl: 缓存过期时间（秒）
            max_size: 最大缓存条目数
        """
        self.ttl = ttl
        self.max_size = max_size
        self.memory_cache: dict[str, CacheEntry] = {}
        self._lock = RLock()

    def get(self, key: str) -> str | None:
        """获取缓存"""
        with self._lock:
            entry = self.memory_cache.get(key)
            if entry is None:
                return None

            if entry.is_expired():
                del self.memory_cache[key]
                return None

            # 更新元数据
            entry.metadata.load_count += 1
            return entry.content

    def set(self, key: str, content: str, metadata: PromptMetadata) -> Any:
        """设置缓存"""
        with self._lock:
            # LRU淘汰
            if len(self.memory_cache) >= self.max_size:
                # 删除最旧的条目
                oldest_key = min(self.memory_cache.keys(),
                               key=lambda k: self.memory_cache[k].created_at)
                del self.memory_cache[oldest_key]

            entry = CacheEntry(
                content=content,
                metadata=metadata,
                created_at=time.time(),
                ttl=self.ttl
            )
            self.memory_cache[key] = entry

    def invalidate(self, key: str = None) -> Any:
        """失效缓存"""
        with self._lock:
            if key:
                self.memory_cache.pop(key, None)
            else:
                self.memory_cache.clear()

    def get_stats(self) -> dict:
        """获取缓存统计"""
        with self._lock:
            total_size = sum(len(e.content) for e in self.memory_cache.values())
            return {
                "entries": len(self.memory_cache),
                "total_bytes": total_size,
                "hit_rate": 0.0  # 需要额外跟踪miss次数
            }


class UnifiedPromptLoader:
    """
    统一提示词加载器

    特性:
    - 支持多智能体（xiaona/xiaonuo/xiaochen）
    - 自动版本检测和切换
    - 智能缓存管理
    - 懒加载和按需加载
    - 质量验证
    - 使用监控
    """

    # 单例模式
    _instance = None
    _lock = RLock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self,
                 base_path: str = None,
                 agent: str = "xiaona",
                 version: str = "latest",
                 use_cache: bool = True,
                 cache_ttl: int = 3600,
                 lazy_loading: bool = True,
                 validation: bool = True,
                 monitoring: bool = True):
        """
        Args:
            base_path: 提示词根目录
            agent: 智能体名称 (xiaona/xiaonuo/xiaochen)
            version: 版本号 (latest/auto/具体版本号)
            use_cache: 是否使用缓存
            cache_ttl: 缓存TTL（秒）
            lazy_loading: 是否懒加载
            validation: 是否验证质量
            monitoring: 是否启用监控
        """
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        self.base_path = Path(base_path or "/Users/xujian/Athena工作平台/prompts")
        self.agent = agent.lower()
        self.version = version
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.lazy_loading = lazy_loading
        self.validation = validation
        self.monitoring = monitoring

        # 核心组件
        self.cache_manager = PromptCacheManager(ttl=cache_ttl) if use_cache else None
        self.usage_monitor = PromptUsageMonitor() if monitoring else None
        self.validator = PromptValidator()

        # 存储已加载的提示词
        self.loaded_prompts: dict[str, tuple[str, PromptMetadata]] = {}
        self._load_lock = RLock()

        # 版本配置
        self.version_config = self._load_version_config()

        # 解析实际使用的版本
        self.actual_version = self._resolve_version()

        # 标记初始化完成
        self._initialized = True

        # 预加载（如果不使用懒加载）
        if not lazy_loading:
            self.load_all_prompts()

    def _load_version_config(self) -> dict:
        """加载版本配置文件"""
        config_path = self.base_path / "VERSION.json"

        if not config_path.exists():
            print(f"⚠️  版本配置文件不存在: {config_path}")
            return {"current": {}, "settings": {}}

        try:
            with open(config_path, encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ 加载版本配置: {config_path}")
            return config
        except Exception as e:
            print(f"❌ 加载版本配置失败: {e}")
            return {"current": {}, "settings": {}}

    def _resolve_version(self) -> dict:
        """解析实际使用的版本配置"""
        if self.version == "latest":
            version_key = self.version_config.get("version", "v2.5.0")
        else:
            version_key = self.version

        agent_config = self.version_config.get("current", {}).get(self.agent, {})

        if not agent_config:
            print(f"⚠️  未找到智能体 '{self.agent}' 的配置，使用默认配置")
            return {}

        return agent_config

    def _get_file_path(self, key: str) -> Path | None:
        """获取文件路径"""
        path_str = self.actual_version.get(key)
        if not path_str:
            return None

        full_path = self.base_path / path_str
        return full_path if full_path.exists() else None

    def _compute_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.md5(content.encode('utf-8'), usedforsecurity=False).hexdigest()[:16]

    def _read_file(self, path: Path, name: str) -> tuple[str | None, PromptMetadata]:
        """
        读取文件

        Returns:
            (内容, 元数据)
        """
        start_time = time.time()

        try:
            with open(path, encoding='utf-8') as f:
                content = f.read()

            duration = time.time() - start_time
            metadata = PromptMetadata(
                name=name,
                path=str(path),
                size=len(content),
                hash=self._compute_hash(content),
                last_modified=path.stat().st_mtime,
                load_count=1,
                total_load_time=duration
            )

            # 验证质量
            if self.validation:
                is_valid, errors = self.validator.validate_format(content)
                if not is_valid:
                    print(f"⚠️  {name} 质量检查失败: {errors}")

            return content, metadata

        except Exception as e:
            print(f"❌ 读取文件失败 {path}: {e}")
            if self.usage_monitor:
                self.usage_monitor.record_usage(self.agent, name, 0,
                                              time.time() - start_time, False)
            return None, PromptMetadata(name=name, path=str(path))

    def _load_prompt(self, key: str, name: str) -> str | None:
        """
        加载单个提示词（内部方法）

        Args:
            key: 配置键（如 l1, l2_overview等）
            name: 提示词名称（用于日志）

        Returns:
            提示词内容
        """
        # 检查是否已加载
        if key in self.loaded_prompts:
            content, metadata = self.loaded_prompts[key]
            metadata.load_count += 1
            return content

        # 检查缓存
        if self.cache_manager:
            cached = self.cache_manager.get(f"{self.agent}:{key}")
            if cached is not None:
                print(f"  🎯 {name} (缓存)")
                return cached

        # 读取文件
        path = self._get_file_path(key)
        if path is None:
            print(f"  ⚠️  {name} (文件未找到: {key})")
            return None

        content, metadata = self._read_file(path, name)
        if content is None:
            return None

        # 存储到内存
        self.loaded_prompts[key] = (content, metadata)

        # 存储到缓存
        if self.cache_manager:
            self.cache_manager.set(f"{self.agent}:{key}", content, metadata)

        # 记录使用
        if self.usage_monitor:
            tokens = self.validator.estimate_tokens(content)
            self.usage_monitor.record_usage(self.agent, name, tokens,
                                          metadata.total_load_time)

        print(f"  ✅ {name} ({len(content):,} 字符)")

        return content

    def load_layer(self, layer: str) -> str | None:
        """
        加载指定层

        Args:
            layer: 层名 (l1/l2_overview/l2_search/l3/l4/hitl)

        Returns:
            提示词内容
        """
        layer_names = {
            "l1": "L1基础层",
            "l2_overview": "L2数据层-总览",
            "l2_search": "L2数据层-搜索",
            "l2_database": "L2数据层-数据库",
            "l2_graph": "L2数据层-知识图谱",
            "l2_vectors": "L2数据层-向量",
            "l3": "L3能力层",
            "l4": "L4业务层",
            "hitl": "HITL协议"
        }

        name = layer_names.get(layer, layer)
        return self._load_prompt(layer, name)

    def load_capability(self, cap_num: int) -> str | None:
        """
        加载指定能力（CAP01-CAP10）

        Args:
            cap_num: 能力编号 (1-10)

        Returns:
            能力提示词内容
        """
        key = f"cap{cap_num:02d}"
        path = self.base_path / f"capability/{key}.md"

        if not path.exists():
            print(f"  ⚠️  能力文件不存在: {path}")
            return None

        name = f"CAP{cap_num:02d}能力"
        return self._load_prompt(key, name)

    def load_business_task(self, task_id: str) -> str | None:
        """
        加载指定业务任务

        Args:
            task_id: 任务ID (如 task_1_1, task_2_1等)

        Returns:
            任务提示词内容
        """
        path = self.base_path / f"business/{task_id}.md"

        if not path.exists():
            print(f"  ⚠️  业务任务不存在: {path}")
            return None

        name = f"业务任务-{task_id}"
        return self._load_prompt(task_id, name)

    def load_all_prompts(self) -> dict[str, str]:
        """
        加载所有提示词

        Returns:
            {layer_key: content} 字典
        """
        print(f"📚 开始加载 {self.agent} 提示词系统 (版本: {self.version})...")

        result = {}

        # 加载L1基础层
        l1 = self.load_layer("l1")
        if l1:
            result["l1"] = l1

        # 加载L2数据层
        for l2_key in ["l2_overview", "l2_search", "l2_database", "l2_graph", "l2_vectors"]:
            content = self.load_layer(l2_key)
            if content:
                result[l2_key] = content

        # 加载L3能力层
        l3 = self.load_layer("l3")
        if l3:
            result["l3"] = l3

        # 加载L4业务层
        l4 = self.load_layer("l4")
        if l4:
            result["l4"] = l4

        # 加载HITL协议
        hitl = self.load_layer("hitl")
        if hitl:
            result["hitl"] = hitl

        print(f"✅ 提示词加载完成！共加载 {len(result)} 个模块")

        return result

    def load_by_task_type(self, task_type: str) -> str:
        """
        按任务类型加载提示词（精细化L4加载）

        Args:
            task_type: 任务类型
                - "general": 通用（全量加载）
                - "patent_writing": 专利撰写（只加载相关任务）
                - "office_action": 意见答复（只加载相关任务）

        Returns:
            完整提示词
        """
        parts = []

        # L1基础层（必需）
        l1 = self.load_layer("l1")
        if l1:
            parts.append(l1)

        # L2数据层（必需）
        l2_overview = self.load_layer("l2_overview")
        if l2_overview:
            parts.append(l2_overview)

        l2_search = self.load_layer("l2_search")
        if l2_search:
            parts.append(l2_search)

        # L3能力层（必需）
        l3 = self.load_layer("l3")
        if l3:
            parts.append(l3)

        # L4业务层（按需加载）
        if task_type == "patent_writing":
            # 加载专利撰写相关任务
            task_ids = ["task_1_1", "task_1_2", "task_1_3", "task_1_4", "task_1_5"]
            task_contents = []
            for task_id in task_ids:
                content = self.load_business_task(task_id)
                if content:
                    task_contents.append(content)

            if task_contents:
                parts.append("\n\n".join(task_contents))

        elif task_type == "office_action":
            # 加载意见答复相关任务
            task_ids = ["task_2_1", "task_2_2", "task_2_3", "task_2_4"]
            task_contents = []
            for task_id in task_ids:
                content = self.load_business_task(task_id)
                if content:
                    task_contents.append(content)

            if task_contents:
                parts.append("\n\n".join(task_contents))

        else:
            # 通用：加载完整L4
            l4 = self.load_layer("l4")
            if l4:
                parts.append(l4)

        # HITL协议（必需）
        hitl = self.load_layer("hitl")
        if hitl:
            parts.append(hitl)

        full_prompt = "\n\n---\n\n".join(parts)

        print(f"📝 生成提示词 (任务类型: {task_type})")
        print(f"   总长度: {len(full_prompt):,} 字符")
        print(f"   估算Token: {self.validator.estimate_tokens(full_prompt):,}")

        return full_prompt

    def get_full_prompt(self, task_type: str = "general") -> str:
        """
        获取完整提示词（兼容接口）

        Args:
            task_type: 任务类型

        Returns:
            完整提示词
        """
        return self.load_by_task_type(task_type)

    def get_prompt(self, layer: str) -> str:
        """
        获取指定层提示词（兼容接口）

        Args:
            layer: 层名

        Returns:
            提示词内容
        """
        content = self.load_layer(layer)
        return content if content else ""

    def validate_all(self) -> tuple[bool, list[str]]:
        """
        验证所有已加载的提示词

        Returns:
            (是否全部有效, 问题列表)
        """
        all_valid = True
        all_issues = []

        for key, (content, _) in self.loaded_prompts.items():
            is_valid, errors = self.validator.validate_format(content)
            if not is_valid:
                all_valid = False
                all_issues.extend([f"{key}: {err}" for err in errors])

        return all_valid, all_issues

    def get_cache_stats(self) -> dict:
        """获取缓存统计"""
        if self.cache_manager:
            return self.cache_manager.get_stats()
        return {"entries": 0, "total_bytes": 0}

    def get_usage_stats(self, hours: int = 24) -> dict:
        """获取使用统计"""
        if self.usage_monitor:
            return self.usage_monitor.get_statistics(self.agent, hours)
        return {}

    def generate_usage_report(self) -> str:
        """生成使用报告"""
        if self.usage_monitor:
            return self.usage_monitor.generate_report(self.agent)
        return "监控未启用"

    def clear_cache(self, key: str = None) -> None:
        """清除缓存"""
        if self.cache_manager:
            self.cache_manager.invalidate(key)
            print(f"🗑️  缓存已清除: {key or '全部'}")

    def reload(self, key: str = None) -> Any:
        """
        重新加载提示词

        Args:
            key: 指定键（None表示全部重新加载）
        """
        if key:
            # 清除指定缓存
            if key in self.loaded_prompts:
                del self.loaded_prompts[key]
            self.clear_cache(f"{self.agent}:{key}")
            print(f"🔄 重新加载: {key}")
        else:
            # 清除所有缓存
            self.loaded_prompts.clear()
            self.clear_cache()
            print("🔄 重新加载全部提示词")

            # 重新加载
            self.load_all_prompts()

    def get_metadata(self, key: str) -> PromptMetadata | None:
        """获取提示词元数据"""
        if key in self.loaded_prompts:
            return self.loaded_prompts[key][1]
        return None

    def list_loaded_prompts(self) -> list[str]:
        """列出已加载的提示词"""
        return list(self.loaded_prompts.keys())

    def get_summary(self) -> dict:
        """获取加载摘要"""
        total_size = sum(meta.size for _, meta in self.loaded_prompts.values())
        total_tokens = sum(self.validator.estimate_tokens(content)
                          for content, _ in self.loaded_prompts.values())

        return {
            "agent": self.agent,
            "version": self.version,
            "loaded_count": len(self.loaded_prompts),
            "total_size": total_size,
            "total_tokens": total_tokens,
            "cache_enabled": self.use_cache,
            "cache_stats": self.get_cache_stats(),
            "monitoring_enabled": self.monitoring
        }


# 便捷函数
def get_prompt_loader(agent: str = "xiaona",
                     version: str = "latest",
                     **kwargs) -> UnifiedPromptLoader:
    """
    获取提示词加载器实例

    Args:
        agent: 智能体名称
        version: 版本号
        **kwargs: 其他参数

    Returns:
        UnifiedPromptLoader实例
    """
    return UnifiedPromptLoader(agent=agent, version=version, **kwargs)


def main() -> None:
    """测试统一加载器"""
    print("=" * 60)
    print("🧪 测试统一提示词加载器")
    print("=" * 60)

    # 创建加载器
    loader = get_prompt_loader(agent="xiaona", version="latest")

    # 测试1: 加载所有提示词
    print("\n📋 测试1: 加载所有提示词")
    all_prompts = loader.load_all_prompts()
    print(f"   加载模块数: {len(all_prompts)}")

    # 测试2: 按任务类型加载
    print("\n📋 测试2: 按任务类型加载")
    patent_prompt = loader.load_by_task_type("patent_writing")
    print(f"   专利撰写提示词长度: {len(patent_prompt):,} 字符")

    # 测试3: 获取摘要
    print("\n📋 测试3: 获取摘要")
    summary = loader.get_summary()
    print(f"   智能体: {summary['agent']}")
    print(f"   版本: {summary['version']}")
    print(f"   加载数量: {summary['loaded_count']}")
    print(f"   总大小: {summary['total_size']:,} 字符")
    print(f"   总Token: {summary['total_tokens']:,}")

    # 测试4: 使用报告
    print("\n📋 测试4: 使用报告")
    report = loader.generate_usage_report()
    print(report)

    print("\n✅ 测试完成！")


if __name__ == "__main__":
    main()
