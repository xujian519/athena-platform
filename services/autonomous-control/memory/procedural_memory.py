#!/usr/bin/env python3
"""
程序记忆库
Procedural Memory Library

存储和复用法律程序和流程

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import json
import logging
import os
import pickle
from dataclasses import dataclass
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)

@dataclass
class LegalProcedure:
    """法律程序结构"""
    procedure_id: str
    name: str
    category: str  # patent, trademark, copyright, contract
    description: str
    steps: list[dict[str, Any]]
    required_documents: list[str]
    timeline: dict[str, str]
    costs: dict[str, float]
    risks: list[dict[str, str]]
    success_rate: float
    last_updated: str
    tags: list[str]

class ProceduralMemory:
    """程序记忆系统"""

    def __init__(self):
        """初始化程序记忆"""
        self.procedures = {}
        self.procedures_file = "/Users/xujian/Athena工作平台/data/procedural_memory.pkl"
        self.templates_file = "/Users/xujian/Athena工作平台/data/procedural_templates.json"
        self.load_procedures()
        self.load_templates()

    def load_procedures(self) -> Any | None:
        """加载已保存的程序"""
        try:
            if os.path.exists(self.procedures_file):
                with open(self.procedures_file, 'rb') as f:
                    self.procedures = pickle.load(f)
                logger.info(f"✅ 已加载 {len(self.procedures)} 个程序")
            else:
                # 初始化基础程序
                self._initialize_base_procedures()
                logger.info("✅ 已初始化基础程序")
        except Exception as e:
            logger.error(f"加载程序失败: {str(e)}")
            self.procedures = {}

    def save_procedures(self) -> None:
        """保存程序"""
        try:
            os.makedirs(os.path.dirname(self.procedures_file), exist_ok=True)
            with open(self.procedures_file, 'wb') as f:
                pickle.dump(self.procedures, f)
            logger.info("✅ 程序已保存")
        except Exception as e:
            logger.error(f"保存程序失败: {str(e)}")

    def load_templates(self) -> Any | None:
        """加载程序模板"""
        try:
            if os.path.exists(self.templates_file):
                with open(self.templates_file, encoding='utf-8') as f:
                    self.templates = json.load(f)
                logger.info(f"✅ 已加载 {len(self.templates)} 个模板")
            else:
                self.templates = {}
                logger.info("✅ 已初始化模板")
        except Exception as e:
            logger.error(f"加载模板失败: {str(e)}")
            self.templates = {}

    def _initialize_base_procedures(self) -> Any:
        """初始化基础法律程序"""
        # 专利申请程序
        patent_procedure = LegalProcedure(
            procedure_id="PATENT_APPLICATION_V1",
            name="发明专利申请流程",
            category="patent",
            description="标准发明专利申请程序",
            steps=[
                {
                    "step": 1,
                    "name": "技术交底书准备",
                    "description": "准备详细的技术交底书",
                    "duration": "3-7天",
                    "responsible": "发明人/申请人",
                    "outputs": ["技术交底书"]
                },
                {
                    "step": 2,
                    "name": "专利检索",
                    "description": "进行现有技术检索",
                    "duration": "5-10天",
                    "responsible": "专利代理人",
                    "outputs": ["检索报告"]
                },
                {
                    "step": 3,
                    "name": "专利撰写",
                    "description": "撰写专利申请文件",
                    "duration": "7-14天",
                    "responsible": "专利代理人",
                    "outputs": ["专利申请文件"]
                },
                {
                    "step": 4,
                    "name": "提交申请",
                    "description": "向专利局提交申请",
                    "duration": "1天",
                    "responsible": "申请人/代理机构",
                    "outputs": ["申请受理通知书"]
                },
                {
                    "step": 5,
                    "name": "审查答复",
                    "description": "答复审查意见",
                    "duration": "2-4月",
                    "responsible": "专利代理人",
                    "outputs": ["审查答复文件"]
                },
                {
                    "step": 6,
                    "name": "授权办证",
                    "description": "办理授权登记手续",
                    "duration": "1-2月",
                    "responsible": "申请人",
                    "outputs": ["专利证书"]
                }
            ],
            required_documents=[
                "技术交底书",
                "申请人身份证明",
                "发明人信息",
                "委托书（如委托代理）"
            ],
            timeline={
                "total_duration": "6-12个月",
                "key_milestones": [
                    "申请日",
                    "初审合格日",
                    "公布日",
                    "授权日"
                ]
            },
            costs={
                "申请费": 900,
                "代理费": 5000-20000,
                "审查费": 2500,
                "年费": 900-9000
            },
            risks=[
                {"risk": "新颖性问题", "probability": "30%"},
                {"risk": "创造性不足", "probability": "25%"},
                {"risk": "撰写缺陷", "probability": "15%"},
                {"risk": "审查延迟", "probability": "20%"}
            ],
            success_rate=0.65,
            last_updated=datetime.now().isoformat(),
            tags=["发明专利", "标准流程", "国内申请"]
        )

        # 商标注册程序
        trademark_procedure = LegalProcedure(
            procedure_id="TRADEMARK_REGISTRATION_V1",
            name="商标注册流程",
            category="trademark",
            description="标准商标注册程序",
            steps=[
                {
                    "step": 1,
                    "name": "商标查询",
                    "description": "查询商标是否可注册",
                    "duration": "1-3天",
                    "responsible": "申请人/代理机构",
                    "outputs": ["商标查询报告"]
                },
                {
                    "step": 2,
                    "name": "申请提交",
                    "description": "提交商标注册申请",
                    "duration": "1天",
                    "responsible": "申请人/代理机构",
                    "outputs": ["申请受理通知书"]
                },
                {
                    "step": 3,
                    "name": "形式审查",
                    "description": "商标局形式审查",
                    "duration": "1个月",
                    "responsible": "商标局",
                    "outputs": ["审查结果通知书"]
                },
                {
                    "step": 4,
                    "name": "实质审查",
                    "description": "商标局实质审查",
                    "duration": "6-9个月",
                    "responsible": "商标局",
                    "outputs": ["审定公告或驳回通知书"]
                },
                {
                    "step": 5,
                    "name": "公告期",
                    "description": "3个月异议期",
                    "duration": "3个月",
                    "responsible": "商标局",
                    "outputs": ["异议情况"]
                },
                {
                    "step": 6,
                    "name": "注册证发放",
                    "description": "发放商标注册证",
                    "duration": "1-2个月",
                    "responsible": "商标局",
                    "outputs": ["商标注册证"]
                }
            ],
            required_documents=[
                "商标图样",
                "申请人身份证明",
                "商品/服务分类表",
                "委托书（如委托代理）"
            ],
            timeline={
                "total_duration": "9-12个月",
                "key_milestones": [
                    "申请日",
                    "初审公告日",
                    "注册公告日",
                    "注册日"
                ]
            },
            costs={
                "申请费": 300,
                "代理费": 1000-5000,
                "公告费": 0
            },
            risks=[
                {"risk": "商标近似", "probability": "35%"},
                {"risk": "缺乏显著性", "probability": "20%"},
                {"risk": "异议", "probability": "10%"},
                {"risk": "审查驳回", "probability": "15%"}
            ],
            success_rate=0.75,
            last_updated=datetime.now().isoformat(),
            tags=["商标注册", "标准流程", "国内申请"]
        )

        # 合同审查程序
        contract_procedure = LegalProcedure(
            procedure_id="CONTRACT_REVIEW_V1",
            name="合同审查流程",
            category="contract",
            description="标准合同审查程序",
            steps=[
                {
                    "step": 1,
                    "name": "合同接收",
                    "description": "接收合同文本",
                    "duration": "1天",
                    "responsible": "法务/申请人",
                    "outputs": ["合同文本"]
                },
                {
                    "step": 2,
                    "name": "主体资格审查",
                    "description": "审查合同主体资格",
                    "duration": "1-2天",
                    "responsible": "法务",
                    "outputs": ["主体资格审查报告"]
                },
                {
                    "step": 3,
                    "name": "条款完整性检查",
                    "description": "检查合同条款完整性",
                    "duration": "2-3天",
                    "responsible": "法务",
                    "outputs": ["条款检查清单"]
                },
                {
                    "step": 4,
                    "name": "合法性审查",
                    "description": "审查合同条款合法性",
                    "duration": "2-3天",
                    "responsible": "法务",
                    "outputs": ["合法性审查意见"]
                },
                {
                    "step": 5,
                    "name": "风险评估",
                    "description": "评估合同风险",
                    "duration": "2天",
                    "responsible": "法务",
                    "outputs": ["风险评估报告"]
                },
                {
                    "step": 6,
                    "name": "修改建议",
                    "description": "提供修改建议",
                    "duration": "1-2天",
                    "responsible": "法务",
                    "outputs": ["修改建议书"]
                }
            ],
            required_documents=[
                "合同文本",
                "当事人身份证明",
                "相关资质证明"
            ],
            timeline={
                "total_duration": "7-12天",
                "key_milestones": [
                    "接收合同",
                    "完成审查",
                    "出具意见"
                ]
            },
            costs={
                "审查费": 2000-10000,
                "修改费": 1000-5000
            },
            risks=[
                {"risk": "条款歧义", "probability": "25%"},
                {"risk": "法律风险", "probability": "20%"},
                {"risk": "履行风险", "probability": "15%"},
                {"risk": "争议风险", "probability": "10%"}
            ],
            success_rate=0.90,
            last_updated=datetime.now().isoformat(),
            tags=["合同审查", "标准流程", "风险控制"]
        )

        # 添加到程序库
        self.procedures[patent_procedure.procedure_id] = patent_procedure
        self.procedures[trademark_procedure.procedure_id] = trademark_procedure
        self.procedures[contract_procedure.procedure_id] = contract_procedure

    def add_procedure(self, procedure: LegalProcedure) -> str:
        """添加程序"""
        self.procedures[procedure.procedure_id] = procedure
        self.save_procedures()
        logger.info(f"✅ 已添加程序: {procedure.name}")
        return procedure.procedure_id

    def get_procedure(self, procedure_id: str) -> LegalProcedure | None:
        """获取程序"""
        return self.procedures.get(procedure_id)

    def search_procedures(self, category: str = None,
                          tags: list[str] = None) -> list[LegalProcedure]:
        """搜索程序"""
        results = []
        for procedure in self.procedures.values():
            if category and procedure.category != category:
                continue
            if tags and not any(tag in procedure.tags for tag in tags):
                continue
            results.append(procedure)
        return results

    def recommend_procedure(self, user_request: str,
                            category: str = None) -> LegalProcedure | None:
        """推荐程序"""
        # 简化的推荐逻辑
        if not category:
            # 根据请求内容推断类别
            if any(word in user_request for word in ["专利", "发明", "技术"]):
                category = "patent"
            elif any(word in user_request for word in ["商标", "品牌", "logo"]):
                category = "trademark"
            elif any(word in user_request for word in ["合同", "协议", "条款"]):
                category = "contract"
            else:
                category = "legal_advice"

        # 获取该类别的程序
        procedures = self.search_procedures(category=category)

        # 返回成功率最高的程序
        if procedures:
            return max(procedures, key=lambda p: p.success_rate)

        return None

    def adapt_procedure(self, procedure_id: str,
                       adaptations: dict[str, Any]) -> LegalProcedure:
        """调整程序"""
        base_procedure = self.get_procedure(procedure_id)
        if not base_procedure:
            raise ValueError(f"程序不存在: {procedure_id}")

        # 创建调整后的程序
        adapted_procedure = LegalProcedure(
            procedure_id=f"{procedure_id}_ADAPTED_{datetime.now().strftime('%Y%m%d')}",
            name=f"{base_procedure.name}（调整版）",
            category=base_procedure.category,
            description=f"调整版：{base_procedure.description}",
            steps=adaptations.get("steps", base_procedure.steps),
            required_documents=adaptations.get("required_documents", base_procedure.required_documents),
            timeline=adaptations.get("timeline", base_procedure.timeline),
            costs=adaptations.get("costs", base_procedure.costs),
            risks=adaptations.get("risks", base_procedure.risks),
            success_rate=adaptations.get("success_rate", base_procedure.success_rate),
            last_updated=datetime.now().isoformat(),
            tags=base_procedure.tags + adaptations.get("additional_tags", [])
        )

        # 保存调整后的程序
        self.add_procedure(adapted_procedure)
        return adapted_procedure

    def get_procedure_template(self, category: str) -> dict[str, Any]:
        """获取程序模板"""
        template = self.templates.get(category, {})
        if not template:
            # 创建基础模板
            template = {
                "category": category,
                "steps_template": [
                    {
                        "step": "{step_number}",
                        "name": "{step_name}",
                        "description": "{step_description}",
                        "duration": "{duration}",
                        "responsible": "{responsible}",
                        "outputs": ["{output}"]
                    }
                ],
                "required_documents_template": [
                    "{document_name}"
                ],
                "timeline_template": {
                    "total_duration": "{duration}",
                    "key_milestones": ["{milestone}"]
                },
                "risks_template": [
                    {"risk": "{risk_description}", "probability": "{probability}"}
                ]
            }
        return template

    def generate_custom_procedure(self, requirements: dict[str, Any]) -> LegalProcedure:
        """生成定制程序"""
        category = requirements.get("category", "legal_advice")
        template = self.get_procedure_template(category)

        procedure_id = f"CUSTOM_{category.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        procedure = LegalProcedure(
            procedure_id=procedure_id,
            name=requirements.get("name", f"定制{category}程序"),
            category=category,
            description=requirements.get("description", "定制法律程序"),
            steps=requirements.get("steps", template.get("steps_template", [])),
            required_documents=requirements.get("required_documents",
                                           template.get("required_documents_template", [])),
            timeline=requirements.get("timeline", template.get("timeline_template", {})),
            costs=requirements.get("costs", {"咨询费": 1000}),
            risks=requirements.get("risks", template.get("risks_template", [])),
            success_rate=requirements.get("success_rate", 0.80),
            last_updated=datetime.now().isoformat(),
            tags=requirements.get("tags", ["定制程序"])
        )

        self.add_procedure(procedure)
        return procedure

    def update_procedure_usage(self, procedure_id: str, success: bool) -> None:
        """更新程序使用记录"""
        procedure = self.get_procedure(procedure_id)
        if procedure:
            # 简化的更新逻辑
            # 实际应该记录使用次数和成功率
            if success:
                procedure.success_rate = min(1.0, procedure.success_rate * 1.01)
            else:
                procedure.success_rate = max(0.1, procedure.success_rate * 0.99)
            procedure.last_updated = datetime.now().isoformat()
            self.procedures[procedure_id] = procedure
            self.save_procedures()

    def get_statistics(self) -> dict[str, Any]:
        """获取统计信息"""
        stats = {
            "total_procedures": len(self.procedures),
            "by_category": {},
            "average_success_rate": 0,
            "most_used_procedures": []
        }

        # 按类别统计
        category_counts = {}
        total_success = 0
        for procedure in self.procedures.values():
            category = procedure.category
            category_counts[category] = category_counts.get(category, 0) + 1
            total_success += procedure.success_rate

        stats["by_category"] = category_counts

        # 平均成功率
        if self.procedures:
            stats["average_success_rate"] = total_success / len(self.procedures)

        # 最常用的程序（简化实现）
        stats["most_used_procedures"] = [
            {
                "procedure_id": pid,
                "name": proc.name,
                "success_rate": proc.success_rate
            }
            for pid, proc in list(self.procedures.items())[:5]
        ]

        return stats

# 使用示例
def main() -> None:
    """测试程序记忆"""
    procedural_memory = ProceduralMemory()

    # 推荐程序
    procedure = procedural_memory.recommend_procedure(
        "我想申请一个发明专利"
    )
    if procedure:
        print(f"推荐程序: {procedure.name}")
        print(f"成功率: {procedure.success_rate}")
        print(f"步骤数: {len(procedure.steps)}")

    # 获取统计
    stats = procedural_memory.get_statistics()
    print(f"统计信息: {stats}")

if __name__ == "__main__":
    main()
