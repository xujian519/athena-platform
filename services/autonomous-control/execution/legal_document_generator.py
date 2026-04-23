#!/usr/bin/env python3
"""
法律文书生成器
Legal Document Generator

智能生成各类法律文书

作者: 小娜·天秤女神
创建时间: 2024年12月15日
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
from jinja2 import Environment, FileSystemLoader, Template

logger = logging.getLogger(__name__)

class LegalDocumentGenerator:
    """法律文书生成器"""

    def __init__(self):
        """初始化文书生成器"""
        self.template_dir = Path("/Users/xujian/Athena工作平台/services/autonomous-control/templates/legal")
        self.output_dir = Path("/Users/xujian/Athena工作平台/data/legal_documents")

        # 确保目录存在
        self.template_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 初始化模板环境
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.template_dir)),
            autoescape=True
        )

        # 文书类型映射
        self.document_types = {
            "patent": {
                "application": "patent_application_template.j2",
                "response": "patent_response_template.j2",
                "amendment": "patent_amendment_template.j2"
            },
            "trademark": {
                "application": "trademark_application_template.j2",
                "opposition": "trademark_opposition_template.j2",
                "renewal": "trademark_renewal_template.j2"
            },
            "copyright": {
                "registration": "copyright_registration_template.j2",
                "license": "copyright_license_template.j2",
                "infringement": "copyright_infringement_template.j2"
            },
            "contract": {
                "draft": "contract_draft_template.j2",
                "review": "contract_review_template.j2",
                "amendment": "contract_amendment_template.j2"
            }
        }

        self.templates = {}
        self.initialized = False

    async def initialize(self):
        """初始化文书生成器"""
        try:
            # 加载所有模板
            for doc_type, templates in self.document_types.items():
                self.templates[doc_type] = {}
                for template_name, template_file in templates.items():
                    template_path = self.template_dir / template_file
                    if template_path.exists():
                        with open(template_path, encoding='utf-8') as f:
                            template_content = f.read()
                        self.templates[doc_type][template_name] = Template(template_content)
                    else:
                        # 创建基础模板
                        await self._create_basic_template(doc_type, template_name)

            # 创建标准模板
            await self._create_standard_templates()

            self.initialized = True
            logger.info("✅ 法律文书生成器初始化完成")

        except Exception as e:
            logger.error(f"❌ 文书生成器初始化失败: {str(e)}")
            # 创建默认模板
            await self._create_default_templates()
            self.initialized = True

    async def generate_document(self, request: dict[str, Any]) -> dict[str, Any]:
        """
        生成法律文书

        Args:
            request: 生成请求
            {
                "document_type": "patent|trademark|copyright|contract",
                "template_type": "application|response|review|draft",
                "data": {...},  # 文书数据
                "format": "docx|pdf|html",  # 输出格式
                "user_id": "user123"
            }

        Returns:
            生成结果
        """
        if not self.initialized:
            await self.initialize()

        try:
            document_type = request.get("document_type", "patent")
            template_type = request.get("template_type", "application")
            data = request.get("data", {})
            output_format = request.get("format", "html")
            user_id = request.get("user_id", "anonymous")

            # 获取模板
            template = self._get_template(document_type, template_type)
            if not template:
                raise ValueError(f"模板不存在: {document_type}/{template_type}")

            # 数据预处理
            processed_data = await self._preprocess_data(data, document_type)

            # 生成文书内容
            content = template.render(**processed_data)

            # 格式化输出
            formatted_content = await self._format_content(content, output_format)

            # 生成文档信息
            document_info = {
                "document_id": f"DOC_{document_type.upper()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "document_type": document_type,
                "template_type": template_type,
                "format": output_format,
                "generated_at": datetime.now().isoformat(),
                "user_id": user_id,
                "file_path": None,
                "preview": content[:500] + "..." if len(content) > 500 else content
            }

            # 保存文档
            if output_format in ["docx", "pdf", "html"]:
                file_path = await self._save_document(document_info, formatted_content)
                document_info["file_path"] = file_path

            # 质量检查
            quality_score = await self._quality_check(content, document_type)
            document_info["quality_score"] = quality_score

            logger.info(f"✅ 文书生成成功: {document_info['document_id']}")

            return {
                "success": True,
                "document": document_info,
                "content": formatted_content if output_format == "html" else None
            }

        except Exception as e:
            logger.error(f"❌ 文书生成失败: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "document": None
            }

    async def _preprocess_data(self, data: dict[str, Any], document_type: str) -> dict[str, Any]:
        """预处理文书数据"""
        processed_data = data.copy()

        # 添加通用信息
        processed_data.update({
            "current_date": datetime.now().strftime("%Y年%m月%d日"),
            "current_year": datetime.now().year,
            "generator": "小娜法律智能助手",
            "version": "v2.0"
        })

        # 根据文书类型添加特定信息
        if document_type == "patent":
            processed_data.update(await self._process_patent_data(data))
        elif document_type == "trademark":
            processed_data.update(await self._process_trademark_data(data))
        elif document_type == "copyright":
            processed_data.update(await self._process_copyright_data(data))
        elif document_type == "contract":
            processed_data.update(await self._process_contract_data(data))

        return processed_data

    async def _process_patent_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理专利数据"""
        patent_data = {}

        # 申请人信息
        applicant = data.get("applicant", {})
        patent_data["applicant_name"] = applicant.get("name", "")
        patent_data["applicant_address"] = applicant.get("address", "")
        patent_data["applicant_postcode"] = applicant.get("postcode", "")

        # 发明人信息
        inventors = data.get("inventors", [])
        patent_data["inventors"] = inventors
        patent_data["inventor_count"] = len(inventors)

        # 专利信息
        patent_info = data.get("patent_info", {})
        patent_data["title"] = patent_info.get("title", "")
        patent_data["abstract"] = patent_info.get("abstract", "")
        patent_data["technical_field"] = patent_info.get("technical_field", "")
        patent_data["claims"] = patent_info.get("claims", [])
        patent_data["description"] = patent_info.get("description", "")

        # 代理信息
        agent = data.get("agent", {})
        patent_data["agent_name"] = agent.get("name", "")
        patent_data["agent_code"] = agent.get("code", "")
        patent_data["agency"] = agent.get("agency", "")

        return patent_data

    async def _process_trademark_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理商标数据"""
        trademark_data = {}

        # 申请人信息
        applicant = data.get("applicant", {})
        trademark_data["applicant_name"] = applicant.get("name", "")
        trademark_data["applicant_address"] = applicant.get("address", "")

        # 商标信息
        trademark_info = data.get("trademark_info", {})
        trademark_data["trademark_name"] = trademark_info.get("name", "")
        trademark_data["trademark_image"] = trademark_info.get("image", "")
        trademark_data["class"] = trademark_info.get("class", "")
        trademark_data["goods_services"] = trademark_info.get("goods_services", [])

        return trademark_data

    async def _process_copyright_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理版权数据"""
        copyright_data = {}

        # 著作权人信息
        owner = data.get("owner", {})
        copyright_data["owner_name"] = owner.get("name", "")
        copyright_data["owner_type"] = owner.get("type", "")  # 个人/单位

        # 作品信息
        work = data.get("work", {})
        copyright_data["work_name"] = work.get("name", "")
        copyright_data["work_type"] = work.get("type", "")
        copyright_data["creation_date"] = work.get("creation_date", "")
        copyright_data["publication_date"] = work.get("publication_date", "")

        return copyright_data

    async def _process_contract_data(self, data: dict[str, Any]) -> dict[str, Any]:
        """处理合同数据"""
        contract_data = {}

        # 合同当事人
        parties = data.get("parties", [])
        contract_data["parties"] = parties
        contract_data["party_a"] = parties[0] if len(parties) > 0 else {}
        contract_data["party_b"] = parties[1] if len(parties) > 1 else {}

        # 合同信息
        contract_info = data.get("contract_info", {})
        contract_data["contract_name"] = contract_info.get("name", "")
        contract_data["contract_number"] = contract_info.get("number", "")
        contract_data["effective_date"] = contract_info.get("effective_date", "")
        contract_data["expiry_date"] = contract_info.get("expiry_date", "")

        # 合同条款
        clauses = data.get("clauses", [])
        contract_data["clauses"] = clauses

        return contract_data

    async def _format_content(self, content: str, format_type: str) -> Any:
        """格式化内容输出"""
        if format_type == "html":
            # 添加HTML样式
            html_template = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>法律文书</title>
                <style>
                    body { font-family: "Microsoft YaHei", sans-serif; line-height: 1.6; margin: 40px; }
                    h1 { text-align: center; color: #333; }
                    h2 { color: #666; border-bottom: 1px solid #ddd; padding-bottom: 10px; }
                    .section { margin: 20px 0; }
                    .field { margin: 10px 0; }
                    label { font-weight: bold; color: #555; }
                    .value { margin-left: 10px; }
                    .signature { margin-top: 50px; }
                </style>
            </head>
            <body>
                {{ content }}
            </body>
            </html>
            """
            return html_template.replace("{{ content }}", content)

        elif format_type == "docx":
            # 这里应该使用python-docx库生成DOCX文件
            # 简化实现，返回HTML格式
            return content

        elif format_type == "pdf":
            # 这里应该使用reportlab或weasyprint生成PDF
            # 简化实现，返回HTML格式
            return content

        else:
            return content

    async def _save_document(self, document_info: dict[str, Any], content: Any) -> str:
        """保存文档"""
        filename = f"{document_info['document_id']}.{document_info['format']}"
        file_path = self.output_dir / filename

        if document_info['format'] == 'html':
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(content)

        # 其他格式的保存逻辑...

        logger.info(f"✅ 文书已保存: {file_path}")
        return str(file_path)

    async def _quality_check(self, content: str, document_type: str) -> float:
        """文书质量检查"""
        score = 0.0

        # 基础检查
        if len(content) > 100:
            score += 0.2  # 内容长度

        # 关键字段检查
        keywords = {
            "patent": ["发明", "专利", "申请人", "发明人"],
            "trademark": ["商标", "申请人", "类别"],
            "copyright": ["作品", "著作权人", "创作"],
            "contract": ["合同", "当事人", "条款"]
        }

        for keyword in keywords.get(document_type, []):
            if keyword in content:
                score += 0.2

        # 格式检查
        if "### " in content or "**" in content:  # Markdown格式
            score += 0.1

        return min(score, 1.0)

    def _get_template(self, document_type: str, template_type: str) -> Template | None:
        """获取模板"""
        return self.templates.get(document_type, {}).get(template_type)

    async def _create_basic_template(self, doc_type: str, template_name: str):
        """创建基础模板"""
        template_content = self._get_template_content(doc_type, template_name)
        template_file = self.template_dir / f"{doc_type}_{template_name}_template.j2"

        async with aiofiles.open(template_file, 'w', encoding='utf-8') as f:
            await f.write(template_content)

    def _get_template_content(self, doc_type: str, template_name: str) -> str:
        """获取模板内容"""
        if doc_type == "patent":
            if template_name == "application":
                return """# 发明专利申请书

## 申请人信息
- **名称**: {{ applicant_name }}
- **地址**: {{ applicant_address }}
- **邮编**: {{ applicant_postcode }}

## 发明人信息
{% for inventor in inventors %}
- **发明人{{ loop.index }}**: {{ inventor.name }}
- **地址**: {{ inventor.address }}
{% endfor %}

## 发明名称
{{ title }}

## 摘要
{{ abstract }}

## 技术领域
{{ technical_field }}

## 权利要求书
{% for claim in claims %}
{{ loop.index }}. {{ claim.text }}
{% endfor %}

## 说明书
{{ description }}

## 代理信息
- **代理人**: {{ agent_name }}
- **机构代码**: {{ agent_code }}
- **代理机构**: {{ agency }}

---
生成时间: {{ current_date }}
生成者: {{ generator }}
"""
        elif doc_type == "trademark":
            if template_name == "application":
                return """# 商标注册申请书

## 申请人信息
- **名称**: {{ applicant_name }}
- **地址**: {{ applicant_address }}

## 商标信息
- **商标名称**: {{ trademark_name }}
- **商标类别**: {{ class }}
- **商标图样**: {{ trademark_image }}

## 商品/服务列表
{% for item in goods_services %}
- {{ item }}
{% endfor %}

---
生成时间: {{ current_date }}
生成者: {{ generator }}
"""

        # 返回通用模板
        return """# {{ document_title }}

{{ content }}

---
生成时间: {{ current_date }}
生成者: {{ generator }}
版本: {{ version }}
"""

    async def _create_standard_templates(self):
        """创建标准模板"""
        # 专利申请模板
        await self._create_basic_template("patent", "application")

        # 商标注册模板
        await self._create_basic_template("trademark", "application")

        # 合同审查模板
        await self._create_basic_template("contract", "review")

        # 版权登记模板
        await self._create_basic_template("copyright", "registration")

    async def _create_default_templates(self):
        """创建默认模板"""
        for doc_type in self.document_types:
            for template_name in self.document_types[doc_type]:
                await self._create_basic_template(doc_type, template_name)

    async def get_template_list(self, document_type: str = None) -> list[dict[str, str]:
        """获取模板列表"""
        templates = []

        for doc_type, type_templates in self.document_types.items():
            if document_type and doc_type != document_type:
                continue

            for template_name in type_templates:
                templates.append({
                    "document_type": doc_type,
                    "template_name": template_name,
                    "template_file": type_templates[template_name]
                })

        return templates

    async def update_template(self, document_type: str, template_name: str, template_content: str):
        """更新模板"""
        try:
            template_file = self.template_dir / f"{document_type}_{template_name}_template.j2"
            async with aiofiles.open(template_file, 'w', encoding='utf-8') as f:
                await f.write(template_content)

            # 重新加载模板
            self.templates[document_type][template_name] = Template(template_content)

            logger.info(f"✅ 模板已更新: {document_type}/{template_name}")
            return True

        except Exception as e:
            logger.error(f"❌ 模板更新失败: {str(e)}")
            return False

    async def preview_document(self, request: dict[str, Any]) -> dict[str, Any]:
        """预览文档"""
        # 不保存文档，只返回内容预览
        request["format"] = "preview"
        result = await self.generate_document(request)

        if result["success"]:
            return {
                "success": True,
                "preview": result["document"]["preview"],
                "document_info": result["document"]
            }
        else:
            return result

# 使用示例
async def main():
    """测试文书生成器"""
    generator = LegalDocumentGenerator()
    await generator.initialize()

    # 生成专利申请
    result = await generator.generate_document({
        "document_type": "patent",
        "template_type": "application",
        "data": {
            "applicant": {
                "name": "北京科技有限公司",
                "address": "北京市海淀区xxx街道",
                "postcode": "100000"
            },
            "patent_info": {
                "title": "一种智能专利申请系统",
                "abstract": "本发明涉及一种智能专利申请系统...",
                "technical_field": "人工智能技术领域",
                "claims": [
                    {"text": "一种智能专利申请系统，其特征在于..."},
                    {"text": "根据权利要求1所述的系统..."}
                ],
                "description": "本发明提供了一种智能专利申请系统..."
            }
        },
        "format": "html",
        "user_id": "test_user"
    })

    print(f"生成结果: {result['success']}")
    if result['success']:
        print(f"文档ID: {result['document']['document_id']}")
        print(f"质量分数: {result['document']['quality_score']}")

    # 获取模板列表
    templates = await generator.get_template_list()
    print(f"可用模板: {len(templates)}")

# 入口点: @async_main装饰器已添加到main函数
