#!/usr/bin/env python3
"""
小娜提示词加载器 - 生产环境
负责加载和管理小娜的所有提示词
"""

from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from typing import Any


class XiaonaPromptLoader:
    """小娜提示词加载器"""

    def __init__(self, base_path: str = None):
        """
        初始化提示词加载器

        Args:
            base_path: 提示词根目录，默认为 /Users/xujian/Athena工作平台/prompts
        """
        self.base_path = Path(base_path or "/Users/xujian/Athena工作平台/prompts")
        self.prompts = {}
        self.metadata = {
            "version": "v2.0",
            "last_updated": datetime.now().isoformat(),
            "total_prompts": 0
        }

    def load_all_prompts(self) -> dict[str, str]:
        """
        加载所有提示词

        Returns:
            提示词字典 {名称: 内容}
        """
        print("📚 开始加载小娜提示词系统...")

        # 1. 加载基础层提示词 (L1)
        foundation = self._load_foundation()
        self.prompts["foundation"] = foundation

        # 2. 加载数据层配置 (L2)
        data_layer = self._load_data_layer()
        self.prompts["data_layer"] = data_layer

        # 3. 加载能力层提示词 (L3)
        capabilities = self._load_capabilities()
        self.prompts["capabilities"] = capabilities

        # 4. 加载业务层提示词 (L4)
        business = self._load_business_layer()
        self.prompts["business"] = business

        # 5. 加载人机协作协议
        hitl = self._load_hitl_protocol()
        self.prompts["hitl"] = hitl

        # 更新元数据
        self.metadata["total_prompts"] = len(self.prompts)

        print(f"✅ 提示词加载完成！共加载 {self.metadata['total_prompts']} 个模块")
        self._print_summary()

        return self.prompts

    def _load_foundation(self) -> str:
        """加载基础层提示词"""
        path = self.base_path / "foundation" / "xiaona_l1_foundation.md"
        return self._read_file(path, "L1基础层")

    def _load_data_layer(self) -> str:
        """加载数据层配置"""
        # L2主要是数据源信息，可以从蓝图文件提取
        path = self.base_path.parent / "design" / "xiaona_implementation_blueprint.md"
        content = self._read_file(path, "L2数据层", optional=True)
        if content:
            # 提取数据层部分
            if "## 🏗️ 第二部分：四层提示词架构" in content:
                parts = content.split("## 🏗️ 第二部分：四层提示词架构")
                if len(parts) > 1:
                    data_part = parts[1].split("##")[0]  # 取第二部分，到下一个##之前
                    return f"# L2: 数据层\n\n{data_part}"
        return "# L2: 数据层\n\n数据源配置请参考设计蓝图"

    def _load_capabilities(self) -> str:
        """加载能力层提示词"""
        capabilities_dir = self.base_path / "capability"
        if not capabilities_dir.exists():
            return "# L3: 能力层\n\n能力层提示词文件未找到"

        capabilities = []
        for file in sorted(capabilities_dir.glob("cap*.md")):
            content = self._read_file(file, file.name)
            capabilities.append(f"\n\n# {file.stem.upper()}\n\n{content}")

        return f"# L3: 能力层\n\n{chr(10).join(capabilities)}"

    def _load_business_layer(self) -> str:
        """加载业务层提示词"""
        business_dir = self.base_path / "business"
        if not business_dir.exists():
            return "# L4: 业务层\n\n业务层提示词文件未找到"

        business_tasks = []
        for file in sorted(business_dir.glob("task_*.md")):
            content = self._read_file(file, file.name)
            business_tasks.append(f"\n\n# {file.stem.upper()}\n\n{content}")

        return f"# L4: 业务层\n\n{chr(10).join(business_tasks)}"

    def _load_hitl_protocol(self) -> str:
        """加载人机协作协议"""
        path = self.base_path / "foundation" / "hitl_protocol.md"
        return self._read_file(path, "HITL协议")

    def _read_file(self, path: Path, name: str, optional: bool = False) -> str:
        """读取文件内容"""
        try:
            with open(path, encoding='utf-8') as f:
                content = f.read()
            print(f"  ✅ {name}")
            return content
        except FileNotFoundError:
            if optional:
                print(f"  ⚠️  {name} (未找到)")
                return ""
            else:
                print(f"  ❌ {name} (未找到)")
                raise
        except Exception as e:
            print(f"  ❌ {name} (读取失败: {e})")
            if not optional:
                raise
            return ""

    def _print_summary(self) -> Any:
        """打印加载摘要"""
        print("\n📊 提示词模块统计:")
        for key in ["foundation", "data_layer", "capabilities", "business", "hitl"]:
            if key in self.prompts and self.prompts[key]:
                char_count = len(self.prompts[key])
                print(f"  - {key}: {char_count:,} 字符")

    def get_prompt(self, layer: str) -> str:
        """
        获取指定层的提示词

        Args:
            layer: 层名 (foundation/data_layer/capabilities/business/hitl)

        Returns:
            提示词内容
        """
        return self.prompts.get(layer, "")

    def get_full_prompt(self, task_type: str = "general") -> str:
        """
        获取完整提示词

        Args:
            task_type: 任务类型 (general/patent_writing/office_action/etc)

        Returns:
            完整提示词
        """
        parts = []

        # 基础层（必需）
        if "foundation" in self.prompts:
            parts.append(self.prompts["foundation"])

        # 数据层（必需）
        if "data_layer" in self.prompts:
            parts.append(self.prompts["data_layer"])

        # 能力层（必需）
        if "capabilities" in self.prompts:
            parts.append(self.prompts["capabilities"])

        # 业务层（根据任务类型选择性加载）
        if task_type == "patent_writing" and "business" in self.prompts:
            # 只加载专利撰写相关任务
            business_content = self._filter_business_tasks(
                self.prompts["business"],
                ["task_1_1", "task_1_2", "task_1_3", "task_1_4", "task_1_5"]
            )
            parts.append(business_content)
        elif task_type == "office_action" and "business" in self.prompts:
            # 只加载意见答复相关任务
            business_content = self._filter_business_tasks(
                self.prompts["business"],
                ["task_2_1", "task_2_2", "task_2_3", "task_2_4"]
            )
            parts.append(business_content)
        elif "business" in self.prompts:
            # 加载所有业务任务
            parts.append(self.prompts["business"])

        # HITL协议（必需）
        if "hitl" in self.prompts:
            parts.append(self.prompts["hitl"])

        return "\n\n---\n\n".join(parts)

    def _filter_business_tasks(self, business_content: str, task_prefixes: list[str]) -> str:
        """过滤业务任务"""
        lines = business_content.split('\n')
        filtered = []
        current_task = None
        capture = False

        for line in lines:
            # 检查是否是任务开始
            is_task_start = False
            for prefix in task_prefixes:
                if f"# {prefix.upper()}" in line or line.strip() == f"# {prefix}":
                    current_task = prefix
                    capture = True
                    is_task_start = True
                    filtered.append(line)
                    break

            if is_task_start:
                continue

            if capture:
                # 检查是否到了下一个任务
                if line.strip().startswith("# ") and not any(f"#{p}" in line for p in task_prefixes):
                    break
                filtered.append(line)

        return "\n".join(filtered)

    def save_cache(self, cache_path: str = None) -> None:
        """
        保存提示词缓存

        Args:
            cache_path: 缓存文件路径
        """
        if cache_path is None:
            cache_path = self.base_path / ".cache" / "prompts_cache.json"
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
        """
        从缓存加载提示词

        Args:
            cache_path: 缓存文件路径

        Returns:
            是否成功加载
        """
        if cache_path is None:
            cache_path = self.base_path / ".cache" / "prompts_cache.json"
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


def main() -> None:
    """测试提示词加载器"""
    loader = XiaonaPromptLoader()

    # 尝试从缓存加载
    if not loader.load_cache():
        # 缓存不存在，重新加载
        loader.load_all_prompts()
        # 保存缓存
        loader.save_cache()

    # 测试获取提示词
    print("\n🧪 测试获取提示词:")

    # 获取专利撰写任务提示词
    patent_prompt = loader.get_full_prompt("patent_writing")
    print(f"专利撰写提示词长度: {len(patent_prompt):,} 字符")

    # 获取意见答复任务提示词
    office_prompt = loader.get_full_prompt("office_action")
    print(f"意见答复提示词长度: {len(office_prompt):,} 字符")


if __name__ == "__main__":
    main()
