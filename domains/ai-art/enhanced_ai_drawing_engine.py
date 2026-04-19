#!/usr/bin/env python3
"""
增强版AI绘图引擎
Enhanced AI Drawing Engine

解决API超时和SVG格式问题，提供更稳定的绘图服务

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 2.0.0
"""

import logging
import re
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 智谱清言配置
ZHIPU_API_KEY = '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'
ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

@dataclass
class DrawingConfig:
    """绘图配置"""
    max_retries: int = 3
    timeout: int = 45  # 增加超时时间
    temperature: float = 0.3  # 降低随机性
    max_tokens: int = 3000  # 增加token限制
    retry_delay: float = 1.0  # 重试延迟

class EnhancedAIDrawingEngine:
    """增强版AI绘图引擎"""

    def __init__(self, config: DrawingConfig = None):
        self.config = config or DrawingConfig()
        self.stats = {
            'total_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'avg_response_time': 0.0
        }

        # SVG模板和验证
        self.svg_templates = self._load_svg_templates()

    def _load_svg_templates(self) -> dict[str, str]:
        """加载SVG模板"""
        return {
            'flowchart': self._get_flowchart_template(),
            'architecture': self._get_architecture_template(),
            'patent': self._get_patent_template(),
            'system': self._get_system_template()
        }

    def _get_flowchart_template(self) -> str:
        """流程图模板"""
        return """
<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600' view_box='0 0 800 600'>
  <defs>
    <marker id='arrow' marker_width='10' marker_height='7' ref_x='0' ref_y='3.5' orient='auto'>
      <polygon points='0 0, 10 3.5, 0 7' fill='#333' />
    </marker>
  </defs>
  <style>
    .box { fill: #e3f2fd; stroke: #1976d2; stroke-width: 2; rx: 5; }
    .decision { fill: #fff3e0; stroke: #f57c00; stroke-width: 2; }
    .text { font-family: Arial, sans-serif; font-size: 14px; fill: #333; }
    .title { font-size: 18px; font-weight: bold; fill: #1976d2; }
    .arrow { stroke: #333; stroke-width: 2; fill: none; marker-end: url(#arrow); }
  </style>

  <!-- 标题 -->
  <text x='400' y='40' text-anchor='middle' class='title'>{title}</text>

  <!-- 内容占位符 -->
  {content}

</svg>
        """.strip()

    def _get_architecture_template(self) -> str:
        """架构图模板"""
        return """
<svg xmlns='http://www.w3.org/2000/svg' width='900' height='600' view_box='0 0 900 600'>
  <defs>
    <marker id='arrow' marker_width='10' marker_height='7' ref_x='0' ref_y='3.5' orient='auto'>
      <polygon points='0 0, 10 3.5, 0 7' fill='#666' />
    </marker>
    <linear_gradient id='grad1' x1='0%' y1='0%' x2='100%' y2='100%'>
      <stop offset='0%' style='stop-color:#f0f0f0;stop-opacity:1' />
      <stop offset='100%' style='stop-color:#e0e0e0;stop-opacity:1' />
    </linear_gradient>
  </defs>
  <style>
    .component { fill: url(#grad1); stroke: #424242; stroke-width: 2; rx: 8; }
    .database { fill: #ffecb3; stroke: #f57f17; stroke-width: 2; }
    .service { fill: #e8f5e9; stroke: #388e3c; stroke-width: 2; rx: 8; }
    .text { font-family: Arial, sans-serif; font-size: 13px; fill: #333; }
    .title { font-size: 20px; font-weight: bold; fill: #424242; }
    .arrow { stroke: #666; stroke-width: 2; fill: none; marker-end: url(#arrow); }
  </style>

  <!-- 标题 -->
  <text x='450' y='35' text-anchor='middle' class='title'>{title}</text>

  <!-- 内容占位符 -->
  {content}

</svg>
        """.strip()

    def _get_patent_template(self) -> str:
        """专利技术图模板"""
        return """
<svg xmlns='http://www.w3.org/2000/svg' width='800' height='600' view_box='0 0 800 600'>
  <defs>
    <pattern id='grid' width='20' height='20' pattern_units='user_space_on_use'>
      <path d='M 20 0 L 0 0 0 20' fill='none' stroke='#f0f0f0' stroke-width='1'/>
    </pattern>
  </defs>
  <style>
    .component { fill: #f5f5f5; stroke: #333; stroke-width: 2; }
    .annotation { font-family: Arial, sans-serif; font-size: 12px; fill: #666; }
    .label { font-size: 14px; font-weight: bold; fill: #333; }
    .title { font-size: 18px; font-weight: bold; fill: #1976d2; }
    .dimension { font-size: 10px; fill: #999; }
  </style>

  <!-- 网格背景 -->
  <rect width='800' height='600' fill='url(#grid)' />

  <!-- 标题 -->
  <text x='400' y='40' text-anchor='middle' class='title'>{title}</text>

  <!-- 内容占位符 -->
  {content}

</svg>
        """.strip()

    def _get_system_template(self) -> str:
        """系统图模板"""
        return """
<svg xmlns='http://www.w3.org/2000/svg' width='900' height='600' view_box='0 0 900 600'>
  <defs>
    <marker id='arrow' marker_width='10' marker_height='7' ref_x='0' ref_y='3.5' orient='auto'>
      <polygon points='0 0, 10 3.5, 0 7' fill='#555' />
    </marker>
  </defs>
  <style>
    .system { fill: #e1f5fe; stroke: #0277bd; stroke-width: 2; rx: 10; }
    .module { fill: #f3e5f5; stroke: #7b1fa2; stroke-width: 2; rx: 5; }
    .interface { fill: #e8f5e9; stroke: #2e7d32; stroke-width: 2; }
    .text { font-family: Arial, sans-serif; font-size: 13px; fill: #333; }
    .title { font-size: 20px; font-weight: bold; fill: #0277bd; }
    .arrow { stroke: #555; stroke-width: 2; fill: none; marker-end: url(#arrow); }
  </style>

  <!-- 标题 -->
  <text x='450' y='35' text-anchor='middle' class='title'>{title}</text>

  <!-- 内容占位符 -->
  {content}

</svg>
        """.strip()

    def _determine_diagram_type(self, description: str) -> str:
        """确定图纸类型"""
        desc_lower = description.lower()

        if any(keyword in desc_lower for keyword in ['流程', 'flow', '步骤', 'step', '决策', 'decision']):
            return 'flowchart'
        elif any(keyword in desc_lower for keyword in ['架构', 'architecture', '微服务', 'microservice']):
            return 'architecture'
        elif any(keyword in desc_lower for keyword in ['专利', 'patent', '机械', 'mechanical', '结构']):
            return 'patent'
        else:
            return 'system'

    def _enhance_prompt(self, original_prompt: str, diagram_type: str) -> str:
        """增强提示词"""
        enhancement = f"""
请生成专业的{diagram_type}类型SVG技术图纸。

要求：
1. 使用标准的{diagram_type}符号和表示方法
2. 布局清晰、层次分明
3. 包含必要的标注和说明
4. 使用专业的配色方案
5. 确保图纸具有技术文档的专业性

原始描述：{original_prompt}

请直接返回完整的SVG代码，不需要任何解释。
        """.strip()

        return enhancement

    def _validate_svg(self, svg_content: str) -> bool:
        """验证SVG格式"""
        try:
            # 基本格式检查
            if not svg_content.startswith('<svg') or not svg_content.endswith('</svg>'):
                return False

            # 检查必要的属性
            required_attrs = ['xmlns', 'width', 'height']
            for attr in required_attrs:
                if attr not in svg_content:
                    logger.warning(f"SVG缺少必要属性: {attr}")
                    return False

            # 检查是否包含内容
            if len(svg_content.strip()) < 100:
                logger.warning('SVG内容过短')
                return False

            return True

        except Exception as e:
            logger.error(f"SVG验证失败: {e}")
            return False

    def _clean_svg_content(self, svg_content: str) -> str:
        """清理SVG内容"""
        # 移除代码块标记
        svg_content = re.sub(r'```svg\s*', '', svg_content)
        svg_content = re.sub(r'```\s*', '', svg_content)

        # 移除多余的空白行
        svg_content = re.sub(r'\n\s*\n\s*\n', '\n\n', svg_content)

        # 确保SVG标签正确闭合
        svg_content = svg_content.strip()

        return svg_content

    def _call_zhipu_api_with_retry(self, prompt: str) -> str | None:
        """带重试机制的API调用"""
        last_error = None

        for attempt in range(self.config.max_retries):
            try:
                start_time = time.time()

                headers = {
                    'Authorization': f"Bearer {ZHIPU_API_KEY}",
                    'Content-Type': 'application/json'
                }

                system_prompt = """
你是专业的技术绘图专家，生成完整、专业的SVG技术图纸。

输出要求：
1. 只返回SVG代码，不要任何解释
2. SVG必须完整可用，包含所有必要的标签和属性
3. 使用专业的绘图规范和标准
4. 确保生成的SVG可以直接在浏览器中显示

SVG格式要求：
- 必须以<svg>开始，</svg>结束
- 包含xmlns属性
- 设置合适的width和height
- 使用清晰的结构和样式
                """.strip()

                data = {
                    'model': 'glm-4',
                    'messages': [
                        {'role': 'system', 'content': system_prompt},
                        {'role': 'user', 'content': prompt}
                    ],
                    'max_tokens': self.config.max_tokens,
                    'temperature': self.config.temperature
                }

                response = requests.post(
                    ZHIPU_API_URL,
                    headers=headers,
                    json=data,
                    timeout=self.config.timeout
                )

                time.time() - start_time

                if response.status_code == 200:
                    result = response.json()
                    svg_content = result['choices'][0]['message']['content']

                    # 清理和验证SVG
                    svg_content = self._clean_svg_content(svg_content)

                    if self._validate_svg(svg_content):
                        self.stats['successful_calls'] += 1
                        self.stats['total_calls'] += 1
                        return svg_content
                    else:
                        logger.warning(f"SVG验证失败，尝试重试 (尝试 {attempt + 1})")

                else:
                    logger.error(f"API调用失败: {response.status_code} - {response.text}")
                    last_error = f"HTTP {response.status_code}"

            except requests.exceptions.Timeout:
                logger.warning(f"请求超时，尝试重试 (尝试 {attempt + 1})")
                last_error = 'Timeout'
            except Exception as e:
                logger.error(f"API调用异常: {e}")
                last_error = str(e)

            # 更新统计
            self.stats['total_calls'] += 1

            # 重试前等待
            if attempt < self.config.max_retries - 1:
                time.sleep(self.config.retry_delay * (attempt + 1))

        # 所有重试都失败
        self.stats['failed_calls'] += 1
        logger.error(f"API调用最终失败: {last_error}")
        return None

    def generate_drawing(self, description: str, filename: str = None) -> dict[str, Any]:
        """生成图纸"""
        logger.info(f"开始生成图纸: {description[:50]}...")

        # 确定图纸类型
        diagram_type = self._determine_diagram_type(description)

        # 增强提示词
        enhanced_prompt = self._enhance_prompt(description, diagram_type)

        # 调用API
        svg_content = self._call_zhipu_api_with_retry(enhanced_prompt)

        result = {
            'success': False,
            'svg_content': None,
            'file_path': None,
            'diagram_type': diagram_type,
            'error': None,
            'stats': self.stats.copy()
        }

        if svg_content:
            # 生成文件名
            if not filename:
                filename = f"enhanced_{diagram_type}_{int(time.time())}.svg"

            # 保存文件
            try:
                output_path = Path(f"/tmp/{filename}")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)

                result.update({
                    'success': True,
                    'svg_content': svg_content,
                    'file_path': str(output_path)
                })

                logger.info(f"图纸生成成功: {output_path}")

            except Exception as e:
                result['error'] = f"文件保存失败: {e}"
                logger.error(f"文件保存失败: {e}")
        else:
            # 尝试使用模板生成基础图纸
            logger.info('API失败，尝试使用模板生成基础图纸')
            svg_content = self._generate_with_template(description, diagram_type)

            if svg_content:
                if not filename:
                    filename = f"template_{diagram_type}_{int(time.time())}.svg"

                output_path = Path(f"/tmp/{filename}")
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(svg_content)

                result.update({
                    'success': True,
                    'svg_content': svg_content,
                    'file_path': str(output_path),
                    'fallback': True
                })

                logger.info(f"使用模板生成图纸成功: {output_path}")

        return result

    def _generate_with_template(self, description: str, diagram_type: str) -> str:
        """使用模板生成基础图纸"""
        try:
            template = self.svg_templates.get(diagram_type, self.svg_templates['system'])

            # 提取标题
            title = self._extract_title_from_description(description)

            # 生成基础内容
            content = self._generate_basic_content(description, diagram_type)

            svg_content = template.format(
                title=title,
                content=content
            )

            return svg_content

        except Exception as e:
            logger.error(f"模板生成失败: {e}")
            return None

    def _extract_title_from_description(self, description: str) -> str:
        """从描述中提取标题"""
        # 简单的标题提取逻辑
        sentences = description.split('。')
        if sentences:
            title = sentences[0][:20]  # 取第一句的前20个字符
            return title
        return '技术图纸'

    def _generate_basic_content(self, description: str, diagram_type: str) -> str:
        """生成基础内容"""
        # 根据描述生成基础的SVG元素
        if diagram_type == 'flowchart':
            return """
  <!-- 基础流程图元素 -->
  <rect x='100' y='100' width='150' height='60' class='box' />
  <text x='175' y='135' text-anchor='middle' class='text'>开始</text>

  <rect x='350' y='100' width='150' height='60' class='box' />
  <text x='425' y='135' text-anchor='middle' class='text'>处理</text>

  <rect x='600' y='100' width='150' height='60' class='box' />
  <text x='675' y='135' text-anchor='middle' class='text'>结束</text>

  <path d='M 250 130 L 350 130' class='arrow' />
  <path d='M 500 130 L 600 130' class='arrow' />
            """
        elif diagram_type == 'architecture':
            return """
  <!-- 基础架构图元素 -->
  <rect x='50' y='100' width='150' height='80' class='component' />
  <text x='125' y='145' text-anchor='middle' class='text'>前端</text>

  <rect x='300' y='100' width='150' height='80' class='service' />
  <text x='375' y='145' text-anchor='middle' class='text'>API网关</text>

  <rect x='550' y='100' width='150' height='80' class='service' />
  <text x='625' y='145' text-anchor='middle' class='text'>业务服务</text>

  <rect x='700' y='200' width='150' height='80' class='database' />
  <text x='775' y='245' text-anchor='middle' class='text'>数据库</text>
            """
        else:
            return """
  <!-- 基础系统图元素 -->
  <rect x='100' y='150' width='200' height='100' class='system' />
  <text x='200' y='205' text-anchor='middle' class='text'>系统模块</text>

  <rect x='400' y='150' width='200' height='100' class='module' />
  <text x='500' y='205' text-anchor='middle' class='text'>子模块</text>

  <rect x='250' y='350' width='300' height='80' class='interface' />
  <text x='400' y='395' text-anchor='middle' class='text'>接口层</text>
            """

    def get_stats(self) -> dict[str, Any]:
        """获取统计信息"""
        total = self.stats['total_calls']
        if total > 0:
            success_rate = (self.stats['successful_calls'] / total) * 100
        else:
            success_rate = 0

        return {
            **self.stats,
            'success_rate': f"{success_rate:.1f}%",
            'timestamp': datetime.now().isoformat()
        }

def demo_enhanced_engine() -> Any:
    """演示增强版引擎"""
    logger.info('🚀 增强版AI绘图引擎演示')
    logger.info(str('=' * 50))

    engine = EnhancedAIDrawingEngine()

    # 测试用例
    test_cases = [
        {
            'name': '用户登录流程图',
            'description': '用户登录流程：输入用户名密码 -> 验证 -> 成功/失败判断 -> 登录成功或重试',
            'type': 'flowchart'
        },
        {
            'name': '微服务架构图',
            'description': '电商平台微服务架构：包含API网关、用户服务、订单服务、支付服务、数据库集群',
            'type': 'architecture'
        },
        {
            'name': '专利技术图',
            'description': '智能传感器专利技术：传感器阵列、信号处理模块、数据分析单元、输出接口',
            'type': 'patent'
        }
    ]

    for i, test_case in enumerate(test_cases, 1):
        logger.info(f"\n📋 测试 {i}: {test_case['name']}")
        logger.info(f"   类型: {test_case['type']}")
        logger.info(f"   描述: {test_case['description'][:50]}...")

        result = engine.generate_drawing(
            test_case['description'],
            f"demo_{test_case['type']}_{i}.svg"
        )

        if result['success']:
            logger.info(f"   ✅ 成功: {result['file_path']}")
            if result.get('fallback'):
                logger.info("   ⚠️ 使用模板生成")
        else:
            logger.info(f"   ❌ 失败: {result.get('error', '未知错误')}")

    # 显示统计
    logger.info("\n📊 生成统计")
    logger.info(str('-' * 30))
    stats = engine.get_stats()
    for key, value in stats.items():
        logger.info(f"   {key}: {value}")

if __name__ == '__main__':
    demo_enhanced_engine()
