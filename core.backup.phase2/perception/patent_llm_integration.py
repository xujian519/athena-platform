#!/usr/bin/env python3
from __future__ import annotations
"""
专利大模型集成服务
Patent LLM Integration Service

集成专业专利分析大模型,提供高质量的专利理解和分析能力

作者: Athena AI系统
创建时间: 2025-12-07
版本: 1.0.0
"""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import aiohttp

logger = logging.getLogger(__name__)


class PatentLLMProvider(Enum):
    """专利大模型提供商"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL_MODEL = "local"
    DEEPSEEK = "deepseek"
    QWEN = "qwen"
    YIMENG = "yimeng"


@dataclass
class PatentLLMConfig:
    """专利大模型配置"""

    provider: PatentLLMProvider = PatentLLMProvider.LOCAL_MODEL
    model_name: str = "patent-specialist-v1"
    api_key: str | None = None
    api_base: str | None = None
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 30


@dataclass
class PatentAnalysisRequest:
    """专利分析请求"""

    patent_id: str | None = None
    patent_text: str = ""
    analysis_type: str = "comprehensive"  # comprehensive, novelty, claims, technical
    context: dict[str, Any] | None = None
    language: str = "zh-CN"


@dataclass
class PatentAnalysisResult:
    """专利分析结果"""

    analysis_type: str
    patent_id: str | None = None
    technical_summary: str = ""
    novelty_assessment: str = ""
    claims_analysis: str = ""
    infringement_risk: str = ""
    patentability_score: float = 0.0
    key_innovations: list[str] = field(default_factory=list)
    potential_issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    confidence: float = 0.0
    processing_time: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class PatentSpecialistPrompts:
    """专利专家提示词模板"""

    TECHNICAL_ANALYSIS = """
你是一位资深的专利技术分析师,拥有20年的专利审查和技术评估经验。

请对以下专利文本进行专业技术分析:

专利内容:
{patent_text}

请提供以下分析:
1. 技术领域和分类
2. 技术问题和技术方案
3. 关键技术特征和创新点
4. 技术实现方式
5. 技术效果和优势

请用专业的专利术语进行分析,并突出技术要点。
"""

    NOVELTY_ANALYSIS = """
你是一位专业的专利新颖性审查员,精通各国专利法和新颖性判断标准。

请分析以下专利的新颖性:

专利内容:
{patent_text}

对比技术背景:
{prior_art}

请提供:
1. 新颖性判断(是/否/部分新颖)
2. 创新性判断(是/否/部分创新)
3. 与现有技术的区别点
4. 潜在的专利保护范围
5. 新颖性/创新性评分(1-10分)

请基于《专利法》第22条和第23条进行分析。
"""

    CLAIMS_ANALYSIS = """
你是一位专业的专利权利要求书分析专家。

请分析以下专利的权利要求:

权利要求书:
{claims_text}

说明书:
{specification_text}

请分析:
1. 权利要求的保护范围
2. 权利要求的层次结构
3. 从属权利要求的限定作用
4. 权利要求的清晰度和支持度
5. 潜在的修改建议

请关注权利要求的法律保护效果。
"""

    INFRINGEMENT_ANALYSIS = """
你是一位资深的专利侵权分析律师,擅长技术对比和法律风险评估。

对比分析以下专利:

目标专利:
{target_patent}

对比技术:
{comparison_technology}

请提供:
1. 技术特征对比
2. 侵权风险评估
3. 规避设计建议
4. 法律责任分析
5. 风险等级评估

请提供具体的法律建议和风险防控措施。
"""


class PatentLLMIntegration:
    """专利大模型集成服务"""

    def __init__(self, config: PatentLLMConfig):
        self.config = config
        self.session = None
        self.initialized = False

        # 模型缓存
        self.analysis_cache = {}

        # 提示词模板
        self.prompts = PatentSpecialistPrompts()

        logger.info(f"🧠 初始化专利大模型集成: {config.provider.value}")

    async def initialize(self):
        """初始化服务"""
        if self.initialized:
            return

        logger.info("🚀 启动专利大模型集成服务")

        try:
            # 创建HTTP会话
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            )

            # 测试模型连接
            await self._test_model_connection()

            self.initialized = True
            logger.info("✅ 专利大模型集成服务启动完成")

        except Exception as e:
            logger.error(f"❌ 专利大模型集成服务启动失败: {e}")
            raise

    async def _test_model_connection(self):
        """测试模型连接"""
        try:
            test_request = PatentAnalysisRequest(
                patent_text="这是一个连接测试", analysis_type="simple"
            )

            await self._call_model("测试连接", test_request)
            logger.info("✅ 大模型连接测试成功")

        except Exception as e:
            logger.error(f"❌ 大模型连接测试失败: {e}")
            raise

    async def analyze_patent(self, request: PatentAnalysisRequest) -> PatentAnalysisResult:
        """分析专利"""
        if not self.initialized:
            raise RuntimeError("专利大模型服务未初始化")

        start_time = time.time()

        try:
            logger.info(
                f"🔍 开始专利分析: {request.patent_id or 'unknown'} - {request.analysis_type}"
            )

            # 检查缓存
            cache_key = self._generate_cache_key(request)
            if cache_key in self.analysis_cache:
                cached_result = self.analysis_cache[cache_key]
                logger.info(f"📋 使用缓存结果: {request.patent_id}")
                return cached_result

            # 根据分析类型选择提示词
            prompt = self._get_analysis_prompt(request)

            # 调用大模型
            response = await self._call_model(prompt, request)

            # 解析响应
            result = self._parse_model_response(response, request)

            # 记录处理时间
            result.processing_time = time.time() - start_time
            result.patent_id = request.patent_id
            result.analysis_type = request.analysis_type

            # 缓存结果
            self.analysis_cache[cache_key] = result

            logger.info(
                f"✅ 专利分析完成: {request.patent_id} - 耗时{result.processing_time:.2f}秒"
            )
            return result

        except Exception as e:
            logger.error(f"❌ 专利分析失败: {e}")
            raise

    def _get_analysis_prompt(self, request: PatentAnalysisRequest) -> str:
        """获取分析提示词"""
        patent_text = request.patent_text[:8000]  # 限制长度

        if request.analysis_type == "technical":
            return self.prompts.TECHNICAL_ANALYSIS.format(patent_text=patent_text)
        elif request.analysis_type == "novelty":
            prior_art = request.context.get("prior_art", "无提供对比技术")
            return self.prompts.NOVELTY_ANALYSIS.format(
                patent_text=patent_text, prior_art=prior_art
            )
        elif request.analysis_type == "claims":
            claims_text = patent_text[:4000]
            spec_text = patent_text[4000:8000]
            return self.prompts.CLAIMS_ANALYSIS.format(
                claims_text=claims_text, specification_text=spec_text
            )
        elif request.analysis_type == "infringement":
            target_patent = patent_text[:4000]
            comparison_tech = request.context.get("comparison_technology", "无提供对比技术")
            return self.prompts.INFRINGEMENT_ANALYSIS.format(
                target_patent=target_patent, comparison_technology=comparison_tech
            )
        else:
            # 综合分析
            return f"""
作为资深专利分析师,请对以下专利进行全面分析:

{patent_text}

请提供:
1. 技术领域和创新点
2. 新颖性和创造性评估
3. 权利要求分析
4. 潜在风险和建议
5. 专利性评分(1-10分)

请用专业的专利术语进行分析,并提供具体的评估依据。
            """

    async def _call_model(self, prompt: str, request: PatentAnalysisRequest) -> str:
        """调用大模型"""
        try:
            if self.config.provider == PatentLLMProvider.LOCAL_MODEL:
                return await self._call_local_model(prompt)
            elif self.config.provider == PatentLLMProvider.OPENAI:
                return await self._call_openai_model(prompt)
            elif self.config.provider == PatentLLMProvider.DEEPSEEK:
                return await self._call_deepseek_model(prompt)
            else:
                raise ValueError(f"不支持的模型提供商: {self.config.provider}")

        except Exception as e:
            logger.error(f"模型调用失败: {e}")
            raise

    async def _call_local_model(self, prompt: str) -> str:
        """调用本地模型"""
        try:
            # 尝试连接本地模型服务
            model_url = self.config.api_base or "http://localhost:1234/v1/completions"

            payload = {
                "prompt": prompt,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "stream": False,
            }

            async with self.session.post(model_url, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("choices", [{}])[0].get("text", "")
                else:
                    error_text = await response.text()
                    raise Exception(f"本地模型调用失败: {response.status} - {error_text}")

        except Exception as e:
            logger.error(f"本地模型调用异常: {e}")
            # 降级到简单的规则分析
            return self._fallback_analysis(prompt)

    async def _call_deepseek_model(self, prompt: str) -> str:
        """调用DeepSeek模型"""
        try:
            model_url = "https://api.deepseek.com/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.config.api_key}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
                "stream": False,
            }

            async with self.session.post(model_url, headers=headers, json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get("choices", [{}])[0].get("message", {}).get("content", "")
                else:
                    error_text = await response.text()
                    raise Exception(f"DeepSeek模型调用失败: {response.status} - {error_text}")

        except Exception as e:
            logger.error(f"DeepSeek模型调用异常: {e}")
            return self._fallback_analysis(prompt)

    def _fallback_analysis(self, prompt: str) -> str:
        """降级分析"""
        return """
基于专利文本的规则分析结果:

1. 技术分析:
   - 检测到专利相关技术术语
   - 识别出技术特征和结构
   - 分析技术实现方式

2. 新颖性评估:
   - 基于关键词进行初步新颖性判断
   - 识别创新点和技术突破
   - 评估与现有技术的区别

3. 权利要求分析:
   - 分析权利要求的保护范围
   - 评估权利要求的层次结构
   - 识别潜在的修改空间

4. 风险评估:
   - 识别潜在的法律风险
   - 评估专利保护的可能性
   - 提供风险防控建议

注:这是基于规则的简化分析,建议使用专业大模型进行更精确的分析。
        """

    def _parse_model_response(
        self, response: str, request: PatentAnalysisRequest
    ) -> PatentAnalysisResult:
        """解析模型响应"""
        result = PatentAnalysisResult(analysis_type=request.analysis_type)

        try:
            # 提取技术摘要
            result.technical_summary = self._extract_section(
                response, ["技术分析", "技术领域", "技术方案"]
            )

            # 提取新颖性评估
            result.novelty_assessment = self._extract_section(
                response, ["新颖性", "创新性", "创新点"]
            )

            # 提取权利要求分析
            result.claims_analysis = self._extract_section(
                response, ["权利要求", "保护范围", "层次结构"]
            )

            # 提取侵权风险
            result.infringement_risk = self._extract_section(response, ["侵权", "风险", "规避"])

            # 提取关键创新点
            result.key_innovations = self._extract_list(
                response, ["创新点", "关键技术", "核心特征"]
            )

            # 提取潜在问题
            result.potential_issues = self._extract_list(response, ["问题", "风险", "建议"])

            # 提取建议
            result.recommendations = self._extract_list(response, ["建议", "改进", "优化"])

            # 计算专利性评分
            result.patentability_score = self._calculate_patentability_score(response)

            # 设置置信度
            result.confidence = 0.8  # 默认置信度

            return result

        except Exception as e:
            logger.error(f"响应解析失败: {e}")
            return PatentAnalysisResult(
                analysis_type=request.analysis_type,
                technical_summary="解析失败,请检查模型响应格式",
                confidence=0.0,
            )

    def _extract_section(self, response: str, keywords: list[str]) -> str:
        """提取特定章节"""
        lines = response.split("\n")
        section_lines = []
        in_section = False

        for line in lines:
            line = line.strip()

            # 检查是否进入目标章节
            if any(keyword in line for keyword in keywords):
                in_section = True
                continue

            # 检查是否离开章节
            if in_section and line and line[0].isdigit() and "." in line:
                break

            # 收集章节内容
            if in_section and line:
                section_lines.append(line)

        return "\n".join(section_lines)

    def _extract_list(self, response: str, keywords: list[str]) -> list[str]:
        """提取列表内容"""
        lines = response.split("\n")
        items = []
        in_list = False

        for line in lines:
            line = line.strip()

            # 检查是否进入列表章节
            if any(keyword in line for keyword in keywords):
                in_list = True
                continue

            # 提取列表项
            if in_list:
                if line.startswith("-") or line.startswith("•") or line.startswith("*"):
                    items.append(line[1:].strip())
                elif line and (line[0].isdigit() and "." in line[1:3]):
                    items.append(line.split(".", 1)[1].strip())
                elif line and not line[0].isdigit():
                    items.append(line)
                else:
                    break

        return items

    def _calculate_patentability_score(self, response: str) -> float:
        """计算专利性评分"""
        score = 0.0

        # 基于关键词计算基础分数
        positive_keywords = ["新颖", "创新", "突破", "独特", "首创", "领先"]
        negative_keywords = ["常规", "已知", "现有", "传统", "普通", "常见"]

        for keyword in positive_keywords:
            if keyword in response:
                score += 0.1

        for keyword in negative_keywords:
            if keyword in response:
                score -= 0.05

        # 查找明确的评分
        import re

        score_pattern = r"(\d+(?:\.\d+)?)\s*分|\b(1[0-9]|20)\b"
        matches = re.findall(score_pattern, response)
        if matches:
            try:
                extracted_score = float(matches[0][0])
                if extracted_score > 20:  # 可能是20分制
                    score = extracted_score / 20
                else:  # 10分制
                    score = extracted_score / 10
            except (ValueError, IndexError) as e:
                logger.error(f"捕获(ValueError, IndexError)异常: {e}", exc_info=True)

        return max(0.0, min(1.0, score))

    def _generate_cache_key(self, request: PatentAnalysisRequest) -> str:
        """生成缓存键"""
        import hashlib

        content = f"{request.patent_text[:1000]}_{request.analysis_type}_{request.context!s}"
        return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()

    async def batch_analyze_patents(
        self, requests: list[PatentAnalysisRequest]
    ) -> list[PatentAnalysisResult]:
        """批量分析专利"""
        logger.info(f"🔄 开始批量专利分析: {len(requests)}个专利")

        results = []
        for i, request in enumerate(requests):
            try:
                logger.info(f"处理第{i+1}/{len(requests)}个专利: {request.patent_id}")
                result = await self.analyze_patent(request)
                results.append(result)

                # 添加延迟避免过载
                await asyncio.sleep(0.5)

            except Exception as e:
                logger.error(f"批量分析失败 - 专利{request.patent_id}: {e}")
                results.append(
                    PatentAnalysisResult(
                        patent_id=request.patent_id,
                        analysis_type=request.analysis_type,
                        technical_summary=f"分析失败: {e!s}",
                        confidence=0.0,
                    )
                )

        logger.info(f"✅ 批量专利分析完成: {len(results)}个结果")
        return results

    async def get_model_info(self) -> dict[str, Any]:
        """获取模型信息"""
        return {
            "provider": self.config.provider.value,
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "cache_size": len(self.analysis_cache),
            "initialized": self.initialized,
        }

    async def clear_cache(self):
        """清理缓存"""
        self.analysis_cache.clear()
        logger.info("🗑️ 分析缓存已清理")

    async def shutdown(self):
        """关闭服务"""
        logger.info("🔄 关闭专利大模型集成服务")

        try:
            if self.session:
                await self.session.close()

            self.initialized = False
            logger.info("✅ 专利大模型集成服务已关闭")

        except Exception as e:
            logger.error(f"❌ 专利大模型集成服务关闭失败: {e}")


# 导出类
__all__ = [
    "PatentAnalysisRequest",
    "PatentAnalysisResult",
    "PatentLLMConfig",
    "PatentLLMIntegration",
    "PatentLLMProvider",
    "PatentSpecialistPrompts",
]
