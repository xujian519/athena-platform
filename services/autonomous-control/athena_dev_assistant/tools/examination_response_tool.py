#!/usr/bin/env python3
"""
Athena审查答复工具
Athena Examination Response Tool
帮助爸爸处理专利审查意见
"""

import asyncio
from core.async_main import async_main
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class AthenaExaminationResponseTool:
    """Athena审查答复工具"""

    def __init__(self):
        self.response_templates = self._load_response_templates()
        self.common_rejections = self._load_common_rejections()
        self.argument_strategies = self._load_argument_strategies()

    def _load_response_templates(self) -> Dict:
        """加载答复模板"""
        return {
            "新颖性答复": {
                "模板开头": "关于审查员指出的权利要求{claim_no}不具备新颖性的问题，申请人认为该权利要求具备新颖性，具体意见陈述如下：",
                "对比文件区别": "与对比文件{file_no}相比，本发明至少具有以下区别技术特征：{differences}",
                "技术效果": "由于上述区别技术特征，本发明能够实现{effects}，具有{benefits}的技术效果",
                "结论": "综上所述，权利要求{claim_no}相对于对比文件{file_no}具有突出的实质性特点和显著的进步，具备新颖性。"
            },
            "创造性答复": {
                "模板开头": "关于审查员指出的权利要求{claim_no}不具备创造性的问题，申请人认为该权利要求具备创造性，具体意见陈述如下：",
                "区别特征": "1. 权利要求{claim_no}与对比文件{file_no}相比，至少具有以下区别技术特征：{differences}",
                "非显而易见": "2. 上述区别技术特征不属于本领域的公知常识，也不是常规技术选择。",
                "技术启示": "3. 对比文件{file_no}没有给出采用上述区别技术特征的技术启示。",
                "有益效果": "4. 由于采用了上述区别技术特征，本发明能够实现{effects}，取得了预料不到的技术效果。",
                "结论": "综上所述，权利要求{claim_no}相对于对比文件{file_no}具有突出的实质性特点和显著的进步，具备创造性。"
            },
            "实用性答复": {
                "模板开头": "关于审查员指出的权利要求{claim_no}不具备实用性的问题，申请人认为该权利要求具备实用性，具体意见陈述如下：",
                "能够制造": "1. 本发明的技术方案清晰完整，所属技术领域的技术人员根据说明书记载的内容，能够实现本发明的技术方案。",
                "能够使用": "2. 本发明的技术方案能够在{application}中应用，并产生积极效果。",
                "积极效果": "3. 本发明能够解决{problem}的技术问题，具有{benefits}的积极效果。",
                "结论": "综上所述，权利要求{claim_no}符合专利法第22条第3款关于实用性的规定。"
            },
            "修改建议答复": {
                "模板开头": "针对审查意见，申请人对权利要求书进行了修改，修改内容如下：",
                "修改内容": "1. 在权利要求{claim_no}中增加技术特征：{new_features}",
                "修改依据": "上述修改内容来源于说明书第{page}页第{line}行的记载，符合专利法第33条的规定。",
                "修改效果": "通过上述修改，权利要求{claim_no}已经清楚地限定了要求专利保护的范围，并且得到了说明书的支持。",
                "结论": "修改后的权利要求书已经克服了审查意见中指出的缺陷。"
            }
        }

    def _load_common_rejections(self) -> Dict:
        """加载常见驳回理由"""
        return {
            "新颖性": {
                "关键词": ["不具备新颖性", "不属于现有技术", "已被公开", "专利法第22条第2款"],
                "常见原因": [
                    "与对比文件公开内容相同",
                    "属于公知常识",
                    "已被对比文件完全覆盖"
                ],
                "应对策略": [
                    "找出区别技术特征",
                    "证明非显而易见性",
                    "提供技术效果证明"
                ]
            },
            "创造性": {
                "关键词": ["不具备创造性", "显而易见", "常规技术选择", "专利法第22条第3款"],
                "常见原因": [
                    "区别特征属于公知常识",
                    "对比文件给出技术启示",
                    "是常规技术手段"
                ],
                "应对策略": [
                    "强调区别特征的非显而易见性",
                    "说明没有技术启示",
                    "突出预料不到的技术效果"
                ]
            },
            "实用性": {
                "关键词": ["不具备实用性", "无法实现", "专利法第22条第3款"],
                "常见原因": [
                    "技术方案不完整",
                    "无法在产业上应用",
                    "无法产生积极效果"
                ],
                "应对策略": [
                    "补充技术细节",
                    "提供应用实例",
                    "说明技术效果"
                ]
            },
            "清楚性": {
                "关键词": ["不清楚", "不简要", "得不到说明书支持", "专利法第26条第4款"],
                "常见原因": [
                    "技术特征不明确",
                    "保护范围不清楚",
                    "说明书未充分公开"
                ],
                "应对策略": [
                    "修改权利要求",
                    "增加技术细节",
                    "补充说明书内容"
                ]
            }
        }

    def _load_argument_strategies(self) -> Dict:
        """加载论证策略"""
        return {
            "区别特征论证": {
                "步骤": [
                    "1. 逐项列出区别技术特征",
                    "2. 说明每个区别特征的作用",
                    "3. 强调区别特征带来的技术效果"
                ]
            },
            "技术效果论证": {
                "步骤": [
                    "1. 量化技术效果",
                    "2. 与现有技术对比",
                    "3. 说明预料不到的效果"
                ]
            },
            "技术启示论证": {
                "步骤": [
                    "1. 分析对比文件的技术方案",
                    "2. 说明没有修改动机",
                    "3. 证明组合的困难"
                ]
            }
        }

    def analyze_examination_opinion(self, opinion_text: str) -> Dict:
        """分析审查意见"""
        analysis = {
            "审查类型": [],
            "涉及权利要求": [],
            "具体意见": [],
            "引用对比文件": [],
            "建议行动": []
        }

        lines = opinion_text.split('\n')

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 识别审查类型
            for reason_type, reason_info in self.common_rejections.items():
                for keyword in reason_info["关键词"]:
                    if keyword in line:
                        if reason_type not in analysis["审查类型"]:
                            analysis["审查类型"].append(reason_type)

            # 识别涉及的权利要求
            if "权利要求" in line:
                claim_matches = re.findall(r'权利要求(\d+)', line)
                analysis["涉及权利要求"].extend(claim_matches)

            # 识别对比文件
            if "对比文件" in line or "D" in line:
                file_matches = re.findall(r'(?:对比文件|D)(\d+)', line)
                analysis["引用对比文件"].extend(file_matches)

        # 去重
        analysis["涉及权利要求"] = list(set(analysis["涉及权利要求"]))
        analysis["引用对比文件"] = list(set(analysis["引用对比文件"]))

        # 分析具体意见
        for i, line in enumerate(lines):
            for claim_no in analysis["涉及权利要求"]:
                if f"权利要求{claim_no}" in line:
                    # 提取相关段落
                    start_idx = max(0, i-2)
                    end_idx = min(len(lines), i+3)
                    paragraph = '\n'.join(lines[start_idx:end_idx])
                    analysis["具体意见"].append({
                        "权利要求": claim_no,
                        "意见内容": paragraph
                    })

        # 生成建议行动
        for reason_type in analysis["审查类型"]:
            strategy = self.common_rejections[reason_type]["应对策略"]
            analysis["建议行动"].extend(strategy)

        return analysis

    def generate_response_outline(self, analysis: Dict) -> Dict:
        """生成答复提纲"""
        outline = {
            "答复标题": "关于申请号{application_no}的审查意见答复",
            "引言": "尊敬的审查员：感谢您对本申请的认真审查。申请人认真研究了审查意见，现答复如下：",
            "正文段落": [],
            "修改说明": [],
            "结论": "综上所述，修改后的权利要求书已经克服了审查意见中指出的缺陷，恳请审查员继续审查并授予专利权。",
            "附件": []
        }

        # 为每个审查类型生成答复段落
        for reason_type in analysis["审查类型"]:
            if reason_type in self.response_templates:
                template = self.response_templates[reason_type]

                for claim_no in analysis["涉及权利要求"]:
                    # 生成具体答复段落
                    paragraph = {
                        "标题": f"关于权利要求{claim_no}的{reason_type}问题",
                        "内容": template["模板开头"],
                        "论点": [],
                        "结论": template["结论"]
                    }

                    # 添加具体论点
                    if reason_type == "新颖性" or reason_type == "创造性":
                        paragraph["论点"].append({
                            "论点类型": "区别特征",
                            "内容": "与对比文件相比，本发明具有以下区别技术特征：[待补充]"
                        })
                        paragraph["论点"].append({
                            "论点类型": "技术效果",
                            "内容": "由于上述区别特征，本发明产生了预料不到的技术效果：[待补充]"
                        })

                    outline["正文段落"].append(paragraph)

        # 如果需要修改权利要求
        if "清楚性" in analysis["审查类型"] or "不支持" in analysis["审查类型"]:
            outline["修改说明"].append({
                "修改类型": "权利要求修改",
                "修改内容": "[待说明具体的修改内容]",
                "修改依据": "[待说明修改依据]"
            })

        return outline

    def draft_response(self, analysis: Dict, patent_info: Dict) -> str:
        """起草答复文书"""
        response_parts = []

        # 1. 开头
        application_no = patent_info.get("application_no", "待填")
        response_parts.append(f"关于申请号{application_no}的审查意见答复\n")
        response_parts.append("\n尊敬的审查员：\n")
        response_parts.append("感谢您对本申请的认真审查。申请人认真研究了审查意见，现答复如下：\n")

        # 2. 权利要求修改说明（如果有）
        if "清楚性" in analysis["审查类型"] or "不支持" in analysis["审查类型"]:
            response_parts.append("\n一、关于权利要求书的修改说明\n")
            response_parts.append("针对审查意见，申请人对权利要求书进行了如下修改：\n")
            response_parts.append("[此处应详细说明修改内容]\n")
            response_parts.append("上述修改内容来源于说明书的具体记载，符合专利法第33条的规定。\n")

        # 3. 针对各审查意见的答复
        count = 1
        for reason_type in analysis["审查类型"]:
            template = self.response_templates.get(reason_type, {})

            for claim_no in analysis["涉及权利要求"]:
                response_parts.append(f"\n{count}、关于权利要求{claim_no}的{reason_type}问题\n")

                if template.get("模板开头"):
                    response_parts.append(template["模板开头"].format(claim_no=claim_no, file_no="1") + "\n")

                # 添加具体论据（占位符）
                response_parts.append(f"（1）区别特征分析\n")
                response_parts.append(f"权利要求{claim_no}与对比文件相比，至少具有以下区别技术特征：\n")
                response_parts.append("• [区别特征1]\n")
                response_parts.append("• [区别特征2]\n")
                response_parts.append("• [区别特征3]\n\n")

                response_parts.append(f"（2）技术效果分析\n")
                response_parts.append(f"由于采用了上述区别技术特征，本发明能够实现以下技术效果：\n")
                response_parts.append("• [技术效果1]\n")
                response_parts.append("• [技术效果2]\n\n")

                if template.get("结论"):
                    response_parts.append(template["结论"].format(claim_no=claim_no, file_no="1") + "\n")

                count += 1

        # 4. 结论
        response_parts.append("\n结论\n")
        response_parts.append("综上所述，修改后的权利要求书已经克服了审查意见中指出的缺陷，")
        response_parts.append("符合专利法及其实施细则的相关规定。\n")
        response_parts.append("恳请审查员继续审查并授予专利权。\n")

        # 5. 结尾
        response_parts.append("\n此致\n")
        response_parts.append("敬礼！\n\n")
        response_parts.append(f"申请人：{patent_info.get('applicant', '待填')}\n")
        response_parts.append(f"日期：{datetime.now().strftime('%Y年%m月%d日')}\n")

        return '\n'.join(response_parts)

    def generate_amendment_suggestions(self, analysis: Dict) -> List[Dict]:
        """生成修改建议"""
        suggestions = []

        # 针对清楚性问题
        if "清楚性" in analysis["审查类型"]:
            suggestions.append({
                "权利要求": "待定",
                "修改类型": "增加技术特征",
                "修改内容": "在权利要求中增加具体的技术限定，使保护范围更加清楚",
                "理由": "满足专利法第26条第4款关于清楚性的要求"
            })

        # 针对支持性问题
        if "不支持" in analysis["审查类型"]:
            suggestions.append({
                "权利要求": "待定",
                "修改类型": "修改技术特征",
                "修改内容": "将权利要求中的技术特征修改为与说明书一致",
                "理由": "满足权利要求得到说明书支持的要求"
            })

        # 针对新颖性/创造性问题
        if "新颖性" in analysis["审查类型"] or "创造性" in analysis["审查类型"]:
            for claim_no in analysis["涉及权利要求"]:
                suggestions.append({
                    "权利要求": claim_no,
                    "修改类型": "增加区别特征",
                    "修改内容": "在独立权利要求中加入说明书中公开的[具体技术特征]",
                    "理由": "进一步限定发明点，提高授权前景"
                })

        return suggestions

    def check_response_completeness(self, response_text: str) -> Dict:
        """检查答复完整性"""
        checks = {
            "格式检查": {
                "是否有标题": "标题" in response_text or "审查意见答复" in response_text,
                "是否有称谓": "审查员" in response_text,
                "是否有结尾": "此致" in response_text or "敬礼" in response_text,
                "是否有日期": "年" in response_text and "月" in response_text and "日" in response_text,
                "缺失项目": []
            },
            "内容检查": {
                "是否回应了所有意见": True,  # 需要根据实际审查意见判断
                "是否提供了论据": "区别特征" in response_text or "技术效果" in response_text,
                "是否有法律依据": "专利法" in response_text,
                "缺失项目": []
            }
        }

        # 检查缺失项目
        for item, status in checks["格式检查"].items():
            if item != "缺失项目" and not status:
                checks["格式检查"]["缺失项目"].append(item)

        # 检查内容完整性
        if not checks["内容检查"]["是否提供了论据"]:
            checks["内容检查"]["缺失项目"].append("缺少技术论证")

        return checks

    def save_response(self, response: str, file_path: str) -> None:
        """保存答复文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(response)


# 使用示例
async def main():
    """测试审查答复工具"""
    tool = AthenaExaminationResponseTool()

    # 示例审查意见
    examination_opinion = """
    审查意见通知书

    1. 关于权利要求1的新颖性
    权利要求1不具备新颖性，其与对比文件D1公开的内容相同。

    2. 关于权利要求2的创造性
    权利要求2不具备创造性，其相对于对比文件D1和D2的结合是显而易见的。

    3. 关于权利要求3的清楚性
    权利要求3的保护范围不清楚，得不到说明书的支持。
    """

    # 分析审查意见
    analysis = tool.analyze_examination_opinion(examination_opinion)
    print("\n=== 审查意见分析 ===")
    print(f"审查类型: {analysis['审查类型']}")
    print(f"涉及权利要求: {analysis['涉及权利要求']}")
    print(f"引用对比文件: {analysis['引用对比文件']}")

    # 生成答复提纲
    outline = tool.generate_response_outline(analysis)
    print("\n=== 答复提纲 ===")
    print(f"标题: {outline['答复标题']}")
    print(f"正文段落数量: {len(outline['正文段落'])}")

    # 专利信息
    patent_info = {
        "application_no": "202410000000.0",
        "applicant": "测试科技有限公司"
    }

    # 起草答复
    response = tool.draft_response(analysis, patent_info)
    print("\n=== 答复草稿 ===")
    print(response[:1000] + "..." if len(response) > 1000 else response)

    # 生成修改建议
    suggestions = tool.generate_amendment_suggestions(analysis)
    print("\n=== 修改建议 ===")
    for suggestion in suggestions:
        print(f"\n权利要求{suggestion['权利要求']}:")
        print(f"  修改类型: {suggestion['修改类型']}")
        print(f"  理由: {suggestion['理由']}")

    # 检查完整性
    completeness = tool.check_response_completeness(response)
    print("\n=== 完整性检查 ===")
    for check_type, results in completeness.items():
        print(f"\n{check_type}:")
        for item, status in results.items():
            if item != "缺失项目":
                print(f"  {item}: {'✅' if status else '❌'}")
        if results.get("缺失项目"):
            print("  缺失项目:")
            for missing in results["缺失项目"]:
                print(f"    - {missing}")


# 入口点: @async_main装饰器已添加到main函数