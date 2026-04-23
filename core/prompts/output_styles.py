from __future__ import annotations
"""
输出风格管理系统

借鉴 kode-agent 的输出风格设计，提供可配置的输出风格系统。
支持内置风格和用户自定义风格（从 .md 文件加载）。

内置风格：
- Default: 保持当前行为（大姐姐角色）
- Professional: 法律专业风格（正式、权威）
- Educational: 教学风格（附带知识讲解）
- Concise: 极简风格（少于4行回答）

自定义风格：
- 从 ~/.athena/output-styles/ 和 .athena/output-styles/ 加载 .md 文件

Author: Athena Team
"""

import logging
import threading
from dataclasses import dataclass
from pathlib import Path

from core.agents.declarative.utils import parse_frontmatter

logger = logging.getLogger("prompts.output_styles")


@dataclass
class OutputStyleDefinition:
    """
    输出风格定义

    Attributes:
        name: 风格名称（唯一标识符）
        description: 风格描述
        prompt: 风格提示词（注入到系统提示词中）
        source: 来源（builtin / user / project）
        keep_default_instructions: 是否保留默认指令（False 则完全替换）
    """
    name: str
    description: str = ""
    prompt: str = ""
    source: str = "builtin"
    keep_default_instructions: bool = True


class OutputStyleManager:
    """
    输出风格管理器

    管理内置和自定义输出风格的加载、切换和应用。

    使用示例：
        manager = OutputStyleManager()
        manager.load_all_styles()

        # 切换风格
        manager.set_current_style("professional")

        # 获取风格提示词注入内容
        additions = manager.get_style_prompt_additions()
    """

    def __init__(self, project_root: str | Path | None = None):
        self._project_root = Path(project_root) if project_root else Path.cwd()
        self._styles: dict[str, OutputStyleDefinition] = {}
        self._current_style: Optional[str] = None
        self._loaded = False

    def _get_builtin_styles(self) -> list[OutputStyleDefinition]:
        """获取内置风格列表"""
        return [
            OutputStyleDefinition(
                name="default",
                description="默认风格 - 保持小娜大姐姐角色",
                prompt="",  # 空字符串表示不注入额外指令
                source="builtin",
                keep_default_instructions=True,
            ),
            OutputStyleDefinition(
                name="professional",
                description="法律专业风格 - 正式权威，移除角色化",
                prompt="""\
## 输出风格：法律专业模式

### 基本原则
- 使用正式的法律文书用语
- 严格引用法条，标注完整出处
- 采用"首先→其次→再次→结论"的结构化表述
- 移除角色化互动（大姐姐语气、表情符号等）

### 回答格式
```
[法律问题概述]

## 法律依据
1. 《专利法》第X条第X款：[条文引用]
2. 《审查指南》第X部分：[指引引用]

## 分析意见
首先，[要点一]；
其次，[要点二]；
再次，[要点三]。

## 结论与建议
[明确的法律结论和实务建议]

## 风险提示
[潜在风险和注意事项]
```

### 注意事项
- 不使用"亲爱的爸爸"等角色化称呼
- 不使用表情符号
- 法律结论必须有法条支撑
- 分析过程体现专业严谨性
""",
                source="builtin",
                keep_default_instructions=False,
            ),
            OutputStyleDefinition(
                name="educational",
                description="教学风格 - 在回答中附带法律知识讲解",
                prompt="""\
## 输出风格：教学模式

### 核心原则
在回答法律问题的同时，主动解释相关法律概念和知识，帮助用户理解法律逻辑。

### 回答结构
1. **简要回答**: 先给出直接结论
2. **法律知识**: 解释涉及的法律概念
3. **实务要点**: 说明在实践中如何应用
4. **延伸学习**: 推荐进一步了解的内容

### 知识讲解要求
- 使用通俗语言解释法律术语
- 适当使用生活类比帮助理解
- 标注相关法条的学习优先级
- 给出实际案例说明应用场景

### 示例
> 用户问："什么是创造性？"

回答结构：
1. 简要回答：创造性是指...
2. 知识讲解：
   - 法律定义（《专利法》第22条第3款）
   - 通俗理解：就像...
   - "三步法"判断流程
3. 实务要点：在答复审查意见时...
4. 延伸学习：建议了解"技术启示"概念
""",
                source="builtin",
                keep_default_instructions=True,
            ),
            OutputStyleDefinition(
                name="concise",
                description="极简风格 - 少于4行回答，只给核心结论",
                prompt="""\
## 输出风格：极简模式

### 核心规则
- 回答不超过4行
- 只给核心结论和关键依据
- 使用列表，不用段落
- 省略问候、过渡语和角色化表达

### Few-shot 示例

用户: "这个技术方案有新颖性吗？"
回答:
- 有新颖性。对比文件D1未公开特征X。
- 依据：专利法第22条第2款。
- 建议：在独立权利要求中保留该特征。
- 风险：需注意D2是否隐含公开。

用户: "创造性怎么判断？"
回答:
- 三步法：确定最接近现有技术→确定区别特征→判断技术启示。
- 关键：区别特征是否解决技术问题。
- 参考：审查指南第二部分第四章。
""",
                source="builtin",
                keep_default_instructions=False,
            ),
        ]

    def _load_custom_styles_from_dir(
        self, dir_path: Path, source_name: str
    ) -> dict[str, OutputStyleDefinition]:
        """
        从目录加载自定义风格 .md 文件

        Args:
            dir_path: 目录路径
            source_name: 来源名称

        Returns:
            加载的风格定义字典
        """
        styles = {}
        if not dir_path.is_dir():
            return styles

        for md_file in dir_path.glob("*.md"):
            try:
                content = md_file.read_text(encoding="utf-8")
                style = self._parse_style_file(content, md_file.stem, source_name)
                if style:
                    styles[style.name] = style
            except Exception as e:
                logger.warning(f"加载风格文件失败 {md_file}: {e}")

        return styles

    def _parse_style_file(
        self, content: str, fallback_name: str, source_name: str
    ) -> OutputStyleDefinition | None:
        """
        解析风格 .md 文件

        使用公共 parse_frontmatter() 解析 YAML frontmatter。

        格式：
        ---
        name: my-style
        description: "我的自定义风格"
        keep_default_instructions: true
        ---

        [风格提示词正文]
        """
        metadata, body = parse_frontmatter(content)

        name = metadata.get("name", fallback_name)
        description = metadata.get("description", "")
        keep_default = metadata.get("keep_default_instructions", True)

        return OutputStyleDefinition(
            name=name,
            description=description,
            prompt=body,
            source=source_name,
            keep_default_instructions=keep_default,
        )

    def load_all_styles(self, force_reload: bool = False) -> dict[str, OutputStyleDefinition]:
        """
        加载所有风格定义（内置 + 自定义）

        Args:
            force_reload: 是否强制重新加载

        Returns:
            {name: OutputStyleDefinition} 字典
        """
        if self._loaded and not force_reload:
            return self._styles.copy()

        self._styles.clear()

        # 1. 加载内置风格
        for style in self._get_builtin_styles():
            self._styles[style.name] = style

        # 2. 加载用户级自定义风格
        user_dir = Path.home() / ".athena" / "output-styles"
        user_styles = self._load_custom_styles_from_dir(user_dir, "user")
        for name, style in user_styles.items():
            self._styles[name] = style  # 用户级覆盖内置

        # 3. 加载项目级自定义风格
        project_dir = self._project_root / ".athena" / "output-styles"
        project_styles = self._load_custom_styles_from_dir(project_dir, "project")
        for name, style in project_styles.items():
            self._styles[name] = style  # 项目级优先级最高

        self._loaded = True
        logger.info(f"加载 {len(self._styles)} 个输出风格")
        return self._styles.copy()

    def get_style(self, name: str) -> OutputStyleDefinition | None:
        """获取指定名称的风格定义"""
        if not self._loaded:
            self.load_all_styles()
        return self._styles.get(name)

    def get_current_style(self) -> OutputStyleDefinition | None:
        """获取当前激活的风格"""
        if not self._loaded:
            self.load_all_styles()
        if self._current_style is None or self._current_style == "default":
            return None
        return self._styles.get(self._current_style)

    def set_current_style(self, name: str) -> None:
        """
        设置当前风格

        Args:
            name: 风格名称

        Raises:
            ValueError: 风格不存在
        """
        if not self._loaded:
            self.load_all_styles()
        if name not in self._styles:
            available = ", ".join(self._styles.keys())
            raise ValueError(f"未知风格: {name}. 可用风格: {available}")
        self._current_style = name
        logger.info(f"切换输出风格: {name}")

    def reset_style(self) -> None:
        """重置为默认风格"""
        self._current_style = None

    def get_style_prompt_additions(self) -> list[str]:
        """
        获取当前风格的提示词注入内容

        Returns:
            需要注入到系统提示词中的文本片段列表
        """
        style = self.get_current_style()
        if style is None or not style.prompt:
            return []
        return [style.prompt]

    def list_styles(self) -> list[dict[str, str]]:
        """列出所有可用风格"""
        if not self._loaded:
            self.load_all_styles()
        return [
            {
                "name": s.name,
                "description": s.description,
                "source": s.source,
            }
            for s in self._styles.values()
        ]


# 模块级单例
_manager_instance: OutputStyleManager | None = None
_manager_lock = threading.Lock()


def get_style_manager(project_root: Optional[str] = None) -> OutputStyleManager:
    """获取 OutputStyleManager 单例（线程安全）"""
    global _manager_instance
    if _manager_instance is None:
        with _manager_lock:
            if _manager_instance is None:
                _manager_instance = OutputStyleManager(project_root)
    elif project_root is not None:
        # 需要指定 project_root 时返回新实例，不覆盖全局单例
        return OutputStyleManager(project_root)
    return _manager_instance


__all__ = [
    "OutputStyleDefinition",
    "OutputStyleManager",
    "get_style_manager",
]
