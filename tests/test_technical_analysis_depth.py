#!/usr/bin/env python3
"""
验证技术分析深度
Verify Technical Analysis Depth

作者: 小诺·双鱼公主
版本: v1.0
创建时间: 2025-12-31
"""

import os
import sys


class TechnicalAnalysisValidator:
    """技术分析深度验证器"""

    def __init__(self):
        self.cap02_path = "prompts/capability/cap02_technical_deep_analysis_v2_enhanced.md"
        self.validation_results = []

    def validate_file_exists(self):
        """验证1：文件存在"""
        print("=" * 60)
        print("验证1：检查文件存在")
        print("=" * 60)

        exists = os.path.exists(self.cap02_path)

        if exists:
            file_size = os.path.getsize(self.cap02_path)
            print(f"✅ 文件存在: {self.cap02_path}")
            print(f"📊 文件大小: {file_size} 字节")
            self.validation_results.append(("file_exists", True, f"{file_size} bytes"))
            return True
        else:
            print(f"❌ 文件不存在: {self.cap02_path}")
            self.validation_results.append(("file_exists", False, "文件不存在"))
            return False

    def validate_three_level_analysis(self):
        """验证2：三级技术分析框架"""
        print("\n" + "=" * 60)
        print("验证2：三级技术分析框架")
        print("=" * 60)

        with open(self.cap02_path, encoding='utf-8') as f:
            content = f.read()

        # 检查三级分析
        levels = [
            ("一级：表面特征提取", "一级：表面特征提取" in content or "表面特征提取" in content),
            ("二级：技术手段解构", "二级：技术手段解构" in content or "技术手段解构" in content),
            ("三级：技术效果对比", "三级：技术效果对比" in content or "技术效果对比" in content),
        ]

        all_present = True
        for level_name, present in levels:
            status = "✅" if present else "❌"
            print(f"{status} {level_name}: {'已包含' if present else '缺失'}")
            if not present:
                all_present = False

        # 检查递进关系说明
        has_progression = "递进关系" in content or "→" in content
        print(f"{'✅' if has_progression else '⚠️'} 三级递进关系说明: {'已包含' if has_progression else '缺失'}")

        if all_present and has_progression:
            print("\n✅ 通过：三级技术分析框架完整")
            self.validation_results.append(("three_level_analysis", True, "三级分析完整"))
            return True
        else:
            print("\n⚠️ 警告：三级技术分析框架不完整")
            self.validation_results.append(("three_level_analysis", False, "三级分析不完整"))
            return False

    def validate_7_dimensions(self):
        """验证3：7维度深度解析"""
        print("\n" + "=" * 60)
        print("验证3：7维度深度解析")
        print("=" * 60)

        with open(self.cap02_path, encoding='utf-8') as f:
            content = f.read()

        # 检查7个维度
        dimensions = [
            "技术方案本质",
            "技术手段拆解",
            "技术效果实现机制",
            "技术问题解决链",
            "技术领域特征",
            "实施方式细节",
            "变形与等同"
        ]

        found_count = 0
        for dim in dimensions:
            present = dim in content
            status = "✅" if present else "❌"
            print(f"{status} {dim}: {'已包含' if present else '缺失'}")
            if present:
                found_count += 1

        print(f"\n📊 包含维度: {found_count}/{len(dimensions)}")

        if found_count == len(dimensions):
            print("✅ 通过：7维度深度解析完整")
            self.validation_results.append(("7_dimensions", True, f"{found_count}/7"))
            return True
        else:
            print(f"⚠️ 警告：只包含 {found_count}/{len(dimensions)} 个维度")
            self.validation_results.append(("7_dimensions", False, f"{found_count}/7"))
            return False

    def validate_comparison_matrix(self):
        """验证4：深度技术对比矩阵"""
        print("\n" + "=" * 60)
        print("验证4：深度技术对比矩阵")
        print("=" * 60)

        with open(self.cap02_path, encoding='utf-8') as f:
            content = f.read()

        # 检查4层级对比
        comparison_levels = [
            ("层级1：特征级对比", "特征级对比" in content or "特征级" in content),
            ("层级2：手段级对比", "手段级对比" in content or "手段级" in content),
            ("层级3：效果级对比", "效果级对比" in content or "效果级" in content),
            ("层级4：因果关系链对比", "因果关系链对比" in content or "因果关系链" in content),
        ]

        all_present = True
        for level_name, present in comparison_levels:
            status = "✅" if present else "❌"
            print(f"{status} {level_name}: {'已包含' if present else '缺失'}")
            if not present:
                all_present = False

        # 检查对比矩阵结构
        has_matrix = "对比矩阵" in content or "对比表" in content
        print(f"{'✅' if has_matrix else '⚠️'} 对比矩阵结构: {'已包含' if has_matrix else '缺失'}")

        if all_present and has_matrix:
            print("\n✅ 通过：深度技术对比矩阵完整")
            self.validation_results.append(("comparison_matrix", True, "4层级完整"))
            return True
        else:
            print("\n⚠️ 警告：深度技术对比矩阵不完整")
            self.validation_results.append(("comparison_matrix", False, "4层级不完整"))
            return False

    def validate_distinguishing_features(self):
        """验证5：区别特征4层次识别"""
        print("\n" + "=" * 60)
        print("验证5：区别特征4层次识别")
        print("=" * 60)

        with open(self.cap02_path, encoding='utf-8') as f:
            content = f.read()

        # 检查4层次
        feature_levels = [
            ("层次1：表面区别", "表面区别" in content),
            ("层次2：功能区别", "功能区别" in content),
            ("层次3：原理区别", "原理区别" in content),
            ("层次4：技术启示判断", "技术启示判断" in content),
        ]

        all_present = True
        for level_name, present in feature_levels:
            status = "✅" if present else "❌"
            print(f"{status} {level_name}: {'已包含' if present else '缺失'}")
            if not present:
                all_present = False

        # 检查技术启示判断依据
        has_teaching_away_criteria = (
            "技术领域" in content and
            "技术问题" in content and
            "技术效果" in content
        )
        print(f"{'✅' if has_teaching_away_criteria else '⚠️'} 技术启示判断依据: {'完整' if has_teaching_away_criteria else '不完整'}")

        if all_present and has_teaching_away_criteria:
            print("\n✅ 通过：区别特征4层次识别完整")
            self.validation_results.append(("distinguishing_features", True, "4层次完整"))
            return True
        else:
            print("\n⚠️ 警告：区别特征4层次识别不完整")
            self.validation_results.append(("distinguishing_features", False, "4层次不完整"))
            return False

    def validate_mandatory_hitl(self):
        """验证6：5个强制HITL确认点"""
        print("\n" + "=" * 60)
        print("验证6：5个强制HITL确认点")
        print("=" * 60)

        with open(self.cap02_path, encoding='utf-8') as f:
            content = f.read()

        # 检查5个确认点（使用精确的标题格式）
        confirmation_points = [
            "确认点1：技术解构完成后",
            "确认点2：区别特征确认后",
            "确认点3：技术启示判断后",
            "确认点4：答复策略选择前",
            "确认点5：答复文件撰写完成后"
        ]

        found_count = 0
        for point in confirmation_points:
            # 精确匹配
            present = point in content
            status = "✅" if present else "❌"
            # 简化显示名称
            short_name = point.split("：")[1][:10] + "..."
            print(f"{status} 确认点{short_name}: {'已包含' if present else '缺失'}")
            if present:
                found_count += 1

        print(f"\n📊 包含确认点: {found_count}/{len(confirmation_points)}")

        # 检查强制HITL说明
        has_mandatory = "强制" in content or "不可跳过" in content
        print(f"{'✅' if has_mandatory else '⚠️'} 强制HITL说明: {'已包含' if has_mandatory else '缺失'}")

        if found_count >= 4 and has_mandatory:
            print("✅ 通过：强制HITL确认点配置完整")
            self.validation_results.append(("mandatory_hitl", True, f"{found_count}/5确认点"))
            return True
        else:
            print(f"⚠️ 警告：只包含 {found_count}/{len(confirmation_points)} 个确认点")
            self.validation_results.append(("mandatory_hitl", False, f"{found_count}/5确认点"))
            return False

    def validate_output_format(self):
        """验证7：输出格式模板"""
        print("\n" + "=" * 60)
        print("验证7：输出格式模板")
        print("=" * 60)

        with open(self.cap02_path, encoding='utf-8') as f:
            content = f.read()

        # 检查关键输出格式
        formats = [
            ("技术解构输出", "【目标专利技术解构】" in content or "技术解构" in content),
            ("对比矩阵", "对比矩阵" in content),
            ("区别特征识别", "区别特征本质" in content),
            ("HITL交互", "【小娜】" in content or "🤝" in content),
        ]

        all_present = True
        for format_name, present in formats:
            status = "✅" if present else "❌"
            print(f"{status} {format_name}: {'已包含' if present else '缺失'}")
            if not present:
                all_present = False

        if all_present:
            print("\n✅ 通过：输出格式模板完整")
            self.validation_results.append(("output_format", True, "格式完整"))
            return True
        else:
            print("\n⚠️ 警告：输出格式模板不完整")
            self.validation_results.append(("output_format", False, "格式不完整"))
            return False

    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "=" * 60)
        print("验证摘要")
        print("=" * 60)

        total_validations = len(self.validation_results)
        passed_validations = sum(1 for _, passed, _ in self.validation_results if passed)

        print(f"\n总验证项: {total_validations}")
        print(f"通过数: {passed_validations}")
        print(f"失败数: {total_validations - passed_validations}")
        print(f"通过率: {passed_validations / total_validations * 100:.1f}%")

        print("\n详细结果:")
        for validation_name, passed, message in self.validation_results:
            status = "✅" if passed else "❌"
            print(f"{status} {validation_name}: {message}")

        if passed_validations == total_validations:
            print("\n🎉 所有验证通过！技术分析深度提示词已正确实现。")
            return True
        else:
            print(f"\n⚠️ 有 {total_validations - passed_validations} 个验证项需要改进。")
            return False

    def run_all_validations(self):
        """运行所有验证"""
        print("🔍 开始验证技术分析深度")
        print("小诺·双鱼公主 v4.0.0 为爸爸执行验证\n")

        self.validate_file_exists()

        if not self.validation_results[-1][1]:  # 如果文件不存在
            print("❌ 文件不存在，无法继续验证")
            return False

        self.validate_three_level_analysis()
        self.validate_7_dimensions()
        self.validate_comparison_matrix()
        self.validate_distinguishing_features()
        self.validate_mandatory_hitl()
        self.validate_output_format()

        return self.print_summary()


def main():
    """主函数"""
    validator = TechnicalAnalysisValidator()
    success = validator.run_all_validations()

    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
