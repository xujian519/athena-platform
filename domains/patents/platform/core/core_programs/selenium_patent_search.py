#!/usr/bin/env python3
"""
基于Selenium + DeepSeek的专利检索系统
绕过Browser-Use的CDP连接问题
"""

import json
import logging
import os
import sys
import time
from datetime import datetime

import requests

logger = logging.getLogger(__name__)

# 加载环境变量
from dotenv import load_dotenv

load_dotenv()

try:
    from selenium import webdriver
    from selenium.common.exceptions import TimeoutException
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait
    logger.info('✅ Selenium导入成功')
except ImportError as e:
    logger.info(f"❌ Selenium未安装: {e}")
    logger.info('请安装: pip install selenium')
    sys.exit(1)


class SeleniumPatentSearch:
    """基于Selenium的专利检索系统"""

    def __init__(self):
        self.driver = None
        self.deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')

        # 目标专利信息
        self.target_patent = {
            'number': 'CN201815134U',
            'title': '混二元酸二甲酯生产中的甲醇精馏装置',
            'features': [
                '混二元酸二甲酯生产',
                '甲醇精馏装置',
                '精馏塔',
                '酯化反应釜',
                '冷凝器',
                '直接连通',
                '气相连接',
                '节能工艺'
            ]
        }

        self.search_results = []

    def setup_chrome_driver(self):
        """设置Chrome驱动"""
        try:
            # 配置Chrome选项
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # 无头模式
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36')

            # 禁用图片加载以提高速度
            prefs = {
                'profile.managed_default_content_settings.images': 2,
                'profile.default_content_setting_values.notifications': 2
            }
            chrome_options.add_experimental_option('prefs', prefs)

            # 创建WebDriver
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info('✅ Chrome WebDriver初始化成功')
            return True

        except Exception as e:
            logger.info(f"❌ Chrome WebDriver初始化失败: {e}")
            return False

    def call_deepseek_api(self, prompt: str, max_retries=3):
        """调用DeepSeek API，带重试机制"""
        for attempt in range(max_retries):
            try:
                url = 'https://api.deepseek.com/v1/chat/completions'
                headers = {
                    'Authorization': f"Bearer {self.deepseek_api_key}",
                    'Content-Type': 'application/json'
                }

                payload = {
                    'model': 'deepseek-chat',
                    'messages': [
                        {
                            'role': 'system',
                            'content': '你是一位专业的专利检索和分析专家，具有丰富的化学工程背景知识。请提供准确、专业的专利技术分析。'
                        },
                        {
                            'role': 'user',
                            'content': prompt
                        }
                    ],
                    'temperature': 0.1,
                    'max_tokens': 1500,
                    'timeout': 20
                }

                logger.info(f"🔄 尝试DeepSeek API调用 (第{attempt+1}次)...")
                response = requests.post(url, headers=headers, json=payload, timeout=30)
                response.raise_for_status()

                result = response.json()
                return result['choices'][0]['message']['content']

            except requests.exceptions.Timeout:
                logger.info(f"⏰ 第{attempt+1}次调用超时")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                    continue
                else:
                    raise Exception('所有重试均超时')
            except Exception as e:
                logger.info(f"❌ DeepSeek API调用失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                else:
                    raise e

    def search_google_patents(self, query: str):
        """使用Selenium搜索Google Patents"""
        logger.info(f"\n🔍 Selenium搜索: {query}")

        try:
            # 构建搜索URL
            encoded_query = query.replace(' ', '+')
            search_url = f"https://patents.google.com/?q={encoded_query}"

            # 访问页面
            logger.info(f"🌐 访问: {search_url}")
            self.driver.get(search_url)

            # 等待页面加载
            time.sleep(3)

            # 尝试找到搜索结果
            search_results = []

            # 查找专利结果元素
            try:
                # 等待搜索结果加载
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, '[data-result-id]'))
                )

                # 获取前5个专利结果
                result_elements = self.driver.find_elements(By.CSS_SELECTOR, '[data-result-id]')[:5]

                for element in result_elements:
                    try:
                        # 提取专利信息
                        patent_data = {
                            'title': element.find_element(By.CSS_SELECTOR, 'h2 a').text if element.find_elements(By.CSS_SELECTOR, 'h2 a') else '',
                            'patent_number': '',
                            'assignee': '',
                            'publication_date': '',
                            'abstract': ''
                        }

                        # 获取链接
                        link_element = element.find_element(By.CSS_SELECTOR, 'h2 a')
                        patent_url = link_element.get_attribute('href')
                        patent_data['url'] = patent_url

                        search_results.append(patent_data)

                    except Exception as e:
                        logger.info(f"⚠️ 解析专利元素失败: {e}")
                        continue

                logger.info(f"✅ 找到 {len(search_results)} 个专利结果")

            except TimeoutException:
                logger.info('⚠️ 未找到搜索结果元素，可能是页面结构变化或访问限制')

            # 使用DeepSeek分析结果
            if search_results or True:  # 即使没有找到也分析
                analysis = self.analyze_with_deepseek(query, search_results)
                return analysis

        except Exception as e:
            logger.info(f"❌ Selenium搜索失败: {e}")
            return None

    def analyze_with_deepseek(self, query: str, patent_results: list):
        """使用DeepSeek分析专利检索结果"""
        logger.info('🤖 DeepSeek分析检索结果...')

        # 构建分析提示
        prompt = f"""
        请分析以下专利检索结果：

        **目标专利:**
        - 专利号: {self.target_patent['number']}
        - 标题: {self.target_patent['title']}
        - 技术特征: {', '.join(self.target_patent['features'])}

        **检索查询:** {query}

        **检索结果:**
        找到 {len(patent_results)} 个相关专利
        {json.dumps(patent_results[:3], ensure_ascii=False, indent=2) if patent_results else '未找到具体专利结果'}

        **分析任务:**
        1. 评估该技术领域可能存在的现有专利
        2. 分析目标专利的新颖性前景
        3. 识别潜在的技术冲突点
        4. 提供改进的检索建议

        请返回JSON格式分析：
        {{
            'query_analysis': {{
                'technical_field': '技术领域',
                'search_effectiveness': '检索效果评估',
                'recommendations': ['改进建议']
            }},
            'novelty_assessment': {{
                'novelty_level': 'HIGH/MEDIUM/LOW',
                'confidence': 0.8,
                'key_risks': ['主要风险'],
                'technical_differentiation': '技术差异化点'
            }},
            'potential_conflicts': [
                {{
                    'technology_area': '技术领域',
                    'conflict_probability': '冲突概率',
                    'mitigation_strategy': '缓解策略'
                }}
            ]
        }}
        """

        try:
            analysis_result = self.call_deepseek_api(prompt)

            # 保存结果
            search_result = {
                'query': query,
                'patent_results': patent_results,
                'deepseek_analysis': analysis_result,
                'timestamp': datetime.now().isoformat()
            }

            self.search_results.append(search_result)
            logger.info('✅ DeepSeek分析完成')
            return search_result

        except Exception as e:
            logger.info(f"❌ DeepSeek分析失败: {e}")
            return None

    def run_comprehensive_search(self):
        """运行综合专利检索"""
        logger.info('🚀 启动Selenium + DeepSeek专利检索系统')
        logger.info(str('='*60))
        logger.info('✅ 使用Selenium绕过Browser-Use CDP问题')
        logger.info('✅ 集成DeepSeek AI分析')
        logger.info(str('='*60))

        if not self.deepseek_api_key:
            logger.info('❌ 请配置DEEPSEEK_API_KEY')
            return

        # 初始化浏览器
        if not self.setup_chrome_driver():
            return

        try:
            # 执行多策略检索
            queries = [
                '混二元酸二甲酯生产 甲醇精馏装置',
                '酯化反应釜 精馏塔 直接连通',
                'dimethyl adipate methanol distillation',
                'DBE production methanol recovery reactor',
                '反应器与精馏塔气相连接节能技术'
            ]

            for i, query in enumerate(queries, 1):
                logger.info(f"\n{'='*50}")
                logger.info(f"🔄 检索 {i}/{len(queries)}")
                logger.info(f"{'='*50}")

                self.search_google_patents(query)

                # 添加延迟避免被限制
                if i < len(queries):
                    logger.info('⏰ 等待5秒...')
                    time.sleep(5)

            # 生成最终报告
            self.generate_final_report()

        finally:
            if self.driver:
                self.driver.quit()
                logger.info('✅ 浏览器已关闭')

    def generate_final_report(self):
        """生成最终检索分析报告"""
        logger.info("\n📋 生成最终检索报告...")

        report = {
            'patent_number': self.target_patent['number'],
            'patent_title': self.target_patent['title'],
            'search_date': datetime.now().isoformat(),
            'search_method': 'Selenium + DeepSeek API',
            'target_features': self.target_patent['features'],
            'search_statistics': {
                'total_queries': len(self.search_results),
                'successful_analyses': len([r for r in self.search_results if r.get('deepseek_analysis')]),
                'success_rate': f"{len([r for r in self.search_results if r.get('deepseek_analysis')])/len(self.search_results)*100:.1f}%' if self.search_results else '0%"
            },
            'search_results': self.search_results,
            'technical_advantages': [
                '使用Selenium绕过Browser-Use CDP限制',
                'DeepSeek API提供专业的中文专利分析',
                '重试机制提高API调用成功率',
                '稳定的浏览器自动化'
            ],
            'system_architecture': {
                'browser_automation': 'Selenium WebDriver',
                'ai_analysis': 'DeepSeek API',
                'patent_database': 'Google Patents',
                'fallback_mechanism': 'API重试 + 错误处理'
            },
            'next_steps': [
                '验证检索结果的准确性',
                '在专业数据库中进一步检索',
                '委托专业检索机构验证',
                '基于分析结果完善专利申请策略'
            ]
        }

        # 保存报告
        report_file = '/Users/xujian/Athena工作平台/CN201815134U_selenium_patent_search_report.json'
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 最终报告已保存: {report_file}")

        # 显示总结
        logger.info("\n🎯 Selenium + DeepSeek检索总结:")
        logger.info(f"  📊 总检索数: {report['search_statistics']['total_queries']}")
        logger.info(f"  ✅ 成功分析: {report['search_statistics']['successful_analyses']}")
        logger.info(f"  📈 成功率: {report['search_statistics']['success_rate']}")
        logger.info("  🔧 方法: Selenium + DeepSeek API")


def main():
    """主函数"""
    logger.info('🚀 Selenium + DeepSeek专利检索系统')
    logger.info(str('='*50))

    # 检查API密钥
    deepseek_api_key = os.getenv('DEEPSEEK_API_KEY')
    if not deepseek_api_key:
        logger.info('❌ 未找到DEEPSEEK_API_KEY环境变量')
        return

    logger.info(f"✅ DeepSeek API密钥已配置 (长度: {len(deepseek_api_key)})")

    # 创建检索系统
    search_system = SeleniumPatentSearch()

    try:
        search_system.run_comprehensive_search()
        logger.info("\n🎉 专利检索分析完成！")

    except KeyboardInterrupt:
        logger.info("\n⏹️ 用户中断")
    except Exception as e:
        logger.info(f"\n❌ 检索过程出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
