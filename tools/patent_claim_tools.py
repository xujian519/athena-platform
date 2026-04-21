#!/usr/bin/env python3
"""
权利要求生成工具 - Patent Claims Generation Tool

这是一个wrapper工具,将 core/patent/claim_generator.py 中的功能
封装为可通过工具系统调用的简单函数。

使用方法:
    from tools.patent_claim_tools import generate_claims, extract_claims_from_text, validate_claims

    # 从发明描述生成权利要求
    claims = generate_claims("一种光伏充电装置，包括光伏板、控制器和电池...")

    # 从专利文本提取权利要求
    extracted = extract_claims_from_text(patent_text)

    # 验证权利要求质量
    validation = validate_claims(claims_text)

Author: Athena Team
Date: 2026-02-24
Version: 1.0.0
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def generate_claims(
    description: str,
    invention_type: str = "device",
    num_independent: int = 1,
    num_dependent: int = 5
) -> dict[str, Any]:
    """
    从发明描述生成权利要求

    Args:
        description: 发明描述文本
        invention_type: 发明类型 (device/method/system/composition/use)
        num_independent: 独立权利要求数量
        num_dependent: 从属权利要求数量

    Returns:
        包含生成的权利要求的字典

    Example:
        >>> result = generate_claims("一种太阳能充电装置...")
        >>> print(result['invention_title'])
        >>> print(result['total_claims'])
    """
    try:
        from patents.core.claim_generator import InventionType, PatentClaimGenerator

        # 映射发明类型
        type_map = {
            "device": InventionType.DEVICE,
            "method": InventionType.METHOD,
            "system": InventionType.SYSTEM,
            "composition": InventionType.COMPOSITION,
            "use": InventionType.USE
        }

        inv_type = type_map.get(invention_type.lower(), InventionType.DEVICE)

        # 创建生成器 (不需要LLM客户端时使用简化模式)
        generator = PatentClaimGenerator(llm_client=None, knowledge_base=None)

        # 如果没有LLM客户端,返回模拟结果
        if generator.llm is None:
            return {
                "success": True,
                "simulated": True,
                "message": "LLM未配置,返回模拟结果",
                "invention_title": description[:50] + "...",
                "invention_type": invention_type,
                "total_claims": num_independent + num_dependent,
                "independent_claims": [
                    {
                        "claim_number": i + 1,
                        "claim_type": "independent",
                        "text": f"{i+1}. 一种{description[:100]}..."
                    }
                    for i in range(num_independent)
                ],
                "dependent_claims": [
                    {
                        "claim_number": num_independent + i + 1,
                        "claim_type": "dependent",
                        "parent_ref": (i % num_independent) + 1,
                        "text": f"{num_independent + i + 1}. 根据权利要求{(i % num_independent) + 1}所述..."
                    }
                    for i in range(num_dependent)
                ]
            }

        # 使用LLM生成 (需要配置LLM客户端)
        claims_set = generator.generate(
            description=description,
            invention_type=inv_type,
            num_independent=num_independent,
            num_dependent=num_dependent
        )

        return {
            "success": True,
            "simulated": False,
            **claims_set.to_dict()
        }

    except Exception as e:
        logger.error(f"生成权利要求失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "权利要求生成失败"
        }


def extract_claims_from_text(
    patent_text: str,
    extract_features: bool = True
) -> dict[str, Any]:
    """
    从专利文本中提取权利要求

    Args:
        patent_text: 专利全文文本
        extract_features: 是否提取技术特征

    Returns:
        提取的权利要求信息

    Example:
        >>> text = "权利要求书：1. 一种装置，包括..."
        >>> result = extract_claims_from_text(text)
        >>> print(f"提取到 {len(result['claims'])} 项权利要求")
    """
    try:
        import re

        from patents.core.claim_generator import ClaimType

        claims = []

        # 查找权利要求书部分
        claims_section = re.search(
            r'权利要求书[：:：]?\s*(.+?)(?=\n\n[【\[]|说明书|附图说明|$)',
            patent_text,
            re.DOTALL
        )

        if not claims_section:
            return {
                "success": False,
                "error": "未找到权利要求书部分",
                "claims": []
            }

        claims_text = claims_section.group(1)

        # 提取各个权利要求
        claim_pattern = r'(\d+)[.、　]\s*(.+?)(?=\n\d+[.、]|$)'
        matches = re.finditer(claim_pattern, claims_text, re.MULTILINE)

        for match in matches:
            claim_num = int(match.group(1))
            claim_content = match.group(2).strip()

            # 清理权利要求内容
            claim_content = re.sub(r'\s+', ' ', claim_content)
            claim_content = claim_content[:500]  # 限制长度

            # 判断是独立还是从属
            if claim_num == 1 or "根据权利要求" in claim_content[:30]:
                claim_type = ClaimType.INDEPENDENT if claim_num == 1 else ClaimType.DEPENDENT
            else:
                claim_type = ClaimType.INDEPENDENT

            # 提取父权利要求引用
            parent_ref = None
            if claim_type == ClaimType.DEPENDENT:
                parent_match = re.search(r'根据权利要求(\d+)', claim_content)
                if parent_match:
                    parent_ref = int(parent_match.group(1))

            if len(claim_content) > 20:  # 过滤太短的
                claims.append({
                    "claim_number": claim_num,
                    "claim_type": claim_type.value,
                    "text": claim_content,
                    "parent_ref": parent_ref,
                    "length": len(claim_content)
                })

        return {
            "success": True,
            "total_claims": len(claims),
            "claims": claims,
            "independent_count": sum(1 for c in claims if c["claim_type"] == "independent"),
            "dependent_count": sum(1 for c in claims if c["claim_type"] == "dependent")
        }

    except Exception as e:
        logger.error(f"提取权利要求失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "claims": []
        }


def validate_claims(
    claims_text: str,
    check_rules: list[str] = None
) -> dict[str, Any]:
    """
    验证权利要求质量

    Args:
        claims_text: 权利要求文本
        check_rules: 要检查的规则列表

    Returns:
        验证结果

    Example:
        >>> result = validate_claims(claims_text)
        >>> print(f"有效性: {result['valid']}")
        >>> print(f"问题数: {len(result['issues'])}")
    """
    try:
        issues = []
        score = 100

        # 默认检查规则
        default_rules = [
            "completeness",  # 完整性检查
            "clarity",  # 清晰度检查
            "terminology",  # 术语一致性
            "structure"  # 结构规范
        ]
        check_rules = check_rules or default_rules

        # 完整性检查
        if "completeness" in check_rules:
            if not claims_text or len(claims_text.strip()) < 50:
                issues.append({
                    "rule": "completeness",
                    "level": "error",
                    "message": "权利要求文本过短或不完整"
                })
                score -= 30

        # 清晰度检查
        if "clarity" in check_rules:
            # 检查是否有过于模糊的表述
            vague_terms = ["适当", "合适", "一定", "大约", "左右"]
            found_vague = [term for term in vague_terms if term in claims_text]
            if found_vague:
                issues.append({
                    "rule": "clarity",
                    "level": "warning",
                    "message": f"发现模糊术语: {', '.join(found_vague)}",
                    "terms": found_vague
                })
                score -= len(found_vague) * 5

        # 术语一致性检查
        if "terminology" in check_rules:
            # 检查"所述"的使用
            if "所述" not in claims_text and "权利要求" in claims_text:
                issues.append({
                    "rule": "terminology",
                    "level": "warning",
                    "message": "缺少标准术语\"所述\""
                })
                score -= 10

        # 结构规范检查
        if "structure" in check_rules:
            # 检查是否有序号
            if not any(str(i) in claims_text for i in range(1, 20)):
                issues.append({
                    "rule": "structure",
                    "level": "error",
                    "message": "缺少权利要求序号"
                })
                score -= 20

        # 计算有效性
        valid = score >= 60 and not any(i["level"] == "error" for i in issues)

        return {
            "success": True,
            "valid": valid,
            "score": max(0, score),
            "issues": issues,
            "issue_count": len(issues),
            "error_count": sum(1 for i in issues if i["level"] == "error"),
            "warning_count": sum(1 for i in issues if i["level"] == "warning")
        }

    except Exception as e:
        logger.error(f"验证权利要求失败: {e}")
        return {
            "success": False,
            "error": str(e),
            "valid": False,
            "score": 0
        }


def analyze_claim_structure(
    claim_text: str
) -> dict[str, Any]:
    """
    分析单个权利要求的结构

    Args:
        claim_text: 单项权利要求文本

    Returns:
        结构分析结果
    """
    try:
        import re

        # 解析序号
        number_match = re.match(r'(\d+)[.、　]\s*', claim_text)
        claim_number = int(number_match.group(1)) if number_match else None

        # 去掉序号后的内容
        content = re.sub(r'^\d+[.、　]\s*', '', claim_text)

        # 判断类型
        is_dependent = "根据权利要求" in content[:50]
        claim_type = "dependent" if is_dependent else "independent"

        # 提取父权利要求引用
        parent_ref = None
        if is_dependent:
            parent_match = re.search(r'根据权利要求(\d+)', content)
            if parent_match:
                parent_ref = int(parent_match.group(1))

        # 提取前序部分
        preamble = ""
        transition = ""
        body = ""

        if claim_type == "independent":
            # 独立权利要求: 前序部分 + 过渡短语 + 主体部分
            transitions = ["包括", "具有", "包含", "其特征在于", "其中"]
            for trans in transitions:
                if trans in content:
                    parts = content.split(trans, 1)
                    preamble = parts[0].strip()
                    transition = trans
                    body = parts[1].strip() if len(parts) > 1 else ""
                    break
        else:
            # 从属权利要求
            preamble_match = re.match(r'(.*?根据权利要求\d+所述的[^，,。、]+)[，,。、]?', content)
            if preamble_match:
                preamble = preamble_match.group(1).strip()
            body = content[len(preamble):].strip()

        return {
            "success": True,
            "claim_number": claim_number,
            "claim_type": claim_type,
            "parent_ref": parent_ref,
            "preamble": preamble,
            "transition": transition,
            "body": body,
            "length": len(content),
            "structure": {
                "has_preamble": bool(preamble),
                "has_transition": bool(transition),
                "has_body": bool(body)
            }
        }

    except Exception as e:
        logger.error(f"分析权利要求结构失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


# 导出函数列表 (供工具扫描器识别)
__all__ = [
    "generate_claims",
    "extract_claims_from_text",
    "validate_claims",
    "analyze_claim_structure"
]


# 测试代码
if __name__ == "__main__":
    print("=" * 80)
    print("🔧 权利要求工具测试")
    print("=" * 80)
    print()

    # 测试1: 生成权利要求
    print("📝 测试1: 生成权利要求")
    result = generate_claims(
        description="一种太阳能充电装置，包括光伏板、控制器和蓄电池组",
        invention_type="device",
        num_independent=1,
        num_dependent=2
    )
    print(f"   成功: {result['success']}")
    print(f"   模拟: {result.get('simulated', False)}")
    print(f"   总权利要求: {result.get('total_claims', 0)}")
    print()

    # 测试2: 提取权利要求
    print("🔍 测试2: 从文本提取权利要求")
    sample_text = """
    权利要求书：
    1. 一种太阳能充电装置，其特征在于包括光伏板、控制器和蓄电池组。
    2. 根据权利要求1所述的太阳能充电装置，其特征在于所述控制器为MPPT控制器。
    3. 根据权利要求1所述的太阳能充电装置，其特征在于还包括散热风扇。
    """
    result = extract_claims_from_text(sample_text)
    print(f"   成功: {result['success']}")
    print(f"   提取权利要求: {result['total_claims']} 项")
    print(f"   独立: {result['independent_count']}, 从属: {result['dependent_count']}")
    print()

    # 测试3: 验证权利要求
    print("✅ 测试3: 验证权利要求质量")
    claims = "1. 一种装置，包括光伏板和控制器。所述控制器为MPPT控制器。"
    result = validate_claims(claims)
    print(f"   有效: {result['valid']}")
    print(f"   得分: {result['score']}")
    print(f"   问题数: {result['issue_count']}")
    print()

    # 测试4: 分析结构
    print("🏗️ 测试4: 分析权利要求结构")
    result = analyze_claim_structure(sample_text.split('\n')[2].strip())
    print(f"   成功: {result['success']}")
    print(f"   类型: {result.get('claim_type')}")
    print(f"   前序部分: {result.get('preamble', '')[:50]}...")
    print()

    print("=" * 80)
    print("✅ 测试完成")
    print("=" * 80)
