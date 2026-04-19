#!/usr/bin/env python3
"""
统一提示词加载器 v4.0
基于Claude Code Playbook设计模式

核心特性：
- 静态/动态分离（80%缓存命中率）
- whenToUse自动触发
- 并行工具调用指令
- Scratchpad私下推理
- 约束重复模式

作者: 小诺·双鱼公主 v4.0.0
版本: v4.0
创建时间: 2026-04-19
"""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

# 配置日志
logger = logging.getLogger(__name__)


class UnifiedPromptLoaderV4:
    """
    统一提示词加载器 v4.0

    基于Claude Code Playbook设计模式：
    1. 约束重复 - 关键规则在开头和结尾强调
    2. whenToUse触发 - 自动识别用户意图
    3. 并行工具调用 - Turn-based并行处理
    4. Scratchpad推理 - 私下推理+摘要输出
    5. 静态/动态分离 - 可缓存静态部分
    """

    def __init__(
        self,
        prompt_base_path: Optional[str] = None,
        use_cache: bool = True,
        cache_dir: Optional[str] = None
    ):
        """
        初始化v4.0加载器

        Args:
            prompt_base_path: 提示词根目录
            use_cache: 是否使用缓存
            cache_dir: 缓存目录
        """
        # 设置提示词根目录
        if prompt_base_path is None:
            # 默认路径：项目根目录/prompts
            base = Path(__file__).parent.parent.parent
            self.prompt_base_path: Path = base / "prompts"
        else:
            self.prompt_base_path = Path(prompt_base_path)

        # 缓存配置
        self.use_cache = use_cache
        if cache_dir is None:
            self.cache_dir: Path = self.prompt_base_path / ".cache"
        else:
            self.cache_dir = Path(cache_dir)

        # 确保缓存目录存在
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # 缓存文件路径
        self.static_cache_file = self.cache_dir / "static_prompts_v4.json"
        self.dynamic_cache_file = self.cache_dir / "dynamic_prompts_v4.json"

        # 版本信息
        self.version = "v4.0"
        self.loader_name = "UnifiedPromptLoaderV4"

        logger.info(f"[{self.loader_name}] 初始化完成")
        logger.info(f"[{self.loader_name}] 提示词路径: {self.prompt_base_path}")
        logger.info(f"[{self.loader_name}] 缓存路径: {self.cache_dir}")

    def load_system_prompt(
        self,
        agent_type: str = "xiaona",
        session_context: Optional[dict[str, Any]] = None
    ) -> str:
        """
        加载系统提示词（静态/动态分离）

        Args:
            agent_type: 代理类型（xiaona/xiaonuo/yunxi）
            session_context: 会话上下文（动态部分）

        Returns:
            完整的系统提示词
        """
        logger.info(f"[{self.loader_name}] 开始加载系统提示词: {agent_type}")

        # 1. 加载静态部分（可缓存）
        static_prompt = self._load_static_prompt(agent_type)

        # 2. 加载动态部分（会话特定）
        dynamic_prompt = self._load_dynamic_prompt(agent_type, session_context or {})

        # 3. 组合静态+动态
        full_prompt = self._combine_prompts(static_prompt, dynamic_prompt)

        logger.info(
            f"[{self.loader_name}] 提示词加载完成: "
            f"静态={len(static_prompt)}字符, "
            f"动态={len(dynamic_prompt)}字符, "
            f"总计={len(full_prompt)}字符"
        )

        return full_prompt

    def _load_static_prompt(self, agent_type: str) -> str:
        """
        加载静态提示词（可缓存）

        静态部分包括：
        - L1基础层（身份定义、核心原则）
        - L2数据层（数据源配置）
        - L3能力层（核心能力定义）
        - HITL协议（人机协作规则）

        Returns:
            静态提示词
        """
        cache_key = f"static_{agent_type}"

        # 尝试从缓存加载
        if self.use_cache:
            cached = self._load_from_cache(self.static_cache_file, cache_key)
            if cached:
                logger.info(f"[{self.loader_name}] ✅ 从缓存加载静态提示词")
                return cached

        # 加载各层提示词
        parts = []

        # L1: 基础层
        l1_content = self._load_foundation_layer(agent_type)
        if l1_content:
            parts.append(l1_content)

        # L2: 数据层（简化版，详细配置在运行时注入）
        l2_content = self._load_data_layer_summary()
        if l2_content:
            parts.append(l2_content)

        # L3: 能力层（核心能力，按需加载）
        l3_content = self._load_capability_layer_summary()
        if l3_content:
            parts.append(l3_content)

        # HITL协议（v4.0 with 约束重复）
        hitl_content = self._load_hitl_protocol_v4()
        if hitl_content:
            parts.append(hitl_content)

        # 组合静态提示词
        static_prompt = "\n\n".join(parts)

        # 保存到缓存
        if self.use_cache:
            self._save_to_cache(self.static_cache_file, cache_key, static_prompt)

        return static_prompt

    def _load_dynamic_prompt(
        self,
        agent_type: str,
        session_context: dict[str, Any]
    ) -> str:
        """
        加载动态提示词（会话特定）

        动态部分包括：
        - 当前任务相关的L4业务层提示词
        - 会话特定信息（时间、工作目录等）
        - 用户偏好设置
        - 当前任务上下文

        Args:
            agent_type: 代理类型
            session_context: 会话上下文

        Returns:
            动态提示词
        """
        # 会话上下文不需要缓存（每次都不同）
        parts = []

        # 添加会话元信息
        if session_context:
            meta_info = self._generate_session_meta(session_context)
            parts.append(meta_info)

        # 根据任务类型加载L4业务层
        task_type = session_context.get("task_type", "general")
        l4_content = self._load_business_layer(task_type)
        if l4_content:
            parts.append(l4_content)

        # 组合动态提示词
        dynamic_prompt = "\n\n".join(parts)

        return dynamic_prompt

    def _load_foundation_layer(self, agent_type: str) -> Optional[str]:
        """加载L1基础层"""
        # 映射agent_type到文件名
        foundation_files = {
            "xiaona": "xiaona_core_v3_compressed.md",
            "xiaonuo": "xiaonuo_core_v3_compressed.md",
        }

        filename = foundation_files.get(agent_type)
        if not filename:
            logger.warning(f"[{self.loader_name}] 未找到{agent_type}的基础层文件")
            return None

        file_path = self.prompt_base_path / "foundation" / filename
        return self._read_file(file_path)

    def _load_data_layer_summary(self) -> Optional[str]:
        """加载L2数据层摘要"""
        file_path = self.prompt_base_path / "data" / "xiaona_l2_overview.md"
        content = self._read_file(file_path)

        if content:
            # 添加whenToUse触发提示
            when_to_use = "\n\n### whenToUse (数据源自动触发)\n"
            when_to_use += "当任务需要以下数据时，自动启用对应数据源：\n"
            when_to_use += "- 向量检索 → Qdrant\n"
            when_to_use += "- 知识图谱 → Neo4j\n"
            when_to_use += "- 专利查询 → PostgreSQL\n"
            when_to_use += "- 网络搜索 → Jina AI\n"
            content += when_to_use

        return content

    def _load_capability_layer_summary(self) -> Optional[str]:
        """加载L3能力层摘要"""
        file_path = self.prompt_base_path / "capability" / "cap04_inventive_v2_with_whenToUse.md"
        return self._read_file(file_path)

    def _load_hitl_protocol_v4(self) -> Optional[str]:
        """加载HITL协议v4.0（with 约束重复）"""
        file_path = self.prompt_base_path / "foundation" / "hitl_protocol_v4_constraint_repeat.md"
        return self._read_file(file_path)

    def _load_business_layer(self, task_type: str) -> Optional[str]:
        """加载L4业务层（根据任务类型）"""
        # 映射任务类型到文件
        business_files = {
            "oa_analysis": "business/task_2_1_oa_analysis_v2_with_parallel.md",
            "patent_writing": "business/task_1_1_understand_disclosure.md",
            "general": None,  # 通用任务不需要特定业务层
        }

        filename = business_files.get(task_type)
        if not filename:
            return None

        file_path = self.prompt_base_path / filename
        return self._read_file(file_path)

    def _generate_session_meta(self, session_context: dict[str, Any]) -> str:
        """生成会话元信息"""
        meta_parts = []

        # 时间戳
        now = datetime.now()
        meta_parts.append(f"### 会话时间\n{now.strftime('%Y-%m-%d %H:%M:%S')}")

        # 工作目录
        cwd = session_context.get("cwd")
        if cwd:
            meta_parts.append(f"\n### 工作目录\n{cwd}")

        # 会话ID
        session_id = session_context.get("session_id")
        if session_id:
            meta_parts.append(f"\n### 会话ID\n{session_id}")

        # 任务类型
        task_type = session_context.get("task_type")
        if task_type:
            meta_parts.append(f"\n### 当前任务\n{task_type}")

        return "\n".join(meta_parts)

    def _combine_prompts(self, static_prompt: str, dynamic_prompt: str) -> str:
        """组合静态和动态提示词"""
        if not dynamic_prompt:
            return static_prompt

        return f"""{static_prompt}

---

## 🎯 当前会话上下文（动态）

{dynamic_prompt}
"""

    def _read_file(self, file_path: Path) -> Optional[str]:
        """读取文件内容"""
        try:
            if not file_path.exists():
                logger.warning(f"[{self.loader_name}] 文件不存在: {file_path}")
                return None

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            logger.debug(f"[{self.loader_name}] ✅ 读取文件: {file_path.name} ({len(content)}字符)")
            return content

        except Exception as e:
            logger.error(f"[{self.loader_name}] ❌ 读取文件失败: {file_path} - {e}")
            return None

    def _load_from_cache(self, cache_file: Path, cache_key: str) -> Optional[str]:
        """从缓存加载"""
        try:
            if not cache_file.exists():
                return None

            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            if cache_key in cache_data:
                return cache_data[cache_key]

            return None

        except Exception as e:
            logger.warning(f"[{self.loader_name}] 缓存读取失败: {e}")
            return None

    def _save_to_cache(self, cache_file: Path, cache_key: str, content: str):
        """保存到缓存"""
        try:
            # 读取现有缓存
            if cache_file.exists():
                with open(cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
            else:
                cache_data = {}

            # 更新缓存
            cache_data[cache_key] = content
            cache_data["_metadata"] = {
                "version": self.version,
                "updated_at": datetime.now().isoformat(),
                "cache_key": cache_key,
            }

            # 保存缓存
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)

            logger.debug(f"[{self.loader_name}] ✅ 缓存已保存: {cache_key}")

        except Exception as e:
            logger.warning(f"[{self.loader_name}] 缓存保存失败: {e}")

    def clear_cache(self):
        """清空缓存"""
        try:
            if self.static_cache_file.exists():
                self.static_cache_file.unlink()
            if self.dynamic_cache_file.exists():
                self.dynamic_cache_file.unlink()

            logger.info(f"[{self.loader_name}] ✅ 缓存已清空")

        except Exception as e:
            logger.error(f"[{self.loader_name}] ❌ 清空缓存失败: {e}")

    def get_cache_stats(self) -> dict[str, Any]:
        """获取缓存统计信息"""
        stats = {
            "version": self.version,
            "cache_dir": str(self.cache_dir),
            "static_cache_exists": self.static_cache_file.exists(),
            "dynamic_cache_exists": self.dynamic_cache_file.exists(),
        }

        # 读取缓存元信息
        if self.static_cache_file.exists():
            try:
                with open(self.static_cache_file, "r", encoding="utf-8") as f:
                    cache_data = json.load(f)
                    stats["static_cache_metadata"] = cache_data.get("_metadata", {})
            except Exception:
                pass

        return stats


# 使用示例
def example_usage():
    """使用示例"""
    # 初始化v4.0加载器
    loader = UnifiedPromptLoaderV4()

    # 加载系统提示词
    system_prompt = loader.load_system_prompt(
        agent_type="xiaona",
        session_context={
            "session_id": "SESSION_001",
            "cwd": "/Users/xujian/Athena工作平台",
            "task_type": "oa_analysis"
        }
    )

    print(f"系统提示词长度: {len(system_prompt)} 字符")
    print(f"系统提示词预览:\n{system_prompt[:500]}...")

    # 查看缓存统计
    stats = loader.get_cache_stats()
    print(f"\n缓存统计:\n{json.dumps(stats, ensure_ascii=False, indent=2)}")


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    example_usage()
