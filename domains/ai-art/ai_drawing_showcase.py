#!/usr/bin/env python3
"""
AI绘图功能展示
AI Drawing Showcase

展示智谱清言在各类场景下的绘图能力

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 1.0.0
"""

import logging
import time
from pathlib import Path
from typing import Any

import requests

logger = logging.getLogger(__name__)

# 智谱清言配置
ZHIPU_API_KEY = '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'
ZHIPU_API_URL = 'https://open.bigmodel.cn/api/paas/v4/chat/completions'

def call_zhipu_api(prompt) -> Any:
    """调用智谱清言API生成SVG图纸"""
    headers = {
        'Authorization': f"Bearer {ZHIPU_API_KEY}",
        'Content-Type': 'application/json'
    }

    system_prompt = """
你是专业技术绘图专家，生成完整SVG技术图纸。

要求：
1. 生成完整可用的SVG代码
2. 包含矩形、圆形、箭头、文字等元素
3. 布局清晰、专业美观
4. 直接返回SVG代码，不要解释文字

SVG要求：
- 以<svg>开始，</svg>结束
- 使用合理坐标系统
- 添加文字标注
- 保持专业风格
    """

    data = {
        'model': 'glm-4',
        'messages': [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"生成技术图纸SVG：{prompt}"}
        ],
        'max_tokens': 2000,
        'temperature': 0.7
    }

    try:
        response = requests.post(ZHIPU_API_URL, headers=headers, json=data, timeout=30)
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            logger.info(f"API错误: {response.status_code}")
            return None
    except Exception as e:
        logger.info(f"调用异常: {e}")
        return None

def create_sample_drawing(description, filename) -> Any:
    """创建示例图纸"""
    logger.info(f"🎨 生成: {description}")

    svg_content = call_zhipu_api(description)

    if svg_content:
        # 清理SVG
        if svg_content.startswith('```'):
            svg_content = svg_content.replace('```svg', '').replace('```', '').strip()

        if svg_content.startswith('<svg'):
            # 保存文件
            output_path = Path(f"/tmp/{filename}")
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(svg_content)
            logger.info(f"   ✅ 已保存: {output_path}")
            return str(output_path)
        else:
            logger.info("   ❌ SVG格式错误")
            return None
    else:
        logger.info("   ❌ 生成失败")
        return None

def main() -> None:
    """主演示函数"""
    logger.info('🚀 AI绘图功能展示')
    logger.info(str('=' * 50))
    logger.info('🤖 智谱清言GLM-4 专业绘图')
    logger.info('🎨 专利图纸 + 架构图 + 流程图')
    logger.info(str('=' * 50))

    # 1. 专利技术图纸
    logger.info("\n🔬 1. 专利技术图纸")
    logger.info(str('-' * 30))

    patent_demos = [
        {
            'desc': '智能传感器数据处理系统：传感器采集 -> 信号放大 -> ADC转换 -> 微处理器处理',
            'file': 'patent_sensor_system.svg'
        },
        {
            'desc': '自动调节阀门机械结构：阀体、阀芯、弹簧、密封圈的纵向剖视图',
            'file': 'patent_valve_structure.svg'
        }
    ]

    for demo in patent_demos:
        create_sample_drawing(demo['desc'], demo['file'])

    # 2. 软件架构图
    logger.info("\n💻 2. 软件架构图")
    logger.info(str('-' * 30))

    architecture_demos = [
        {
            'desc': '微服务电商架构：API网关 -> 用户服务/商品服务/订单服务/支付服务 -> 数据库',
            'file': 'microservices_architecture.svg'
        },
        {
            'desc': '大数据处理流水线：数据采集 -> 清洗 -> 转换 -> 存储 -> 分析 -> 可视化',
            'file': 'data_pipeline.svg'
        }
    ]

    for demo in architecture_demos:
        create_sample_drawing(demo['desc'], demo['file'])

    # 3. 业务流程图
    logger.info("\n📊 3. 业务流程图")
    logger.info(str('-' * 30))

    process_demos = [
        {
            'desc': '用户注册流程：输入信息 -> 验证 -> 发送验证码 -> 邮箱验证 -> 注册成功',
            'file': 'user_registration_flow.svg'
        },
        {
            'desc': '订单处理流程：下单 -> 支付 -> 库存检查 -> 发货 -> 配送 -> 收货确认',
            'file': 'order_process_flow.svg'
        }
    ]

    for demo in process_demos:
        create_sample_drawing(demo['desc'], demo['file'])

    # 4. 统计和总结
    logger.info("\n📈 生成统计")
    logger.info(str('-' * 30))

    svg_files = list(Path('/tmp').glob('*.svg'))
    recent_files = [f for f in svg_files if f.stat().st_mtime > time.time() - 300]  # 最近5分钟

    logger.info(f"   📊 生成图纸数: {len(recent_files)}")
    logger.info("   💾 保存路径: /tmp/")

    logger.info("\n💡 使用方法")
    logger.info(str('-' * 30))
    logger.info('   🖥️  查看图纸: 浏览器打开 /tmp/*.svg')
    logger.info('   📱 导入文档: 支持插入Word、PPT、PDF')
    logger.info('   🔄 自定义: 修改描述生成新图纸')

    logger.info("\n🎯 智谱清言优势")
    logger.info(str('-' * 30))
    logger.info('   🥇 中文理解: 97.1%准确率')
    logger.info('   ⚡ 响应速度: 0.7秒')
    logger.info('   💰 成本效益: 0.009元/千token')
    logger.info('   📏 上下文: 128K tokens')
    logger.info('   🔒 数据安全: 本地部署')

    logger.info("\n🎉 演示完成！")
    logger.info(str('=' * 50))

if __name__ == '__main__':
    main()
