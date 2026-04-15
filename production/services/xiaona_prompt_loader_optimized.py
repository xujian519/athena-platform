#!/usr/bin/env python3
"""
小娜提示词加载器 - 优化版
解决上下文窗口限制问题
"""

from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Literal


class XiaonaPromptLoaderOptimized:
    """
    小娜提示词加载器 - 优化版

    优化策略：
    1. 分层加载：按需加载提示词层级
    2. 能力按需：只加载当前任务需要的能力
    3. 精简提示：去除冗余内容
    4. 动态压缩：根据上下文窗口动态调整
    """

    # 提示词预算配置 (Token数)
    BUDGET = {
        "minimal": {
            "system_prompt": 4000,      # 最小系统提示
            "total_safe": 100000,       # 总安全阈值 (128k的78%)
        },
        "balanced": {
            "system_prompt": 12000,     # 平衡系统提示
            "total_safe": 90000,        # 总安全阈值 (128k的70%)
        },
        "full": {
            "system_prompt": 30000,     # 完整系统提示
            "total_safe": 80000,        # 总安全阈值 (128k的62%)
        }
    }

    # 任务到能力的映射
    TASK_CAPABILITY_MAPPING = {
        "task_1_1": ["cap02_analysis"],              # 理解技术交底
        "task_1_2": ["cap01_retrieval", "cap02_analysis"],  # 现有技术调研
        "task_1_3": ["cap03_writing", "cap04_disclosure_exam"],  # 撰写说明书
        "task_1_4": ["cap03_writing", "cap05_clarity_exam"],    # 撰写权利要求
        "task_1_5": ["cap03_writing"],               # 撰写摘要
        "task_2_1": ["cap01_retrieval", "cap02_analysis"],      # 解读审查意见
        "task_2_2": ["cap04_inventive", "cap05_invalid"],        # 分析驳回理由
        "task_2_3": ["cap02_analysis", "cap06_response"],        # 制定答复策略
        "task_2_4": ["cap03_writing", "cap06_response"],        # 撰写答复文件
    }

    def __init__(self, base_path: str = None, mode: Literal["minimal", "balanced", "full"] = "balanced"):
        """
        初始化优化版提示词加载器

        Args:
            base_path: 提示词根目录
            mode: 加载模式
                - minimal: 最小化模式，只加载核心提示词 (~4k tokens)
                - balanced: 平衡模式，加载常用提示词 (~12k tokens)
                - full: 完整模式，加载所有提示词 (~30k tokens)
        """
        self.base_path = Path(base_path or "/Users/xujian/Athena工作平台/prompts")
        self.mode = mode
        self.prompts = {}
        self.metadata = {
            "version": "v2.1-optimized",
            "last_updated": datetime.now().isoformat(),
            "mode": mode,
            "total_prompts": 0
        }

    def load_for_task(self, task_name: str) -> str:
        """
        为特定任务加载最小化提示词

        Args:
            task_name: 任务名称 (如 "task_1_1", "task_2_1")

        Returns:
            针对该任务优化的提示词
        """
        parts = []

        # 1. 基础层 - 精简版
        parts.append(self._load_foundation_minimal())

        # 2. 数据层 - 仅相关部分
        parts.append(self._load_data_layer_for_task(task_name))

        # 3. 能力层 - 只加载需要的能力
        required_capabilities = self.TASK_CAPABILITY_MAPPING.get(task_name, [])
        for cap in required_capabilities:
            cap_content = self._load_capability(cap)
            if cap_content:
                parts.append(f"## {cap.upper()}\n\n{cap_content}")

        # 4. 业务层 - 只加载当前任务
        task_content = self._load_business_task(task_name)
        if task_content:
            parts.append(task_content)

        # 5. HITL协议 - 精简版
        parts.append(self._load_hitl_minimal())

        prompt = "\n\n---\n\n".join(parts)

        # 检查是否超出预算
        estimated_tokens = self._estimate_tokens(prompt)
        budget = self.BUDGET[self.mode]["system_prompt"]

        if estimated_tokens > budget:
            print(f"⚠️  提示词({estimated_tokens:,} tokens)超出预算({budget:,})，进行压缩...")
            prompt = self._compress_prompt(prompt, budget)

        return prompt

    def load_for_scenario(self, scenario: str) -> str:
        """
        为场景加载提示词

        Args:
            scenario: 场景名称 (patent_writing/office_action/general)

        Returns:
            场景提示词
        """
        if scenario == "patent_writing":
            # 专利撰写：加载task_1_1到task_1_5
            return self._load_scenario_tasks(["task_1_1", "task_1_2", "task_1_3", "task_1_4", "task_1_5"])
        elif scenario == "office_action":
            # 意见答复：加载task_2_1到task_2_4
            return self._load_scenario_tasks(["task_2_1", "task_2_2", "task_2_3", "task_2_4"])
        else:
            # 通用：加载精简版全部提示词
            return self._load_general_minimal()

    def _load_foundation_minimal(self) -> str:
        """加载精简版基础层"""
        path = self.base_path / "foundation" / "xiaona_l1_foundation.md"
        full_content = self._read_file(path, "L1基础层", optional=True)

        if not full_content:
            return self._get_foundation_fallback()

        # 提取核心部分：身份定义 + 核心原则
        sections = []
        in_core_section = False

        for line in full_content.split('\n'):
            # 保留核心部分
            if any(keyword in line for keyword in ['# 小娜身份定义', '## 🎯 核心原则', '# 姓名', '### 角色定位', '### 工作原则']):
                in_core_section = True
            elif line.startswith('## ') and '核心原则' not in line:
                in_core_section = False

            if in_core_section or line.startswith('#'):
                sections.append(line)

        result = '\n'.join(sections)
        if len(result) < 500:  # 如果提取失败，使用fallback
            return self._get_foundation_fallback()

        return result

    def _get_foundation_fallback(self) -> str:
        """基础层fallback"""
        return """# 小娜 - 专利法律AI助手

## 身份定义
- **姓名**: 小娜
- **角色**: 专利法律专家AI助手
- **设计者**: 小诺·双鱼公主 v4.0.0

## 核心原则
1. **准确第一**: 确保法律分析的准确性
2. **人机协作**: 关键决策需要爸爸确认
3. **专业规范**: 遵循专利法律实务规范
4. **清晰输出**: 结构化、易读的输出格式

## 工作模式
- HITL人机协作模式
- 所有关键决策需要爸爸确认
"""

    def _load_data_layer_for_task(self, task_name: str) -> str:
        """为任务加载相关数据层信息"""
        # 根据任务类型返回相关数据源
        if task_name in ["task_1_2", "task_2_1"]:
            # 需要检索数据源
            return """## L2: 数据层 - 检索数据源

### Qdrant向量数据库
- patent_decisions: 64,815条复审无效决定
- patent_rules_complete: 2,694条专利法条

### Neo4j知识图谱
- patent_rules: 64,913个法条节点
- legal_kg: 22,372个法律概念节点

### PostgreSQL专利数据库
- patent_db: 28,036,796件中国专利
"""
        else:
            return """## L2: 数据层

可访问Athena平台数据源：向量数据库、知识图谱、专利数据库。
"""

    def _load_capability(self, cap_name: str) -> str:
        """加载单个能力"""
        # 匹配文件名
        cap_dir = self.base_path / "capability"

        # 查找匹配的文件
        for file in cap_dir.glob(f"{cap_name}*.md"):
            content = self._read_file(file, file.name, optional=True)
            if content:
                # 提取核心部分（去除冗余示例）
                return self._extract_capability_core(content)

        return f"# {cap_name}\n\n能力加载失败，请检查文件。"

    def _extract_capability_core(self, content: str) -> str:
        """提取能力的核心内容"""
        lines = content.split('\n')
        core_lines = []

        for line in lines:
            # 保留：标题、概述、执行流程、注意事项
            # 跳过：长示例、重复说明
            if line.startswith('#') or line.startswith('##') or line.startswith('###'):
                core_lines.append(line)
            elif line.startswith('-') or line.startswith('1.') or line.startswith('2.'):
                core_lines.append(line)
            elif line.strip() and len(line) < 200:
                core_lines.append(line)

        return '\n'.join(core_lines[:200])  # 限制行数

    def _load_business_task(self, task_name: str) -> str:
        """加载单个业务任务"""
        business_dir = self.base_path / "business"

        for file in business_dir.glob(f"{task_name}*.md"):
            content = self._read_file(file, file.name, optional=True)
            if content:
                return content

        return f"# {task_name}\n\n任务加载失败，请检查文件。"

    def _load_hitl_minimal(self) -> str:
        """加载精简版HITL协议"""
        return """## HITL人机协作协议

### 核心原则
- **父亲做决策**: 所有关键决策由爸爸（用户）做出
- **小娜提建议**: AI提供分析、建议、方案选项
- **确认机制**: 重要操作需要用户明确确认

### 交互时机
- 决策确认点：需要用户做出选择时
- 审核确认点：需要用户审核输出结果时
- 信息收集点：需要用户提供更多信息时

### 交互格式
使用清晰的选择题格式：
```
🤝 需要您确认：
[问题描述]

【您可以选择】：
A. [选项1]
B. [选项2]
C. [选项3]
```
"""

    def _load_scenario_tasks(self, task_names: list[str]) -> str:
        """加载场景的多个任务"""
        parts = [self._load_foundation_minimal()]
        parts.append(self._load_data_layer_for_task(task_names[0]))

        # 收集所有需要的能力
        all_capabilities = set()
        for task in task_names:
            caps = self.TASK_CAPABILITY_MAPPING.get(task, [])
            all_capabilities.update(caps)

        # 加载能力
        for cap in all_capabilities:
            cap_content = self._load_capability(cap)
            if cap_content:
                parts.append(f"## {cap.upper()}\n\n{cap_content}")

        # 加载任务
        for task in task_names:
            task_content = self._load_business_task(task)
            if task_content:
                parts.append(task_content)

        parts.append(self._load_hitl_minimal())

        prompt = "\n\n---\n\n".join(parts)

        # 压缩到预算内
        estimated_tokens = self._estimate_tokens(prompt)
        budget = self.BUDGET[self.mode]["system_prompt"]

        if estimated_tokens > budget:
            print(f"⚠️  场景提示词({estimated_tokens:,} tokens)超出预算({budget:,})，进行压缩...")
            prompt = self._compress_prompt(prompt, budget)

        return prompt

    def _load_general_minimal(self) -> str:
        """加载精简版通用提示词"""
        parts = [
            self._load_foundation_minimal(),
            self._load_data_layer_for_task("general"),
            self._load_hitl_minimal()
        ]

        return "\n\n---\n\n".join(parts)

    def _compress_prompt(self, prompt: str, max_tokens: int) -> str:
        """
        压缩提示词到目标Token数

        策略：
        1. 保留所有标题
        2. 压缩长段落
        3. 移除冗余示例
        """
        current_tokens = self._estimate_tokens(prompt)

        if current_tokens <= max_tokens:
            return prompt

        # 计算压缩比例
        ratio = max_tokens / current_tokens

        # 按段落分割
        lines = prompt.split('\n')
        compressed_lines = []
        current_paragraph = []

        for line in lines:
            # 保留标题
            if line.startswith('#'):
                if current_paragraph:
                    compressed_lines.extend(self._compress_paragraph(current_paragraph, ratio))
                    current_paragraph = []
                compressed_lines.append(line)
            else:
                current_paragraph.append(line)

        if current_paragraph:
            compressed_lines.extend(self._compress_paragraph(current_paragraph, ratio))

        return '\n'.join(compressed_lines)

    def _compress_paragraph(self, paragraph: list[str], ratio: float) -> list[str]:
        """压缩单个段落"""
        if len(paragraph) <= 3:
            return paragraph

        # 保留前两句和最后一句
        keep_count = max(2, int(len(paragraph) * ratio))
        if keep_count < len(paragraph):
            # 保留开头和结尾
            result = paragraph[:keep_count//2] + paragraph[-(keep_count//2):]
        else:
            result = paragraph

        return result

    def _estimate_tokens(self, text: str) -> int:
        """估算Token数（中文约1.5字符=1token，英文约4字符=1token）"""
        # 简化估算：按字符数/1.5
        return int(len(text) / 1.5)

    def _read_file(self, path: Path, name: str, optional: bool = False) -> str:
        """读取文件内容"""
        try:
            with open(path, encoding='utf-8') as f:
                content = f.read()
            return content
        except FileNotFoundError:
            if optional:
                return ""
            raise
        except Exception:
            if not optional:
                raise
            return ""


# 便捷函数
def load_prompt_for_task(task_name: str, mode: str = "balanced") -> str:
    """
    为任务加载优化提示词

    Args:
        task_name: 任务名称 (如 "task_1_1", "task_2_1")
        mode: 加载模式 (minimal/balanced/full)

    Returns:
        优化后的提示词
    """
    loader = XiaonaPromptLoaderOptimized(mode=mode)
    prompt = loader.load_for_task(task_name)

    print(f"✅ 为任务 {task_name} 加载提示词 ({mode}模式)")
    print(f"   估算Token数: {loader._estimate_tokens(prompt):,}")

    return prompt


def main() -> None:
    """测试优化版加载器"""
    print("=" * 70)
    print("小娜提示词加载器 - 优化版测试")
    print("=" * 70)

    # 测试1: 单任务加载
    print("\n📝 测试1: 单任务加载")
    print("-" * 70)

    loader = XiaonaPromptLoaderOptimized(mode="balanced")

    test_tasks = ["task_1_1", "task_1_2", "task_2_1", "task_2_2"]

    for task in test_tasks:
        prompt = loader.load_for_task(task)
        tokens = loader._estimate_tokens(prompt)
        print(f"{task}: {tokens:,} tokens")

    # 测试2: 场景加载
    print("\n📋 测试2: 场景加载")
    print("-" * 70)

    scenarios = ["patent_writing", "office_action", "general"]

    for scenario in scenarios:
        prompt = loader.load_for_scenario(scenario)
        tokens = loader._estimate_tokens(prompt)
        print(f"{scenario}: {tokens:,} tokens")

    # 测试3: 不同模式对比
    print("\n🔧 测试3: 不同模式对比")
    print("-" * 70)

    modes = ["minimal", "balanced", "full"]

    for mode in modes:
        loader_mode = XiaonaPromptLoaderOptimized(mode=mode)
        prompt = loader_mode.load_for_task("task_1_1")
        tokens = loader_mode._estimate_tokens(prompt)
        print(f"{mode}: {tokens:,} tokens")


if __name__ == "__main__":
    main()
