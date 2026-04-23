#!/usr/bin/env python3
"""
API Key配置管理工具
统一管理所有外部API服务的密钥配置
"""

import getpass
import json
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class APIConfig:
    """API配置数据结构"""
    name: str
    service: str
    key_env_var: str
    config_file: str
    description: str
    website: str
    required: bool = False
    test_endpoint: str | None = None

class APIKeyManager:
    """API Key管理器"""

    def __init__(self):
        self.config_dir = Path('/Users/xujian/Athena工作平台/config')
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.env_file = self.config_dir / '.env'
        self.api_config_file = self.config_dir / 'api_config.json'

        # 定义所有需要的API配置
        self.api_configs = [
            # 智谱清言 (GLM-4.6)
            APIConfig(
                name='智谱清言 GLM-4.6',
                service='zhipu',
                key_env_var='ZHIPU_API_KEY',
                config_file='llm_config.json',
                description='智谱清言大模型服务，提供GLM-4.6等模型',
                website='https://open.bigmodel.cn/',
                required=True,
                test_endpoint='https://open.bigmodel.cn/api/paas/v4/models'
            ),

            # 百度文心一言
            APIConfig(
                name='百度文心一言',
                service='wenxin',
                key_env_var='BAIDU_API_KEY',
                config_file='domestic_llm_config.json',
                description='百度文心一言大模型服务',
                website='https://aip.baidubce.com/',
                required=False,
                test_endpoint='https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/eb-instant'
            ),

            # 阿里通义千问
            APIConfig(
                name='阿里通义千问',
                service='tongyi',
                key_env_var='DASHSCOPE_API_KEY',
                config_file='domestic_llm_config.json',
                description='阿里云通义千问大模型服务',
                website='https://dashscope.aliyuncs.com/',
                required=False,
                test_endpoint='https://dashscope.aliyuncs.com/api/v1/models'
            ),

            # 科大讯飞星火
            APIConfig(
                name='科大讯飞星火',
                service='spark',
                key_env_var='SPARK_API_KEY',
                config_file='domestic_llm_config.json',
                description='科大讯飞星火认知大模型',
                website='https://xinghuo.xfyun.cn/',
                required=False
            ),

            # OpenAI GPT
            APIConfig(
                name='OpenAI GPT',
                service='openai',
                key_env_var='OPENAI_API_KEY',
                config_file='llm_config.json',
                description='OpenAI GPT系列模型',
                website='https://platform.openai.com/',
                required=False,
                test_endpoint='https://api.openai.com/v1/models'
            ),

            # Anthropic Claude
            APIConfig(
                name='Anthropic Claude',
                service='anthropic',
                key_env_var='ANTHROPIC_API_KEY',
                config_file='llm_config.json',
                description='Anthropic Claude系列模型',
                website='https://console.anthropic.com/',
                required=False,
                test_endpoint='https://api.anthropic.com/v1/messages'
            ),

            # Google Gemini
            APIConfig(
                name='Google Gemini',
                service='gemini',
                key_env_var='GOOGLE_API_KEY',
                config_file='domestic_llm_config.json',
                description='Google Gemini多模态模型',
                website='https://makersuite.google.com/app/apikey',
                required=False,
                test_endpoint='https://generativelanguage.googleapis.com/v1beta/models'
            ),

            # ScrapingBee (网页爬虫)
            APIConfig(
                name='ScrapingBee',
                service='scrapingbee',
                key_env_var='SCRAPINGBEE_API_KEY',
                config_file='scraping_config.json',
                description='ScrapingBee网页爬虫服务',
                website='https://www.scrapingbee.com/',
                required=False
            ),

            # Qwen (通义千问API)
            APIConfig(
                name='Qwen API',
                service='qwen',
                key_env_var='QWEN_API_KEY',
                config_file='qwen_config.json',
                description='阿里通义千问API服务',
                website='https://dashscope.aliyuncs.com/',
                required=False
            )
        ]

    def load_current_config(self) -> dict[str, Any]:
        """加载当前配置"""
        config = {
            'configured_services': {},
            'missing_keys': [],
            'configured_keys': []
        }

        # 从环境变量加载
        for api_config in self.api_configs:
            key_value = os.getenv(api_config.key_env_var)
            if key_value:
                config['configured_services'][api_config.service] = {
                    'name': api_config.name,
                    'key_env_var': api_config.key_env_var,
                    'has_key': True,
                    'key_preview': key_value[:10] + '...' if len(key_value) > 10 else key_value
                }
                config['configured_keys'].append(api_config.service)
            else:
                config['missing_keys'].append(api_config.service)

        return config

    def print_status_report(self, config: dict[str, Any]) -> Any:
        """打印状态报告"""
        logger.info(str("\n" + '='*80))
        logger.info('🔑 API Key状态报告')
        logger.info(str('='*80))

        total_services = len(self.api_configs)
        configured_count = len(config['configured_keys'])
        missing_count = len(config['missing_keys'])

        logger.info(f"📊 总计服务: {total_services}")
        logger.info(f"✅ 已配置: {configured_count}")
        logger.info(f"❌ 缺失配置: {missing_count}")

        logger.info("\n📋 详细状态:")
        logger.info(str('-' * 80))

        # 已配置的服务
        if config['configured_services']:
            logger.info('✅ 已配置的服务:')
            for service, info in config['configured_services'].items():
                logger.info(f"   🌟 {info['name']}")
                logger.info(f"      环境变量: {info['key_env_var']}")
                logger.info(f"      Key预览: {info['key_preview']}")
                print()

        # 缺失配置的服务
        if config['missing_keys']:
            logger.info('❌ 缺失配置的服务:')
            for service in config['missing_keys']:
                api_config = next(ac for ac in self.api_configs if ac.service == service)
                required_tag = '【必需】' if api_config.required else '【可选】'
                logger.info(f"   {required_tag} {api_config.name}")
                logger.info(f"      环境变量: {api_config.key_env_var}")
                logger.info(f"      注册地址: {api_config.website}")
                logger.info(f"      描述: {api_config.description}")
                print()

    def save_to_env_file(self, api_config: APIConfig, api_key: str) -> None:
        """保存API Key到环境文件"""
        env_content = ''

        # 如果文件存在，读取现有内容
        if self.env_file.exists():
            with open(self.env_file, encoding='utf-8') as f:
                env_content = f.read()

        # 检查是否已存在该配置
        lines = env_content.split('\n')
        updated_lines = []
        key_found = False

        for line in lines:
            if line.startswith(f"{api_config.key_env_var}="):
                updated_lines.append(f"{api_config.key_env_var}={api_key}")
                key_found = True
            else:
                updated_lines.append(line)

        # 如果没有找到，添加新配置
        if not key_found:
            updated_lines.append(f"{api_config.key_env_var}={api_key}")

        # 写回文件
        with open(self.env_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))

        logger.info(f"✅ API Key已保存到 {self.env_file}")

    def update_config_files(self) -> None:
        """更新各个配置文件"""
        config_updates = {
            'llm_config.json': {
                'zhipu_api_key': os.getenv('ZHIPU_API_KEY', ''),
                'openai_api_key': os.getenv('OPENAI_API_KEY', ''),
                'anthropic_api_key': os.getenv('ANTHROPIC_API_KEY', ''),
                'provider': 'zhipu',
                'model': 'glm-4',
                'configured_at': '2025-12-11T00:00:00Z',
                'status': 'active'
            },
            'domestic_llm_config.json': {
                'zhipu_api_key': os.getenv('ZHIPU_API_KEY', ''),
                'baidu_api_key': os.getenv('BAIDU_API_KEY', ''),
                'dashscope_api_key': os.getenv('DASHSCOPE_API_KEY', ''),
                'spark_api_key': os.getenv('SPARK_API_KEY', ''),
                'google_api_key': os.getenv('GOOGLE_API_KEY', ''),
                'primary_provider': 'zhipu',
                'configured_at': '2025-12-11T00:00:00Z',
                'status': 'active'
            },
            'qwen_config.json': {
                'api_key': os.getenv('QWEN_API_KEY', ''),
                'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
                'model_name': 'qwen-turbo',
                'configured_at': '2025-12-11T00:00:00Z',
                'status': 'active'
            },
            'scraping_config.json': {
                'api_key': os.getenv('SCRAPINGBEE_API_KEY', ''),
                'base_url': 'https://app.scrapingbee.com/api/v1/',
                'configured_at': '2025-12-11T00:00:00Z',
                'status': 'active'
            }
        }

        for filename, content in config_updates.items():
            config_path = self.config_dir / filename
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(content, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 配置文件已更新: {filename}")

    def interactive_configuration(self) -> Any:
        """交互式配置"""
        logger.info("\n🔧 API Key交互式配置")
        logger.info(str('='*50))

        # 显示必需服务
        required_services = [ac for ac in self.api_configs if ac.required]
        logger.info('🎯 以下为必需服务:')
        for api_config in required_services:
            key_value = os.getenv(api_config.key_env_var)
            status = '✅ 已配置' if key_value else '❌ 未配置'
            logger.info(f"   {status} {api_config.name} ({api_config.key_env_var})")

        logger.info("\n💡 可选服务:")
        optional_services = [ac for ac in self.api_configs if not ac.required]
        for api_config in optional_services:
            key_value = os.getenv(api_config.key_env_var)
            status = '✅ 已配置' if key_value else '❌ 未配置'
            logger.info(f"   {status} {api_config.name} ({api_config.key_env_var})")

        logger.info("\n🎯 选择要配置的服务:")
        logger.info('1. 配置智谱清言 (必需)')
        logger.info('2. 配置OpenAI GPT')
        logger.info('3. 配置Anthropic Claude')
        logger.info('4. 配置百度文心一言')
        logger.info('5. 配置阿里通义千问')
        logger.info('6. 配置科大讯飞星火')
        logger.info('7. 配置Google Gemini')
        logger.info('8. 配置ScrapingBee')
        logger.info('9. 配置Qwen API')
        logger.info('10. 批量配置所有必需服务')
        logger.info('11. 测试已配置的服务')

        try:
            choice = input("\n请输入选项 (1-11): ").strip()

            if choice == '1':
                self.configure_service('zhipu')
            elif choice == '2':
                self.configure_service('openai')
            elif choice == '3':
                self.configure_service('anthropic')
            elif choice == '4':
                self.configure_service('wenxin')
            elif choice == '5':
                self.configure_service('tongyi')
            elif choice == '6':
                self.configure_service('spark')
            elif choice == '7':
                self.configure_service('gemini')
            elif choice == '8':
                self.configure_service('scrapingbee')
            elif choice == '9':
                self.configure_service('qwen')
            elif choice == '10':
                self.configure_required_services()
            elif choice == '11':
                self.test_configured_services()
            else:
                logger.info('❌ 无效选项')

        except KeyboardInterrupt:
            logger.info("\n👋 用户中断操作")
        except Exception as e:
            logger.error(f"❌ 配置失败: {e}")

    def configure_service(self, service_name: str) -> Any:
        """配置单个服务"""
        api_config = next(ac for ac in self.api_configs if ac.service == service_name)

        logger.info(f"\n🔧 配置 {api_config.name}")
        logger.info(f"📝 描述: {api_config.description}")
        logger.info(f"🌐 注册地址: {api_config.website}")
        logger.info(f"🔑 环境变量: {api_config.key_env_var}")

        # 检查是否已有配置
        existing_key = os.getenv(api_config.key_env_var)
        if existing_key:
            logger.info(f"⚠️ 当前已配置: {existing_key[:10]}...")
            replace = input('是否替换现有配置? (y/n): ').strip().lower()
            if replace != 'y':
                logger.info('保留现有配置')
                return

        # 获取新的API Key
        try:
            api_key = getpass.getpass('请输入API Key (输入时不显示): ').strip()

            if not api_key:
                logger.info('❌ API Key不能为空')
                return

            # 保存到环境变量文件
            self.save_to_env_file(api_config, api_key)

            # 设置当前进程的环境变量
            os.environ[api_config.key_env_var] = api_key

            logger.info(f"✅ {api_config.name} 配置完成!")

            # 询问是否测试
            test_choice = input('是否测试API Key? (y/n): ').strip().lower()
            if test_choice == 'y':
                self.test_service(api_config)

        except KeyboardInterrupt:
            logger.info("\n👋 配置取消")

    def configure_required_services(self) -> Any:
        """批量配置必需服务"""
        required_services = [ac for ac in self.api_configs if ac.required]
        logger.info(f"\n🚀 批量配置 {len(required_services)} 个必需服务...")

        for api_config in required_services:
            self.configure_service(api_config.service)

        logger.info("\n📝 更新配置文件...")
        self.update_config_files()

    def test_service(self, api_config: APIConfig) -> Any:
        """测试单个服务"""
        if not api_config.test_endpoint:
            logger.info(f"⚠️ {api_config.name} 没有测试端点")
            return

        import requests

        logger.info(f"\n🧪 测试 {api_config.name}...")

        try:
            headers = {}
            api_key = os.getenv(api_config.key_env_var)

            if not api_key:
                logger.info(f"❌ 未找到API Key: {api_config.key_env_var}")
                return

            # 根据服务类型设置请求头
            if api_config.service == 'zhipu':
                headers['Authorization'] = f"Bearer {api_key}"
            elif api_config.service == 'openai':
                headers['Authorization'] = f"Bearer {api_key}"
            elif api_config.service == 'anthropic':
                headers['x-api-key'] = api_key
            elif api_config.service == 'gemini':
                # Google API使用URL参数
                api_config.test_endpoint += f"?key={api_key}"
            else:
                headers['Authorization'] = f"Bearer {api_key}"

            response = requests.get(
                api_config.test_endpoint,
                headers=headers,
                timeout=10
            )

            if response.status_code == 200:
                logger.info(f"✅ {api_config.name} API Key 测试成功!")
            elif response.status_code == 401:
                logger.info(f"❌ {api_config.name} API Key 无效")
            elif response.status_code == 403:
                logger.info(f"❌ {api_config.name} API Key 权限不足")
            else:
                logger.info(f"⚠️ {api_config.name} API Key 测试异常: HTTP {response.status_code}")

        except Exception as e:
            logger.info(f"❌ {api_config.name} API Key 测试失败: {e}")

    def test_configured_services(self) -> Any:
        """测试所有已配置的服务"""
        logger.info("\n🧪 批量测试已配置的服务...")

        for api_config in self.api_configs:
            if os.getenv(api_config.key_env_var):
                self.test_service(api_config)
            else:
                logger.info(f"⚠️ {api_config.name} 未配置，跳过测试")

    def generate_env_file_template(self) -> Any:
        """生成环境变量文件模板"""
        template_path = self.config_dir / '.env.template'

        with open(template_path, 'w', encoding='utf-8') as f:
            f.write("# API Key配置模板\n")
            f.write("# 请复制此文件为 .env 并填入实际的API Key\n\n")

            for api_config in self.api_configs:
                required_tag = '# [必需]' if api_config.required else '# [可选]'
                f.write(f"{required_tag}\n")
                f.write(f"# {api_config.name}\n")
                f.write(f"# {api_config.description}\n")
                f.write(f"# 注册地址: {api_config.website}\n")
                f.write(f"{api_config.key_env_var}=your_api_key_here\n\n")

        logger.info(f"✅ 环境变量模板已生成: {template_path}")

def main() -> None:
    """主函数"""
    manager = APIKeyManager()

    logger.info('🔑 API Key配置管理工具')
    logger.info(str('=' * 50))

    # 加载当前配置
    current_config = manager.load_current_config()
    manager.print_status_report(current_config)

    # 检查必需服务
    required_missing = []
    for api_config in manager.api_configs:
        if api_config.required and api_config.service not in current_config['configured_keys']:
            required_missing.append(api_config)

    if required_missing:
        logger.info("\n⚠️ 警告: 以下必需服务尚未配置:")
        for api_config in required_missing:
            logger.info(f"   ❌ {api_config.name}")

    # 交互式菜单
    logger.info("\n🎯 请选择操作:")
    logger.info('1. 交互式配置API Keys')
    logger.info('2. 生成环境变量模板')
    logger.info('3. 测试已配置的服务')
    logger.info('4. 更新配置文件')
    logger.info('5. 退出')

    try:
        choice = input("\n请输入选项 (1-5): ").strip()

        if choice == '1':
            manager.interactive_configuration()
        elif choice == '2':
            manager.generate_env_file_template()
        elif choice == '3':
            manager.test_configured_services()
        elif choice == '4':
            manager.update_config_files()
        elif choice == '5':
            logger.info('👋 退出')
        else:
            logger.info('❌ 无效选项')

    except KeyboardInterrupt:
        logger.info("\n👋 用户中断操作")
    except Exception as e:
        logger.error(f"❌ 操作失败: {e}")

if __name__ == '__main__':
    main()
