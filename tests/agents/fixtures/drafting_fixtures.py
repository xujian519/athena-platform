"""
专利撰写测试数据Fixtures

提供统一的测试数据，避免在测试文件中重复定义。
"""

from typing import Any, Dict
import pytest
from datetime import datetime


# ========== 技术交底书测试数据 ==========

VALID_DISCLOSURE: Dict[str, Any] = {
    "disclosure_id": "TEST_20240423_001",
    "title": "一种基于深度学习的图像识别方法",
    "technical_field": "人工智能与计算机视觉",
    "background_art": """
    现有技术中，图像识别主要采用传统机器学习方法，如SVM、随机森林等。
    这些方法需要手工设计特征，存在以下问题：
    1. 特征提取过程复杂，依赖领域专家知识
    2. 泛化能力差，对复杂场景识别效果不佳
    3. 计算效率低，难以满足实时性要求
    """,
    "technical_problem": "如何提高图像识别的准确率和实时性",
    "technical_solution": """
    本发明提供一种基于深度学习的图像识别方法，包括：
    1. 构建卷积神经网络模型，包含多层卷积层和池化层
    2. 使用大规模预训练数据集进行模型预训练
    3. 采用迁移学习技术，针对特定场景进行微调
    4. 引入注意力机制，提高关键特征提取能力
    """,
    "beneficial_effects": [
        "识别准确率提高15%以上",
        "处理速度提升3倍",
        "对复杂场景的适应性更强",
        "减少了人工特征设计的工作量"
    ],
    "examples": [
        {
            "实施例编号": 1,
            "描述": "在交通监控场景中，使用本方法对车辆进行识别",
            "关键参数": {"网络层数": "18层", "学习率": "0.001", "批大小": "32"}
        },
        {
            "实施例编号": 2,
            "描述": "在医疗影像诊断中，使用本方法识别病变区域",
            "关键参数": {"网络层数": "50层", "学习率": "0.0001", "批大小": "16"}
        }
    ]
}

MINIMAL_DISCLOSURE: Dict[str, Any] = {
    "disclosure_id": "TEST_MINIMAL_001",
    "title": "测试专利",
    "technical_field": "测试领域",
    "technical_problem": "测试问题",
    "technical_solution": "测试解决方案"
}

INVALID_DISCLOSURE: Dict[str, Any] = {
    "disclosure_id": "",
    "title": "",
    "technical_field": ""
}

DEVICE_DISCLOSURE: Dict[str, Any] = {
    "disclosure_id": "TEST_DEVICE_001",
    "title": "一种智能包装机物品传送装置",
    "technical_field": "食品包装机械",
    "background_art": "现有包装机传送装置存在物料偏移问题",
    "technical_problem": "如何防止物料在传送过程中偏移",
    "technical_solution": """
    包括传送带、限位板、调节机构。限位板设置在传送带两侧，
    调节机构包括丝杆、螺母座、驱动电机，可根据物料宽度自动调节限位板间距。
    """,
    "beneficial_effects": [
        "防止物料偏移",
        "适应不同尺寸物料",
        "提高包装效率"
    ],
    "examples": []
}

METHOD_DISCLOSURE: Dict[str, Any] = {
    "disclosure_id": "TEST_METHOD_001",
    "title": "一种自动驾驶掉头路段脱困规划方法",
    "technical_field": "自动驾驶技术",
    "background_art": "自动驾驶车辆在狭窄路段掉头困难",
    "technical_problem": "如何实现狭窄路段的安全自动掉头",
    "technical_solution": """
    包括以下步骤：
    1. 检测掉头路段的空间边界
    2. 规划多段式掉头轨迹
    3. 模拟拟人驾驶行为进行轨迹优化
    4. 执行控制指令完成掉头
    """,
    "beneficial_effects": [
        "提高掉头安全性",
        "适应不同道路宽度",
        "减少掉头时间"
    ],
    "examples": []
}


# ========== 权利要求书测试数据 ==========

VALID_CLAIMS: Dict[str, Any] = {
    "independent_claim": "1. 一种基于深度学习的图像识别方法，其特征在于，包括：构建卷积神经网络模型；使用预训练数据集进行预训练；采用迁移学习进行微调；引入注意力机制提取特征。",
    "dependent_claims": [
        "2. 根据权利要求1所述的方法，其特征在于，所述卷积神经网络模型包含18-50层卷积层。",
        "3. 根据权利要求1所述的方法，其特征在于，所述预训练数据集包括ImageNet数据集。",
        "4. 根据权利要求2所述的方法，其特征在于，所述注意力机制采用自注意力结构。"
    ]
}

DEVICE_CLAIMS: Dict[str, Any] = {
    "independent_claim": "1. 一种智能包装机物品传送装置，其特征在于，包括：传送带；设置在传送带两侧的限位板；与限位板连接的调节机构，用于调节限位板间距。",
    "dependent_claims": [
        "2. 根据权利要求1所述的装置，其特征在于，所述调节机构包括丝杆和螺母座。",
        "3. 根据权利要求2所述的装置，其特征在于，所述丝杆由驱动电机驱动。"
    ]
}


# ========== 说明书测试数据 ==========

VALID_SPECIFICATION: Dict[str, Any] = {
    "title": "一种基于深度学习的图像识别方法",
    "technical_field": "本发明涉及人工智能技术领域，具体涉及基于深度学习的图像识别方法。",
    "background_art": """
    现有技术中，图像识别主要采用传统机器学习方法。
    这些方法存在特征提取复杂、泛化能力差等问题。
    """,
    "summary": """
    本发明提供一种基于深度学习的图像识别方法。
    通过构建卷积神经网络、使用预训练和迁移学习、引入注意力机制，
    提高了识别准确率和实时性。
    """,
    "brief_description": "图1是本发明实施例的方法流程图；\n图2是网络结构示意图。",
    "detailed_description": """
    下面结合附图和具体实施例对本发明作进一步详细说明。

    实施例1：
    如图1所示，本实施例提供一种基于深度学习的图像识别方法，
    包括以下步骤：

    步骤S1：构建卷积神经网络模型，包含18层卷积层和5层池化层。
    步骤S2：使用ImageNet数据集进行预训练。
    步骤S3：针对交通监控场景进行微调。
    步骤S4：引入自注意力机制提取关键特征。

    实验表明，本方法在交通监控场景下的识别准确率达到98.5%，
    相比传统方法提高了15%。
    """
}


# ========== 审查意见测试数据 ==========

VALID_OFFICE_ACTION: Dict[str, Any] = {
    "patent_number": "CN202310123456.7",
    "decision": "驳回",
    "issues": [
        {
            "claim_number": "1",
            "type": "novelty",
            "reason": "权利要求1相对于对比文件D1不具备新颖性",
            "evidence": "D1: CN102345678A公开了相同的深度学习图像识别方法"
        },
        {
            "claim_number": "2-4",
            "type": "inventive_step",
            "reason": "权利要求2-4相对于D1+D2不具备创造性",
            "evidence": "D2: CN112345678A公开了注意力机制的应用"
        }
    ]
}


# ========== 无效宣告测试数据 ==========

VALID_INVALIDATION_DATA: Dict[str, Any] = {
    "target_patent": {
        "patent_number": "CN201921401279.9",
        "title": "包装机物品传送装置的物料限位板自动调节机构",
        "claims": [
            "1. 一种包装机物品传送装置的物料限位板自动调节机构...",
            "2. 根据权利要求1所述的机构..."
        ]
    },
    "evidence": [
        {
            "number": "D1",
            "patent_number": "CN201198403Y",
            "relevance": "公开了斜向导轨结构"
        },
        {
            "number": "D2",
            "patent_number": "CN206156248U",
            "relevance": "公开了丝杆螺母座调节机构"
        }
    ],
    "ground_for_invalidity": "新颖性/创造性"
}


# ========== LLM响应测试数据 ==========

LLM_SUCCESS_RESPONSES: Dict[str, str] = {
    "claims": """```json
{
    "independent_claim": "1. 一种基于深度学习的图像识别方法，其特征在于，包括：构建卷积神经网络模型；使用预训练数据集进行预训练。",
    "dependent_claims": [
        "2. 根据权利要求1所述的方法，其特征在于，所述网络模型包含18-50层卷积层。",
        "3. 根据权利要求1所述的方法，其特征在于，采用迁移学习技术进行微调。"
    ]
}
```""",
    "specification": """```json
{
    "title": "一种基于深度学习的图像识别方法",
    "technical_field": "本发明涉及人工智能技术领域",
    "background_art": "现有技术存在特征提取复杂的问题",
    "summary": "本发明提供基于深度学习的图像识别方法",
    "brief_description": "图1是方法流程图",
    "detailed_description": "具体实施方式如下..."
}
```""",
    "disclosure_analysis": """```json
{
    "disclosure_id": "TEST_20240423_001",
    "extracted_information": {
        "发明名称": "一种基于深度学习的图像识别方法",
        "技术领域": {"技术领域": "人工智能与计算机视觉", "IPC分类": ["G部：计算"], "关键词": ["深度学习", "图像识别"]},
        "技术问题": "如何提高图像识别的准确率和实时性",
        "技术方案": {"技术方案概述": "构建卷积神经网络模型", "核心特征": ["构建CNN模型", "预训练", "迁移学习", "注意力机制"], "关键技术步骤": []},
        "有益效果": ["识别准确率提高15%", "处理速度提升3倍", "适应性更强", "减少人工工作量"],
        "实施例": []
    },
    "completeness": {
        "发明名称": {"完整": true, "缺失内容": ""},
        "技术领域": {"完整": true, "缺失内容": ""},
        "技术问题": {"完整": true, "缺失内容": ""},
        "技术方案": {"完整": true, "缺失内容": ""},
        "有益效果": {"完整": true, "缺失内容": ""},
        "实施例": {"完整": false, "缺失内容": "缺少实施例"}
    },
    "quality_assessment": {
        "完整性评分": 0.833,
        "详细程度评分": 0.75,
        "清晰度评分": 0.75,
        "综合评分": 0.78,
        "质量等级": "良好"
    },
    "recommendations": ["【实施例】缺少实施例，建议补充至少1个具体实施方式"]
}
```""",
    "patentability": """```json
{
    "disclosure_id": "TEST_20240423_001",
    "novelty_assessment": {"score": 0.75, "description": "具有一定新颖性"},
    "creativity_assessment": {"score": 0.7, "description": "具有一定创造性"},
    "practicality_assessment": {"score": 0.85, "description": "实用性良好"},
    "overall_score": 0.767,
    "patentability_level": "良好",
    "recommendations": []
}
```"""
}

LLM_ERROR_RESPONSE = "错误：无法解析响应"

LLM_INVALID_JSON = """这不是有效的JSON格式
The response is not in JSON format"""


# ========== 上下文测试数据 ==========

VALID_EXECUTION_CONTEXT: Dict[str, Any] = {
    "task_id": "TASK_20240423_001",
    "session_id": "SESSION_001",
    "input_data": {
        "user_input": "请撰写专利申请文件",
        "disclosure": VALID_DISCLOSURE
    },
    "config": {
        "writing_type": "description",
        "task_type": "comprehensive"
    },
    "previous_results": {}
}

WRITER_CONTEXT_CLAIMS: Dict[str, Any] = {
    "task_id": "TASK_CLAIMS_001",
    "input_data": {
        "user_input": "请撰写权利要求书",
        "disclosure": VALID_DISCLOSURE
    },
    "config": {
        "writing_type": "claims"
    },
    "previous_results": {
        "xiaona_analyzer": {
            "features": ["卷积神经网络", "预训练", "迁移学习", "注意力机制"]
        }
    }
}

WRITER_CONTEXT_RESPONSE: Dict[str, Any] = {
    "task_id": "TASK_RESPONSE_001",
    "input_data": {
        "user_input": "请答复审查意见",
        "office_action": VALID_OFFICE_ACTION
    },
    "config": {
        "writing_type": "office_action_response"
    },
    "previous_results": {
        "xiaona_analyzer": {
            "analysis": "对比文件D1未公开注意力机制特征"
        }
    }
}

WRITER_CONTEXT_INVALIDATION: Dict[str, Any] = {
    "task_id": "TASK_INVALIDATION_001",
    "input_data": {
        "user_input": "请撰写无效宣告请求书",
        "target_patent": "CN201921401279.9"
    },
    "config": {
        "writing_type": "invalidation"
    },
    "previous_results": {
        "xiaona_retriever": {
            "patents": [
                {"patent_number": "D1", "title": "CN201198403Y"},
                {"patent_number": "D2", "title": "CN206156248U"}
            ]
        }
    }
}

DRAFTING_PROXY_CONTEXT_ANALYZE: Dict[str, Any] = {
    "task_id": "TASK_ANALYZE_001",
    "session_id": "SESSION_001",
    "input_data": {
        "disclosure": VALID_DISCLOSURE
    },
    "config": {
        "task_type": "analyze_disclosure"
    }
}

DRAFTING_PROXY_CONTEXT_ASSESS: Dict[str, Any] = {
    "task_id": "TASK_ASSESS_001",
    "input_data": {
        "disclosure": VALID_DISCLOSURE,
        "prior_art": []
    },
    "config": {
        "task_type": "assess_patentability"
    }
}

DRAFTING_PROXY_CONTEXT_SPECIFICATION: Dict[str, Any] = {
    "task_id": "TASK_SPEC_001",
    "input_data": {
        "disclosure": VALID_DISCLOSURE,
        "patentability": {
            "overall_score": 0.75,
            "patentability_level": "良好"
        }
    },
    "config": {
        "task_type": "draft_specification"
    }
}

DRAFTING_PROXY_CONTEXT_CLAIMS: Dict[str, Any] = {
    "task_id": "TASK_CLAIMS_001",
    "input_data": {
        "disclosure": VALID_DISCLOSURE,
        "specification": VALID_SPECIFICATION
    },
    "config": {
        "task_type": "draft_claims"
    }
}

DRAFTING_PROXY_CONTEXT_OPTIMIZE: Dict[str, Any] = {
    "task_id": "TASK_OPTIMIZE_001",
    "input_data": {
        "claims": VALID_CLAIMS,
        "prior_art": []
    },
    "config": {
        "task_type": "optimize_protection_scope"
    }
}

DRAFTING_PROXY_CONTEXT_ADEQUACY: Dict[str, Any] = {
    "task_id": "TASK_ADEQUACY_001",
    "input_data": {
        "specification": VALID_SPECIFICATION,
        "claims": VALID_CLAIMS
    },
    "config": {
        "task_type": "review_adequacy"
    }
}

DRAFTING_PROXY_CONTEXT_ERRORS: Dict[str, Any] = {
    "task_id": "TASK_ERRORS_001",
    "input_data": {
        "specification": VALID_SPECIFICATION,
        "claims": VALID_CLAIMS
    },
    "config": {
        "task_type": "detect_common_errors"
    }
}


# ========== Pytest Fixtures ==========

@pytest.fixture
def valid_disclosure():
    """提供有效的技术交底书数据"""
    return VALID_DISCLOSURE.copy()


@pytest.fixture
def minimal_disclosure():
    """提供最小化的技术交底书数据"""
    return MINIMAL_DISCLOSURE.copy()


@pytest.fixture
def invalid_disclosure():
    """提供无效的技术交底书数据"""
    return INVALID_DISCLOSURE.copy()


@pytest.fixture
def device_disclosure():
    """提供装置类技术交底书数据"""
    return DEVICE_DISCLOSURE.copy()


@pytest.fixture
def method_disclosure():
    """提供方法类技术交底书数据"""
    return METHOD_DISCLOSURE.copy()


@pytest.fixture
def valid_claims():
    """提供有效的权利要求数据"""
    return VALID_CLAIMS.copy()


@pytest.fixture
def valid_specification():
    """提供有效的说明书数据"""
    return VALID_SPECIFICATION.copy()


@pytest.fixture
def valid_office_action():
    """提供有效的审查意见数据"""
    return VALID_OFFICE_ACTION.copy()


@pytest.fixture
def valid_invalidation_data():
    """提供有效的无效宣告数据"""
    return VALID_INVALIDATION_DATA.copy()


@pytest.fixture
def llm_success_responses():
    """提供LLM成功响应"""
    return LLM_SUCCESS_RESPONSES.copy()


@pytest.fixture
def valid_execution_context():
    """提供有效的执行上下文"""
    return VALID_EXECUTION_CONTEXT.copy()


@pytest.fixture
def writer_context_claims():
    """提供权利要求撰写上下文"""
    return WRITER_CONTEXT_CLAIMS.copy()


@pytest.fixture
def writer_context_response():
    """提供审查意见答复上下文"""
    return WRITER_CONTEXT_RESPONSE.copy()


@pytest.fixture
def writer_context_invalidation():
    """提供无效宣告上下文"""
    return WRITER_CONTEXT_INVALIDATION.copy()


@pytest.fixture
def drafting_proxy_context_analyze():
    """提供交底书分析上下文"""
    return DRAFTING_PROXY_CONTEXT_ANALYZE.copy()


@pytest.fixture
def drafting_proxy_context_assess():
    """提供可专利性评估上下文"""
    return DRAFTING_PROXY_CONTEXT_ASSESS.copy()


@pytest.fixture
def drafting_proxy_context_specification():
    """提供说明书撰写上下文"""
    return DRAFTING_PROXY_CONTEXT_SPECIFICATION.copy()


@pytest.fixture
def drafting_proxy_context_claims():
    """提供权利要求撰写上下文"""
    return DRAFTING_PROXY_CONTEXT_CLAIMS.copy()


@pytest.fixture
def drafting_proxy_context_optimize():
    """提供保护范围优化上下文"""
    return DRAFTING_PROXY_CONTEXT_OPTIMIZE.copy()


@pytest.fixture
def drafting_proxy_context_adequacy():
    """提供充分公开审查上下文"""
    return DRAFTING_PROXY_CONTEXT_ADEQUACY.copy()


@pytest.fixture
def drafting_proxy_context_errors():
    """提供错误检测上下文"""
    return DRAFTING_PROXY_CONTEXT_ERRORS.copy()
