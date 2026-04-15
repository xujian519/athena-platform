#!/usr/bin/env python3
"""
Athena专利写作工具
Athena Patent Writing Tool
帮助爸爸进行专业的专利撰写
"""

import json
import re


class AthenaPatentWritingTool:
    """Athena专利写作工具"""

    def __init__(self):
        self.templates = self._load_templates()
        self.guidelines = self._load_guidelines()

    def _load_templates(self) -> dict:
        """加载专利模板"""
        return {
            "权利要求书": {
                "独立权利要求": "1. 一种[技术方案名称]，其特征在于，包括：[技术特征A]；[技术特征B]；[技术特征C]。",
                "从属权利要求": "2. 根据权利要求1所述的[技术方案名称]，其特征在于，[附加技术特征]。",
                "方法权利要求": "1. 一种[方法名称]，其特征在于，包括以下步骤：[步骤A]；[步骤B]；[步骤C]。",
                "用途权利要求": "1. [产品A]在[应用领域]中的应用。"
            },
            "说明书": {
                "技术领域": "本发明涉及[技术领域]，具体而言，涉及[具体技术]。",
                "背景技术": "目前，[相关技术背景]。然而，现有技术存在[问题]。",
                "发明内容": "有鉴于此，本发明提供[解决方案]。",
                "具体实施方式": "下面结合附图和具体实施例对本发明作进一步详细说明。",
                "有益效果": "与现有技术相比，本发明具有以下有益效果：[效果1]、[效果2]..."
            }
        }

    def _load_guidelines(self) -> dict:
        """加载撰写指南"""
        return {
            "权利要求撰写要点": [
                "1. 权利要求应当清楚、简要地限定要求专利保护的范围",
                "2. 独立权利要求应当包含解决技术问题所必需的全部技术特征",
                "3. 从属权利要求应当包含附加技术特征，进一步限定独立权利要求",
                "4. 权利要求中的技术特征应当得到说明书的支持",
                "5. 权利要求应当以说明书为依据"
            ],
            "说明书撰写要点": [
                "1. 说明书应当对发明作出清楚、完整的说明",
                "2. 以所属技术领域的技术人员能够实现为准",
                "3. 技术问题、技术方案、有益效果应当清楚、完整",
                "4. 具体实施方式应当详细、具体",
                "5. 附图说明应当与附图相对应"
            ],
            "专利法第26条": {
                "核心要求": "说明书应当对发明作出清楚、完整的说明，以所属技术领域的技术人员能够实现为准",
                "注意要点": [
                    "技术方案必须完整",
                    "实施方式必须具体",
                    "技术效果必须明确",
                    "必须能够实现"
                ]
            }
        }

    def analyze_invention_disclosure(self, disclosure: str) -> dict:
        """分析技术交底书"""
        analysis = {
            "技术领域": "",
            "现有技术": "",
            "技术问题": "",
            "技术方案": "",
            "有益效果": "",
            "实施例": "",
            "关键技术创新点": []
        }

        # 使用正则表达式提取信息
        # 这里是简化版本，实际应用中可以使用更复杂的NLP
        lines = disclosure.split('\n')

        current_section = None
        content_buffer = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 识别章节标题
            if "技术领域" in line or "所属技术" in line:
                if current_section:
                    analysis[current_section] = '\n'.join(content_buffer)
                current_section = "技术领域"
                content_buffer = []
            elif "背景技术" in line or "现有技术" in line:
                if current_section:
                    analysis[current_section] = '\n'.join(content_buffer)
                current_section = "现有技术"
                content_buffer = []
            elif "技术问题" in line or "存在的技术问题" in line:
                if current_section:
                    analysis[current_section] = '\n'.join(content_buffer)
                current_section = "技术问题"
                content_buffer = []
            elif "技术方案" in line or "发明内容" in line:
                if current_section:
                    analysis[current_section] = '\n'.join(content_buffer)
                current_section = "技术方案"
                content_buffer = []
            elif "有益效果" in line or "技术效果" in line:
                if current_section:
                    analysis[current_section] = '\n'.join(content_buffer)
                current_section = "有益效果"
                content_buffer = []
            elif "实施例" in line or "具体实施方式" in line:
                if current_section:
                    analysis[current_section] = '\n'.join(content_buffer)
                current_section = "实施例"
                content_buffer = []
            else:
                content_buffer.append(line)

        # 添加最后一部分
        if current_section and content_buffer:
            analysis[current_section] = '\n'.join(content_buffer)

        # 提取技术创新点（简化版）
        innovation_keywords = ["创新", "改进", "优化", "提高", "降低", "实现", "提供"]
        for section, content in analysis.items():
            for keyword in innovation_keywords:
                if keyword in content and len(content) > 10:
                    analysis["关键技术创新点"].append(f"{section}: {content[:50]}...")

        return analysis

    def draft_claims(self, analysis: dict, claim_type: str = "产品") -> list[str]:
        """起草权利要求"""
        claims = []

        if claim_type == "产品":
            # 独立权利要求
            independent_claim = self.templates["权利要求书"]["独立权利要求"]

            # 从技术方案中提取关键特征
            tech_solution = analysis.get("技术方案", "")

            # 简化版：将技术方案拆分为特征
            features = self._extract_technical_features(tech_solution)

            # 填充模板
            claim_text = independent_claim.replace("[技术方案名称]", "技术装置")
            if features:
                claim_text = claim_text.replace("[技术特征A]", features[0])
                if len(features) > 1:
                    claim_text = claim_text.replace("[技术特征B]", features[1])
                if len(features) > 2:
                    claim_text = claim_text.replace("[技术特征C]", features[2])

            claims.append(claim_text)

            # 添加从属权利要求
            for _i, feature in enumerate(features[3:], 2):
                dependent_claim = self.templates["权利要求书"]["从属权利要求"]
                dependent_claim = dependent_claim.replace("[技术方案名称]", "技术装置")
                dependent_claim = dependent_claim.replace("[附加技术特征]", feature)
                claims.append(dependent_claim)

        elif claim_type == "方法":
            method_claim = self.templates["权利要求书"]["方法权利要求"]

            # 从技术方案中提取步骤
            steps = self._extract_method_steps(analysis.get("技术方案", ""))

            if steps:
                claim_text = method_claim.replace("[方法名称]", "技术方法")
                claim_text = claim_text.replace("[步骤A]", steps[0])
                if len(steps) > 1:
                    claim_text = claim_text.replace("[步骤B]", steps[1])
                if len(steps) > 2:
                    claim_text = claim_text.replace("[步骤C]", steps[2])

                claims.append(claim_text)

        return claims

    def _extract_technical_features(self, tech_solution: str) -> list[str]:
        """提取技术特征"""
        # 简化版：使用正则表达式和关键词识别
        features = []

        # 识别包含"模块"、"单元"、"部件"、"装置"等的短语
        pattern = r'([^，。；！？]*?(?:模块|单元|部件|装置|器件|结构|系统)[^，。；！？]*?)'
        matches = re.findall(pattern, tech_solution)
        features.extend(matches)

        # 识别动词短语（表示功能）
        pattern = r'(?:包括|具有|设置|安装|连接|配置)[^，。；！？]*?(?:模块|单元|部件|装置|器件|结构|系统)[^，。；！？]*?'
        matches = re.findall(pattern, tech_solution)
        features.extend(matches)

        return features[:5]  # 返回前5个特征

    def _extract_method_steps(self, tech_solution: str) -> list[str]:
        """提取方法步骤"""
        steps = []

        # 识别序号步骤
        pattern = r'(?:第一|第二|第三|步骤[一二三四五六七八九十]?\d*?)[：:]\s*([^，。；！？]*?)'
        matches = re.findall(pattern, tech_solution)
        steps.extend(matches)

        # 识别动作短语
        action_words = ["获取", "接收", "处理", "分析", "计算", "判断", "执行", "输出", "发送", "存储"]
        for word in action_words:
            pattern = f'{word}([^，。；！？]*?)'
            matches = re.findall(pattern, tech_solution)
            steps.extend(matches)

        return steps[:5]  # 返回前5个步骤

    def draft_specification(self, analysis: dict) -> dict:
        """起草说明书"""
        spec = {
            "技术领域": "",
            "背景技术": "",
            "发明内容": "",
            "具体实施方式": "",
            "有益效果": ""
        }

        # 技术领域
        spec["技术领域"] = self.templates["说明书"]["技术领域"]
        if analysis.get("技术领域"):
            spec["技术领域"] += analysis["技术领域"]

        # 背景技术
        spec["背景技术"] = self.templates["说明书"]["背景技术"]
        if analysis.get("现有技术"):
            spec["背景技术"] += "\n\n" + analysis["现有技术"]

        # 发明内容
        spec["发明内容"] = self.templates["说明书"]["发明内容"]
        if analysis.get("技术方案"):
            spec["发明内容"] += "\n\n" + "本发明的技术方案是：\n" + analysis["技术方案"]

        # 有益效果
        spec["有益效果"] = self.templates["说明书"]["有益效果"]
        if analysis.get("有益效果"):
            spec["有益效果"] += "\n" + analysis["有益效果"]

        # 具体实施方式
        spec["具体实施方式"] = self.templates["说明书"]["具体实施方式"]
        if analysis.get("实施例"):
            spec["具体实施方式"] += "\n\n" + analysis["实施例"]

        return spec

    def check_patent_law_26(self, specification: str) -> dict:
        """检查是否符合专利法第26条"""
        checks = {
            "完整性检查": {
                "是否清楚": False,
                "是否完整": False,
                "能够实现": False,
                "建议": []
            },
            "支持性检查": {
                "权利要求支持": False,
                "实施方式具体": False,
                "技术效果明确": False,
                "建议": []
            }
        }

        # 简化版检查逻辑
        # 1. 完整性检查
        if len(specification) > 500:
            checks["完整性检查"]["是否完整"] = True
        else:
            checks["完整性检查"]["建议"].append("说明书内容过于简短，需要详细说明")

        # 检查是否有技术方案
        if "技术方案" in specification or "发明内容" in specification:
            checks["完整性检查"]["是否清楚"] = True
        else:
            checks["完整性检查"]["建议"].append("缺少技术方案描述")

        # 检查是否有实施例
        if "实施例" in specification or "具体实施方式" in specification:
            checks["完整性检查"]["能够实现"] = True
            checks["支持性检查"]["实施方式具体"] = True
        else:
            checks["完整性检查"]["建议"].append("缺少具体实施方式")
            checks["support性检查"]["建议"].append("需要提供具体实施例")

        # 检查技术效果
        if "效果" in specification or "优点" in specification or "有益" in specification:
            if "support性检查" in checks and "技术效果明确" in checks["support性检查"]:
                checks["support性检查"]["技术效果明确"] = True
        else:
            if "support性检查" in checks and "建议" in checks["support性检查"]:
                checks["support性检查"]["建议"].append("需要说明技术效果")

        return checks

    def generate_review_comments(self, document: str, doc_type: str) -> list[str]:
        """生成审查意见"""
        comments = []

        if doc_type == "权利要求书":
            # 检查权利要求
            if "权利要求1" not in document:
                comments.append("⚠️ 缺少独立权利要求")

            # 检查是否使用了"所述"
            if document.count("所述") < 3:
                comments.append("💡 建议在从属权利要求中使用'所述'引用在先权利要求")

            # 检查权利要求数量
            claim_count = document.count("权利要求")
            if claim_count > 20:
                comments.append("⚠️ 权利要求数量较多，建议精简")
            elif claim_count < 3:
                comments.append("💡 建议增加从属权利要求，扩大保护范围")

        elif doc_type == "说明书":
            # 检查各部分
            sections = ["技术领域", "背景技术", "发明内容", "具体实施方式", "有益效果"]
            for section in sections:
                if section not in document:
                    comments.append(f"⚠️ 缺少{section}部分")

            # 检查实施例
            if "实施例" not in document:
                comments.append("⚠️ 缺少具体实施例，可能导致不支持")

            # 检查附图说明
            if "附图" in document and "附图说明" not in document:
                comments.append("💡 建议添加附图说明")

        return comments

    def save_draft(self, content: dict, file_path: str) -> None:
        """保存草稿"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)


# 使用示例
async def main():
    """测试专利写作工具"""
    tool = AthenaPatentWritingTool()

    # 示例技术交底书
    disclosure = """
    技术领域
    本发明涉及智能家居技术领域，具体而言，涉及一种智能照明控制系统。

    背景技术
    目前，传统的照明控制系统需要用户手动操作开关，不够智能。现有技术中，虽然有一些自动照明系统，但价格昂贵，功能单一。

    技术问题
    现有技术存在的技术问题是：1）自动化程度低；2）成本高；3）功能单一。

    技术方案
    本发明提供一种智能照明控制系统，包括：光照传感器；中央控制模块；无线通信模块；LED驱动模块。
    中央控制模块用于接收光照传感器的信号，并根据预设的照明策略控制LED驱动模块。
    无线通信模块用于连接智能设备，实现远程控制。

    有益效果
    本发明的有益效果是：1）实现自动控制，提高便利性；2）降低成本；3）支持多种控制方式。
    """

    # 分析交底书
    analysis = tool.analyze_invention_disclosure(disclosure)
    print("\n=== 分析结果 ===")
    for key, value in analysis.items():
        print(f"\n{key}:")
        print(value[:200] + "..." if len(str(value)) > 200 else value)

    # 起草权利要求
    claims = tool.draft_claims(analysis, "产品")
    print("\n=== 权利要求草案 ===")
    for i, claim in enumerate(claims, 1):
        print(f"\n权利要求{i}:")
        print(claim)

    # 起草说明书
    spec = tool.draft_specification(analysis)
    print("\n=== 说明书草案 ===")
    for section, content in spec.items():
        print(f"\n{section}:")
        print(content[:300] + "..." if len(content) > 300 else content)

    # 检查专利法第26条
    check_result = tool.check_patent_law_26("\n".join(spec.values()))
    print("\n=== 专利法第26条检查 ===")
    for check_type, result in check_result.items():
        print(f"\n{check_type}:")
        for item, status in result.items():
            if item != "建议":
                print(f"  {item}: {'✅' if status else '❌'}")
        if result.get("建议"):
            print("  建议:")
            for suggestion in result["建议"]:
                print(f"    - {suggestion}")


# 入口点: @async_main装饰器已添加到main函数
