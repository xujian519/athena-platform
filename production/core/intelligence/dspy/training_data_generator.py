#!/usr/bin/env python3
"""
DSPy训练数据生成器
DSPy Training Data Generator for Athena Platform

自动生成符合DSPy格式的专利分析训练数据

作者: 小娜·天秤女神
创建时间: 2025-12-29
版本: 1.0.0
"""

from __future__ import annotations
import json
import logging
import random
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from core.logging_config import setup_logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()


@dataclass
class PatentCase:
    """专利案例数据结构"""

    case_id: str
    case_type: str  # novelty, creative, disclosure, clarity, complex
    case_title: str
    technical_field: str
    case_description: str
    prior_art: str
    legal_issues: list[str]
    analysis_result: str
    risk_assessment: str
    recommended_actions: str

    def to_dspy_example(self) -> Any:
        """转换为DSPy Example格式"""
        import dspy

        return dspy.Example(
            user_input=self.case_description,
            context=f"现有技术: {self.prior_art}\n法律争议点: {', '.join(self.legal_issues)}",
            task_type=f"capability_2_{self.case_type}",
            analysis_result=self.analysis_result,
            risk_assessment=self.risk_assessment,
            recommended_actions=self.recommended_actions,
        ).with_inputs("user_input", "context", "task_type")


class TrainingDataGenerator:
    """训练数据生成器"""

    def __init__(self):
        """初始化生成器"""
        self.technical_fields = [
            "智能汽车",
            "医疗器械",
            "人工智能",
            "生物医药",
            "新能源",
            "半导体",
            "通信技术",
            "机器人",
            "材料科学",
            "航空航天",
        ]

        self.case_types = {
            "novelty": "新颖性分析",
            "creative": "创造性分析",
            "disclosure": "充分公开分析",
            "clarity": "清楚性分析",
            "complex": "综合分析",
        }

        # 模板库
        self.templates = self._load_templates()

    def _load_templates(self) -> dict[str, dict]:
        """加载案例模板"""
        return {
            "novelty": {
                "title_template": "{field}领域{feature}新颖性争议案",
                "description_template": """
涉案专利: {patent_title}
专利号: CN{patent_number}
发明人: {inventor}
申请日: {application_date}

[技术方案]
{technical_solution}

[对比文件]
{comparison_docs}

[争议焦点]
{dispute_point}
                """,
                "analysis_template": """
[新颖性分析]
1. 对比文件分析
{comparison_analysis}

2. 区别技术特征
{distinguishing_features}

3. 判断结论
{conclusion}
                """,
            },
            "creative": {
                "title_template": "{field}领域{feature}创造性争议案",
                "description_template": """
涉案专利: {patent_title}
专利号: CN{patent_number}
发明人: {inventor}

[技术背景]
{background}

[技术方案]
{technical_solution}

[对比文件]
{comparison_docs}

[争议焦点]
{dispute_point}
                """,
                "analysis_template": """
[创造性分析]
1. 最接近现有技术确定
{closest_prior_art}

2. 区别特征与技术问题
{distinguishing_features_and_problem}

3. 技术效果分析
{technical_effects}

4. 显著性判断
{significance_judgment}

5. 结论
{conclusion}
                """,
            },
            "disclosure": {
                "title_template": "{field}领域{feature}充分公开争议案",
                "analysis_template": """
[充分公开分析]
1. 技术方案公开程度
{disclosure_level}

2. 实施例描述
{embodiments}

3. 技术效果验证
{effects_verification}

4. 再现性评估
{reproducibility}

5. 结论
{conclusion}
                """,
            },
        }

    def generate_case(
        self, case_type: str, technical_field: str | None = None, **kwargs
    ) -> PatentCase:
        """生成单个案例

        Args:
            case_type: 案例类型 (novelty, creative, disclosure, clarity, complex)
            technical_field: 技术领域(可选,默认随机)
            **kwargs: 其他自定义参数

        Returns:
            PatentCase对象
        """
        if technical_field is None:
            technical_field = random.choice(self.technical_fields)

        case_id = f"{case_type.upper()}_{random.randint(1000, 9999)}"

        # 获取模板
        template = self.templates.get(case_type, self.templates["novelty"])

        # 生成案例内容
        case_title = self._generate_title(case_type, technical_field, template)
        case_description = self._generate_description(case_type, technical_field, template)
        prior_art = self._generate_prior_art(case_type, technical_field)
        legal_issues = self._get_legal_issues(case_type)
        analysis_result = self._generate_analysis(case_type, template)
        risk_assessment = random.choice(["低风险", "中风险", "高风险"])
        recommended_actions = self._generate_recommendations(case_type, risk_assessment)

        return PatentCase(
            case_id=case_id,
            case_type=case_type,
            case_title=case_title,
            technical_field=technical_field,
            case_description=case_description.strip(),
            prior_art=prior_art.strip(),
            legal_issues=legal_issues,
            analysis_result=analysis_result.strip(),
            risk_assessment=risk_assessment,
            recommended_actions=recommended_actions,
        )

    def _generate_title(self, case_type: str, field: str, template: dict) -> str:
        """生成案例标题"""
        features = {
            "novelty": ["结构改进", "方法创新", "应用拓展", "组合创新", "功能增强"],
            "creative": ["复合物", "新工艺", "优化算法", "集成系统", "协同方案"],
            "disclosure": ["制备方法", "检测技术", "控制系统", "数据处理", "生物材料"],
            "clarity": ["装置结构", "成分配比", "工艺参数", "使用方法", "应用领域"],
            "complex": ["综合技术", "集成应用", "系统方案", "平台架构", "生态方案"],
        }
        feature = random.choice(features.get(case_type, features["novelty"]))
        return template["title_template"].format(field=field, feature=feature)

    def _generate_description(self, case_type: str, field: str, template: dict) -> str:
        """生成案情描述"""
        patent_number = f"20{random.randint(15, 23)}{random.randint(100000, 999999)}X"
        inventors = ["张某", "李某", "王某", "赵某", "刘某"]
        inventor = random.choice(inventors)

        application_date = (
            f"{random.randint(2015, 2023)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        )

        if case_type == "novelty":
            return template["description_template"].format(
                patent_title=f"一种{field}领域的{random.choice(['装置', '方法', '系统', '设备'])}",
                patent_number=patent_number,
                inventor=inventor,
                application_date=application_date,
                technical_solution=self._generate_technical_solution(field),
                comparison_docs=self._generate_comparison_docs(),
                dispute_point=random.choice(
                    [
                        "对比文件D1是否公开了涉案专利的全部技术特征",
                        "区别技术特征是否属于本领域的公知常识",
                        "涉案专利与D1的技术方案是否实质相同",
                    ]
                ),
            )
        elif case_type == "creative":
            return template["description_template"].format(
                patent_title=f"一种{field}领域的{random.choice(['复合物', '新工艺', '优化方法', '集成系统'])}",
                patent_number=patent_number,
                inventor=inventor,
                background=self._generate_background(field),
                technical_solution=self._generate_technical_solution(field),
                comparison_docs=self._generate_comparison_docs(),
                dispute_point=random.choice(
                    [
                        "区别技术特征是否显而易见",
                        "是否产生了预料不到的技术效果",
                        "技术方案是否属于要素省略或步骤简化",
                    ]
                ),
            )
        else:
            return (
                f"涉案专利涉及{field}领域,专利号: CN{patent_number}\n\n"
                + self._generate_technical_solution(field)
            )

    def _generate_technical_solution(self, field: str) -> str:
        """生成技术方案描述"""
        components = {
            "智能汽车": ["传感器模块", "控制器", "执行机构", "通信模块", "人机界面"],
            "医疗器械": ["检测探头", "信号处理器", "显示单元", "报警装置", "电源模块"],
            "人工智能": ["数据采集层", "特征提取模块", "算法模型", "输出接口", "存储单元"],
            "生物医药": ["活性成分", "辅料", "制剂形式", "给药途径", "剂量范围"],
            "新能源": ["电池单元", "管理系统", "保护电路", "充电接口", "散热结构"],
            "半导体": ["衬底材料", "外延层", "电极结构", "介质层", "互连结构"],
            "通信技术": ["发射模块", "接收模块", "处理单元", "天线系统", "控制接口"],
            "机器人": ["机械臂", "驱动单元", "传感器阵列", "控制系统", "执行末端"],
            "材料科学": ["基体材料", "增强相", "界面层", "涂层", "添加剂"],
            "航空航天": ["动力系统", "导航模块", "控制单元", "通信系统", "机身结构"],
        }

        field_components = components.get(field, components["智能汽车"])
        innovation_type = random.choice(["新装置", "新方法", "新系统", "新工艺"])
        features_list = "\n".join(
            [f"- {comp}" for comp in random.sample(field_components, min(4, len(field_components)))]
        )
        working_principle = random.choice(
            [
                "通过各模块协同工作,实现高效处理",
                "采用闭环控制策略,确保系统稳定性",
                "利用智能算法优化性能指标",
                "基于模块化设计,便于扩展维护",
            ]
        )
        technical_effects = random.choice(
            [
                "提高了系统响应速度,降低了能耗",
                "增强了检测精度,减少了误报率",
                "简化了操作流程,提升了用户体验",
                "降低了生产成本,提高了产品可靠性",
            ]
        )

        return f"""
[技术方案]
涉案专利提供了一种{field}领域的{innovation_type},包括以下技术特征:
{features_list}

[工作原理]
{working_principle}

[技术效果]
{technical_effects}
        """

    def _generate_background(self, field: str) -> str:
        """生成技术背景"""
        return f"""
{field}领域是当前技术发展的热点方向。
现有技术存在以下问题:
- 问题1: 效率较低,成本较高
- 问题2: 精度不足,稳定性差
- 问题3: 结构复杂,维护困难

因此,需要一种新的技术方案来解决上述问题。
        """

    def _generate_prior_art(self, case_type: str, field: str) -> str:
        """生成现有技术描述"""
        num_docs = random.randint(1, 3)
        prior_art_desc = []

        for i in range(num_docs):
            chr(65 + i)  # A, B, C
            prior_art_desc.append(f"""
对比文件D{num_docs}:
文献类型: {random.choice(['中国发明专利', '中国实用新型专利', '外国专利', '科技论文', '技术标准'])}
公开号: {random.choice(['CN', 'US', 'EP', 'WO'])}{random.randint(1000000, 9999999)}{random.choice(['A', 'B1', 'B2'])}
公开日: {random.randint(2010, 2022)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}

公开内容:
{self._generate_prior_art_content(field)}
            """)

        return "\n".join(prior_art_desc)

    def _generate_prior_art_content(self, field: str) -> str:
        """生成现有技术具体内容"""
        contents = [
            "公开了类似的技术结构,包含传感器和处理单元",
            "披露了相关的方法步骤,包括数据采集和处理",
            "描述了相似的功能模块,实现基本的控制功能",
            "揭示了相关的技术原理,采用类似的算法",
            "展示了相近的应用场景,解决类似的技术问题",
        ]
        return random.choice(contents) + "\n" + random.choice(contents)

    def _generate_comparison_docs(self) -> str:
        """生成对比文件列表"""
        return """
对比文件1: D1 - CN2017XXXXXXXU(最接近现有技术)
对比文件2: D2 - CN2016XXXXXXXA(补充参考)
对比文件3: D3 - US2018XXXXXXXA1(相关技术)
        """

    def _get_legal_issues(self, case_type: str) -> list[str]:
        """获取法律争议点"""
        issues_map = {
            "novelty": ["新颖性"],
            "creative": ["创造性"],
            "disclosure": ["充分公开"],
            "clarity": ["清楚性"],
            "complex": ["新颖性", "创造性", "充分公开"],
        }
        return issues_map.get(case_type, ["新颖性"])

    def _generate_analysis(self, case_type: str, template: dict) -> str:
        """生成分析结果"""
        if case_type == "novelty":
            comparison_analysis = random.choice(
                [
                    "D1公开了涉案专利的大部分技术特征,但未公开区别特征X",
                    "D1与涉案专利的技术领域、所要解决的技术问题基本相同",
                    "D1公开了相似的技术手段,但具体实现方式存在差异",
                ]
            )
            distinguishing_features = random.choice(
                [
                    "区别特征1: 涉案专利增加了模块A,实现了功能增强",
                    "区别特征2: 涉案专利采用方法B,提高了效率",
                    "区别特征3: 涉案专利优化了参数C,改善了性能",
                ]
            )
            conclusion = random.choice(
                ["涉案专利具备新颖性", "涉案专利不具备新颖性", "需要进一步评估"]
            )
            return f"""
[新颖性分析]
1. 对比文件分析
{comparison_analysis}

2. 区别技术特征
{distinguishing_features}

3. 判断结论
{conclusion}
            """
        elif case_type == "creative":
            closest_prior_art = random.choice(
                [
                    "D1是最接近的现有技术,公开了基本的技术框架",
                    "D1与涉案专利属于相同技术领域,解决类似技术问题",
                    "D1公开了涉案专利的大部分技术特征",
                ]
            )
            distinguishing_features_and_problem = random.choice(
                [
                    "区别特征在于增加了功能模块A,解决了响应速度慢的问题",
                    "区别特征在于采用了工艺B,提高了产品合格率",
                    "区别特征在于优化了参数C,降低了能耗",
                ]
            )
            technical_effects = random.choice(
                [
                    "显著提升了系统性能,超出预期效果",
                    "降低了生产成本,提高了经济效益",
                    "改善了用户体验,增强了市场竞争力",
                ]
            )
            significance_judgment = random.choice(
                [
                    "区别特征非显而易见,产生预料不到的技术效果",
                    "区别特征属于本领域的常规选择",
                    "需要结合技术效果综合判断",
                ]
            )
            conclusion = random.choice(
                ["涉案专利具备创造性", "涉案专利不具备创造性", "需要进一步评估"]
            )
            return f"""
[创造性分析]
1. 最接近现有技术确定
{closest_prior_art}

2. 区别特征与技术问题
{distinguishing_features_and_problem}

3. 技术效果分析
{technical_effects}

4. 显著性判断
{significance_judgment}

5. 结论
{conclusion}
            """
        elif case_type == "disclosure":
            disclosure_level = random.choice(
                [
                    "说明书公开了完整的技术方案,包括各组成部分",
                    "说明书描述了基本原理,但缺少具体实施细节",
                    "说明书公开了关键技术参数和实施步骤",
                ]
            )
            embodiments = random.choice(
                [
                    "提供了3个具体实施例,涵盖不同应用场景",
                    "仅提供1个实施例,公开不充分",
                    "提供了多个实施例,但关键参数未明确",
                ]
            )
            effects_verification = random.choice(
                [
                    "通过实验数据验证了技术效果",
                    "仅描述性说明,缺乏实验支持",
                    "提供了对比实验,效果显著",
                ]
            )
            reproducibility = random.choice(
                [
                    "本领域技术人员可据此实现",
                    "部分技术特征描述不清,难以再现",
                    "需要结合公知常识才能实现",
                ]
            )
            conclusion = random.choice(
                ["符合充分公开要求", "不符合充分公开要求", "部分内容需要补充"]
            )
            return f"""
[充分公开分析]
1. 技术方案公开程度
{disclosure_level}

2. 实施例描述
{embodiments}

3. 技术效果验证
{effects_verification}

4. 再现性评估
{reproducibility}

5. 结论
{conclusion}
            """
        else:
            return """
[综合分析]
本案例涉及多个法律问题,需要综合考虑:
1. 新颖性评估
2. 创造性评估
3. 其他法律问题

结论: 需要进一步分析
            """

    def _generate_recommendations(self, case_type: str, risk: str) -> str:
        """生成建议行动"""
        if risk == "低风险":
            return random.choice(["维持专利权有效", "可积极应对无效请求", "建议加强专利布局"])
        elif risk == "中风险":
            return random.choice(["建议补充实验数据", "需进一步说明技术效果", "考虑修改权利要求"])
        else:
            return random.choice(
                ["建议主动缩小保护范围", "准备应对无效宣告", "考虑放弃部分权利要求"]
            )

    def generate_batch(
        self, count: int = 50, distribution: dict[str, int] | None = None
    ) -> list[PatentCase]:
        """批量生成案例

        Args:
            count: 总数
            distribution: 类型分布 {"novelty": 15, "creative": 15, ...}

        Returns:
            PatentCase列表
        """
        if distribution is None:
            # 默认分布
            distribution = {
                "novelty": 15,
                "creative": 15,
                "disclosure": 10,
                "clarity": 5,
                "complex": 5,
            }

        cases = []
        for case_type, num in distribution.items():
            for _ in range(num):
                case = self.generate_case(case_type)
                cases.append(case)

        logger.info(f"生成了 {len(cases)} 个案例")
        return cases

    def save_examples(self, cases: list[str], output_file: str = "examples.json", format: str = "json"):
        """保存案例到文件

        Args:
            cases: 案例列表
            output_file: 输出文件路径
            format: 格式 (json, txt)
        """
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if format == "json":
            # 保存为JSON格式
            data = {
                "metadata": {
                    "total_cases": len(cases),
                    "case_types": {},
                    "generated_at": str(Path(__file__).stat().st_mtime),
                },
                "cases": [asdict(case) for case in cases],
            }

            # 统计类型分布
            for case in cases:
                case_type = case.case_type
                data["metadata"]["case_types"][case_type] = (
                    data["metadata"]["case_types"].get(case_type, 0) + 1
                )

            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已保存 {len(cases)} 个案例到 {output_path}")

        elif format == "dspy":
            # 保存为DSPy Python格式

            dspy_examples = [case.to_dspy_example() for case in cases]

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("# DSPy Training Data\n\n")
                f.write("import dspy\n\n")
                f.write("training_data = [\n")

                for i, example in enumerate(dspy_examples):
                    f.write(f"    # Case {i+1}: {cases[i].case_title}\n")
                    f.write("    dspy.Example(\n")
                    f.write(f"        user_input={repr(example.user_input)[:100]}...,\n")
                    f.write(f"        context={repr(example.context)[:100]}...,\n")
                    f.write(f"        task_type={example.task_type!r},\n")
                    f.write(f"        analysis_result={repr(example.analysis_result)[:100]}...,\n")
                    f.write('    ).with_inputs("user_input", "context", "task_type"),\n\n')

                f.write("]\n")

            logger.info(f"已保存 {len(cases)} 个DSPy示例到 {output_path}")

    def validate_data(self, cases: list[PatentCase]) -> dict[str, Any]:
        """验证数据质量

        Args:
            cases: 案例列表

        Returns:
            验证结果
        """
        results = {"total": len(cases), "valid": 0, "invalid": 0, "issues": []}

        for case in cases:
            issues = []

            # 检查必填字段
            if not case.case_id:
                issues.append("缺少case_id")
            if not case.case_description or len(case.case_description) < 100:
                issues.append("case_description太短")
            if not case.analysis_result or len(case.analysis_result) < 50:
                issues.append("analysis_result太短")
            if not case.legal_issues:
                issues.append("缺少legal_issues")

            if issues:
                results["invalid"] += 1
                results[case.case_id]
            else:
                results["valid"] += 1

        logger.info(f"验证完成: {results['valid']}个有效, {results['invalid']}个无效")

        return results


def main() -> None:
    """主函数 - 生成训练数据"""
    generator = TrainingDataGenerator()

    print("=" * 60)
    print("DSPy训练数据生成器")
    print("=" * 60)

    # 生成50个案例
    print("\n正在生成50个训练案例...")
    cases = generator.generate_batch(count=50)

    # 验证数据
    print("\n验证数据质量...")
    validation = generator.validate_data(cases)

    # 保存为JSON格式
    print("\n保存为JSON格式...")
    generator.save_examples(cases, "core/intelligence/dspy/data/training_data.json", format="json")

    # 保存为DSPy格式
    print("\n保存为DSPy Python格式...")
    generator.save_examples(
        cases, "core/intelligence/dspy/data/training_data_dspy.py", format="dspy"
    )

    # 统计信息
    print("\n" + "=" * 60)
    print("生成完成!")
    print("=" * 60)
    print(f"总案例数: {validation['total']}")
    print(f"有效案例: {validation['valid']}")
    print(f"无效案例: {validation['invalid']}")

    # 类型分布
    type_count = {}
    for case in cases:
        type_count[case.case_type] = type_count.get(case.case_type, 0) + 1

    print("\n类型分布:")
    for case_type, count in type_count.items():
        print(f"  {case_type}: {count}个")

    # 技术领域分布
    field_count = {}
    for case in cases:
        field_count[case.technical_field] = field_count.get(case.technical_field, 0) + 1

    print("\n技术领域分布:")
    for field, count in sorted(field_count.items(), key=lambda x: x[1], reverse=True):
        print(f"  {field}: {count}个")


if __name__ == "__main__":
    main()
