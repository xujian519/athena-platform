#!/usr/bin/env python3
"""
统一提示词加载器 - 生产环境 v3.0.0
集成渐进式加载、语义缓存、智能压缩

特性：
1. 渐进式加载 - 初始只加载最小上下文
2. 语义缓存 - 避免重复加载
3. 智能压缩 - 保留核心指令
4. 向后兼容 - 支持旧版API

作者: 小诺·双鱼公主
版本: v3.0.0
"""

from __future__ import annotations
import hashlib
import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Any

# 配置日志
logger = logging.getLogger(__name__)


# ==================== 枚举和数据类 ====================

class TaskType(Enum):
    """任务类型"""
    GENERAL = "general"
    PATENT_WRITING = "patent_writing"
    OFFICE_ACTION = "office_action"
    INVALIDITY = "invalidity"
    PRIOR_ART_SEARCH = "prior_art_search"
    CLAIMS_ANALYSIS = "claims_analysis"


class ComplexityLevel(Enum):
    """复杂度级别"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class LoadMode(Enum):
    """加载模式"""
    FULL = "full"              # 完整加载（旧版兼容）
    PROGRESSIVE = "progressive" # 渐进式加载（推荐）
    MINIMAL = "minimal"        # 仅最小上下文


@dataclass
class PromptConfig:
    """提示词配置"""
    load_mode: LoadMode = LoadMode.PROGRESSIVE
    compression_ratio: float = 0.4
    cache_ttl: int = 3600
    cache_dir: str | None = None
    enable_compression: bool = True
    enable_cache: bool = True
    verbose: bool = False


@dataclass
class PromptSegment:
    """提示词片段"""
    name: str
    content: str
    layer: str
    token_count: int
    compressed: bool = False


@dataclass
class LoadedPrompt:
    """已加载的提示词"""
    segments: list[PromptSegment]
    total_tokens: int
    total_chars: int
    load_time_ms: float
    cache_hit: bool
    compressed: bool
    config: PromptConfig

    def get_content(self) -> str:
        """获取完整内容"""
        return '\n\n---\n\n'.join(s.content for s in self.segments)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            "total_tokens": self.total_tokens,
            "total_chars": self.total_chars,
            "load_time_ms": self.load_time_ms,
            "cache_hit": self.cache_hit,
            "compressed": self.compressed,
            "segments": [
                {"name": s.name, "layer": s.layer, "tokens": s.token_count}
                for s in self.segments
            ],
        }


# ==================== 压缩器 ====================

class PromptCompressor:
    """提示词压缩器"""

    KEEP_PATTERNS = [
        r'^#+\s+',      # 标题
        r'^-\s+',       # 列表项
        r'^\d+\.\s+',   # 有序列表
        r'^\*\*',       # 加粗
        r'^【',         # 中文标注
    ]

    def compress(self, content: str, ratio: float = 0.4) -> str:
        """压缩提示词"""
        import re

        lines = content.split('\n')
        compressed = []
        prev_empty = False

        for line in lines:
            # 跳过装饰性内容
            if re.match(r'^---+$', line):
                continue

            # 压缩连续空行
            if not line.strip():
                if prev_empty:
                    continue
                prev_empty = True
            else:
                prev_empty = False

            compressed.append(line)

        result = '\n'.join(compressed)

        # 如果仍然太长，进一步压缩
        target_len = int(len(content) * ratio)
        if len(result) > target_len:
            result = self._extract_core_instructions(result, target_len)

        return result

    def _extract_core_instructions(self, content: str, target_len: int) -> str:
        """提取核心指令"""
        import re

        lines = content.split('\n')
        core_lines = []
        current_section = []
        in_code_block = False

        for line in lines:
            if line.startswith('```'):
                in_code_block = not in_code_block
                current_section.append(line)
                continue

            if in_code_block:
                current_section.append(line)
                continue

            if line.startswith('#'):
                if current_section:
                    core_lines.extend(current_section)
                    current_section = []
                core_lines.append(line)
                continue

            if re.match(r'^[-\d]+\.\s+', line):
                current_section.append(line)
                continue

            keywords = ['必须', '禁止', '要求', '注意', '步骤', '规则', '确认']
            if any(kw in line for kw in keywords):
                current_section.append(line)
                continue

        if current_section:
            core_lines.extend(current_section)

        result = '\n'.join(core_lines)

        if len(result) > target_len:
            result = result[:target_len] + "\n\n... (内容已压缩)"

        return result


# ==================== 语义缓存 ====================

class SemanticCache:
    """语义缓存"""

    def __init__(self, cache_dir: Path | None = None, ttl: int = 3600):
        self.cache_dir = cache_dir or Path("/tmp/prompt_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
        self.memory_cache: dict[str, tuple[str, float]] = {}
        self.stats = {"hits": 0, "misses": 0}
        self._lock = RLock()

    def _compute_key(self, task_type: str, complexity: str, mode: str) -> str:
        """计算缓存键"""
        key_data = f"{task_type}:{complexity}:{mode}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, task_type: str, complexity: str, mode: str) -> str | None:
        """获取缓存"""
        with self._lock:
            key = self._compute_key(task_type, complexity, mode)

            # 检查内存缓存
            if key in self.memory_cache:
                content, timestamp = self.memory_cache[key]
                if time.time() - timestamp < self.ttl:
                    self.stats["hits"] += 1
                    logger.debug(f"缓存命中 (内存): {key[:8]}")
                    return content

            # 检查磁盘缓存
            cache_file = self.cache_dir / f"{key}.json"
            if cache_file.exists():
                try:
                    with open(cache_file, encoding='utf-8') as f:
                        data = json.load(f)
                    if time.time() - data.get("timestamp", 0) < self.ttl:
                        self.memory_cache[key] = (data["content"], data["timestamp"])
                        self.stats["hits"] += 1
                        logger.debug(f"缓存命中 (磁盘): {key[:8]}")
                        return data["content"]
                except Exception as e:
                    logger.warning(f"缓存读取失败: {e}")

            self.stats["misses"] += 1
            return None

    def set(self, task_type: str, complexity: str, mode: str, content: str) -> None:
        """设置缓存"""
        with self._lock:
            key = self._compute_key(task_type, complexity, mode)
            timestamp = time.time()

            # 存入内存
            self.memory_cache[key] = (content, timestamp)

            # 存入磁盘
            cache_file = self.cache_dir / f"{key}.json"
            try:
                with open(cache_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        "content": content,
                        "timestamp": timestamp,
                        "task_type": task_type,
                        "complexity": complexity,
                        "mode": mode,
                    }, f, ensure_ascii=False)
                logger.debug(f"缓存已保存: {key[:8]}")
            except Exception as e:
                logger.warning(f"缓存保存失败: {e}")

    def clear(self) -> None:
        """清除缓存"""
        with self._lock:
            self.memory_cache.clear()
            for f in self.cache_dir.glob("*.json"):
                try:
                    f.unlink()
                except Exception:
                    pass

    def get_stats(self) -> dict[str, Any]:
        """获取统计"""
        with self._lock:
            total = self.stats["hits"] + self.stats["misses"]
            hit_rate = self.stats["hits"] / total if total > 0 else 0
            return {
                "hits": self.stats["hits"],
                "misses": self.stats["misses"],
                "hit_rate": f"{hit_rate:.1%}",
                "memory_entries": len(self.memory_cache),
            }


# ==================== 统一提示词加载器 ====================

class UnifiedPromptLoader:
    """
    统一提示词加载器 v3.0

    特性：
    - 渐进式加载：初始只加载最小上下文
    - 语义缓存：避免重复加载
    - 智能压缩：保留核心指令
    - 向后兼容：支持旧版API
    """

    # 最小核心上下文
    MINIMAL_CORE = """# 小娜 - 专利法律AI助手

## 身份
你是小娜，专业的专利法律AI助手，服务于爸爸（专利律师）。

## 核心职责
1. 专利撰写：技术交底书分析、权利要求撰写、说明书撰写
2. 审查意见答复：驳回理由分析、答复策略制定、答复文件撰写
3. 无效宣告：无效理由分析、证据检索、请求书撰写

## 工作原则
- 专业严谨：确保法律依据准确
- 贴心服务：理解爸爸的需求和偏好
- 高效执行：快速响应，减少等待
- 决策尊重：重要决策由爸爸做最终决定

## 强制规则

### 必须 (MUST)
- 关键步骤执行前请求确认
- 提供A/B/C选项方便选择
- 引用法条时标注具体条款

### 禁止 (MUST NOT)
- 禁止自行修改爸爸确认的内容
- 禁止跳过强制确认点
- 禁止使用不确定的法律判断

## 人机协作协议 (HITL)

### 强制确认点
1. 事实认定 - 确认理解正确
2. 法律依据 - 确认条文适用
3. 答复策略 - 确认策略方向
4. 修改方案 - 确认A33合规
5. 最终审查 - 确认答复质量

### 中断指令
- "暂停" - 保存进度
- "调整" - 修改内容
- "回退X步" - 跳转到指定步骤
- "结束任务" - 终止执行
"""

    # 能力层映射
    CAPABILITY_MAP = {
        TaskType.PATENT_WRITING: ["retrieval", "analysis", "writing"],
        TaskType.OFFICE_ACTION: ["retrieval", "analysis", "response"],
        TaskType.INVALIDITY: ["retrieval", "analysis", "invalidity"],
        TaskType.PRIOR_ART_SEARCH: ["retrieval"],
        TaskType.CLAIMS_ANALYSIS: ["analysis", "examination"],
        TaskType.GENERAL: [],
    }

    # 业务层映射
    BUSINESS_MAP = {
        TaskType.PATENT_WRITING: [
            "task_1_1_understand_disclosure",
            "task_1_2_prior_art_search",
            "task_1_3_write_specification",
            "task_1_4_write_claims",
            "task_1_5_write_abstract",
        ],
        TaskType.OFFICE_ACTION: [
            "task_2_1_analyze_office_action",
            "task_2_2_analyze_rejection",
            "task_2_3_develop_response_strategy",
            "task_2_4_write_response",
        ],
    }

    def __init__(
        self,
        prompts_dir: str = "/Users/xujian/Athena工作平台/prompts",
        config: PromptConfig | None = None,
    ):
        self.prompts_dir = Path(prompts_dir)
        self.config = config or PromptConfig()

        # 初始化组件
        self.compressor = PromptCompressor() if self.config.enable_compression else None
        self.cache = SemanticCache(
            cache_dir=Path(self.config.cache_dir) if self.config.cache_dir else None,
            ttl=self.config.cache_ttl,
        ) if self.config.enable_cache else None

        # 预加载核心
        self._core_cache: dict[str, str] = {}
        self._load_cores()

        self._lock = RLock()

        if self.config.verbose:
            logger.info(f"统一提示词加载器初始化完成 (模式: {self.config.load_mode.value})")

    def _load_cores(self) -> None:
        """加载核心提示词"""
        # 尝试加载压缩版核心
        compressed_path = self.prompts_dir / "foundation" / "xiaona_core_v3_compressed.md"
        if compressed_path.exists():
            content = compressed_path.read_text()
            if self.config.enable_compression:
                content = self.compressor.compress(content, self.config.compression_ratio)
            self._core_cache["foundation"] = content
        else:
            self._core_cache["foundation"] = self.MINIMAL_CORE

        # 加载HITL协议
        hitl_path = self.prompts_dir / "foundation" / "hitl_protocol_v3_mandatory.md"
        if hitl_path.exists():
            content = hitl_path.read_text()
            if self.config.enable_compression:
                content = self.compressor.compress(content, self.config.compression_ratio)
            self._core_cache["hitl"] = content
        else:
            self._core_cache["hitl"] = ""

    def get_minimal_prompt(self) -> str:
        """获取最小上下文"""
        return self._core_cache["foundation"]

    def get_prompt(
        self,
        task_type: str = "general",
        complexity: str = "medium",
    ) -> str:
        """
        获取提示词（向后兼容接口）

        Args:
            task_type: 任务类型
            complexity: 复杂度

        Returns:
            提示词内容
        """
        loaded = self.load(task_type, complexity)
        return loaded.get_content()

    def load(
        self,
        task_type: str = "general",
        complexity: str = "medium",
        include_data_layer: bool = False,
    ) -> LoadedPrompt:
        """
        加载提示词

        Args:
            task_type: 任务类型
            complexity: 复杂度
            include_data_layer: 是否包含数据层

        Returns:
            LoadedPrompt: 加载结果
        """
        start_time = time.time()

        # 检查缓存
        if self.cache:
            cached = self.cache.get(task_type, complexity, self.config.load_mode.value)
            if cached:
                load_time = (time.time() - start_time) * 1000
                return LoadedPrompt(
                    segments=[PromptSegment(
                        name="cached",
                        content=cached,
                        layer="all",
                        token_count=len(cached) // 4,
                        compressed=self.config.enable_compression,
                    )],
                    total_tokens=len(cached) // 4,
                    total_chars=len(cached),
                    load_time_ms=load_time,
                    cache_hit=True,
                    compressed=self.config.enable_compression,
                    config=self.config,
                )

        # 根据模式加载
        if self.config.load_mode == LoadMode.MINIMAL:
            segments = self._load_minimal()
        elif self.config.load_mode == LoadMode.PROGRESSIVE:
            segments = self._load_progressive(task_type, complexity, include_data_layer)
        else:  # FULL
            segments = self._load_full(task_type, complexity)

        # 计算统计
        total_tokens = sum(s.token_count for s in segments)
        total_chars = sum(len(s.content) for s in segments)
        load_time = (time.time() - start_time) * 1000

        result = LoadedPrompt(
            segments=segments,
            total_tokens=total_tokens,
            total_chars=total_chars,
            load_time_ms=load_time,
            cache_hit=False,
            compressed=self.config.enable_compression,
            config=self.config,
        )

        # 存入缓存
        if self.cache:
            self.cache.set(task_type, complexity, self.config.load_mode.value, result.get_content())

        if self.config.verbose:
            logger.info(
                f"提示词加载完成: task={task_type}, "
                f"tokens={total_tokens}, time={load_time:.1f}ms"
            )

        return result

    def _load_minimal(self) -> list[PromptSegment]:
        """加载最小上下文"""
        return [PromptSegment(
            name="foundation",
            content=self._core_cache["foundation"],
            layer="foundation",
            token_count=len(self._core_cache["foundation"]) // 4,
            compressed=self.config.enable_compression,
        )]

    def _load_progressive(
        self,
        task_type: str,
        complexity: str,
        include_data_layer: bool,
    ) -> list[PromptSegment]:
        """渐进式加载"""
        segments = []

        # 1. 基础层
        segments.append(PromptSegment(
            name="foundation",
            content=self._core_cache["foundation"],
            layer="foundation",
            token_count=len(self._core_cache["foundation"]) // 4,
            compressed=True,
        ))

        # 2. HITL协议
        if self._core_cache.get("hitl"):
            segments.append(PromptSegment(
                name="hitl",
                content=self._core_cache["hitl"],
                layer="foundation",
                token_count=len(self._core_cache["hitl"]) // 4,
                compressed=True,
            ))

        # 3. 数据层（可选）
        if include_data_layer:
            data_content = self._load_data_layer()
            if data_content:
                segments.append(PromptSegment(
                    name="data_layer",
                    content=data_content,
                    layer="data",
                    token_count=len(data_content) // 4,
                    compressed=self.config.enable_compression,
                ))

        # 4. 能力层
        try:
            task_enum = TaskType(task_type)
        except ValueError:
            task_enum = TaskType.GENERAL

        capabilities = self.CAPABILITY_MAP.get(task_enum, [])
        if capabilities:
            cap_content = self._load_capabilities(capabilities)
            if cap_content:
                segments.append(PromptSegment(
                    name="capabilities",
                    content=cap_content,
                    layer="capability",
                    token_count=len(cap_content) // 4,
                    compressed=self.config.enable_compression,
                ))

        # 5. 业务层
        business_tasks = self.BUSINESS_MAP.get(task_enum, [])
        if business_tasks:
            biz_content = self._load_business_tasks(business_tasks)
            if biz_content:
                segments.append(PromptSegment(
                    name="business",
                    content=biz_content,
                    layer="business",
                    token_count=len(biz_content) // 4,
                    compressed=self.config.enable_compression,
                ))

        return segments

    def _load_full(self, task_type: str, complexity: str) -> list[PromptSegment]:
        """完整加载（旧版兼容）"""
        return self._load_progressive(task_type, complexity, include_data_layer=True)

    def _load_data_layer(self) -> str:
        """加载数据层"""
        data_dir = self.prompts_dir / "data"
        if not data_dir.exists():
            return ""

        parts = []
        for file in sorted(data_dir.glob("*.md")):
            content = file.read_text()
            if self.config.enable_compression:
                content = self.compressor.compress(content, self.config.compression_ratio)
            parts.append(f"\n## {file.stem}\n\n{content}")

        return '\n'.join(parts)

    def _load_capabilities(self, capabilities: list[str]) -> str:
        """加载能力层"""
        cap_dir = self.prompts_dir / "capability"
        if not cap_dir.exists():
            return ""

        parts = []
        for cap in capabilities:
            # 尝试多种命名方式
            for pattern in [f"cap*_{cap}*.md", f"*{cap}*.md"]:
                matches = list(cap_dir.glob(pattern))
                if matches:
                    for match in matches[:1]:  # 只取第一个
                        content = match.read_text()
                        if self.config.enable_compression:
                            content = self.compressor.compress(content, self.config.compression_ratio)
                        parts.append(f"\n## {cap}\n\n{content}")
                    break

        return '\n'.join(parts)

    def _load_business_tasks(self, tasks: list[str]) -> str:
        """加载业务任务"""
        biz_dir = self.prompts_dir / "business"
        if not biz_dir.exists():
            return ""

        parts = []
        for task in tasks:
            # 尝试多种命名方式
            for pattern in [f"{task}*.md", f"*{task}*.md"]:
                matches = list(biz_dir.glob(pattern))
                if matches:
                    for match in matches[:1]:
                        content = match.read_text()
                        if self.config.enable_compression:
                            content = self.compressor.compress(content, self.config.compression_ratio)
                        parts.append(f"\n## {task}\n\n{content}")
                    break

        return '\n'.join(parts)

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        return {
            "cache_stats": self.cache.get_stats() if self.cache else None,
            "config": {
                "load_mode": self.config.load_mode.value,
                "compression_ratio": self.config.compression_ratio,
                "enable_cache": self.config.enable_cache,
                "enable_compression": self.config.enable_compression,
            },
            "core_cache_size": {k: len(v) for k, v in self._core_cache.items()},
        }

    def clear_cache(self) -> None:
        """清除缓存"""
        if self.cache:
            self.cache.clear()


# ==================== 便捷函数 ====================

# 全局实例
_loader_instance: UnifiedPromptLoader | None = None


def get_loader(
    prompts_dir: str = "/Users/xujian/Athena工作平台/prompts",
    config: PromptConfig | None = None,
) -> UnifiedPromptLoader:
    """获取全局加载器实例"""
    global _loader_instance
    if _loader_instance is None:
        _loader_instance = UnifiedPromptLoader(prompts_dir, config)
    return _loader_instance


def get_prompt(
    task_type: str = "general",
    complexity: str = "medium",
    load_mode: str = "progressive",
) -> str:
    """
    获取提示词（便捷函数）

    Args:
        task_type: 任务类型
        complexity: 复杂度
        load_mode: 加载模式 (full/progressive/minimal)

    Returns:
        提示词内容
    """
    config = PromptConfig(load_mode=LoadMode(load_mode))
    loader = get_loader(config=config)
    return loader.get_prompt(task_type, complexity)


def get_minimal_prompt() -> str:
    """获取最小上下文"""
    loader = get_loader()
    return loader.get_minimal_prompt()


# ==================== 向后兼容 ====================

class XiaonaPromptLoader(UnifiedPromptLoader):
    """向后兼容类"""

    def __init__(self, base_path: str = "/Users/xujian/Athena工作平台/prompts"):
        config = PromptConfig(
            load_mode=LoadMode.FULL,
            enable_compression=False,
            verbose=True,
        )
        super().__init__(base_path, config)
        self.prompts: dict[str, str] = {}

    def load_all(self) -> None:
        """加载所有提示词（向后兼容）"""
        loaded = self.load("general", "medium")
        self.prompts["full"] = loaded.get_content()

    def get_full_prompt(self, task_type: str = "general") -> str:
        """获取完整提示词（向后兼容）"""
        return self.get_prompt(task_type, "medium")


# ==================== 命令行入口 ====================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="统一提示词加载器")
    parser.add_argument("--task", default="general", help="任务类型")
    parser.add_argument("--complexity", default="medium", help="复杂度")
    parser.add_argument("--mode", default="progressive", help="加载模式")
    parser.add_argument("--stats", action="store_true", help="显示统计")

    args = parser.parse_args()

    # 配置
    config = PromptConfig(
        load_mode=LoadMode(args.mode),
        verbose=True,
    )

    loader = UnifiedPromptLoader(
        prompts_dir="/Users/xujian/Athena工作平台/prompts",
        config=config,
    )

    # 加载
    loaded = loader.load(args.task, args.complexity)

    print("=" * 60)
    print(f"任务类型: {args.task}")
    print(f"复杂度: {args.complexity}")
    print(f"加载模式: {args.mode}")
    print("=" * 60)
    print(f"总Tokens: ~{loaded.total_tokens:,}")
    print(f"总字符: {loaded.total_chars:,}")
    print(f"加载时间: {loaded.load_time_ms:.1f}ms")
    print(f"缓存命中: {loaded.cache_hit}")
    print(f"片段数: {len(loaded.segments)}")

    if args.stats:
        print("\n" + "=" * 60)
        print("统计信息")
        print("=" * 60)
        stats = loader.get_stats()
        print(f"缓存: {stats['cache_stats']}")
        print(f"核心缓存: {stats['core_cache_size']}")
