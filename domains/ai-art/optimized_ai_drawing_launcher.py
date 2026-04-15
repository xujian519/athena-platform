#!/usr/bin/env python3
"""
优化版AI绘图启动器
Optimized AI Drawing Launcher

提供稳定、高质量的AI绘图服务

作者: Athena AI系统
创建时间: 2025年12月6日
版本: 2.0.0
"""

import logging
import time
from pathlib import Path
from typing import Any

from enhanced_ai_drawing_engine import EnhancedAIDrawingEngine

logger = logging.getLogger(__name__)

# 智谱清言配置
ZHIPU_API_KEY = '9efe5766a7cd4bb687e40082ee4032b6.0mYTotbC7aRmoNCe'

class OptimizedAIDrawingLauncher:
    """优化版AI绘图启动器"""

    def __init__(self):
        self.engine = EnhancedAIDrawingEngine()
        self.demo_scenes = self._load_demo_scenes()

    def _load_demo_scenes(self) -> list[dict[str, Any]]:
        """加载演示场景"""
        return [
            # 专利技术图纸
            {
                'category': '专利技术图纸',
                'icon': '🔬',
                'items': [
                    {
                        'name': '智能传感器系统',
                        'description': '''专利技术方案：智能传感器阵列数据处理系统
主要组件：
- 传感器阵列：多模态传感器采集单元
- 信号调理电路：放大、滤波、ADC转换
- 微处理器：FPGA实时信号处理
- 数据分析模块：AI算法智能分析
- 通信接口：4G/5G无线传输
- 电源管理：低功耗设计
技术要求：展示信号流向和数据处理流程''',
                        'filename': 'patent_sensor_system.svg'
                    },
                    {
                        'name': '自动调节阀门',
                        'description': '''专利技术方案：智能自动调节阀门机械结构
主要组件：
- 阀体：不锈钢铸造主体
- 阀芯：精密加工控制芯
- 弹簧机构：自动复位装置
- 密封圈：高分子材料密封
- 调节螺母：精确控制装置
- 进出口接口：标准法兰连接
图纸要求：展示纵向剖视图和主要部件标注''',
                        'filename': 'patent_valve_structure.svg'
                    }
                ]
            },
            # 软件架构图
            {
                'category': '软件架构图',
                'icon': '💻',
                'items': [
                    {
                        'name': '微服务电商平台',
                        'description': '''电商平台微服务架构设计
主要服务：
- API网关：统一入口，路由分发
- 用户服务：用户管理、认证授权
- 商品服务：商品管理、搜索推荐
- 订单服务：订单处理、状态跟踪
- 支付服务：支付处理、交易安全
- 库存服务：库存管理、预警系统
基础设施：MySQL集群、Redis缓存、消息队列
展示要求：服务调用关系和数据流向''',
                        'filename': 'microservices_ecommerce.svg'
                    },
                    {
                        'name': '大数据处理平台',
                        'description': '''企业级大数据处理流水线架构
处理流程：
- 数据采集：Kafka实时数据流
- 数据清洗：Spark ETL处理
- 数据转换：格式标准化
- 数据存储：Hadoop HDFS
- 数据分析：Spark ML机器学习
- 数据可视化：Tableau展示
技术栈：Hadoop生态、Spark、Kafka、Elasticsearch
展示要求：完整的数据处理流水线''',
                        'filename': 'bigdata_pipeline.svg'
                    }
                ]
            },
            # 业务流程图
            {
                'category': '业务流程图',
                'icon': '📊',
                'items': [
                    {
                        'name': '用户注册流程',
                        'description': '''完整的用户注册业务流程
主要步骤：
1. 用户输入基本信息
2. 前端格式验证
3. 后端数据验证
4. 检查用户名重复
5. 发送邮箱验证码
6. 验证码校验
7. 用户信息入库
8. 注册成功通知
决策点：输入验证、重复检查、验证码验证
异常处理：各步骤的失败回滚''',
                        'filename': 'user_registration_flow.svg'
                    },
                    {
                        'name': '订单处理流程',
                        'description': '''电商订单全生命周期处理流程
处理步骤：
1. 用户下单选择商品
2. 库存检查和预留
3. 价格计算和优惠券
4. 支付处理和确认
5. 订单状态更新
6. 仓库分拣打包
7. 物流配送
8. 用户收货确认
9. 订单评价
涉及系统：订单、支付、库存、物流、用户系统
时间要求：标注各步骤的处理时间''',
                        'filename': 'order_processing_flow.svg'
                    }
                ]
            }
        ]

    def show_menu(self) -> Any:
        """显示主菜单"""
        logger.info(str("\n" + '=' * 60))
        logger.info('🚀 优化版AI绘图平台 - 智谱清言GLM-4')
        logger.info('🎨 专业、稳定、高质量的技术图纸生成')
        logger.info(str('=' * 60))

        for i, category in enumerate(self.demo_scenes, 1):
            logger.info(f"{i}. {category['icon']} {category['category']}")

        logger.info('4. 🎨 自定义绘图')
        logger.info('5. 📊 批量生成')
        logger.info('6. 📈 性能统计')
        logger.info('7. 💡 使用技巧')
        logger.info('0. 🚪 退出')

    def show_category_items(self, category_index: int) -> Any:
        """显示分类下的项目"""
        if 0 < category_index <= len(self.demo_scenes):
            category = self.demo_scenes[category_index - 1]
            logger.info(f"\n{category['icon']} {category['category']}")
            logger.info(str('-' * 50))

            for i, item in enumerate(category['items'], 1):
                logger.info(f"{i}. {item['name']}")
                logger.info(f"   {item['description'][:80]}...")
                print()

            logger.info('0. 📋 返回主菜单')
            return category
        return None

    def generate_drawing_with_stats(self, description: str, filename: str) -> bool:
        """带统计信息的图纸生成"""
        logger.info(f"🎨 正在生成: {filename}")
        logger.info('⏳ 处理中...')

        start_time = time.time()
        result = self.engine.generate_drawing(description, filename)
        processing_time = time.time() - start_time

        if result['success']:
            logger.info("✅ 生成成功!")
            logger.info(f"   📏 图纸大小: {len(result['svg_content'])}字符")
            logger.info(f"   ⏱️ 处理时间: {processing_time:.2f}秒")
            logger.info(f"   💾 保存路径: {result['file_path']}")

            if result.get('fallback'):
                logger.info("   ⚠️ 使用模板生成（API超时）")

            return True
        else:
            logger.info(f"❌ 生成失败: {result.get('error', '未知错误')}")
            return False

    def run_custom_drawing(self) -> Any:
        """自定义绘图"""
        logger.info("\n🎨 自定义绘图功能")
        logger.info(str('=' * 50))
        logger.info('💡 提示：描述越详细，生成效果越好')
        logger.info(str('-' * 50))

        while True:
            description = input("\n📝 请输入绘图描述（输入 'exit' 返回）: ").strip()

            if description.lower() == 'exit':
                break

            if not description:
                logger.info('❌ 请输入绘图描述')
                continue

            # 自动生成文件名
            import hashlib
            filename_hash = hashlib.md5(description.encode(), usedforsecurity=False).hexdigest()[:8]
            filename = f"custom_optimized_{filename_hash}.svg"

            self.generate_drawing_with_stats(description, filename)

    def run_batch_generation(self) -> Any:
        """批量生成"""
        logger.info("\n📊 批量生成功能")
        logger.info(str('=' * 50))

        # 收集所有演示项目
        all_items = []
        for category in self.demo_scenes:
            for item in category['items']:
                all_items.append(item)

        logger.info(f"📋 将批量生成 {len(all_items)} 个图纸")
        confirm = input("\n确认开始批量生成？(y/n): ").strip().lower()

        if confirm == 'y':
            success_count = 0
            total_time = 0

            for i, item in enumerate(all_items, 1):
                logger.info(f"\n[{i}/{len(all_items)}] {item['name']}")

                start_time = time.time()
                if self.generate_drawing_with_stats(item['description'], item['filename']):
                    success_count += 1

                total_time += time.time() - start_time

            # 批量生成统计
            logger.info("\n📊 批量生成完成")
            logger.info(str('-' * 30))
            logger.info(f"   成功生成: {success_count}/{len(all_items)}")
            logger.info(f"   成功率: {(success_count/len(all_items))*100:.1f}%")
            logger.info(f"   总耗时: {total_time:.2f}秒")
            logger.info(f"   平均耗时: {total_time/len(all_items):.2f}秒/图")

    def show_performance_stats(self) -> Any:
        """显示性能统计"""
        logger.info("\n📈 性能统计")
        logger.info(str('=' * 50))

        stats = self.engine.get_stats()

        logger.info("📊 调用统计:")
        logger.info(f"   总调用次数: {stats['total_calls']}")
        logger.info(f"   成功次数: {stats['successful_calls']}")
        logger.info(f"   失败次数: {stats['failed_calls']}")
        logger.info(f"   成功率: {stats['success_rate']}")

        # 检查生成的文件
        svg_files = list(Path('/tmp').glob('*.svg'))
        recent_files = [f for f in svg_files if f.stat().st_mtime > time.time() - 3600]

        logger.info("\n📁 文件统计:")
        logger.info(f"   SVG文件总数: {len(svg_files)}")
        logger.info(f"   最近1小时: {len(recent_files)}")

        if recent_files:
            total_size = sum(f.stat().st_size for f in recent_files)
            logger.info(f"   总大小: {total_size/1024:.1f}KB")
            logger.info(f"   平均大小: {total_size/len(recent_files):.1f}KB")

    def show_usage_tips(self) -> Any:
        """显示使用技巧"""
        logger.info("\n💡 AI绘图优化技巧")
        logger.info(str('=' * 50))

        tips = [
            {
                'category': '📝 描述技巧',
                'items': [
                    '使用结构化描述：包含主要组件、连接关系、技术特点',
                    '指定图纸类型：流程图、架构图、专利图、系统图',
                    '提供专业术语：智谱清言能理解专业技术词汇',
                    '说明布局要求：从上到下、从左到右等空间布局'
                ]
            },
            {
                'category': '🎯 质量优化',
                'items': [
                    '描述长度控制在200-500字之间',
                    '按组件→关系→布局的顺序描述',
                    '明确标注关键尺寸和比例要求',
                    '指定颜色风格（蓝色系、灰色系等）'
                ]
            },
            {
                'category': '⚡ 效率提升',
                'items': [
                    '使用批量生成功能提高效率',
                    '成功的描述可以保存为模板复用',
                    '遇到超时会自动使用模板生成',
                    '文件自动保存在/tmp/目录'
                ]
            },
            {
                'category': '🔧 问题解决',
                'items': [
                    'API超时：系统会自动重试3次',
                    'SVG格式错误：检查描述是否完整',
                    '生成质量差：增加更多技术细节',
                    '所有图纸都支持浏览器直接查看'
                ]
            }
        ]

        for tip_category in tips:
            logger.info(f"\n{tip_category['category']}")
            for item in tip_category['items']:
                logger.info(f"   ✅ {item}")

    def run(self) -> None:
        """主运行循环"""
        while True:
            self.show_menu()
            choice = input("\n请选择功能 (0-7): ").strip()

            if choice == '0':
                logger.info("\n👋 感谢使用优化版AI绘图系统！")
                break
            elif choice in ['1', '2', '3']:
                # 显示分类项目
                category = self.show_category_items(int(choice))
                if category:
                    while True:
                        item_choice = input(f"\n请选择图纸 (0-{len(category['items'])}): ").strip()

                        if item_choice == '0':
                            break

                        try:
                            item_index = int(item_choice) - 1
                            if 0 <= item_index < len(category['items']):
                                item = category['items'][item_index]
                                self.generate_drawing_with_stats(
                                    item['description'],
                                    item['filename']
                                )
                                input("\n按回车键继续...")
                        except ValueError:
                            logger.info('❌ 无效选择')

            elif choice == '4':
                self.run_custom_drawing()
            elif choice == '5':
                self.run_batch_generation()
            elif choice == '6':
                self.show_performance_stats()
            elif choice == '7':
                self.show_usage_tips()
            else:
                logger.info('❌ 无效选择，请输入0-7')

def main() -> None:
    """主函数"""
    try:
        launcher = OptimizedAIDrawingLauncher()
        launcher.run()
    except KeyboardInterrupt:
        logger.info("\n👋 用户中断，再见！")
    except Exception as e:
        logger.info(f"\n❌ 系统错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
