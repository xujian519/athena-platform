#!/usr/bin/env python3
"""
小娜提示词加载器 - 生产环境 v2.1
支持优化版提示词加载
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class XiaonaPromptLoaderV2:
    """小娜提示词加载器 v2.1 - 支持优化版"""

    def __init__(self,
                 base_path: str = None,
                 version: str = "v2_optimized",
                 use_cache: bool = True):
        """
        初始化提示词加载器

        Args:
            base_path: 提示词根目录
            version: 提示词版本 (v2_optimized/v1.0)
            use_cache: 是否使用缓存
        """
        self.base_path = Path(base_path or "/Users/xujian/Athena工作平台/prompts")
        self.version = version
        self.use_cache = use_cache
        self.prompts = {}
        self.metadata = {
            "version": f"v2.1-{version}",
            "last_updated": datetime.now().isoformat(),
            "total_prompts": 0,
            "total_tokens": 0
        }

        # 版本映射
        self.version_map = {
            "v2_optimized": {
                "l1": "foundation/xiaona_l1_foundation_v2_optimized.md",
                "l2_overview": "data/xiaona_l2_overview_v2_optimized.md",
                "l2_search": "data/xiaona_l2_search_v2_optimized.md",
                "l3": "capability/xiaona_l3_capability_v2_optimized.md",
                "l4": "business/xiaona_l4_business_v2_optimized.md",
                "hitl": "foundation/hitl_protocol_v2_optimized.md"
            },
            "v1.0": {
                "l1": "foundation/xiaona_l1_foundation.md",
                "l2_overview": "data/xiaona_l2_overview.md",
                "l2_search": "data/xiaona_l2_search.md",
                "l3": "capability/xiaona_l3_capability.md",
                "l4": "business/xiaona_l4_business.md",
                "hitl": "foundation/hitl_protocol.md"
            }
        }

    def load_all_prompts(self) -> dict[str, str]:
        """加载所有提示词"""
        print(f"📚 开始加载小娜提示词系统 (版本: {self.version})...")

        # 1. 加载L1基础层
        self.prompts["l1"] = self._load_layer("l1", "L1基础层")

        # 2. 加载L2数据层
        self.prompts["l2_overview"] = self._load_layer("l2_overview", "L2数据层-总览")
        self.prompts["l2_search"] = self._load_layer("l2_search", "L2数据层-搜索")

        # 3. 加载L3能力层
        self.prompts["l3"] = self._load_layer("l3", "L3能力层")

        # 4. 加载L4业务层
        self.prompts["l4"] = self._load_layer("l4", "L4业务层")

        # 更新元数据
        self.metadata["total_prompts"] = len(self.prompts)
        self.metadata["total_tokens"] = sum(len(p) for p in self.prompts.values())

        print("✅ 提示词加载完成！")
        print(f"   - 版本: {self.version}")
        print(f"   - 模块数: {self.metadata['total_prompts']}")
        print(f"   - 总字符数: {self.metadata['total_tokens']:,}")

        return self.prompts

    def _load_layer(self, layer_key: str, layer_name: str) -> str:
        """加载指定层"""
        file_path = self.base_path / self.version_map[self.version][layer_key]

        try:
            with open(file_path, encoding='utf-8') as f:
                content = f.read()
            print(f"  ✅ {layer_name}: {len(content):,} 字符")
            return content
        except FileNotFoundError:
            print(f"  ⚠️  {layer_name}: 文件未找到 ({file_path})")
            return f"# {layer_name}\n\n提示词文件未找到: {file_path}"
        except Exception as e:
            print(f"  ❌ {layer_name}: 读取失败 ({e})")
            return f"# {layer_name}\n\n读取失败: {e}"

    def get_full_prompt(self,
                       scenario: str = "general",
                       include_external: bool = False) -> str:
        """
        获取完整提示词

        Args:
            scenario: 业务场景 (general/patent_writing/office_action)
            include_external: 是否包含外部文档引用

        Returns:
            完整提示词
        """
        parts = []

        # L1基础层 (必需)
        if "l1" in self.prompts:
            parts.append(self.prompts["l1"])

        # L2数据层 (必需)
        if "l2_overview" in self.prompts:
            parts.append(self.prompts["l2_overview"])
        if "l2_search" in self.prompts:
            parts.append(self.prompts["l2_search"])

        # L3能力层 (必需)
        if "l3" in self.prompts:
            parts.append(self.prompts["l3"])

        # L4业务层 (根据场景)
        if "l4" in self.prompts:
            if scenario != "general":
                l4_content = self._filter_l4_scenario(self.prompts["l4"], scenario)
                parts.append(l4_content)
            else:
                parts.append(self.prompts["l4"])

        # 外部文档引用
        if include_external:
            external_ref = self._get_external_reference()
            parts.append(external_ref)

        return "\n\n---\n\n".join(parts)

    def _filter_l4_scenario(self, l4_content: str, scenario: str) -> str:
        """根据场景过滤L4内容"""
        lines = l4_content.split('\n')
        filtered = []
        capture = False

        # 场景映射
        scenario_map = {
            "patent_writing": ["Task 1.1", "Task 1.2", "Task 1.3", "Task 1.4", "Task 1.5"],
            "office_action": ["Task 2.1", "Task 2.2", "Task 2.3", "Task 2.4"]
        }

        target_tasks = scenario_map.get(scenario, [])

        for line in lines:
            # 检查是否是目标任务
            is_task_line = False
            for task in target_tasks:
                if task in line:
                    capture = True
                    filtered.append(line)
                    is_task_line = True
                    break

            if is_task_line:
                continue

            if capture and line.strip().startswith("# ") and "Task" not in line:
                # 到达下一个非Task章节
                break
            elif capture or not target_tasks:
                if target_tasks or not line.strip().startswith("# Task"):
                    filtered.append(line)

        return "\n".join(filtered)

    def _get_external_reference(self) -> str:
        """获取外部文档引用"""
        external_path = self.base_path.parent / "docs/prompts/xiaona/external"

        references = []
        if external_path.exists():
            for ref_file in external_path.rglob("*.md"):
                rel_path = ref_file.relative_to(self.base_path.parent)
                references.append(f"- {rel_path}")

        if references:
            return "## 🔗 外部详细文档\n\n完整案例模板和示例请参考:\n" + "\n".join(references)
        return ""

    def save_cache(self, cache_path: str = None) -> None:
        """保存提示词缓存"""
        if cache_path is None:
            cache_path = self.base_path / ".cache" / f"prompts_cache_{self.version}.json"
        else:
            cache_path = Path(cache_path)

        cache_path.parent.mkdir(parents=True, exist_ok=True)

        cache_data = {
            "metadata": self.metadata,
            "prompts": self.prompts
        }

        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

        print(f"💾 提示词缓存已保存: {cache_path}")

    def load_cache(self, cache_path: str = None) -> bool:
        """从缓存加载提示词"""
        if cache_path is None:
            cache_path = self.base_path / ".cache" / f"prompts_cache_{self.version}.json"
        else:
            cache_path = Path(cache_path)

        if not cache_path.exists():
            return False

        try:
            with open(cache_path, encoding='utf-8') as f:
                cache_data = json.load(f)

            self.prompts = cache_data["prompts"]
            self.metadata = cache_data["metadata"]

            print(f"📦 从缓存加载提示词: {cache_path}")
            print(f"   版本: {self.metadata['version']}")
            print(f"   更新时间: {self.metadata['last_updated']}")
            return True
        except Exception as e:
            print(f"❌ 缓存加载失败: {e}")
            return False

    def get_token_count(self, scenario: str = "general") -> int:
        """估算提示词token数量"""
        prompt = self.get_full_prompt(scenario)
        # 粗略估算: 1 token ≈ 2.5 字符 (中文)
        return len(prompt) // 2

    def switch_version(self, new_version: str) -> Any:
        """切换提示词版本"""
        if new_version not in self.version_map:
            raise ValueError(f"不支持的版本: {new_version}")

        self.version = new_version
        self.prompts = {}

        print(f"🔄 切换到版本: {new_version}")
        self.load_all_prompts()


def main() -> None:
    """测试提示词加载器"""
    print("=" * 60)
    print("小娜提示词加载器 v2.1 测试")
    print("=" * 60)

    # 测试优化版
    print("\n🧪 测试 v2_optimized 版本:")
    loader = XiaonaPromptLoaderV2(version="v2_optimized")

    if not loader.load_cache():
        loader.load_all_prompts()
        loader.save_cache()

    # 测试不同场景
    for scenario in ["general", "patent_writing", "office_action"]:
        prompt = loader.get_full_prompt(scenario)
        tokens = loader.get_token_count(scenario)
        print(f"\n  {scenario}: {len(prompt):,} 字符 ≈ {tokens:,} tokens")

    # 测试版本切换
    print("\n🔄 测试版本切换:")
    loader.switch_version("v1.0")
    tokens_v1 = loader.get_token_count("general")
    print(f"  v1.0 general: ≈ {tokens_v1:,} tokens")


if __name__ == "__main__":
    main()
