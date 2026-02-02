#!/usr/bin/env python3
"""
Athena平台通用工具 - LangExtract智能信息提取系统
可由小诺和小娜完全控制的企业级结构化信息提取工具
"""

import asyncio
import hashlib
import json
import logging
from core.logging_config import setup_logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

# 添加项目路径
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# 添加LangExtract路径
langextract_path = project_root / 'projects' / 'langextract'
sys.path.append(str(langextract_path))

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = setup_logging()

try:
    import langextract as lx
    from langextract import data
except ImportError:
    logger.warning('LangExtract未安装，将使用模拟模式')
    lx = None
    data = None


class ExtractionScenario(Enum):
    """信息提取场景枚举"""
    PATENT_ANALYSIS = 'patent_analysis'
    CONTRACT_REVIEW = 'contract_review'
    MEDICAL_REPORT = 'medical_report'
    FINANCIAL_STATEMENT = 'financial_statement'
    ACADEMIC_PAPER = 'academic_paper'
    NEWS_ARTICLE = 'news_article'
    PRODUCT_REVIEW = 'product_review'
    LEGAL_DOCUMENT = 'legal_document'
    TECHNICAL_DOCUMENT = 'technical_document'
    BUSINESS_REPORT = 'business_report'
    USER_FEEDBACK = 'user_feedback'
    MARKET_RESEARCH = 'market_research'


@dataclass
class ExtractionTask:
    """信息提取任务定义"""
    task_id: str
    scenario: ExtractionScenario
    text_or_documents: Union[str, List[str]]
    prompt_description: str | None = None
    examples: Optional[List[Any]] = None
    model_id: str = 'gemini-2.5-flash'
    config: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1
    max_retries: int = 3
    timeout: int = 300
    callback_url: str | None = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """信息提取结果"""
    task_id: str
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    extractions: List[Any] = field(default_factory=list)
    error: str | None = None
    stats: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


class LangExtractTool:
    """LangExtract智能信息提取通用工具类"""

    # 工具定义
    TOOL_DEFINITION = {
        'name': 'langextract_intelligent_extractor',
        'display_name': 'LangExtract智能信息提取系统',
        'description': '企业级结构化信息提取工具，支持多场景文本分析和智能理解',
        'version': '1.0.0',
        'capabilities': [
            '专利文档分析',
            '合同条款提取',
            '医学报告解析',
            '财务报表分析',
            '学术论文理解',
            '新闻事件提取',
            '产品评论分析',
            '法律文件审查',
            '技术文档解析',
            '商业报告分析',
            '用户反馈整理',
            '市场研究洞察'
        ],
        'status': 'ready',
        'last_used': None,
        'usage_count': 0
    }

    # 预定义场景配置
    SCENARIOS = {
        ExtractionScenario.PATENT_ANALYSIS: {
            'name': '专利分析',
            'description': '从专利文档中提取技术特征、权利要求、创新点等信息',
            "prompt_template": """
            从专利文档中提取以下结构化信息：
            1. 发明名称和专利号
            2. 技术领域和背景技术
            3. 发明内容和技术方案
            4. 权利要求书的关键技术特征
            5. 具体实施方式
            6. 技术效果和优势
            7. 创新点和突破
            """,
            'examples': [
                {
                    'text': '本发明涉及一种人工智能数据处理方法，包括以下步骤...',
                    'extractions': [
                        {
                            'extraction_class': 'invention_name',
                            'extraction_text': '人工智能数据处理方法',
                            'attributes': {'field': '计算机技术', 'type': '方法发明'}
                        },
                        {
                            'extraction_class': 'technical_feature',
                            'extraction_text': '包括以下步骤',
                            'attributes': {'category': '流程特征', 'importance': 'high'}
                        }
                    ]
                }
            ]
        },
        
        ExtractionScenario.CONTRACT_REVIEW: {
            'name': '合同审查',
            'description': '从合同文档中提取关键条款、当事人信息、权利义务等',
            "prompt_template": """
            从合同文档中提取以下结构化信息：
            1. 合同当事人信息
            2. 合同类型和有效期
            3. 关键条款和条件
            4. 权利和义务
            5. 违约责任
            6. 争议解决方式
            7. 特殊约定和限制
            """,
            'examples': [
                {
                    'text': '甲方：ABC科技有限公司，乙方：XYZ数据服务公司...',
                    'extractions': [
                        {
                            'extraction_class': 'party',
                            'extraction_text': 'ABC科技有限公司',
                            'attributes': {'role': '甲方', 'type': '公司'}
                        },
                        {
                            'extraction_class': 'party',
                            'extraction_text': 'XYZ数据服务公司',
                            'attributes': {'role': '乙方', 'type': '公司'}
                        }
                    ]
                }
            ]
        },

        ExtractionScenario.MEDICAL_REPORT: {
            'name': '医学报告分析',
            'description': '从医学报告中提取诊断信息、检查结果、治疗方案等',
            "prompt_template": """
            从医学报告中提取以下结构化信息：
            1. 患者基本信息（脱敏）
            2. 主诉和症状
            3. 检查结果和数值
            4. 诊断结论
            5. 治疗方案和建议
            6. 用药信息
            7. 医生建议和注意事项
            """,
            'examples': [
                {
                    'text': '患者主诉头痛持续3天，体温37.5°C...',
                    'extractions': [
                        {
                            'extraction_class': 'symptom',
                            'extraction_text': '头痛持续3天',
                            'attributes': {'duration': '3天', 'severity': '待评估'}
                        },
                        {
                            'extraction_class': 'vital_signs',
                            'extraction_text': '体温37.5°C',
                            'attributes': {'parameter': '体温', 'value': '37.5', 'unit': '°C', 'status': '正常'}
                        }
                    ]
                }
            ]
        },

        ExtractionScenario.FINANCIAL_STATEMENT: {
            'name': '财务报表分析',
            'description': '从财务报表中提取关键财务指标、业绩数据等',
            "prompt_template": """
            从财务报表中提取以下结构化信息：
            1. 营业收入和净利润
            2. 资产负债表关键项目
            3. 现金流量表数据
            4. 关键财务比率
            5. 同比增长情况
            6. 业绩展望和风险提示
            """,
            'examples': [
                {
                    'text': '公司2023年营业收入10.5亿元，同比增长15%...',
                    'extractions': [
                        {
                            'extraction_class': 'revenue',
                            'extraction_text': '营业收入10.5亿元',
                            'attributes': {'year': '2023', 'amount': '10.5', 'unit': '亿元'}
                        },
                        {
                            'extraction_class': 'growth_rate',
                            'extraction_text': '同比增长15%',
                            'attributes': {'type': '同比增长', 'rate': '15%'}
                        }
                    ]
                }
            ]
        },

        ExtractionScenario.ACADEMIC_PAPER: {
            'name': '学术论文分析',
            'description': '从学术论文中提取研究方法、实验结果、结论等',
            "prompt_template": """
            从学术论文中提取以下结构化信息：
            1. 论文标题和作者信息
            2. 研究背景和目的
            3. 研究方法和实验设计
            4. 主要结果和发现
            5. 结论和意义
            6. 关键词和分类号
            7. 参考文献和引用
            """,
            'examples': [
                {
                    'text': '本文提出了一种基于深度学习的图像识别算法...',
                    'extractions': [
                        {
                            'extraction_class': 'methodology',
                            'extraction_text': '基于深度学习的图像识别算法',
                            'attributes': {'field': '计算机视觉', 'approach': '深度学习'}
                        }
                    ]
                }
            ]
        },

        ExtractionScenario.NEWS_ARTICLE: {
            'name': '新闻文章分析',
            'description': '从新闻文章中提取关键事件、人物、时间、地点等',
            "prompt_template": """
            从新闻文章中提取以下结构化信息：
            1. 新闻标题和摘要
            2. 关键事件和时间
            3. 涉及人物和组织
            4. 地点和场所
            5. 事件影响和意义
            6. 相关数据和统计
            7. 未来发展趋势
            """,
            'examples': [
                {
                    'text': '北京今日举办人工智能峰会，参会企业超过500家...',
                    'extractions': [
                        {
                            'extraction_class': 'event',
                            'extraction_text': '人工智能峰会',
                            'attributes': {'location': '北京', 'type': '会议'}
                        },
                        {
                            'extraction_class': 'participants',
                            'extraction_text': '参会企业超过500家',
                            'attributes': {'count': '500+', 'category': '企业'}
                        }
                    ]
                }
            ]
        }
    }

    def __init__(self):
        """初始化LangExtract工具"""
        self.is_available = lx is not None
        self.usage_stats = {
            'total_extractions': 0,
            'successful_extractions': 0,
            'failed_extractions': 0,
            'last_used': None
        }
        self.active_tasks = {}
        
        logger.info(f"LangExtract工具初始化完成，可用性: {self.is_available}")

    async def initialize(self) -> bool:
        """初始化工具"""
        try:
            if not self.is_available:
                logger.warning('LangExtract未安装，使用模拟模式')
                return True
            
            # 测试LangExtract是否正常工作
            test_text = '这是一个测试文本，用于验证LangExtract功能。'
            test_examples = [
                data.ExampleData(
                    text='测试文本',
                    extractions=[
                        data.Extraction(
                            extraction_class='test',
                            extraction_text='测试文本',
                            attributes={'type': 'sample'}
                        )
                    ]
                )
            ]
            
            # 这里只是验证模块可用，不实际执行提取
            logger.info('LangExtract工具初始化成功')
            return True
            
        except Exception as e:
            logger.error(f"LangExtract工具初始化失败: {e}")
            return False

    def get_status(self) -> Dict[str, Any]:
        """获取工具状态"""
        return {
            'tool': {
                'name': self.TOOL_DEFINITION['name'],
                'display_name': self.TOOL_DEFINITION['display_name'],
                'version': self.TOOL_DEFINITION['version'],
                'status': self.TOOL_DEFINITION['status'],
                'available': self.is_available,
                'last_used': self.TOOL_DEFINITION['last_used'],
                'usage_count': self.TOOL_DEFINITION['usage_count']
            },
            'scenarios': {
                'total': len(self.SCENARIOS),
                'available': list(self.SCENARIOS.keys())
            },
            'performance': self.usage_stats,
            'active_tasks': len(self.active_tasks)
        }

    async def list_scenarios(self) -> Dict[str, Any]:
        """列出可用的提取场景"""
        scenarios_info = {}
        for scenario, config in self.SCENARIOS.items():
            scenarios_info[scenario.value] = {
                'name': config['name'],
                'description': config['description'],
                'capabilities': config.get('capabilities', [])
            }
        
        return {
            'total_scenarios': len(self.SCENARIOS),
            'scenarios': scenarios_info
        }

    async def execute_scenario(
        self, 
        scenario: str, 
        text_or_documents: Union[str, List[str]], 
        config: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """执行预定义场景的信息提取"""
        start_time = datetime.now()
        
        try:
            # 验证场景
            if scenario not in [s.value for s in ExtractionScenario]:
                raise ValueError(f"不支持的场景: {scenario}")
            
            scenario_enum = ExtractionScenario(scenario)
            scenario_config = self.SCENARIOS[scenario_enum]
            
            # 创建任务
            task = ExtractionTask(
                task_id=self._generate_task_id(),
                scenario=scenario_enum,
                text_or_documents=text_or_documents,
                prompt_description=scenario_config['prompt_template'],
                examples=scenario_config['examples'],
                config=config or {}
            )
            
            # 执行提取
            result = await self._execute_extraction(task)
            
            # 更新统计
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            if result.success:
                self.usage_stats['successful_extractions'] += 1
            else:
                self.usage_stats['failed_extractions'] += 1
            
            self.usage_stats['total_extractions'] += 1
            self.usage_stats['last_used'] = datetime.now().isoformat()
            
            # 更新工具定义
            self.TOOL_DEFINITION['last_used'] = datetime.now().isoformat()
            self.TOOL_DEFINITION['usage_count'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"场景执行失败: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return ExtractionResult(
                task_id='error',
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    async def execute_custom_extraction(
        self,
        text_or_documents: Union[str, List[str]],
        prompt_description: str,
        examples: Optional[List[Any]] = None,
        model_id: str = 'gemini-2.5-flash',
        config: Optional[Dict[str, Any]] = None
    ) -> ExtractionResult:
        """执行自定义信息提取"""
        start_time = datetime.now()
        
        try:
            # 创建任务
            task = ExtractionTask(
                task_id=self._generate_task_id(),
                scenario=ExtractionScenario.BUSINESS_REPORT,  # 使用通用场景
                text_or_documents=text_or_documents,
                prompt_description=prompt_description,
                examples=examples or [],
                model_id=model_id,
                config=config or {}
            )
            
            # 执行提取
            result = await self._execute_extraction(task)
            
            # 更新统计
            execution_time = (datetime.now() - start_time).total_seconds()
            result.execution_time = execution_time
            
            if result.success:
                self.usage_stats['successful_extractions'] += 1
            else:
                self.usage_stats['failed_extractions'] += 1
            
            self.usage_stats['total_extractions'] += 1
            self.usage_stats['last_used'] = datetime.now().isoformat()
            
            return result
            
        except Exception as e:
            logger.error(f"自定义提取失败: {e}")
            execution_time = (datetime.now() - start_time).total_seconds()
            return ExtractionResult(
                task_id='error',
                success=False,
                error=str(e),
                execution_time=execution_time
            )

    async def _execute_extraction(self, task: ExtractionTask) -> ExtractionResult:
        """执行信息提取任务"""
        if not self.is_available:
            # 模拟模式
            return self._simulate_extraction(task)
        
        try:
            # 准备示例数据
            examples = []
            for example in task.examples:
                if isinstance(example, dict) and 'text' in example and 'extractions' in example:
                    # 转换为LangExtract格式
                    extractions = []
                    for ext in example['extractions']:
                        extractions.append(
                            data.Extraction(
                                extraction_class=ext['extraction_class'],
                                extraction_text=ext['extraction_text'],
                                attributes=ext.get('attributes', {})
                            )
                        )
                    
                    examples.append(
                        data.ExampleData(
                            text=example['text'],
                            extractions=extractions
                        )
                    )
            
            # 如果没有提供示例，创建一个默认示例
            if not examples:
                examples = [
                    data.ExampleData(
                        text='示例文本',
                        extractions=[
                            data.Extraction(
                                extraction_class='sample',
                                extraction_text='示例',
                                attributes={'type': 'default'}
                            )
                        ]
                    )
                ]
            
            # 执行LangExtract
            logger.info(f"开始执行信息提取任务: {task.task_id}")
            
            result = lx.extract(
                text_or_documents=task.text_or_documents,
                prompt_description=task.prompt_description,
                examples=examples,
                model_id=task.model_id,
                **task.config
            )
            
            # 处理结果
            if hasattr(result, 'extractions'):
                extractions = [
                    {
                        'extraction_class': ext.extraction_class,
                        'extraction_text': ext.extraction_text,
                        'attributes': getattr(ext, 'attributes', {}),
                        'start_char': getattr(ext, 'start_char', None),
                        'end_char': getattr(ext, 'end_char', None)
                    }
                    for ext in result.extractions
                ]
            else:
                extractions = []
            
            # 构建返回数据
            result_data = {
                'text_length': len(str(task.text_or_documents)),
                'extraction_count': len(extractions),
                'extraction_types': list(set(ext['extraction_class'] for ext in extractions))
            }
            
            stats = {
                'model_used': task.model_id,
                'text_length': len(str(task.text_or_documents)),
                'extraction_count': len(extractions),
                'processing_time': datetime.now().isoformat()
            }
            
            logger.info(f"信息提取完成: {len(extractions)}个实体提取成功")
            
            return ExtractionResult(
                task_id=task.task_id,
                success=True,
                data=result_data,
                extractions=extractions,
                stats=stats
            )
            
        except Exception as e:
            logger.error(f"信息提取执行失败: {e}")
            return ExtractionResult(
                task_id=task.task_id,
                success=False,
                error=str(e)
            )

    def _simulate_extraction(self, task: ExtractionTask) -> ExtractionResult:
        """模拟信息提取（当LangExtract不可用时）"""
        logger.info(f"使用模拟模式执行提取任务: {task.task_id}")
        
        # 模拟一些提取结果
        simulated_extractions = [
            {
                'extraction_class': 'simulated_entity',
                'extraction_text': '模拟提取的实体',
                'attributes': {'source': 'simulation', 'confidence': 0.95}
            }
        ]
        
        result_data = {
            'text_length': len(str(task.text_or_documents)),
            'extraction_count': len(simulated_extractions),
            'extraction_types': ['simulated_entity'],
            'mode': 'simulation'
        }
        
        stats = {
            'model_used': 'simulation',
            'text_length': len(str(task.text_or_documents)),
            'extraction_count': len(simulated_extractions),
            'processing_time': datetime.now().isoformat()
        }
        
        return ExtractionResult(
            task_id=task.task_id,
            success=True,
            data=result_data,
            extractions=simulated_extractions,
            stats=stats
        )

    def _generate_task_id(self) -> str:
        """生成任务ID"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        hash_obj = hashlib.md5(timestamp.encode(), usedforsecurity=False))
        return f"langextract_{hash_obj.hexdigest()[:8]}_{timestamp}"

    async def visualize_results(self, extractions: List[Dict[str, Any]], output_path: str = None) -> str:
        """生成交互式可视化结果"""
        try:
            if not self.is_available:
                # 生成简单的HTML可视化
                html_content = self._generate_simple_visualization(extractions)
                if output_path:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                return html_content
            
            # 转换为LangExtract格式进行可视化
            # 这里需要根据实际LangExtract的可视化功能实现
            logger.info('生成可视化结果')
            return '<html><body><h1>LangExtract可视化</h1><p>功能开发中...</p></body></html>'
            
        except Exception as e:
            logger.error(f"可视化生成失败: {e}")
            return f"<html><body><h1>可视化生成失败</h1><p>{str(e)}</p></body></html>"

    def _generate_simple_visualization(self, extractions: List[Dict[str, Any]]) -> str:
        """生成简单的HTML可视化"""
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>LangExtract提取结果</title>
            <meta charset='utf-8'>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                .extraction { border: 1px solid #ddd; margin: 10px 0; padding: 10px; border-radius: 5px; }
                .extraction-class { color: #0066cc; font-weight: bold; }
                .extraction-text { background-color: #f0f0f0; padding: 5px; margin: 5px 0; }
                .attributes { margin-top: 10px; }
                .attribute { background-color: #e8f4fd; padding: 2px 5px; margin: 2px; border-radius: 3px; }
            </style>
        </head>
        <body>
            <h1>LangExtract信息提取结果</h1>
            <p>共提取了 """ + str(len(extractions)) + """ 个实体</p>
        """
        
        for i, ext in enumerate(extractions):
            html += f"""
            <div class='extraction'>
                <div class='extraction-class'>{ext.get('extraction_class', 'Unknown')}</div>
                <div class='extraction-text'>"{ext.get('extraction_text', '')}"</div>
                <div class='attributes'>
            """
            
            attributes = ext.get('attributes', {})
            for key, value in attributes.items():
                html += f'<span class='attribute'>{key}: {value}</span> '
            
            html += """
                </div>
            </div>
            """
        
        html += """
        </body>
        </html>
        """
        
        return html


# 全局实例
_langextract_tool = None

def get_langextract_tool() -> LangExtractTool:
    """获取LangExtract工具实例"""
    global _langextract_tool
    if _langextract_tool is None:
        _langextract_tool = LangExtractTool()
    return _langextract_tool