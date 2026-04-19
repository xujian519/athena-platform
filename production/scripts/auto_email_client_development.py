#!/usr/bin/env python3
"""
专利代理客户开发自动邮件发送系统
Patent Agency Client Development Auto Email System

作者: 小诺 (Xiaonuo Pisces Princess)
创建时间: 2025-01-04
版本: v1.0.0

功能：
1. 自动给目标客户发送个性化邮件
2. 每周定时发送
3. 跟踪发送记录
4. 避免重复发送
"""

from __future__ import annotations
import json
import logging
import smtplib
import time
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

import schedule

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


class EmailClientDeveloper:
    """专利代理客户开发邮件自动发送系统"""

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

    def load_config(self) -> None:
        """加载邮件配置"""
        if self.config_file.exists():
            with open(self.config_file, encoding='utf-8') as f:
                self.email_config = json.load(f)
        else:
            # 默认配置模板
            self.email_config = {
                "smtp_server": "smtp.qq.com",  # QQ邮箱
                "smtp_port": 587,
                "sender_email": "",  # 需要填写
                "sender_password": "",  # 需要填写（QQ邮箱使用授权码）
                "sender_name": "专利代理师",
                "sender_phone": "",
                "sender_wechat": ""
            }
            self.save_config_template()

    def save_config_template(self) -> None:
        """保存配置模板"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.email_config, f, ensure_ascii=False, indent=2)
        logger.info("✅ 邮件配置模板已创建，请填写配置文件！")

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

    def generate_email_content(self, client: dict[str, Any], week_number: int = 1) -> tuple:
        """生成个性化邮件内容"""
        company_name = client['company_name']
        industry = client['industry']
        level = client['level']

        # 根据周数生成不同的邮件内容
        if week_number == 1:
            subject = f"【专利服务】关于{company_name}的专利布局和技术保护建议"
            body = f'''尊敬的{company_name}负责人：

您好！

我是专业的专利代理师，关注到贵公司作为{level}企业，在{industry}领域具有强大的技术实力。

经过初步分析，我发现贵公司在相关技术领域可能存在专利布局机会。我可以为您提供：

✅ 免费专利诊断报告
✅ 竞争对手专利分析
✅ 专利挖掘与布局策略
✅ 高价值专利培育方案

期待与您进一步交流，为贵公司的技术创新保驾护航！

此致
敬礼！

专利代理师：{self.email_config['sender_name']}
电话：{self.email_config['sender_phone']}
微信：{self.email_config['sender_wechat']}
邮箱：{self.email_config['sender_email']}

---
本邮件由专利代理客户开发系统自动发送
如需人工服务，请直接回复或电话联系
'''

        elif week_number == 2:
            subject = f"【专利分析】{company_name}的竞争对手专利布局情况"
            body = f'''尊敬的{company_name}负责人：

您好！

上周我向您介绍了专利保护的重要性。今天想和您分享一些关于{industry}行业专利布局的最新情况。

通过对{industry}行业的专利分析，我发现：

📊 行业专利申请趋势
📊 主要竞争对手的专利布局
📊 技术热点的专利分布

如果您感兴趣，我可以为您生成一份详细的行业专利分析报告，帮助贵公司制定更有效的专利策略。

期待您的回复！

此致
敬礼！

专利代理师：{self.email_config['sender_name']}
电话：{self.email_config['sender_phone']}
微信：{self.email_config['sender_wechat']}
邮箱：{self.email_config['sender_email']}
'''

        elif week_number == 3:
            subject = f"【案例分享】{industry}行业专利保护成功案例"
            body = f'''尊敬的{company_name}负责人：

您好！

前两周我向您介绍了专利保护的重要性和行业分析。今天想和您分享一个{industry}行业的专利保护成功案例。

📚 案例背景：
某{industry}企业通过系统的专利布局，成功：
- 保护了核心技术
- 阻止了竞争对手抄袭
- 提升了企业估值
- 增强了市场竞争力

💡 启示：
对于像贵公司这样的{level}企业，专利保护不仅是法律手段，更是重要的战略资产。

如果需要了解更多案例详情，欢迎随时联系我！

此致
敬礼！

专利代理师：{self.email_config['sender_name']}
电话：{self.email_config['sender_phone']}
微信：{self.email_config['sender_wechat']}
邮箱：{self.email_config['sender_email']}
'''

        else:
            subject = "【服务跟进】专利保护服务建议"
            body = f'''尊敬的{company_name}负责人：

您好！

感谢您关注我之前发送的专利保护相关信息。

作为专业的专利代理师，我深知{industry}企业的技术保护需求。我已服务过多家{level}企业，在专利申请、布局、维权等方面有丰富经验。

本周我想和您探讨一下：
🎯 贵公司当前的专利保护状况
🎯 可能存在的专利布局机会
🎯 如何通过专利提升企业价值

如果您方便的话，我希望能安排一次10-15分钟的电话交流，为贵公司提供免费的专利保护建议。

期待您的回复！

此致
敬礼！

专利代理师：{self.email_config['sender_name']}
电话：{self.email_config['sender_phone']}
微信：{self.email_config['sender_wechat']}
邮箱：{self.email_config['sender_email']}
'''

        return subject, body

    def send_email(self, to_email: str, subject: str, body: str) -> bool:
        """发送邮件"""
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = f"{self.email_config['sender_name']} <{self.email_config['sender_email']}>"
            msg['To'] = to_email
            msg['Subject'] = subject

            # 添加邮件正文
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)

            # 连接SMTP服务器
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                server.send_message(msg)

            logger.info(f"✅ 邮件发送成功: {to_email}")
            return True

        except Exception as e:
            logger.error(f"❌ 邮件发送失败 {to_email}: {e}")
            return False

    def send_weekly_emails(self, week_number: int = 1) -> dict[str, Any]:
        """每周发送邮件"""
        logger.info(f"🚀 开始发送第{week_number}周邮件...")

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

            # 发送邮件
            success = self.send_email(client['email'], subject, body)

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
                logger.info(f"✅ {client['company_name']} - 邮件发送成功")
            else:
                results['failed'] += 1
                logger.error(f"❌ {client['company_name']} - 邮件发送失败")

            # 避免发送过快
            time.sleep(30)  # 每30秒发送一封

        # 保存发送历史
        self.save_sent_history()

        logger.info(f"📊 第{week_number}周邮件发送完成！")
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
💡 建议：
   1. 成功率低的公司，建议电话跟进
   2. 每周定时发送，保持联系
   3. 根据客户回复及时调整策略

═══════════════════════════════════════════════════════
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""

        return report


def main() -> None:
    """主函数 - 启动自动邮件发送系统"""
    print("\n" + "="*60)
    print("💖 专利代理客户开发自动邮件发送系统")
    print("   Patent Agency Client Development Auto Email System")
    print("   小诺 (Xiaonuo Pisces Princess) v1.0.0")
    print("="*60 + "\n")

    # 创建系统实例
    system = EmailClientDeveloper()

    # 检查配置
    if not system.email_config['sender_email'] or not system.email_config['sender_password']:
        print("❌ 请先配置邮件信息！")
        print(f"\n📝 配置文件位置: {system.config_file}")
        print("\n请填写以下信息：")
        print("1. sender_email: 您的邮箱地址")
        print("2. sender_password: 邮箱密码或授权码（QQ邮箱使用授权码）")
        print("3. sender_name: 您的姓名")
        print("4. sender_phone: 您的电话")
        print("5. sender_wechat: 您的微信号")
        print("\n配置完成后，重新运行此程序！")
        return

    print("✅ 邮件配置已加载")
    print(f"   发件人: {system.email_config['sender_name']}")
    print(f"   邮箱: {system.email_config['sender_email']}")

    # 显示目标客户
    print(f"\n📋 目标客户列表 (共{len(system.clients)}家):")
    for i, client in enumerate(system.clients, 1):
        print(f"   {i}. {client['company_name']} - {client['industry']} ({client['level']})")

    print("\n" + "="*60)
    print("请选择操作：")
    print("1. 立即发送第一周邮件")
    print("2. 查看发送统计报告")
    print("3. 设置每周定时发送")
    print("4. 手动发送指定周的邮件")
    print("5. 退出")
    print("="*60)

    choice = input("\n请输入选项 (1-5): ").strip()

    if choice == '1':
        # 立即发送第一周邮件
        print("\n🚀 开始发送第一周邮件...")
        results = system.send_weekly_emails(week_number=1)
        print("\n✅ 发送完成！")
        print(system.get_sending_report())

    elif choice == '2':
        # 查看统计报告
        print("\n📊 发送统计报告")
        print(system.get_sending_report())

    elif choice == '3':
        # 设置定时发送
        print("\n⏰ 设置每周定时发送")
        print("建议：每周二上午10:00发送邮件")

        # 使用schedule库设置定时任务
        schedule.every().tuesday.at("10:00").do(
            system.send_weekly_emails,
            week_number=datetime.now().isocalendar()[1]  # 当前周数
        )

        print("✅ 定时任务已设置！每周二上午10:00自动发送邮件")
        print("💡 提示：请保持此程序运行，或使用systemd/cron配置自启动")

        print("\n程序将持续运行，按Ctrl+C退出...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n👋 程序已停止")

    elif choice == '4':
        # 手动发送指定周的邮件
        week = int(input("\n请输入要发送的周数 (1-N): "))
        print(f"\n🚀 开始发送第{week}周邮件...")
        results = system.send_weekly_emails(week_number=week)
        print("\n✅ 发送完成！")
        print(system.get_sending_report())

    elif choice == '5':
        print("\n👋 再见爸爸！小诺随时为您服务！")

    else:
        print("\n❌ 无效选项！")


if __name__ == "__main__":
    main()
