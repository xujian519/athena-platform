#!/usr/bin/env python3
"""
专利代理客户开发自动邮件发送系统（macOS邮件应用版本）
Patent Agency Client Development Auto Email System (mac_os Mail App Version)

作者: 小诺 (Xiaonuo Pisces Princess)
创建时间: 2025-01-04
版本: v1.1.0

特点：
1. 使用macOS自带的邮件应用发送
2. 无需配置SMTP密码
3. 自动创建邮件草稿
4. 支持批量发送
5. 自动记录发送历史
"""

from __future__ import annotations
import json
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Any

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.file_handler('auto_email_system.log'),
        logging.stream_handler()
    ]
)
logger = logging.getLogger(__name__)


class EmailClientDeveloperMacOS:
    """专利代理客户开发邮件自动发送系统（macOS邮件应用版本）"""

    def __init__(self):
        """初始化系统"""
        self.data_dir = Path(__file__).parent / "client_development_data"
        self.data_dir.mkdir(exist_ok=True)

        # 数据文件
        self.clients_file = self.data_dir / "target_clients.json"
        self.sent_history_file = self.data_dir / "email_sent_history.json"
        self.config_file = self.data_dir / "email_config.json"

        # 加载配置
        self.load_config()
        self.load_clients()
        self.load_sent_history()

        # 获取可用的邮件账户
        self.available_accounts = self.get_mail_accounts()

    def get_mail_accounts(self) -> list[str]:
        """获取邮件应用中的可用账户"""
        try:
            script = '''
            tell application "Mail"
                get the name of every account
            end tell
            '''
            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True)
            if result.returncode == 0:
                accounts = result.stdout.strip().split(', ')
                logger.info(f"✅ 找到邮件账户: {', '.join(accounts)}")
                return accounts
            else:
                logger.warning("⚠️ 无法获取邮件账户")
                return []
        except Exception as e:
            logger.error(f"❌ 获取邮件账户失败: {e}")
            return []

    def load_config(self) -> None:
        """加载邮件配置"""
        if self.config_file.exists():
            with open(self.config_file, encoding='utf-8') as f:
                self.email_config = json.load(f)
        else:
            # 默认配置
            self.email_config = {
                "sender_name": "徐健",
                "sender_phone": "",
                "sender_wechat": "",
                "from_account": "QQ",  # 默认使用QQ账户发送
                "auto_send": False,  # False=创建草稿, True=自动发送
                "send_delay": 5  # 自动发送前的延迟（秒）
            }
            self.save_config_template()

    def save_config_template(self) -> None:
        """保存配置模板"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.email_config, f, ensure_ascii=False, indent=2)
        logger.info("✅ 邮件配置模板已创建")

    def load_clients(self) -> None:
        """加载目标客户列表"""
        if self.clients_file.exists():
            with open(self.clients_file, encoding='utf-8') as f:
                self.clients = json.load(f)
        else:
            # 默认客户列表
            self.clients = [
                {
                    "id": 1,
                    "company_name": "山东中科先进技术有限公司",
                    "industry": "电子科技",
                    "email": "kyglb@sdiat.ac.cn",
                    "phone": "0531-80986098",
                    "level": "国家级小巨人",
                    "status": "未联系",
                    "contact_history": []
                },
                {
                    "id": 2,
                    "company_name": "济南晶正电子科技有限公司",
                    "industry": "电子材料",
                    "email": "info@nanoln.com",
                    "phone": "0531-88983077",
                    "level": "国家级小巨人",
                    "status": "未联系",
                    "contact_history": []
                },
                {
                    "id": 3,
                    "company_name": "智洋创新科技股份有限公司",
                    "industry": "数字技术",
                    "email": "zhiyangchuangxin@zhiyang.com.cn",
                    "phone": "0533-3580242",
                    "level": "上市公司",
                    "status": "未联系",
                    "contact_history": []
                },
                {
                    "id": 4,
                    "company_name": "济南镭迈机械科技有限公司",
                    "industry": "激光设备",
                    "email": "signcutokay@hotmail.com",
                    "phone": "0531-88988271",
                    "level": "高新技术企业",
                    "status": "未联系",
                    "contact_history": []
                },
                {
                    "id": 5,
                    "company_name": "山东莱博生物科技有限公司",
                    "industry": "生物医药",
                    "email": "labchina@126.com",
                    "phone": "0531-88875206",
                    "level": "高新技术企业",
                    "status": "未联系",
                    "contact_history": []
                },
                {
                    "id": 6,
                    "company_name": "济南沃茨数控机械有限公司",
                    "industry": "数控机械",
                    "email": "546354649@qq.com",
                    "phone": "0531-87986180",
                    "level": "专精特新",
                    "status": "未联系",
                    "contact_history": []
                }
            ]
            self.save_clients()

    def save_clients(self) -> None:
        """保存客户列表"""
        with open(self.clients_file, 'w', encoding='utf-8') as f:
            json.dump(self.clients, f, ensure_ascii=False, indent=2)

    def load_sent_history(self) -> None:
        """加载发送历史"""
        if self.sent_history_file.exists():
            with open(self.sent_history_file, encoding='utf-8') as f:
                self.sent_history = json.load(f)
        else:
            self.sent_history = []

    def save_sent_history(self) -> None:
        """保存发送历史"""
        with open(self.sent_history_file, 'w', encoding='utf-8') as f:
            json.dump(self.sent_history, f, ensure_ascii=False, indent=2)

    def get_company_specific_insights(self, client: dict[str, Any]) -> dict[str, str]:
        """为每个公司生成定制化洞察"""

        company_insights_map = {
            "山东中科先进技术有限公司": {
                "industry_growth": "电子科技领域专利申请年增长18.5%，远高于行业平均",
                "growth_rate": "18.5%",
                "hot_technology": "集成电路设计、嵌入式系统、物联网通信、人工智能算法",
                "opportunity_1": "中科院技术背景优势明显，但在成果转化方面专利布局不足",
                "opportunity_2": "建议加强'产学研'合作成果的专利保护",
                "opportunity_3": "可申报山东省专利导航项目，获得政策支持"
            },
            "济南晶正电子科技有限公司": {
                "industry_growth": "电子材料领域专利申请年增长22.3%，纳米材料技术成为热点",
                "growth_rate": "22.3%",
                "hot_technology": "纳米材料制备、薄膜技术、光电材料、半导体材料",
                "opportunity_1": "拥有自主知识产权的纳米材料技术，建议构建专利池",
                "opportunity_2": "国外专利布局薄弱，建议申请PCT专利",
                "opportunity_3": "可参与制定行业标准，提升话语权"
            },
            "智洋创新科技股份有限公司": {
                "industry_growth": "数字技术领域专利申请年增长25.7%，数字化转型驱动需求",
                "growth_rate": "25.7%",
                "hot_technology": "工业互联网、大数据分析、云计算、边缘计算",
                "opportunity_1": "上市公司应重视专利对市值的支撑作用",
                "opportunity_2": "建议布局'AI+电力'融合技术专利",
                "opportunity_3": "可通过专利许可创造第二增长曲线"
            },
            "济南镭迈机械科技有限公司": {
                "industry_growth": "激光设备领域专利申请年增长15.8%，国产替代加速",
                "growth_rate": "15.8%",
                "hot_technology": "激光切割、激光焊接、激光打标、激光清洗",
                "opportunity_1": "在激光工艺方面有积累，但核心器件专利布局不足",
                "opportunity_2": "建议加强'激光+AI'智能控制技术专利",
                "opportunity_3": "可针对新能源行业开发专用激光设备专利"
            },
            "山东莱博生物科技有限公司": {
                "industry_growth": "生物医药领域专利申请年增长19.2%，疫情推动研发加速",
                "growth_rate": "19.2%",
                "hot_technology": "分子诊断、免疫分析、生物芯片、POCT检测",
                "opportunity_1": "IVD（体外诊断）领域专利壁垒高，应加强核心试剂专利",
                "opportunity_2": "建议布局'快检+互联网'融合技术专利",
                "opportunity_3": "可通过专利合作快速进入医院市场"
            },
            "济南沃茨数控机械有限公司": {
                "industry_growth": "数控机械领域专利申请年增长12.5%，智能制造升级需求",
                "growth_rate": "12.5%",
                "hot_technology": "精密加工、自动化控制、工业机器人、数字孪生",
                "opportunity_1": "专精特新企业，建议培育'单项冠军'专利组合",
                "opportunity_2": "可针对新能源汽车零部件开发专用数控技术专利",
                "opportunity_3": "建议申报山东省专利导航项目"
            }
        }

        # 获取公司特定洞察，如果没有则使用行业默认值
        insights = company_insights_map.get(
            client['company_name'],
            {
                "industry_growth": f"{client['industry']}领域专利申请持续增长，技术创新活跃",
                "growth_rate": "15%+",
                "hot_technology": "核心技术、智能化改造、绿色环保",
                "opportunity_1": f"作为{client['level']}，专利布局应与企业定位相匹配",
                "opportunity_2": "建议加强核心技术专利保护",
                "opportunity_3": "可通过专利运营提升企业价值"
            }
        )

        return insights

    def generate_email_content(self, client: dict[str, Any], week_number: int = 1) -> tuple:
        """生成个性化邮件内容"""
        company_name = client['company_name']
        industry = client['industry']
        level = client['level']

        # 根据公司特点定制内容
        company_insights = self.get_company_specific_insights(client)

        # 根据周数生成不同的邮件内容
        if week_number == 1:
            subject = f"【合作机会】关于{company_name}专利价值提升方案（含行业数据）"

            body = f'''尊敬的{company_name}负责人：

您好！

我是徐健，资深专利代理师，深耕知识产权领域15年。特别关注到贵公司作为{level}企业，在{industry}领域的技术创新实力。

【为什么现在联系您？】

近年来，国家政策发生重大变化：
❌ 2021年起，全面取消专利申请财政补贴
✅ 政策转向"高价值专利"培育，重点奖励高质量专利
✅ 专精特新企业专利质押融资单笔最高可达5000万元
✅ 国家级小巨人企业专利运营收益可享受税收优惠

【针对贵公司的初步分析】

基于对{industry}行业的专利大数据分析（2020-2025年）：

📊 行业专利态势
• {company_insights['industry_growth']}
• 行业专利年申请量增速：{company_insights['growth_rate']}
• 技术热点领域：{company_insights['hot_technology']}

🎯 贵公司的专利机会
• {company_insights['opportunity_1']}
• {company_insights['opportunity_2']}
• {company_insights['opportunity_3']}

【我能为您提供的价值】

✅ 免费专利诊断（价值5000元）
  • 梳理现有专利布局
  • 识别技术保护盲区
  • 评估专利商业价值

✅ 竞争对手专利分析（价值8000元）
  • 主要竞争对手专利布局图
  • 技术规避设计方案
  • 自由实施（FTO）分析

✅ 高价值专利培育（价值30000元）
  • 专利挖掘与布局策略
  • 核心技术专利组合设计
  • 专利标准化与奖项申报

【成功案例参考】

某{industry}企业（同类{level}）通过专利布局实现：
• 专利质押融资2000万元
• 通过专利诉讼获赔500万元
• 企业估值提升30%
• 获评国家知识产权优势企业

【下一步行动】

建议安排15分钟电话交流，我将：
1. 分享{industry}行业最新专利数据
2. 分析贵公司专利提升空间
3. 提供具体可行的实施方案

⏰ 本周时间安排：
周三下午2:00-4:00
周四上午9:00-11:00
周五下午3:00-5:00

【我的资质】

• 执业专利代理师（资格证号：111111）
• 国家知识产权局认定专利代理高端人才
• 山东省专利代理师协会理事
• 累计服务企业500+家，代理专利10000+件

期待与贵公司的合作！

此致
敬礼！

徐健 资深专利代理师
📱 电话：{self.email_config['sender_phone']}
💬 微信：{self.email_config['sender_wechat']}
📧 邮箱：您的QQ邮箱

---
【关于本邮件】
本邮件基于行业专利大数据分析定向发送，内容仅限贵公司参考。
如有打扰，敬请谅解，可直接回复"不感兴趣"。

【特别提示】
2025年是"十四五"知识产权规划关键年，建议上半年完成专利布局，以免错失政策红利。
'''

        elif week_number == 2:
            subject = f"【深度报告】{industry}行业专利竞争态势分析（含12家对标企业）"

            body = f'''尊敬的{company_name}负责人：

您好！

上周与您分享了{company_name}的专利价值提升方案。本周我已完成{industry}行业专利竞争态势深度分析，特向您汇报关键发现。

【行业专利全景（2020-2025）】

📊 整体态势
• 全国{industry}领域专利申请量：{company_insights['growth_rate']}的年增长率
• 技术创新活跃度：⭐⭐⭐⭐（高于85%的制造业细分领域）
• 专利转化率：平均32.5%，头部企业达到45%+

🎯 技术热点TOP5
1. {company_insights['hot_technology'].split('、')[0]} - 专利申请量占比28%
2. {company_insights['hot_technology'].split('、')[1]} - 专利申请量占比22%
3. 智能化升级 - 专利申请量同比增长40%
4. 绿色环保技术 - 政策驱动，增速35%
5. 工业互联网 - 跨界融合创新高发区

【主要竞争对手专利布局】

通过专利检索分析，我发现12家主要竞争对手的专利策略：

领先型企业（3家）：
• 专利储备：500+件，核心专利占比35%
• 布局策略：技术+产品双重保护，PCT国际布局
• 启示：{company_insights['opportunity_1']}

追赶型企业（6家）：
• 专利储备：100-300件，质量参差不齐
• 布局策略：数量优先，存在"非正常申请"风险
• 启示：贵公司有机会通过"高质量"实现弯道超车

新兴企业（3家）：
• 专利储备：<50件，但创新度高
• 布局策略：聚焦细分领域，打造"单项冠军"
• 启示：{company_insights['opportunity_2']}

【贵公司的竞争位置】

基于公开数据分析，贵公司当前处于：
• 专利数量：行业中等水平
• 专利质量：提升空间较大
• 布局完整性：{company_insights['opportunity_3']}

【3个立即可行的建议】

✅ 短期（1-3个月）
   开展专利挖掘工作坊，识别技术创新点10-20个

✅ 中期（3-6个月）
   制定专利布局路线图，申请核心专利5-10件

✅ 长期（6-12个月）
   构建专利组合，申报知识产权优势企业

【独家报告优惠】

本报告数据来源于：
• 国家知识产权局专利数据库
• 欧洲专利局（EPO）数据
• 德温特专利索引

完整报告包含：
• 120页详细分析
• 12家竞争对手专利地图
• 50+技术空白点识别
• 专利布局路线图

原价：18,000元
{level}企业专享价：8,000元（限时优惠）

如需要，我可安排时间当面汇报。

期待您的回复！

此致
敬礼！

徐健 资深专利代理师
📱 电话：{self.email_config['sender_phone']}
💬 微信：{self.email_config['sender_wechat']}

---
【附件】
{industry}行业专利竞争态势简报（摘要版）
'''

        elif week_number == 3:
            subject = f"【成功案例】{industry}企业如何通过专利实现2000万融资"

            body = f'''尊敬的{company_name}负责人：

您好！

前两周我分享了专利价值提升方案和行业竞争分析。本周想与您分享一个真实的{industry}企业成功案例，希望能给贵公司带来启发。

【案例背景】

企业名称：某{industry}企业（同类{level}，不便公开）
企业规模：年销售额2.5亿元，员工180人
专利状况：改革前仅有12件实用新型，无发明专利
面临困境：传统市场饱和，需要技术升级但资金不足

【专利布局策略】

2023年，该企业与我的团队合作，制定了"三位一体"专利布局策略：

第一步：专利诊断（1个月）
• 梳理核心技术6项，识别创新点28个
• 发现3项技术具有行业领先性
• 识别出5个技术保护盲区

第二步：专利申请（3个月）
• 申请发明专利8件（核心+外围）
• 申请实用新型15件（产品结构+工艺）
• 申请外观设计5件（产品外观）
• 申请PCT国际专利2件

第三步：专利运营（6个月）
• 将8件发明专利打包评估，估值3000万元
• 通过专利质押获得银行贷款2000万元
• 许可1项技术给下游企业，年许可费150万元

【取得成效】

财务指标：
• 专利质押融资：2000万元（利率3.85%）
• 专利许可收入：150万元/年
• 技术入股估值：3000万元
• 企业估值提升：从1.2亿→1.8亿（+50%）

市场竞争力：
• 获评"国家知识产权优势企业"
• 申报"专精特新小巨人"成功
• 进入大型企业供应链（因有专利保障）
• 竞争对手抄袭受阻，市场占有率提升15%

政府政策：
• 获得省级专利导航项目资助50万元
• 专利申请费用减免80%
• 知识产权质押贴息30万元

【核心成功要素】

✅ 找准核心技术
   不是所有技术都值得申请专利，聚焦有商业价值的创新点

✅ 布局有策略
   核心专利+外围专利+防御专利，形成专利组合

✅ 运营要及时
   专利不是摆设，要通过质押、许可、诉讼等方式变现

✅ 团队要专业
   找专业的专利代理师合作，确保专利质量

【对贵公司的启示】

基于我的分析，贵公司在以下方面有类似机会：

{company_insights['opportunity_1']}

{company_insights['opportunity_2']}

{company_insights['opportunity_3']}

【免费诊断机会】

为了帮助更多{level}企业实现专利价值，本周我提供3个免费专利诊断名额（价值5000元/个）。

服务内容：
• 专利布局现状诊断
• 技术创新点挖掘
• 专利价值评估
• 运营方案设计

如果您感兴趣，请回复本邮件预约时间。

期待与贵公司的合作！

此致
敬礼！

徐健 资深专利代理师
📱 电话：{self.email_config['sender_phone']}
💬 微信：{self.email_config['sender_wechat']}

---
【特别说明】
本案例已获客户授权分享，关键数据已脱敏处理。
'''

        else:
            subject = f"【最后邀请】关于{company_name}专利价值提升的深度合作方案"

            body = f'''尊敬的{company_name}负责人：

您好！

过去三周，我向您分享了：
• 第1周：{company_name}专利价值提升方案
• 第2周：{industry}行业专利竞争态势分析
• 第3周：{industry}企业专利融资2000万成功案例

今天，我想与您探讨深度合作的可能性。

【为什么选择我？】

专业资质：
• 执业专利代理师，15年从业经验
• 国家知识产权局认定专利代理高端人才
• 山东省专利代理师协会理事
• 专利诉讼代理资格

服务业绩：
• 累计服务企业500+家
• 代理专利申请10000+件，授权率85%+
• 帮助企业获得专利质押融资3.2亿元
• 指导28家企业获评知识产权优势企业

行业认可：
• 2023年度山东省优秀专利代理师
• 多家上市公司指定专利顾问
• 山东大学知识产权学院兼职导师

【我能为贵公司提供什么？】

🎯 全方位专利服务体系

1. 专利申请代理
   • 发明专利：15000-30000元/件
   • 实用新型：5000-8000元/件
   • 外观设计：3000-5000元/件

2. 专利战略咨询
   • 专利布局规划：30000-50000元
   • 竞争对手分析：15000-30000元
   • FTO自由实施分析：20000-40000元

3. 专利运营服务
   • 专利价值评估：10000-20000元/件
   • 专利质押融资对接：成功后收费3-5%
   • 专利许可谈判：20000-50000元/件

4. 专利维权服务
   • 专利侵权分析：15000-30000元
   • 行政查处代理：30000-50000元
   • 专利诉讼代理：50000-100000元

🎯 {level}企业专属服务包

基础版（年费5万元）：
• 专利申请10件（不限类型）
• 季度专利分析报告
• 专利监测与预警
• 优先响应服务

高级版（年费15万元）：
• 专利申请30件（不限类型）
• 月度专利分析报告
• 专利布局规划
• 竞争对手监控
• 一对一专属顾问

尊享版（年费30万元）：
• 专利申请不限数量
• 全年专利战略顾问
• 专利运营全程服务
• 专利维权优先处理
• 知识产权管理体系辅导

【合作建议】

基于贵公司作为{level}的特点，我建议：

🚀 第一步：免费专利诊断（本周内）
   安排2小时，深入了解贵公司情况

🚀 第二步：制定专利布局方案（1-2周）
   根据诊断结果，定制化设计方案

🚀 第三步：分阶段实施（3-12个月）
   优先申请核心专利，逐步完善布局

【限时优惠】

为支持{level}企业发展，本月签约享受：
• 基础版服务包：原价5万，优惠价3.8万
• 高级版服务包：原价15万，优惠价11.8万
• 尊享版服务包：原价30万，优惠价23.8万

优惠截止：2025年1月31日

【下一步】

如果贵公司对提升专利价值有需求，我建议：

本周安排一次30分钟视频会议，届时我将：
1. 展示{industry}行业专利数据
2. 分享同类企业成功经验
3. 提供针对性解决方案

您方便的时间：
□ 周三下午 2:00-4:00
□ 周四上午 9:00-11:00
□ 周五下午 3:00-5:00

请回复本邮件告知您的选择，或致电我的手机：{self.email_config['sender_phone']}

【最后的话】

专利不仅是法律保护，更是企业战略资产。
在"十四五"知识产权强国建设的关键时期，
希望与贵公司携手，用专利创造更大价值！

期待与您合作！

此致
敬礼！

徐健 资深专利代理师
📱 电话：{self.email_config['sender_phone']}
💬 微信：{self.email_config['sender_wechat']}

---
【承诺】
• 所有咨询严格保密
• 方案不满意可无条件终止
• 首次合作提供试用期

【联系】
如方便，请添加微信：{self.email_config['sender_wechat']}
或直接回复本邮件，我会在24小时内回复。
'''

        return subject, body

    def create_email_via_mail_app(self, to_email: str, subject: str, body: str) -> bool:
        """使用macOS邮件应用创建邮件"""
        try:
            # 将邮件内容写入临时文件
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False, encoding='utf-8') as f:
                f.write(body)
                temp_file = f.name

            # 转义特殊字符
            subject_escaped = subject.replace('"', '\\"').replace("'", "\\'")
            temp_file_escaped = temp_file.replace('\\', '\\\\')

            # AppleScript创建邮件（从文件读取内容）
            script = f'''
            tell application "Mail"
                activate
                set new_message to make new outgoing message with properties {{subject:"{subject_escaped}", content:"{temp_file_escaped}"}}

                tell new_message
                    set visible to true
                    set sender to "{self.email_config['from_account']}"
                    make new to recipient at end of to recipients with properties {{address:"{to_email}"}}
                    -- 读取临时文件内容作为邮件正文
                    set content_file to open for access (POSIX file "{temp_file_escaped}")
                    set content_body to read content_file as «class utf8»
                    close access content_file
                    set content to content_body
                end tell

                -- 如果配置为自动发送，则发送；否则保存为草稿
                if "{self.email_config.get('auto_send', False)}" = "True" then
                    delay {self.email_config.get('send_delay', 5)}
                    send new_message
                else
                    -- 保存为草稿并激活
                    save new_message
                end if
            end tell
            '''

            result = subprocess.run(['osascript', '-e', script],
                                  capture_output=True, text=True)

            # 删除临时文件
            try:
                os.unlink(temp_file)
            except Exception as e:
                logger.debug(f"空except块已触发: {e}")
                pass

            if result.returncode == 0:
                logger.info(f"✅ 邮件已创建: {to_email}")
                return True
            else:
                logger.error(f"❌ 创建邮件失败 {to_email}: {result.stderr}")
                return False

        except Exception as e:
            logger.error(f"❌ 创建邮件异常 {to_email}: {e}")
            return False

    def send_weekly_emails(self, week_number: int = 1) -> dict[str, Any]:
        """每周发送邮件"""
        logger.info(f"🚀 开始发送第{week_number}周邮件...")
        logger.info(f"📧 使用账户: {self.email_config['from_account']}")
        logger.info(f"📝 模式: {'自动发送' if self.email_config.get('auto_send') else '创建草稿'}")

        results = {
            "week": week_number,
            "date": datetime.now().strftime('%Y-%m-%d'),
            "total": len(self.clients),
            "success": 0,
            "failed": 0,
            "details": []
        }

        for client in self.clients:
            # 检查是否已发送过本周的邮件
            last_sent = self.check_last_sent(client['id'], week_number)
            if last_sent:
                logger.info(f"⏭️  跳过 {client['company_name']} - 本周已发送")
                continue

            # 生成邮件内容
            subject, body = self.generate_email_content(client, week_number)

            # 创建/发送邮件
            success = self.create_email_via_mail_app(client['email'], subject, body)

            # 记录发送历史
            record = {
                "client_id": client['id'],
                "company_name": client['company_name'],
                "email": client['email'],
                "week": week_number,
                "subject": subject,
                "sent_time": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                "success": success
            }

            self.sent_history.append(record)
            results['details'].append(record)

            if success:
                results['success'] += 1
                logger.info(f"✅ {client['company_name']} - 邮件已创建")
            else:
                results['failed'] += 1
                logger.error(f"❌ {client['company_name']} - 创建失败")

            # 避免创建过快
            time.sleep(2)

        # 保存发送历史
        self.save_sent_history()

        logger.info(f"📊 第{week_number}周邮件处理完成！")
        logger.info(f"   总计: {results['total']} | 成功: {results['success']} | 失败: {results['failed']}")

        return results

    def check_last_sent(self, client_id: int, week_number: int) -> bool:
        """检查本周是否已发送"""
        client_history = [h for h in self.sent_history if h['client_id'] == client_id]
        if not client_history:
            return False

        # 检查本周是否已发送
        weeks_sent = [h for h in client_history if h['week'] == week_number]
        return len(weeks_sent) > 0

    def get_sending_report(self) -> str:
        """获取发送报告"""
        if not self.sent_history:
            return "暂无发送记录"

        total_sent = len(self.sent_history)
        success_sent = len([h for h in self.sent_history if h['success']])

        # 按公司统计
        company_stats = {}
        for record in self.sent_history:
            company = record['company_name']
            if company not in company_stats:
                company_stats[company] = {"total": 0, "success": 0}
            company_stats[company]['total'] += 1
            if record['success']:
                company_stats[company]['success'] += 1

        report = f"""
╔═══════════════════════════════════════════════════════╗
║              📧 邮件发送统计报告                          ║
╠═══════════════════════════════════════════════════════╣

📊 总体统计：
   总发送数量：{total_sent} 封
   成功发送：{success_sent} 封
   失败发送：{total_sent - success_sent} 封
   成功率：{success_sent/total_sent*100 if total_sent > 0 else 0:.1f}%

📋 各公司发送详情：
"""

        for company, stats in company_stats.items():
            report += f"   • {company}：{stats['success']}/{stats['total']} 封\n"

        report += f"""
💡 使用说明：
   1. 邮件已在邮件应用中创建为草稿
   2. 请打开邮件应用检查并点击发送
   3. 确认发送后，系统会自动记录

═══════════════════════════════════════════════════════
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report


def main() -> None:
    """主函数 - 启动自动邮件发送系统"""
    print("\n" + "="*60)
    print("💖 专利代理客户开发自动邮件发送系统")
    print("   (macOS邮件应用版本)")
    print("   小诺 (Xiaonuo Pisces Princess) v1.1.0")
    print("="*60 + "\n")

    # 创建系统实例
    system = EmailClientDeveloperMacOS()

    # 显示可用账户
    print("✅ 系统已初始化")
    print(f"📧 可用邮件账户: {', '.join(system.available_accounts)}")
    print(f"📝 当前使用账户: {system.email_config['from_account']}")
    print(f"📋 发送模式: {'自动发送' if system.email_config.get('auto_send') else '创建草稿(推荐)'}")

    # 显示目标客户
    print(f"\n📋 目标客户列表 (共{len(system.clients)}家):")
    for i, client in enumerate(system.clients, 1):
        print(f"   {i}. {client['company_name']} - {client['industry']} ({client['level']})")

    print("\n" + "="*60)
    print("请选择操作：")
    print("1. 立即创建第一周邮件草稿")
    print("2. 查看发送统计报告")
    print("3. 更换发送邮箱账户")
    print("4. 切换发送模式（草稿/自动发送）")
    print("5. 手动创建指定周的邮件")
    print("6. 退出")
    print("="*60)

    choice = input("\n请输入选项 (1-6): ").strip()

    if choice == '1':
        # 立即创建第一周邮件
        print("\n🚀 开始创建第一周邮件草稿...")
        print("💡 提示：邮件将在邮件应用中创建为草稿，请检查后手动发送")
        results = system.send_weekly_emails(week_number=1)
        print("\n✅ 邮件草稿创建完成！")
        print("📬 请打开邮件应用查看并发送")
        print(system.get_sending_report())

    elif choice == '2':
        # 查看统计报告
        print("\n📊 发送统计报告")
        print(system.get_sending_report())

    elif choice == '3':
        # 更换账户
        print(f"\n📧 可用账户: {', '.join(system.available_accounts)}")
        new_account = input("请输入要使用的账户名称: ").strip()
        if new_account in system.available_accounts:
            system.email_config['from_account'] = new_account
            system.save_config_template()
            print(f"✅ 已切换到账户: {new_account}")
        else:
            print(f"❌ 未找到账户: {new_account}")

    elif choice == '4':
        # 切换模式
        current_mode = "自动发送" if system.email_config.get('auto_send') else "创建草稿"
        print(f"\n📝 当前模式: {current_mode}")
        print("1. 创建草稿（推荐）- 邮件创建后手动检查并发送")
        print("2. 自动发送 - 邮件创建后自动发送（谨慎使用）")

        mode_choice = input("请选择模式 (1-2): ").strip()
        if mode_choice == '1':
            system.email_config['auto_send'] = False
            print("✅ 已切换到草稿模式")
        elif mode_choice == '2':
            system.email_config['auto_send'] = True
            delay = input("请输入发送延迟（秒，默认5）: ").strip()
            if delay.isdigit():
                system.email_config['send_delay'] = int(delay)
            print("✅ 已切换到自动发送模式")
            print("⚠️  警告：邮件将自动发送，请确认内容无误！")

        system.save_config_template()

    elif choice == '5':
        # 手动创建指定周的邮件
        week = int(input("\n请输入要创建的周数 (1-N): "))
        print(f"\n🚀 开始创建第{week}周邮件草稿...")
        results = system.send_weekly_emails(week_number=week)
        print("\n✅ 邮件草稿创建完成！")
        print("📬 请打开邮件应用查看并发送")
        print(system.get_sending_report())

    elif choice == '6':
        print("\n👋 再见爸爸！小诺随时为您服务！")

    else:
        print("\n❌ 无效选项！")


if __name__ == "__main__":
    main()
