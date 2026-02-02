#!/usr/bin/env python3
"""
邮件通知工具
统一处理邮件发送功能
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging
from datetime import datetime

from core.config import config
from utils.logger import ScriptLogger


@dataclass
class EmailConfig:
    """邮件配置"""
    smtp_server: str
    smtp_port: int
    username: str
    password: str
    use_tls: bool = True
    from_email: str = None
    from_name: str = None


class EmailNotifier:
    """邮件通知器"""

    def __init__(self, email_config: EmailConfig = None):
        self.logger = ScriptLogger("EmailNotifier")
        self.config = email_config or self._load_email_config()
        self.smtp = None

    def _load_email_config(self) -> EmailConfig:
        """加载邮件配置"""
        # 从配置文件加载
        email_config = config.get('email', {})

        # 默认配置
        default_config = EmailConfig(
            smtp_server='smtp.gmail.com',
            smtp_port=587,
            username='',
            password='',
            use_tls=True
        )

        # 合并配置
        if email_config:
            default_config.smtp_server = email_config.get('smtp_server', default_config.smtp_server)
            default_config.smtp_port = email_config.get('smtp_port', default_config.smtp_port)
            default_config.username = email_config.get('username', '')
            default_config.password = email_config.get('password', '')
            default_config.use_tls = email_config.get('use_tls', default_config.use_tls)
            default_config.from_email = email_config.get('from_email', default_config.username)
            default_config.from_name = email_config.get('from_name', 'Athena Platform')

        return default_config

    def connect(self) -> Any:
        """连接SMTP服务器"""
        try:
            self.smtp = smtplib.SMTP(self.config.smtp_server, self.config.smtp_port)

            if self.config.use_tls:
                self.smtp.starttls()

            if self.config.username and self.config.password:
                self.smtp.login(self.config.username, self.config.password)

            self.logger.info("SMTP服务器连接成功")
            return True

        except Exception as e:
            self.logger.error(f"连接SMTP服务器失败: {e}")
            return False

    def disconnect(self) -> Any:
        """断开SMTP连接"""
        if self.smtp:
            try:
                self.smtp.quit()
                self.logger.info("SMTP连接已关闭")
            except:
                pass
            finally:
                self.smtp = None

    def send_email(self, to_emails: List[str], subject: str, body: str,
                   html_body: str = None, attachments: Optional[List[str] = None,
                   cc_emails: Optional[List[str] = None, bcc_emails: Optional[List[str] = None) -> bool:
        """发送邮件"""
        if not self.smtp:
            if not self.connect():
                return False

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.config.from_name} <{self.config.from_email}>"
            msg['To'] = ', '.join(to_emails)

            if cc_emails:
                msg['Cc'] = ', '.join(cc_emails)

            # 添加文本内容
            text_part = MIMEText(body, 'plain', 'utf-8')
            msg.attach(text_part)

            # 添加HTML内容
            if html_body:
                html_part = MIMEText(html_body, 'html', 'utf-8')
                msg.attach(html_part)

            # 添加附件
            if attachments:
                for file_path in attachments:
                    if os.path.exists(file_path):
                        self._add_attachment(msg, file_path)
                    else:
                        self.logger.warning(f"附件不存在: {file_path}")

            # 发送邮件
            all_emails = to_emails + (cc_emails or []) + (bcc_emails or [])
            self.smtp.send_message(msg, to_addrs=all_emails)

            self.logger.info(f"邮件发送成功: {subject} -> {', '.join(to_emails)}")
            return True

        except Exception as e:
            self.logger.error(f"发送邮件失败: {e}")
            return False

    def _add_attachment(self, msg: MIMEMultipart, file_path: str) -> Any:
        """添加附件"""
        try:
            with open(file_path, 'rb') as f:
                # 创建附件
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())

            # 编码附件
            encoders.encode_base64(part)

            # 添加附件头
            filename = os.path.basename(file_path)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )

            msg.attach(part)

        except Exception as e:
            self.logger.error(f"添加附件失败 {file_path}: {e}")

    def send_template_email(self, template_name: str, to_emails: List[str],
                           variables: Dict[str, Any] = None,
                           attachments: Optional[List[str] = None) -> bool:
        """发送模板邮件"""
        # 获取邮件模板
        templates = {
            'deployment_success': {
                'subject': 'Athena平台部署成功通知',
                'body': '''您好，

Athena平台已成功部署。

部署信息：
- 配置名称: {config_name}
- 版本: {version}
- 环境: {environment}
- 部署时间: {deploy_time}

谢谢！
Athena平台自动化系统
'''
            },
            'deployment_failed': {
                'subject': 'Athena平台部署失败通知',
                'body': '''您好，

Athena平台部署失败。

部署信息：
- 配置名称: {config_name}
- 版本: {version}
- 环境: {environment}
- 失败时间: {deploy_time}
- 错误信息: {error}

请及时处理！

谢谢！
Athena平台自动化系统
'''
            },
            'service_alert': {
                'subject': 'Athena平台服务告警',
                'body': '''您好，

检测到Athena平台服务异常。

告警信息：
- 服务名称: {service_name}
- 告警级别: {alert_level}
- 告警信息: {message}
- 发生时间: {alert_time}

请及时处理！

谢谢！
Athena平台监控系统
'''
            }
        }

        template = templates.get(template_name)
        if not template:
            self.logger.error(f"邮件模板不存在: {template_name}")
            return False

        # 替换变量
        variables = variables or {}
        subject = template['subject'].format(**variables)
        body = template['body'].format(**variables)

        # 发送邮件
        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=body,
            attachments=attachments
        )

    def send_report(self, to_emails: List[str], report_title: str,
                   report_content: str, report_file: str = None) -> bool:
        """发送报告邮件"""
        subject = f"{report_title} - {report_title}"

        body = f'''您好，

{report_title}

{report_content}

请查看附件了解详情。

谢谢！
Athena平台自动化系统
'''

        attachments = [report_file] if report_file and os.path.exists(report_file) else None

        return self.send_email(
            to_emails=to_emails,
            subject=subject,
            body=body,
            attachments=attachments
        )


# 全局实例
email_notifier = EmailNotifier()


# 装饰器：发送邮件通知
def email_notification_on_success(recipients: List[str],
                                 subject: str = "任务完成通知",
                                 message: str = "任务已成功完成"):
    """任务成功时发送邮件通知的装饰器"""
    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            try:
                result = func(*args, **kwargs)
                # 任务成功，发送邮件
                email_notifier.send_email(
                    to_emails=recipients,
                    subject=subject,
                    body=f"{message}\n\n执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                return result
            except Exception as e:
                # 任务失败，不发送邮件
                raise
        return wrapper
    return decorator


def email_notification_on_failure(recipients: List[str],
                                 subject: str = "任务失败通知"):
    """任务失败时发送邮件通知的装饰器"""
    def decorator(func) -> None:
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # 任务失败，发送邮件
                email_notifier.send_email(
                    to_emails=recipients,
                    subject=subject,
                    body=f"任务执行失败！\n\n错误信息: {str(e)}\n\n执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                raise
        return wrapper
    return decorator