#!/usr/bin/env python3
"""
Dolphin提示词管理器

提供结构化的提示词模板,方便在代码中调用Dolphin文档解析服务。

Author: Athena工作平台
Date: 2026-01-16
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class PromptType(Enum):
    """提示词类型"""

    # 基础提示词
    BASIC = "basic"  # 通用文档解析
    LAYOUT = "layout"  # 布局分析
    TABLE = "table"  # 表格解析
    FORMULA = "formula"  # 公式解析
    TEXT = "text"  # 文本解析
    CODE = "code"  # 代码解析

    # 场景化提示词
    PATENT = "patent"  # 专利文档
    ACADEMIC = "academic"  # 学术论文
    TECHNICAL = "technical"  # 技术文档
    LEGAL = "legal"  # 法律文书

    # 专业领域
    MEDICAL = "medical"  # 医学文档
    FINANCIAL = "financial"  # 财务报表
    ENGINEERING = "engineering"  # 工程图纸

    # 高级提示词
    BATCH = "batch"  # 批量处理
    MULTILINGUAL = "multilingual"  # 多语言
    COMPARISON = "comparison"  # 对比分析
    QUALITY_CHECK = "quality_check"  # 质量验证


@dataclass
class PromptConfig:
    """提示词配置"""

    output_format: str = "markdown"  # markdown, json, xml
    preserve_structure: bool = True  # 保持结构
    extract_tables: bool = True  # 提取表格
    extract_formulas: bool = True  # 提取公式
    extract_images: bool = True  # 提取图片
    language: str = "auto"  # auto, zh, en
    quality_level: str = "high"  # low, medium, high


class DolphinPromptManager:
    """Dolphin提示词管理器"""

    def __init__(self):
        """初始化提示词管理器"""
        self._prompts = self._load_prompts()

    def get_prompt(
        self, prompt_type: PromptType, config: PromptConfig | None = None, **kwargs
    ) -> str:
        """
        获取提示词

        Args:
            prompt_type: 提示词类型
            config: 提示词配置
            **kwargs: 额外参数

        Returns:
            完整的提示词字符串
        """
        template = self._prompts.get(prompt_type.value, self._prompts["basic"])

        # 应用配置
        if config:
            template = self._apply_config(template, config)

        # 应用额外参数
        if kwargs:
            template = template.format(**kwargs)

        return template

    def get_custom_prompt(
        self,
        task_description: str,
        requirements: list[str],
        constraints: list[str] | None = None,
        output_format: str = "markdown",
    ) -> str:
        """
        创建自定义提示词

        Args:
            task_description: 任务描述
            requirements: 要求列表
            constraints: 约束条件列表(可选)
            output_format: 输出格式

        Returns:
            自定义提示词
        """
        parts = [f"[任务]{task_description}\n"]

        if requirements:
            parts.append("[要求]")
            for i, req in enumerate(requirements, 1):
                parts.append(f"{i}. {req}")
            parts.append("")

        if constraints:
            parts.append("[约束条件]")
            for i, constraint in enumerate(constraints, 1):
                parts.append(f"- {constraint}")
            parts.append("")

        parts.append(f"[输出格式]{output_format}")

        return "\n".join(parts)

    def _load_prompts(self) -> dict[str, str]:
        """加载提示词模板"""
        return {
            # ========== 基础提示词 ==========
            "basic": """请解析这个文档的内容,按照以下要求输出:

1. 保持原始文档结构:
   - 标题层级(使用 # ## ### 等)
   - 段落结构
   - 列表格式

2. 准确识别并转换:
   - 表格 → Markdown表格
   - 公式 → LaTeX数学公式(使用 $$...$$ 或 $...$)
   - 图片 → ![图片描述](路径)
   - 代码块 → ```语言\\n代码\\n```

3. 文本处理要求:
   - 保持原始文字内容
   - 中文文本不添加额外空格
   - 英文单词之间保留一个空格
   - 标点符号保持原样

4. 输出格式:
   - 使用标准Markdown格式
   - 确保格式正确且可渲染

请开始解析文档。""",
            "layout": """请分析这个文档的布局结构,输出所有元素的阅读顺序。

输出格式要求:
[x1,y1,x2,y2][元素类型][标签1][标签2]...[PAIR_SEP][x1,y1,x2,y2][元素类型]...

元素类型说明:
- sec_0 ~ sec_5: 标题层级(一级到六级)
- para: 普通段落
- tab: 表格
- equ: 数学公式
- fig: 图片/图表
- code: 代码块
- list: 列表项

注意事项:
1. 按照阅读顺序排列元素
2. 坐标使用 [x1,y1,x2,y2] 格式(左上角和右下角)
3. 每个元素用 [PAIR_SEP] 分隔
4. 识别文档的主要结构和层次关系

请开始分析文档布局。""",
            "table": """请解析图片中的表格内容,输出为Markdown表格格式。

要求:
1. 准确识别表格结构(行、列、合并单元格)
2. 提取所有单元格文本内容
3. 识别表头(通常在第一行或有特殊格式)
4. 保持表格的对齐和层次

输出格式:
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 内容1 | 内容2 | 内容3 |

注意事项:
- 空单元格用空字符串表示
- 保留数字和单位的格式
- 识别表格中的公式并转换为LaTeX格式

请开始解析表格。""",
            "formula": """请解析图片中的数学公式,输出为LaTeX格式。

要求:
1. 准确识别所有数学符号和运算符
2. 使用标准LaTeX数学语法
3. 保持公式的层次结构(分数、上下标、矩阵等)
4. 识别并转换特殊符号

常用LaTeX命令参考:
- 分数: \\frac{{分子}}{{分母}}
- 上标: x^{{2}}
- 下标: x_{{i}}
- 根号: \\sqrt{{x}}
- 求和: \\sum_{{i=1}}^{{n}}
- 积分: \\int_{{a}}^{{b}}
- 希腊字母: \\alpha, \\beta, \\gamma, \\delta...
- 矩阵: \\begin{{matrix}} ... \\end{{matrix}}

输出格式:
行内公式: $公式$
块级公式: $$公式$$

请开始解析公式。""",
            "text": """请解析图片中的文本内容。

要求:
1. 准确识别所有文字内容
2. 保持段落结构和换行
3. 识别标题层级
4. 保留列表格式
5. 识别并保留强调格式(加粗、斜体等)

文本处理规则:
- 中文文本保持原样,不添加额外空格
- 英文单词之间保留一个空格
- 标点符号保持原样
- 数字和单位之间保留空格(如:10 kg)

请开始解析文本。""",
            "code": """请解析图片中的代码内容。

要求:
1. 识别代码块及其边界
2. 准确提取代码内容
3. 保留缩进和格式
4. 识别编程语言(如可能)

输出格式:
```language
代码内容
```

注意事项:
- 保持原始缩进
- 保留注释
- 保留特殊字符和符号
- 如无法确定语言,使用 "text" 或不指定语言

请开始解析代码。""",
            # ========== 场景化提示词 ==========
            "patent": """请解析这个专利文档,重点关注以下内容:

1. 专利基本信息:
   - 专利号
   - 专利名称
   - 申请日期
   - 申请人/发明人

2. 技术内容:
   - 技术领域
   - 背景技术
   - 发明内容
   - 具体实施方式
   - 权利要求

3. 格式要求:
   - 保持原始章节结构
   - 准确识别权利要求编号
   - 提取技术参数和数值
   - 识别附图说明

4. 特殊处理:
   - 权利要求使用编号列表
   - 技术术语保持准确
   - 化学式使用LaTeX格式
   - 流程图和框图进行文字描述

输出为结构化的Markdown文档,便于后续技术分析。""",
            "academic": """请解析这篇学术论文,提取以下内容:

1. 论文元数据:
   - 标题
   - 作者
   - 单位/机构
   - 发表时间/会议/期刊
   - 摘要
   - 关键词

2. 论文结构:
   - 引言/Introduction
   - 方法/Methodology
   - 实验/Experiments
   - 结果/Results
   - 讨论/Discussion
   - 结论/Conclusion
   - 参考文献/References

3. 关键内容:
   - 核心公式(LaTeX格式)
   - 表格数据
   - 图片说明
   - 算法描述

4. 格式要求:
   - 保持章节层次结构
   - 公式使用标准LaTeX
   - 表格转换为Markdown表格
   - 参考文献列表格式统一

输出为完整的Markdown论文文档。""",
            "technical": """请解析这个技术文档(用户手册/API文档/技术规格书等):

1. 文档结构:
   - 目录/TOC
   - 章节标题
   - 子章节
   - 附录

2. 内容元素:
   - 文字说明
   - 代码示例
   - 配置参数
   - 命令行指令
   - 输出结果
   - 警告/注意/提示

3. 格式处理:
   - 代码块使用语言标识
   - 命令行使用 ```bash
   - 警告使用 > **警告**
   - 注意使用 > **注意**
   - 提示使用 > **提示**

4. 特殊要求:
   - 保持技术术语准确
   - 保留代码缩进
   - 识别超链接和引用
   - 提取版本信息

输出为清晰易读的Markdown技术文档。""",
            "legal": """请解析这个法律文书(判决书/合同/法规等):

1. 文书类型识别:
   - 判决书/裁定书
   - 合同/协议
   - 法律法规
   - 其他法律文书

2. 关键信息提取:
   - 案号/文号
   - 当事人信息
   - 案由/合同类型
   - 日期时间
   - 关键条款
   - 判决结果/合同要点

3. 格式要求:
   - 保持法律文书结构
   - 条款使用编号列表
   - 金额数字保持准确
   - 日期使用标准格式
   - 引用条款标注清晰

4. 特殊处理:
   - 法律术语保持准确
   - 保留法律效力表述
   - 识别附件和附录

输出为结构化的Markdown法律文书。""",
            # ========== 专业领域提示词 ==========
            "medical": """请解析这个医学文档(病历/检查报告/医学文献等):

1. 患者信息(如适用):
   - 姓名/ID
   - 性别/年龄
   - 就诊日期

2. 医学内容:
   - 主诉
   - 现病史
   - 既往史
   - 体格检查
   - 辅助检查
   - 诊断
   - 治疗方案
   - 用药信息

3. 格式要求:
   - 医学术语保持准确
   - 数值和单位保留(如:血压 120/80 mm_hg)
   - 化学式使用LaTeX
   - 表格数据准确提取

4. 特殊处理:
   - 药品名称使用通用名
   - 剂量单位保持标准(mg, ml, μg等)
   - 识别关键指标和参考范围

输出为专业的Markdown医学文档。""",
            "financial": """请解析这个财务报表(资产负债表/利润表/现金流量表等):

1. 报表基本信息:
   - 报表类型
   - 报告期间
   - 公司名称
   - 货币单位

2. 关键数据:
   - 所有表格数据
   - 数值字段
   - 百分比
   - 同比/环比数据

3. 格式要求:
   - 表格使用Markdown格式
   - 数值保留原始精度
   - 金额使用千分位分隔(如:1,234,567.89)
   - 负数使用括号或负号

4. 特殊处理:
   - 识别总计/小计行
   - 提取关键财务指标
   - 保留注释和说明

输出为准确的Markdown财务报表。""",
            "engineering": """请解析这个工程图纸(建筑图/机械图/电路图等):

1. 图纸信息:
   - 图纸名称
   - 图号
   - 比例
   - 日期
   - 绘制/审核人员

2. 图纸内容:
   - 主要视图
   - 尺寸标注
   - 技术要求
   - 材料规格
   - 图例说明

3. 格式要求:
   - 使用文字描述图纸内容
   - 尺寸标注提取为文本
   - 技术要求列表化
   - 图例转换为表格

4. 特殊处理:
   - 识别关键尺寸
   - 提取公差信息
   - 识别材料和规格
   - 标注符号说明

由于工程图纸的复杂性,请尽可能详细地描述图纸内容。""",
            # ========== 高级提示词 ==========
            "batch": """请批量解析这些文档,为每个文档执行以下操作:

1. 文档识别:
   - 识别文档类型
   - 提取文档元数据
   - 确定页面数量

2. 内容解析:
   - 按页面顺序解析
   - 保持跨页内容的连续性
   - 识别页眉页脚(排除)

3. 输出要求:
   - 每个文档独立输出
   - 使用文档名称作为标题
   - 保持文档间分隔

4. 质量控制:
   - 检查解析完整性
   - 验证关键信息提取
   - 标注不确定的内容

请开始批量解析。""",
            "multilingual": """请解析这个多语言文档(中英文混合):

1. 语言识别:
   - 识别每个段落的语言
   - 标注语言类型(中文/英文/其他)

2. 内容提取:
   - 准确提取各语言内容
   - 保持原始语言
   - 识别双语对照内容

3. 格式处理:
   - 中文文本:不添加额外空格
   - 英文文本:单词间保留空格
   - 混合文本:按语言规则处理

4. 特殊处理:
   - 专业术语保持原样
   - 识别翻译对照
   - 保留语言切换标记

输出为准确的多语言Markdown文档。""",
            "comparison": """请解析这两个文档的对比内容:

1. 文档识别:
   - 识别文档A和文档B
   - 确定对比维度
   - 提取对比基准

2. 对比内容:
   - 相同点
   - 不同点
   - 差异程度
   - 变化趋势

3. 格式要求:
   - 使用对比表格
   - 标注变化(新增/删除/修改)
   - 使用符号标记差异

4. 输出结构:
   - 文档概述
   - 详细对比
   - 差异汇总
   - 变化影响分析

输出为清晰的对比分析报告。""",
            "quality_check": """请解析文档并进行质量验证:

1. 完整性检查:
   - 确认所有页面已解析
   - 检查内容是否完整
   - 识别缺失部分

2. 准确性验证:
   - 检查关键数据
   - 验证数字和单位
   - 确认专业术语

3. 格式验证:
   - 检查Markdown格式
   - 验证表格结构
   - 确认公式语法

4. 问题标注:
   - 标注不确定的内容
   - 指出可能的错误
   - 建议人工复核部分

5. 质量评分:
   - 完整性评分(0-100)
   - 准确性评分(0-100)
   - 格式正确性评分(0-100)
   - 综合评分

输出包含解析内容和质量报告.""",
        }

    def _apply_config(self, template: str, config: PromptConfig) -> str:
        """应用配置到提示词"""
        # 这里可以根据配置调整提示词
        # 例如:添加特定的格式要求、质量控制要求等

        additions = []

        if config.quality_level == "high":
            additions.append("\n5. 质量要求:")
            additions.append("   - 确保高准确率")
            additions.append("   - 验证关键信息")
            additions.append("   - 标注不确定内容")

        if not config.extract_tables:
            additions.append("\n注意:表格内容转换为文字描述")

        if not config.extract_formulas:
            additions.append("\n注意:公式使用文字描述")

        if additions:
            return template + "\n".join(additions)

        return template


# 全局实例
_prompt_manager = None


def get_prompt_manager() -> DolphinPromptManager:
    """获取提示词管理器单例"""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = DolphinPromptManager()
    return _prompt_manager


# 便捷函数
def get_prompt(prompt_type: PromptType | None = None, config: PromptConfig | None = None, **kwargs) -> str:
    """
    获取提示词的便捷函数

    Args:
        prompt_type: 提示词类型
        config: 提示词配置
        **kwargs: 额外参数

    Returns:
        提示词字符串

    示例:
        >>> prompt = get_prompt(PromptType.PATENT)
        >>> prompt = get_prompt(PromptType.TABLE, config=PromptConfig(quality_level="high"))
    """
    manager = get_prompt_manager()
    return manager.get_prompt(prompt_type, config, **kwargs)


def create_custom_prompt(
    task_description: str,
    requirements: list[str],
    constraints: list[str] | None = None,
    output_format: str = "markdown",
) -> str:
    """
    创建自定义提示词的便捷函数

    Args:
        task_description: 任务描述
        requirements: 要求列表
        constraints: 约束条件列表
        output_format: 输出格式

    Returns:
        自定义提示词

    示例:
        >>> prompt = create_custom_prompt(
        ...     "提取专利权利要求",
        ...     ["保持原始编号", "识别技术术语"],
        ...     ["不添加额外内容"]
        ... )
    """
    manager = get_prompt_manager()
    return manager.get_custom_prompt(task_description, requirements, constraints, output_format)


# 预定义配置
PREDEFINED_CONFIGS = {
    "fast": PromptConfig(
        quality_level="low",
        extract_formulas=False,
        extract_tables=False,
    ),
    "standard": PromptConfig(
        quality_level="medium",
        extract_formulas=True,
        extract_tables=True,
    ),
    "high_quality": PromptConfig(
        quality_level="high",
        extract_formulas=True,
        extract_tables=True,
        extract_images=True,
    ),
}


def get_config(config_name: str) -> PromptConfig:
    """
    获取预定义配置

    Args:
        config_name: 配置名称 (fast, standard, high_quality)

    Returns:
        PromptConfig实例
    """
    return PREDEFINED_CONFIGS.get(config_name, PREDEFINED_CONFIGS["standard"])
