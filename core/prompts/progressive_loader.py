#!/usr/bin/env python3
from __future__ import annotations
"""
渐进式提示词加载器
Progressive Prompt Loader

核心设计原则：
1. 初始只加载最小上下文（~5K tokens）
2. 按需加载能力层和业务层
3. 语义缓存避免重复加载
4. 智能压缩保留核心信息

作者: 小诺·双鱼公主
版本: v2.0
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    GENERAL = "general"
    PATENT_WRITING = "patent_writing"
    OFFICE_ACTION = "office_action"
    INVALIDITY = "invalidity"
    PRIOR_ART_SEARCH = "prior_art_search"
    CLAIMS_ANALYSIS = "claims_analysis"


class ComplexityLevel(Enum):
    """复杂度级别"""
    SIMPLE = "simple"      # 简单查询
    MEDIUM = "medium"      # 标准任务
    COMPLEX = "complex"    # 复杂任务（OA答复等）


@dataclass
class PromptContext:
    """提示词上下文"""
    task_type: TaskType
    complexity: ComplexityLevel
    domain: str = "general"
    user_id: str = "default"
    conversation_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PromptSegment:
    """提示词片段"""
    name: str
    content: str
    layer: str  # foundation, data, capability, business
    token_count: int
    dependencies: list[str] = field(default_factory=list)


@dataclass
class LoadedPrompt:
    """已加载的提示词"""
    context: PromptContext
    segments: list[PromptSegment]
    total_tokens: int
    cache_hit: bool
    load_time_ms: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class PromptCompressor:
    """提示词压缩器"""

    # 核心保留模式
    KEEP_PATTERNS = [
        r'^#+\s+',           # 标题
        r'^-\s+',            # 列表项
        r'^\d+\.\s+',        # 有序列表
        r'^\*\*',            # 加粗
        r'^【',              # 中文标注
        r'^```',             # 代码块标记
    ]

    # 可删除模式
    REMOVE_PATTERNS = [
        r'^>\s+\*\*',        # 引用块中的装饰
        r'^---+$',           # 分隔线
        r'^\s*$',            # 空行（保留一个）
    ]

    def compress(self, content: str, ratio: float = 0.4) -> str:
        """
        压缩提示词

        Args:
            content: 原始内容
            ratio: 目标压缩比（0.4 = 保留40%）

        Returns:
            压缩后的内容
        """
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

            # 保留核心内容
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
            # 代码块完整保留
            if line.startswith('```'):
                in_code_block = not in_code_block
                current_section.append(line)
                continue

            if in_code_block:
                current_section.append(line)
                continue

            # 标题 - 保留
            if line.startswith('#'):
                if current_section:
                    core_lines.extend(current_section)
                    current_section = []
                core_lines.append(line)
                continue

            # 列表项/指令 - 保留
            if re.match(r'^[-\d]+\.\s+', line):
                current_section.append(line)
                continue

            # 包含关键词的行 - 保留
            keywords = ['必须', '禁止', '要求', '注意', '步骤', '规则', '确认', 'MUST', 'MUST NOT']
            if any(kw in line for kw in keywords):
                current_section.append(line)
                continue

        # 添加最后一个部分
        if current_section:
            core_lines.extend(current_section)

        result = '\n'.join(core_lines)

        # 如果仍然超长，截断
        if len(result) > target_len:
            result = result[:target_len] + "\n\n... (内容已压缩)"

        return result


class SemanticCache:
    """语义缓存"""

    def __init__(self, cache_dir: Path | None = None):
        self.cache_dir = cache_dir or Path("/tmp/prompt_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.memory_cache: dict[str, LoadedPrompt] = {}
        self.stats = {"hits": 0, "misses": 0}

    def _compute_key(self, context: PromptContext) -> str:
        """计算缓存键"""
        key_data = f"{context.task_type.value}:{context.complexity.value}:{context.domain}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, context: PromptContext) -> LoadedPrompt | None:
        """获取缓存的提示词"""
        key = self._compute_key(context)

        # 先查内存缓存
        if key in self.memory_cache:
            self.stats["hits"] += 1
            logger.debug(f"缓存命中 (内存): {key[:8]}...")
            return self.memory_cache[key]

        # 再查磁盘缓存
        cache_file = self.cache_dir / f"{key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, encoding='utf-8') as f:
                    data = json.load(f)
                prompt = self._deserialize(data)
                self.memory_cache[key] = prompt
                self.stats["hits"] += 1
                logger.debug(f"缓存命中 (磁盘): {key[:8]}...")
                return prompt
            except Exception as e:
                logger.warning(f"缓存读取失败: {e}")

        self.stats["misses"] += 1
        return None

    def set(self, context: PromptContext, prompt: LoadedPrompt) -> None:
        """设置缓存"""
        key = self._compute_key(context)
        prompt.cache_hit = False

        # 存入内存
        self.memory_cache[key] = prompt

        # 存入磁盘
        cache_file = self.cache_dir / f"{key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._serialize(prompt), f, ensure_ascii=False, indent=2)
            logger.debug(f"缓存已保存: {key[:8]}...")
        except Exception as e:
            logger.warning(f"缓存保存失败: {e}")

    def _serialize(self, prompt: LoadedPrompt) -> dict:
        """序列化"""
        return {
            "context": {
                "task_type": prompt.context.task_type.value,
                "complexity": prompt.context.complexity.value,
                "domain": prompt.context.domain,
                "user_id": prompt.context.user_id,
            },
            "segments": [
                {
                    "name": s.name,
                    "content": s.content,
                    "layer": s.layer,
                    "token_count": s.token_count,
                }
                for s in prompt.segments
            ],
            "total_tokens": prompt.total_tokens,
            "load_time_ms": prompt.load_time_ms,
            "created_at": prompt.created_at,
        }

    def _deserialize(self, data: dict) -> LoadedPrompt:
        """反序列化"""
        ctx_data = data["context"]
        context = PromptContext(
            task_type=TaskType(ctx_data["task_type"]),
            complexity=ComplexityLevel(ctx_data["complexity"]),
            domain=ctx_data.get("domain", "general"),
            user_id=ctx_data.get("user_id", "default"),
        )

        segments = [
            PromptSegment(
                name=s["name"],
                content=s["content"],
                layer=s["layer"],
                token_count=s["token_count"],
            )
            for s in data["segments"]
        ]

        return LoadedPrompt(
            context=context,
            segments=segments,
            total_tokens=data["total_tokens"],
            cache_hit=True,
            load_time_ms=data["load_time_ms"],
            created_at=data["created_at"],
        )

    def get_stats(self) -> dict:
        """获取缓存统计"""
        total = self.stats["hits"] + self.stats["misses"]
        hit_rate = self.stats["hits"] / total if total > 0 else 0
        return {
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": f"{hit_rate:.1%}",
            "memory_entries": len(self.memory_cache),
        }


class ProgressivePromptLoader:
    """
    渐进式提示词加载器

    设计理念：
    1. 最小上下文优先 - 初始只加载必要内容
    2. 按需加载 - 根据任务需要动态加载
    3. 智能压缩 - 保留核心指令
    4. 语义缓存 - 避免重复构建
    """

    # 最小核心上下文 (~5K tokens)
    MINIMAL_CORE = {
        "foundation": {
            "identity": "你是小娜，专业的专利法律AI助手。",
            "role": "你的核心职责是帮助爸爸处理专利法律事务，包括专利撰写、审查意见答复、无效宣告等。",
            "values": "专业、严谨、贴心、高效。始终以爸爸的需求为中心。",
            "decision_method": "遇到复杂决策时，提供多个选项供爸爸选择，说明利弊，由爸爸做最终决定。",
        },
        "hitl_core": {
            "confirmation": "关键步骤执行前必须请求爸爸确认。",
            "options": "提供 A/B/C 选项，方便快速选择。",
            "interruption": "支持随时中断、调整、回退。",
        },
        "task_router": {
            "patent_writing": "专利撰写任务 → 加载 task_1_1 到 task_1_5",
            "office_action": "审查意见答复 → 加载 task_2_1 到 task_2_4",
            "prior_art_search": "现有技术检索 → 加载 cap01_retrieval",
            "analysis": "技术分析 → 加载 cap02_analysis",
        },
    }

    # 能力层映射
    CAPABILITY_MAP = {
        "retrieval": ["cap01_retrieval"],
        "analysis": ["cap02_analysis", "cap04_inventive"],
        "writing": ["cap03_writing"],
        "examination": ["cap04_disclosure_exam", "cap05_clarity_exam", "cap07_formal_exam"],
        "response": ["cap06_response"],
        "invalidity": ["cap05_invalid", "cap06_prior_art_ident"],
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
        TaskType.INVALIDITY: [
            "task07_invalid_strategy",
            "task05_inventive",
        ],
    }

    def __init__(
        self,
        prompts_dir: str = "/Users/xujian/Athena工作平台/prompts",
        cache_dir: str | None = None,
        compression_ratio: float = 0.4,
    ):
        self.prompts_dir = Path(prompts_dir)
        self.compressor = PromptCompressor()
        self.compression_ratio = compression_ratio
        self.cache = SemanticCache(Path(cache_dir) if cache_dir else None)

        # 预加载精简版核心
        self._core_cache: dict[str, str] = {}
        self._load_compressed_cores()

        logger.info(f"渐进式提示词加载器初始化完成 (压缩比: {compression_ratio})")

    def _load_compressed_cores(self) -> None:
        """加载压缩后的核心提示词"""
        # 基础层核心
        foundation_path = self.prompts_dir / "foundation" / "xiaona_l1_foundation_v2_optimized.md"
        if foundation_path.exists():
            content = foundation_path.read_text()
            self._core_cache["foundation"] = self.compressor.compress(content, self.compression_ratio)
        else:
            self._core_cache["foundation"] = self._build_minimal_foundation()

        # HITL核心
        hitl_path = self.prompts_dir / "foundation" / "hitl_protocol_v3_mandatory.md"
        if hitl_path.exists():
            content = hitl_path.read_text()
            self._core_cache["hitl"] = self.compressor.compress(content, self.compression_ratio)
        else:
            self._core_cache["hitl"] = self._build_minimal_hitl()

        logger.info(f"核心提示词已加载: foundation={len(self._core_cache['foundation'])} chars, hitl={len(self._core_cache['hitl'])} chars")

    def _build_minimal_foundation(self) -> str:
        """构建最小基础层"""
        return """# 小娜 - 专利法律AI助手

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

## 输出规范
- 使用简体中文
- 结构清晰，分段明确
- 提供选项（A/B/C）方便选择
"""

    def _build_minimal_hitl(self) -> str:
        """构建最小HITL协议"""
        return """# 人机协作协议 (HITL)

## 核心原则
1. 爸爸拥有最终决策权
2. 关键步骤必须确认
3. 支持随时中断
4. 提供多个选项

## 强制确认点（OA答复等高难度任务）
1. 事实认定 - 确认理解正确
2. 法律依据 - 确认条文适用
3. 答复策略 - 确认策略方向
4. 修改方案 - 确认A33合规
5. 最终审查 - 确认答复质量

## 中断指令
- "暂停" - 保存进度
- "调整" - 修改内容
- "回退X步" - 跳转到指定步骤
- "结束任务" - 终止执行
"""

    def get_minimal_context(self) -> str:
        """
        获取最小上下文

        包含：
        - 基础身份和角色
        - HITL核心协议
        - 任务路由信息

        约 5K tokens
        """
        parts = [
            self._core_cache.get("foundation", self._build_minimal_foundation()),
            "",
            self._core_cache.get("hitl", self._build_minimal_hitl()),
            "",
            "# 任务路由",
            "根据任务类型，我会动态加载相关专业提示词：",
            "- 专利撰写 → 加载撰写相关能力",
            "- OA答复 → 加载答复相关能力",
            "- 检索分析 → 加载检索分析能力",
        ]
        return '\n'.join(parts)

    def get_capability_context(
        self,
        capabilities: list[str],
        compress: bool = True,
    ) -> str:
        """
        获取能力层上下文

        Args:
            capabilities: 需要的能力列表
            compress: 是否压缩

        Returns:
            能力层提示词
        """
        segments = []

        for cap in capabilities:
            cap_files = self.CAPABILITY_MAP.get(cap, [])
            for cap_file in cap_files:
                cap_path = self.prompts_dir / "capability" / f"{cap_file}.md"
                if cap_path.exists():
                    content = cap_path.read_text()
                    if compress:
                        content = self.compressor.compress(content, self.compression_ratio)
                    segments.append(f"\n## 能力: {cap}\n\n{content}")

        return '\n'.join(segments)

    def get_business_context(
        self,
        task_type: TaskType,
        compress: bool = True,
    ) -> str:
        """
        获取业务层上下文

        Args:
            task_type: 任务类型
            compress: 是否压缩

        Returns:
            业务层提示词
        """
        task_files = self.BUSINESS_MAP.get(task_type, [])
        segments = []

        for task_file in task_files:
            task_path = self.prompts_dir / "business" / f"{task_file}.md"
            if task_path.exists():
                content = task_path.read_text()
                if compress:
                    content = self.compressor.compress(content, self.compression_ratio)
                segments.append(f"\n## 任务: {task_file}\n\n{content}")

        return '\n'.join(segments)

    def build_prompt(
        self,
        context: PromptContext,
        include_data_layer: bool = False,
    ) -> LoadedPrompt:
        """
        构建完整提示词

        Args:
            context: 提示词上下文
            include_data_layer: 是否包含数据层

        Returns:
            加载的提示词
        """
        import time
        start_time = time.time()

        # 检查缓存
        cached = self.cache.get(context)
        if cached:
            cached.cache_hit = True
            return cached

        segments = []

        # 1. 基础层（必需）
        foundation = self.get_minimal_context()
        segments.append(PromptSegment(
            name="foundation",
            content=foundation,
            layer="foundation",
            token_count=len(foundation) // 4,  # 粗略估算
        ))

        # 2. 数据层（可选）
        if include_data_layer:
            data_content = self._get_data_layer(context.domain)
            segments.append(PromptSegment(
                name="data_layer",
                content=data_content,
                layer="data",
                token_count=len(data_content) // 4,
            ))

        # 3. 能力层（按需）
        capabilities = self._infer_capabilities(context)
        if capabilities:
            cap_content = self.get_capability_context(capabilities)
            segments.append(PromptSegment(
                name="capabilities",
                content=cap_content,
                layer="capability",
                token_count=len(cap_content) // 4,
            ))

        # 4. 业务层（按需）
        if context.task_type != TaskType.GENERAL:
            biz_content = self.get_business_context(context.task_type)
            segments.append(PromptSegment(
                name="business",
                content=biz_content,
                layer="business",
                token_count=len(biz_content) // 4,
            ))

        load_time_ms = (time.time() - start_time) * 1000
        total_tokens = sum(s.token_count for s in segments)

        prompt = LoadedPrompt(
            context=context,
            segments=segments,
            total_tokens=total_tokens,
            cache_hit=False,
            load_time_ms=load_time_ms,
        )

        # 存入缓存
        self.cache.set(context, prompt)

        logger.info(
            f"提示词构建完成: task={context.task_type.value}, "
            f"tokens={total_tokens}, time={load_time_ms:.1f}ms"
        )

        return prompt

    def _get_data_layer(self, domain: str) -> str:
        """获取数据层信息"""
        # 简化版数据层
        return """# 数据层

## 可用数据源
- PostgreSQL: 专利数据库、案例库
- Neo4j: 法律知识图谱
- Qdrant: 向量检索库

## 检索策略
- 法条检索 → patent_rules_complete
- 案例检索 → patent_decisions
- 技术检索 → patent_vectors
"""

    def _infer_capabilities(self, context: PromptContext) -> list[str]:
        """推断需要的能力"""
        capability_map = {
            TaskType.PATENT_WRITING: ["retrieval", "analysis", "writing"],
            TaskType.OFFICE_ACTION: ["retrieval", "analysis", "response"],
            TaskType.INVALIDITY: ["retrieval", "analysis", "invalidity"],
            TaskType.PRIOR_ART_SEARCH: ["retrieval"],
            TaskType.CLAIMS_ANALYSIS: ["analysis", "examination"],
            TaskType.GENERAL: [],
        }
        return capability_map.get(context.task_type, [])

    def get_full_prompt_text(self, context: PromptContext) -> str:
        """获取完整提示词文本"""
        loaded = self.build_prompt(context)
        return '\n\n---\n\n'.join(s.content for s in loaded.segments)

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "cache_stats": self.cache.get_stats(),
            "core_cache_size": {k: len(v) for k, v in self._core_cache.items()},
            "compression_ratio": self.compression_ratio,
        }


# 便捷函数
def create_loader(
    prompts_dir: str = "/Users/xujian/Athena工作平台/prompts",
    compression_ratio: float = 0.4,
) -> ProgressivePromptLoader:
    """创建加载器"""
    return ProgressivePromptLoader(
        prompts_dir=prompts_dir,
        compression_ratio=compression_ratio,
    )


def get_quick_prompt(
    task_type: str = "general",
    complexity: str = "medium",
) -> str:
    """快速获取提示词"""
    loader = create_loader()
    context = PromptContext(
        task_type=TaskType(task_type),
        complexity=ComplexityLevel(complexity),
    )
    return loader.get_full_prompt_text(context)


# 命令行测试
if __name__ == "__main__":

    print("=" * 60)
    print("渐进式提示词加载器测试")
    print("=" * 60)

    loader = create_loader()

    # 测试最小上下文
    print("\n1. 最小上下文:")
    minimal = loader.get_minimal_context()
    print(f"   长度: {len(minimal):,} chars (~{len(minimal)//4:,} tokens)")

    # 测试不同任务类型
    test_cases = [
        ("patent_writing", "medium"),
        ("office_action", "complex"),
        ("prior_art_search", "simple"),
    ]

    for task, complexity in test_cases:
        print(f"\n2. {task} ({complexity}):")
        context = PromptContext(
            task_type=TaskType(task),
            complexity=ComplexityLevel(complexity),
        )
        loaded = loader.build_prompt(context)
        print(f"   片段数: {len(loaded.segments)}")
        print(f"   总tokens: {loaded.total_tokens:,}")
        print(f"   加载时间: {loaded.load_time_ms:.1f}ms")
        print(f"   缓存命中: {loaded.cache_hit}")

    # 测试缓存
    print("\n3. 缓存测试（重复请求）:")
    context = PromptContext(
        task_type=TaskType("patent_writing"),
        complexity=ComplexityLevel("medium"),
    )
    loaded2 = loader.build_prompt(context)
    print(f"   缓存命中: {loaded2.cache_hit}")

    # 统计
    print("\n4. 统计信息:")
    stats = loader.get_stats()
    print(f"   缓存统计: {stats['cache_stats']}")
    print(f"   核心缓存: {stats['core_cache_size']}")
