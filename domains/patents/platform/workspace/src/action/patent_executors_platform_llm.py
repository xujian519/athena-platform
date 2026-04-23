#!/usr/bin/env python3
"""
专利执行器 - 平台LLM层集成版本
Patent Executors with Platform LLM Layer Integration

使用Athena平台统一LLM层的专利执行器

Created by Athena AI系统
Date: 2025-12-14
Version: 2.1.0
"""

import asyncio
import hashlib
import json
import logging
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any

# 添加项目路径
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "core" / "llm"))

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 导入平台LLM层
try:
    from core.ai.llm.base import LLMRequest, LLMResponse
    from core.ai.llm.model_registry import get_model_registry
    from core.ai.llm.unified_llm_manager import UnifiedLLMManager, get_unified_llm_manager
    PLATFORM_LLM_AVAILABLE = True
    logger.info("✅ 平台LLM层可用")
except ImportError as e:
    logger.warning(f"⚠️ 平台LLM层不可用: {e}")
    PLATFORM_LLM_AVAILABLE = False


# =============================================================================
# 数据模型定义 (与增强版保持一致)
# =============================================================================

class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    PARTIAL = 'partial'
    CANCELLED = 'cancelled'


class TaskPriority(Enum):
    """任务优先级"""
    LOW = 1
    NORMAL = 5
    HIGH = 8
    URGENT = 10


class AnalysisType(Enum):
    """分析类型"""
    NOVELTY = 'novelty'
    INVENTIVENESS = 'inventiveness'
    INDUSTRIAL_APPLICABILITY = 'industrial_applicability'
    COMPREHENSIVE = 'comprehensive'
    TECHNICAL_ANALYSIS = 'technical_analysis'
    LEGAL_ANALYSIS = 'legal_analysis'


class FilingType(Enum):
    """申请类型"""
    INVENTION_PATENT = 'invention_patent'
    UTILITY_MODEL = 'utility_model'
    DESIGN_PATENT = 'design_patent'


class MonitoringType(Enum):
    """监控类型"""
    LEGAL_STATUS = 'legal_status'
    INFRINGEMENT = 'infringement'
    COMPETITOR = 'competitor'
    TECHNOLOGY_TREND = 'technology_trend'


@dataclass
class PatentTask:
    """专利任务数据类"""
    id: str
    task_type: str
    parameters: dict[str, Any]
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    retry_count: int = 0
    max_retries: int = 3
    timeout_seconds: int = 3600
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'parameters': self.parameters,
            'priority': self.priority.value,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'retry_count': self.retry_count,
            'max_retries': self.max_retries,
            'timeout_seconds': self.timeout_seconds,
            'metadata': self.metadata
        }


@dataclass
class ExecutionResult:
    """执行结果数据类"""
    status: str = 'success'
    data: dict[str, Any] | None = None
    error: str | None = None
    execution_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    task_id: str | None = None
    confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """转换为字典"""
        return {
            'status': self.status,
            'data': self.data,
            'error': self.error,
            'execution_time': self.execution_time,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'task_id': self.task_id,
            'confidence': self.confidence,
            'warnings': self.warnings
        }

    def is_success(self) -> bool:
        """是否执行成功"""
        return self.status == 'success'

    def is_failed(self) -> bool:
        """是否执行失败"""
        return self.status == 'failed'


# =============================================================================
# 平台LLM层集成
# =============================================================================

class PlatformLLMService:
    """
    平台LLM服务客户端
    集成Athena平台的统一LLM层
    """

    def __init__(self):
        self.llm_manager: UnifiedLLMManager | None = None
        self.model_registry = None
        self._initialized = False
        self._init_llm_manager()

    def _init_llm_manager(self):
        """初始化LLM管理器"""
        if not PLATFORM_LLM_AVAILABLE:
            logger.warning("平台LLM层不可用，将使用规则引擎")
            return

        try:
            # 获取LLM管理器实例
            self.llm_manager = get_unified_llm_manager()
            self.model_registry = get_model_registry()
            self._initialized = True
            logger.info("✅ 平台LLM管理器初始化成功")
        except Exception as e:
            logger.error(f"❌ 平台LLM管理器初始化失败: {e}", exc_info=True)
            self._initialized = False

    async def ensure_initialized(self):
        """确保LLM管理器已初始化"""
        if not self._initialized or not self.llm_manager:
            logger.warning("LLM管理器未初始化，尝试初始化...")
            self._init_llm_manager()

        if self.llm_manager and not self.llm_manager.adapters:
            try:
                await self.llm_manager.initialize(enable_cache_warmup=False)
                logger.info("✅ LLM管理器初始化完成")
            except Exception as e:
                logger.error(f"❌ LLM管理器初始化失败: {e}")

    async def analyze_patent(self,
                            patent_data: dict[str, Any],
                            analysis_type: str = 'comprehensive') -> dict[str, Any]:
        """
        使用平台LLM分析专利

        Args:
            patent_data: 专利数据
            analysis_type: 分析类型

        Returns:
            分析结果字典
        """
        await self.ensure_initialized()

        if not self._initialized or not self.llm_manager:
            logger.warning("LLM不可用，使用规则引擎分析")
            return await self._rule_based_analysis(patent_data, analysis_type)

        try:
            # 构建分析提示
            prompt = self._build_analysis_prompt(patent_data, analysis_type)
            system_prompt = self._build_system_prompt(analysis_type)

            # 选择最佳模型
            model_id = self._select_model_for_task(analysis_type)

            # 创建LLM请求
            request = LLMRequest(
                message=prompt,
                context={
                    'system_prompt': system_prompt,
                    'task_type': 'patent_analysis',
                    'analysis_type': analysis_type
                },
                temperature=0.7,
                max_tokens=2000
            )

            # 调用LLM
            start_time = time.time()
            response: LLMResponse = await self.llm_manager.generate(
                model_id=model_id,
                request=request
            )
            latency = time.time() - start_time

            # 解析响应
            return self._parse_llm_response(response, latency, model_id)

        except Exception as e:
            logger.error(f"LLM分析失败: {e}", exc_info=True)
            logger.info("降级到规则引擎分析")
            return await self._rule_based_analysis(patent_data, analysis_type)

    def _build_analysis_prompt(self,
                               patent_data: dict[str, Any],
                               analysis_type: str) -> str:
        """构建分析提示词"""
        title = patent_data.get('title', '未知标题')
        abstract = patent_data.get('abstract', '')
        claims = patent_data.get('claims', '')
        description = patent_data.get('description', '')

        prompt = f"""请对以下专利进行{analysis_type}分析：

【专利标题】
{title}

【摘要】
{abstract}

【权利要求】
{claims[:1500]}

【技术描述】
{description[:2000]}

请提供结构化的分析结果，包括：
1. 评分（0-100分）
2. 关键发现
3. 优势点
4. 风险点
5. 改进建议

请以JSON格式返回分析结果。
"""

        return prompt

    def _build_system_prompt(self, analysis_type: str) -> str:
        """构建系统提示词"""
        system_prompts = {
            'novelty': """你是一位专业的专利新颖性分析专家。
你需要评估专利技术方案的创新性和与现有技术的区别。
重点关注技术特征的新颖性和技术创新点。""",

            'inventiveness': """你是一位专业的专利创造性分析专家。
你需要评估专利技术方案的创造性和技术进步程度。
重点关注技术方案的显而易见性和技术难度。""",

            'industrial_applicability': """你是一位专业的专利实用性分析专家。
你需要评估专利技术方案的工业应用价值。
重点关注技术实施可行性和产业化前景。""",

            'comprehensive': """你是一位资深的专利分析师。
你需要对专利进行全面的可专利性分析，包括新颖性、创造性和实用性。
提供综合评估和整体建议。""",

            'technical_analysis': """你是一位技术分析专家。
你需要分析专利的技术方案、技术特征和技术优势。
重点关注技术实现方法和技术效果。""",

            'legal_analysis': """你是一位专利法律专家。
你需要分析专利的法律合规性、权利要求保护范围和法律风险。
重点关注专利的有效性和侵权风险。"""
        }

        return system_prompts.get(analysis_type, system_prompts['comprehensive'])

    def _select_model_for_task(self, analysis_type: str) -> str:
        """为任务选择最佳模型"""
        # 分析类型与模型的映射
        model_preferences = {
            'novelty': ['glm-4-plus', 'deepseek-chat'],
            'inventiveness': ['glm-4-plus', 'deepseek-reasoner'],
            'comprehensive': ['glm-4-plus', 'deepseek-reasoner'],
            'technical_analysis': ['glm-4-flash', 'glm-4-plus'],
            'legal_analysis': ['glm-4-plus', 'deepseek-chat'],
            'industrial_applicability': ['glm-4-flash', 'glm-4-plus']
        }

        preferred_models = model_preferences.get(analysis_type, ['glm-4-plus'])

        # 检查可用模型
        if self.llm_manager and self.llm_manager.adapters:
            for model_id in preferred_models:
                if model_id in self.llm_manager.adapters:
                    logger.info(f"选择模型: {model_id} (分析类型: {analysis_type})")
                    return model_id

        # 返回默认模型
        logger.warning("首选模型不可用，使用默认模型: glm-4-flash")
        return 'glm-4-flash'

    def _parse_llm_response(self,
                           response: LLMResponse,
                           latency: float,
                           model_id: str) -> dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试解析JSON响应
            content = response.content.strip()

            # 提取JSON（如果响应包含markdown代码块）
            if '```json' in content:
                json_start = content.find('```json') + 7
                json_end = content.find('```', json_start)
                json_str = content[json_start:json_end].strip()
            elif '```' in content:
                json_start = content.find('```') + 3
                json_end = content.find('```', json_start)
                json_str = content[json_start:json_end].strip()
            else:
                json_str = content

            # 尝试解析JSON
            try:
                analysis_data = json.loads(json_str)
                return {
                    'status': 'success',
                    'analysis_result': analysis_data,
                    'provider': 'platform_llm',
                    'model': model_id,
                    'latency': latency,
                    'tokens_used': response.tokens_used,
                    'confidence': 0.85,
                    'method': 'llm_analysis'
                }
            except json.JSONDecodeError:
                # JSON解析失败，返回原始文本
                logger.warning("JSON解析失败，返回原始文本")
                return {
                    'status': 'success',
                    'analysis_result': {
                        'content': content,
                        'summary': content[:500]
                    },
                    'provider': 'platform_llm',
                    'model': model_id,
                    'latency': latency,
                    'tokens_used': response.tokens_used,
                    'confidence': 0.75,
                    'method': 'llm_analysis'
                }

        except Exception as e:
            logger.error(f"解析LLM响应失败: {e}")
            return {
                'status': 'partial',
                'analysis_result': {
                    'content': response.content,
                    'error': '响应解析失败'
                },
                'provider': 'platform_llm',
                'model': model_id,
                'latency': latency,
                'confidence': 0.5,
                'method': 'llm_analysis'
            }

    async def _rule_based_analysis(self,
                                   patent_data: dict[str, Any],
                                   analysis_type: str) -> dict[str, Any]:
        """基于规则的分析（降级方案）"""
        logger.info(f"使用规则引擎进行{analysis_type}分析")

        # 简单的规则评分
        title = patent_data.get('title', '')
        abstract = patent_data.get('abstract', '')
        claims = patent_data.get('claims', '')

        scores = {
            'title_length': min(len(title) / 100, 1.0),
            'abstract_length': min(len(abstract) / 500, 1.0),
            'claims_count': min(len(claims.split('。')) / 10, 1.0),
            'technical_terms': self._count_technical_terms(title + ' ' + abstract) / 50
        }

        overall_score = sum(scores.values()) / len(scores) * 100

        return {
            'status': 'success',
            'analysis_result': {
                'score': round(overall_score, 2),
                'method': 'rule_based',
                'detailed_scores': {k: round(v * 100, 2) for k, v in scores.items()},
                'assessment': f'基于规则的分析结果，综合得分: {round(overall_score, 2)}分'
            },
            'provider': 'rule_engine',
            'model': 'rule_based',
            'confidence': 0.65,
            'method': 'rule_analysis'
        }

    def _count_technical_terms(self, text: str) -> int:
        """统计技术术语数量"""
        technical_terms = [
            '系统', '方法', '装置', '设备', '模块', '组件',
            '算法', '技术', '特征', '步骤', '实现', '应用',
            '包括', '包含', '具有', '设置', '配置', '连接'
        ]
        count = 0
        for term in technical_terms:
            count += text.count(term)
        return count

    async def generate_document(self,
                               doc_type: str,
                               patent_data: dict[str, Any]) -> str:
        """
        生成专利文档

        Args:
            doc_type: 文档类型 (specification, claims, abstract等)
            patent_data: 专利数据

        Returns:
            生成的文档内容
        """
        await self.ensure_initialized()

        if not self._initialized or not self.llm_manager:
            return self._generate_template_document(doc_type, patent_data)

        try:
            prompt = self._build_document_prompt(doc_type, patent_data)
            system_prompt = self._build_document_system_prompt(doc_type)

            request = LLMRequest(
                message=prompt,
                context={'system_prompt': system_prompt},
                temperature=0.6,
                max_tokens=3000
            )

            response = await self.llm_manager.generate(
                model_id='glm-4-flash',  # 使用快速模型
                request=request
            )

            return response.content

        except Exception as e:
            logger.error(f"文档生成失败: {e}")
            return self._generate_template_document(doc_type, patent_data)

    def _build_document_prompt(self, doc_type: str, patent_data: dict[str, Any]) -> str:
        """构建文档生成提示"""
        title = patent_data.get('title', '')
        abstract = patent_data.get('abstract', '')
        description = patent_data.get('description', '')

        if doc_type == 'specification':
            return f"""请根据以下信息生成完整的专利说明书：

【发明名称】
{title}

【摘要】
{abstract}

【技术描述】
{description}

请生成包含以下部分的完整说明书：
1. 技术领域
2. 背景技术
3. 发明内容
4. 具体实施方式
5. 有益效果
"""

        elif doc_type == 'claims':
            return f"""请根据以下信息生成权利要求书：

【发明名称】
{title}

【技术方案】
{description}

请生成：
1. 一个独立权利要求
2. 3-5个从属权利要求
"""

        elif doc_type == 'abstract':
            return f"""请根据以下信息生成专利摘要（不超过400字）：

【发明名称】
{title}

【技术方案】
{description}

请生成简洁、准确的专利摘要。
"""

        return f"请生成{doc_type}文档"

    def _build_document_system_prompt(self, doc_type: str) -> str:
        """构建文档生成系统提示"""
        return f"""你是一位专业的专利文档撰写专家。
你需要生成符合专利法规范的{doc_type}文档。
文档应当准确、清晰、完整。"""

    def _generate_template_document(self, doc_type: str, patent_data: dict[str, Any]) -> str:
        """生成模板文档（降级方案）"""
        title = patent_data.get('title', '技术发明')

        templates = {
            'specification': f"""
【技术领域】
本发明涉及技术领域，具体涉及{title}相关技术。

【背景技术】
现有技术存在以下问题...

【发明内容】
本发明的目的是提供{title}，以解决上述问题。

【具体实施方式】
下面结合附图和具体实施例对本发明进行详细说明。
""",

            'claims': f"""
1. 一种{title}，其特征在于，包括：
   步骤1：...
   步骤2：...

2. 根据权利要求1所述的{title}，其特征在于，所述步骤1还包括...
""",

            'abstract': f"""
本发明公开了{title}。该技术方案包括...，具有以下有益效果...
"""
        }

        return templates.get(doc_type, f"请补充{doc_type}内容")


# =============================================================================
# 性能监控装饰器
# =============================================================================

def measure_time(func):
    """测量执行时间的装饰器"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 执行时间: {execution_time:.2f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败 ({execution_time:.2f}秒): {e}")
            raise
    return wrapper


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """失败重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_retries - 1:
                        logger.warning(f"{func.__name__} 失败，第{attempt + 1}次重试...")
                        await asyncio.sleep(delay * (attempt + 1))
                    else:
                        logger.error(f"{func.__name__} 达到最大重试次数")
            raise last_error
        return wrapper
    return decorator


# =============================================================================
# 缓存服务（简化版）
# =============================================================================

class CacheService:
    """缓存服务（简化版）"""

    def __init__(self):
        self.cache: dict[str, tuple[Any, float] = {}
        self.enable_cache = True
        self.cache_ttl = 300

    def get(self, key: str) -> Any | None:
        """获取缓存"""
        if not self.enable_cache:
            return None

        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.cache_ttl:
                logger.debug(f"缓存命中: {key}")
                return value
            else:
                del self.cache[key]

        return None

    def set(self, key: str, value: Any):
        """设置缓存"""
        if not self.enable_cache:
            return

        self.cache[key] = (value, time.time())
        logger.debug(f"缓存设置: {key}")

    def delete(self, key: str):
        """删除缓存"""
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        """清空缓存"""
        self.cache.clear()

    def _generate_key(self, *args) -> str:
        """生成缓存键"""
        content = '|'.join(str(arg) for arg in args)
        return hashlib.md5(content.encode()).hexdigest()


# =============================================================================
# 数据库服务（简化版）
# =============================================================================

class DatabaseService:
    """数据库服务（简化版）"""

    def __init__(self):
        self.connected = False

    async def save_analysis_result(self, task_id: str, result: dict[str, Any]) -> bool:
        """保存分析结果（模拟）"""
        logger.info(f"模拟保存任务 {task_id} 的分析结果")
        return True

    async def get_patent_data(self, patent_id: str) -> dict[str, Any] | None:
        """获取专利数据（模拟）"""
        return None


# =============================================================================
# 专利分析执行器 - 使用平台LLM层
# =============================================================================

class PatentAnalysisExecutor:
    """专利分析执行器 - 使用平台LLM层"""

    def __init__(self):
        self.name = 'PatentAnalysisExecutor-PlatformLLM'
        self.description = '专利分析执行器（平台LLM层集成版）'
        self.logger = logging.getLogger(f"{__name__}.PatentAnalysisExecutor")

        # 初始化平台LLM服务
        self.llm_service = PlatformLLMService()

        # 缓存服务
        self.cache_service = CacheService()

    def validate_parameters(self, parameters: dict[str, Any]) -> tuple[bool, str | None]:
        """验证分析参数"""
        if 'patent_data' not in parameters:
            return False, "缺少必需参数: patent_data"

        patent_data = parameters['patent_data']
        if not isinstance(patent_data, dict):
            return False, "patent_data必须是字典类型"

        if not any(key in patent_data for key in ['title', 'abstract', 'description']):
            return False, "patent_data必须包含title、abstract或description中的至少一个"

        return True, None

    @measure_time
    @retry_on_failure(max_retries=2)
    async def execute(self, task: PatentTask) -> ExecutionResult:
        """执行专利分析"""
        start_time = datetime.now()
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        try:
            self.logger.info(f"开始执行专利分析任务: {task.id} (使用平台LLM层)")

            # 验证参数
            is_valid, error_msg = self.validate_parameters(task.parameters)
            if not is_valid:
                task.status = TaskStatus.FAILED
                return ExecutionResult(
                    status='failed',
                    error=f'参数验证失败: {error_msg}',
                    task_id=task.id
                )

            patent_data = task.parameters['patent_data']
            analysis_type = task.parameters.get('analysis_type', 'comprehensive')
            depth = task.parameters.get('depth', 'standard')

            # 调用平台LLM进行分析
            self.logger.info(f"使用平台LLM进行{analysis_type}分析...")
            ai_result = await self.llm_service.analyze_patent(
                patent_data=patent_data,
                analysis_type=analysis_type
            )

            # 生成分析报告
            report = await self._generate_analysis_report(
                ai_result,
                analysis_type,
                patent_data
            )

            # 生成建议
            recommendations = await self._generate_recommendations(
                ai_result,
                analysis_type
            )

            # 构建结果
            result_data = {
                'analysis_type': analysis_type,
                'analysis_result': ai_result,
                'report': report,
                'recommendations': recommendations,
                'depth': depth,
                'patent_id': patent_data.get('patent_id', 'unknown'),
                'llm_provider': ai_result.get('provider', 'unknown'),
                'model_used': ai_result.get('model', 'unknown')
            }

            execution_time = (datetime.now() - start_time).total_seconds()

            task.status = TaskStatus.SUCCESS
            task.completed_at = datetime.now()

            self.logger.info(f"专利分析完成，耗时: {execution_time:.2f}秒")

            return ExecutionResult(
                status='success',
                data=result_data,
                execution_time=execution_time,
                task_id=task.id,
                confidence=ai_result.get('confidence', 0.0),
                metadata={
                    'depth': depth,
                    'analysis_type': analysis_type,
                    'patent_id': patent_data.get('patent_id'),
                    'llm_provider': ai_result.get('provider'),
                    'model_used': ai_result.get('model'),
                    'tokens_used': ai_result.get('tokens_used', 0)
                }
            )

        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"专利分析执行失败: {str(e)}", exc_info=True)
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()

            return ExecutionResult(
                status='failed',
                error=str(e),
                execution_time=execution_time,
                task_id=task.id
            )

    async def _generate_analysis_report(self,
                                       ai_result: dict[str, Any],
                                       analysis_type: str,
                                       patent_data: dict[str, Any]) -> dict[str, Any]:
        """生成分析报告"""
        analysis_result = ai_result.get('analysis_result', {})

        report = {
            'title': f"专利{analysis_type}分析报告",
            'patent_id': patent_data.get('patent_id', 'unknown'),
            'patent_title': patent_data.get('title', 'unknown'),
            'analysis_date': datetime.now().isoformat(),
            'analysis_type': analysis_type,
            'llm_provider': ai_result.get('provider', 'unknown'),
            'model_used': ai_result.get('model', 'unknown'),
            'executive_summary': '',
            'detailed_findings': [],
            'conclusions': [],
            'confidence_level': ai_result.get('confidence', 0.0)
        }

        # 提取关键信息
        if isinstance(analysis_result, dict):
            if 'score' in analysis_result:
                score = analysis_result['score']
                report['executive_summary'] = f"综合评分: {score}分"

            if 'assessment' in analysis_result:
                report['executive_summary'] = analysis_result['assessment']

            # 提取详细发现
            for key, value in analysis_result.items():
                if key not in ['score', 'confidence', 'method']:
                    report['detailed_findings'].append({
                        'aspect': key,
                        'finding': str(value)[:500]  # 限制长度
                    })

        # 生成结论
        confidence = ai_result.get('confidence', 0.0)
        if confidence >= 0.8:
            report['conclusions'].append("分析结果可信度高，可作为决策参考")
        elif confidence >= 0.6:
            report['conclusions'].append("分析结果可信度中等，建议结合人工审查")
        else:
            report['conclusions'].append("分析结果可信度较低，强烈建议人工审查")

        return report

    async def _generate_recommendations(self,
                                       ai_result: dict[str, Any],
                                       analysis_type: str) -> list[str]:
        """生成建议"""
        recommendations = []

        confidence = ai_result.get('confidence', 0.0)
        if confidence < 0.7:
            recommendations.append("建议进行补充分析以提高可信度")

        # 基于分析类型的建议
        if analysis_type == 'novelty':
            recommendations.extend([
                "建议进行全面的现有技术检索",
                "关注同族专利和相关技术领域的专利文献"
            ])
        elif analysis_type == 'inventiveness':
            recommendations.extend([
                "建议突出技术方案的显著进步",
                "准备技术对比表格以说明创造性"
            ])
        elif analysis_type == 'comprehensive':
            recommendations.extend([
                "建议完善权利要求的层次结构",
                "考虑增加实施例以支持权利要求"
            ])

        return recommendations


# =============================================================================
# 执行器工厂 - 使用平台LLM层
# =============================================================================

class PatentExecutorFactory:
    """专利执行器工厂 - 使用平台LLM层"""

    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.PatentExecutorFactory")
        self.executors = {
            'patent_analysis': PatentAnalysisExecutor()
        }

        self.logger.info("执行器工厂初始化完成（使用平台LLM层）")

    def get_executor(self, executor_name: str):
        """获取执行器实例"""
        return self.executors.get(executor_name)

    async def execute_with_executor(self,
                                   executor_name: str,
                                   task: PatentTask) -> ExecutionResult:
        """使用指定执行器执行任务"""
        executor = self.get_executor(executor_name)
        if not executor:
            return ExecutionResult(
                status='failed',
                error=f"未找到执行器: {executor_name}",
                task_id=task.id
            )

        return await executor.execute(task)

    def list_executors(self) -> dict[str, dict[str, Any]:
        """列出所有可用执行器"""
        return {
            name: {
                'name': executor.name,
                'description': executor.description
            }
            for name, executor in self.executors.items()
        }


# =============================================================================
# 测试代码
# =============================================================================

async def test_platform_llm_integration():
    """测试平台LLM集成"""
    logger.info('='*60)
    logger.info('🧪 平台LLM层集成测试')
    logger.info('='*60)

    # 创建工厂
    factory = PatentExecutorFactory()

    # 列出执行器
    logger.info('\n📋 可用执行器:')
    for name, info in factory.list_executors().items():
        logger.info(f"  - {name}: {info['description']}")

    # 测试专利分析
    logger.info('\n' + '='*60)
    logger.info('🔬 测试专利分析（使用平台LLM层）')
    logger.info('='*60)

    task = PatentTask(
        id='test_platform_llm_001',
        task_type='patent_analysis',
        parameters={
            'patent_data': {
                'patent_id': 'CN202410001234.5',
                'title': '基于深度学习的智能图像识别系统及方法',
                'abstract': '本发明公开了一种基于深度学习的智能图像识别系统，包括图像预处理模块、特征提取模块、分类模块和输出模块。该系统具有高精度、实时性强的特点。',
                'claims': '1. 一种基于深度学习的智能图像识别系统，其特征在于，包括：图像预处理模块，用于对输入图像进行标准化处理；特征提取模块，使用卷积神经网络提取图像特征；分类模块，通过全连接层实现图像分类；输出模块，生成分类结果和置信度。',
                'description': '本发明涉及人工智能技术领域，具体涉及一种基于深度学习的图像识别方法...'
            },
            'analysis_type': 'novelty',
            'depth': 'standard'
        }
    )

    result = await factory.execute_with_executor('patent_analysis', task)

    logger.info('\n✅ 分析结果:')
    logger.info(f'  状态: {result.status}')
    logger.info(f'  执行时间: {result.execution_time:.2f}秒')
    logger.info(f'  置信度: {result.confidence:.2f}')

    if result.data:
        logger.info(f'  LLM提供商: {result.data.get("llm_provider")}')
        logger.info(f'  使用的模型: {result.data.get("model_used")}')
        logger.info(f'  Token使用: {result.data.get("tokens_used", 0)}')
        logger.info('\n📊 分析摘要:')
        logger.info(f'  {result.data.get("report", {}).get("executive_summary", "N/A")}')

    logger.info('\n' + '='*60)
    logger.info('🎉 测试完成!')
    logger.info('='*60)


if __name__ == '__main__':
    asyncio.run(test_platform_llm_integration())
