import smtplib
import socket
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.utils import formatdate, make_msgid

from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path
from db.database import db


@dataclass
class SMTPConfig:
    smtp_server: str
    port: int
    sender_email: str
    password: str


@dataclass
class MailTemplate:
    body_template: str
    signature: str


class MailSender:
    @staticmethod
    def get_config() -> Optional[SMTPConfig]:
        conn = db.get_connection()
        try:
            cursor = conn.execute(
                "SELECT smtp_server, port, sender_email, password FROM smtp_config LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                return SMTPConfig(
                    smtp_server=row['smtp_server'],
                    port=row['port'],
                    sender_email=row['sender_email'],
                    password=row['password']
                )
            return None
        finally:
            conn.close()
    
    @staticmethod
    def save_config(config: SMTPConfig) -> None:
        conn = db.get_connection()
        try:
            conn.execute("DELETE FROM smtp_config")
            conn.execute(
                "INSERT INTO smtp_config (smtp_server, port, sender_email, password) VALUES (?, ?, ?, ?)",
                (config.smtp_server, config.port, config.sender_email, config.password)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def get_template() -> MailTemplate:
        conn = db.get_connection()
        try:
            cursor = conn.execute("SELECT body_template, signature FROM mail_template LIMIT 1")
            row = cursor.fetchone()
            if row:
                return MailTemplate(body_template=row['body_template'], signature=row['signature'])
            return MailTemplate(body_template="@{owner} 这是{month}月的绩效数据结果，请查收。", signature="")
        finally:
            conn.close()
    
    @staticmethod
    def save_template(template: MailTemplate) -> None:
        conn = db.get_connection()
        try:
            conn.execute("DELETE FROM mail_template")
            conn.execute(
                "INSERT INTO mail_template (body_template, signature) VALUES (?, ?)",
                (template.body_template, template.signature)
            )
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    @staticmethod
    def _build_message(
        to_email: str,
        normalized_cc: List[str],
        subject: str,
        body: str,
        attachment_path: str,
        sender_email: str,
    ) -> MIMEMultipart:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        if normalized_cc:
            msg['Cc'] = ', '.join(normalized_cc)
        msg['Subject'] = subject
        msg['Message-ID'] = make_msgid(domain=sender_email.split('@')[-1])
        msg['Date'] = formatdate(localtime=True)

        msg.attach(MIMEText(body, 'html', 'utf-8'))

        file_path = Path(attachment_path)
        if file_path.exists():
            with open(file_path, 'rb') as f:
                part = MIMEBase('application', 'vnd.openxmlformats-officedocument.spreadsheetml.sheet')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                filename = file_path.name
                part.add_header(
                    'Content-Disposition',
                    'attachment',
                    filename=('utf-8', '', filename)
                )
                msg.attach(part)
        return msg

    @staticmethod
    def _connect_smtp(config: SMTPConfig) -> smtplib.SMTP:
        if config.port == 465:
            server = smtplib.SMTP_SSL(config.smtp_server, config.port, timeout=30)
        else:
            server = smtplib.SMTP(config.smtp_server, config.port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        server.login(config.sender_email, config.password)
        return server

    @staticmethod
    def send_email(
        to_email: str,
        cc_emails: List[str],
        subject: str,
        body: str,
        attachment_path: str,
        config: SMTPConfig,
        max_retries: int = 2,
    ) -> tuple[bool, Optional[str]]:
        """Send an email with retry logic for partial recipient refusal.

        Some mail servers (e.g. Aliyun) may refuse CC recipients due to
        rate limiting. When this happens, ``sendmail()`` returns a dict of
        refused addresses without raising an exception. We detect this and
        retry up to ``max_retries`` times with exponential backoff.
        """

        # Normalize CC emails: flatten any comma-separated strings and
        # strip whitespace to ensure each entry is a single address.
        normalized_cc: List[str] = []
        for addr in cc_emails:
            for part in addr.split(','):
                part = part.strip()
                if part:
                    normalized_cc.append(part)

        all_recipients = [to_email] + normalized_cc
        msg = MailSender._build_message(
            to_email=to_email,
            normalized_cc=normalized_cc,
            subject=subject,
            body=body,
            attachment_path=attachment_path,
            sender_email=config.sender_email,
        )
        # Use max_header_len=0 to prevent the generator from folding
        # long header lines (e.g. Cc with many addresses), which can
        # cause some mail servers to mis-parse the recipient list.
        raw_message = msg.as_string(maxheaderlen=0)

        last_error: Optional[str] = None
        pending_recipients = list(all_recipients)

        for attempt in range(max_retries + 1):
            try:
                server = MailSender._connect_smtp(config)
                try:
                    refused = server.sendmail(
                        config.sender_email, pending_recipients, raw_message
                    )
                finally:
                    server.quit()

                if refused:
                    refused_addrs = ', '.join(refused.keys())
                    last_error = f"以下收件人被邮件服务器拒绝: {refused_addrs}"
                    # On retry, only re-send to the refused recipients.
                    # The MIME headers (To, Cc) stay unchanged so the
                    # displayed email is identical, but the envelope
                    # shrinks to avoid duplicating delivery to addresses
                    # that were already accepted.
                    pending_recipients = list(refused.keys())
                    if attempt < max_retries:
                        time.sleep(2 ** attempt)
                        continue
                    return False, last_error

                return True, None
            except Exception as e:
                last_error = str(e)
                if attempt < max_retries:
                    time.sleep(2 ** attempt)
                    continue
                return False, last_error

        return False, last_error
    
    @staticmethod
    def test_connection(config: SMTPConfig) -> tuple[bool, Optional[str]]:
        try:
            sock = socket.create_connection((config.smtp_server, config.port), timeout=10)
            sock.close()
        except socket.timeout:
            return False, f"无法连接到 {config.smtp_server}:{config.port}（超时），请检查网络或使用代理"
        except socket.gaierror:
            return False, f"无法解析服务器地址 {config.smtp_server}"
        except ConnectionRefusedError:
            return False, f"连接被拒绝 {config.smtp_server}:{config.port}"
        except Exception as e:
            return False, f"网络连接失败: {e}"
        
        server = None
        try:
            if config.port == 465:
                server = smtplib.SMTP_SSL(config.smtp_server, config.port, timeout=30)
            else:
                server = smtplib.SMTP(config.smtp_server, config.port, timeout=30)
            
            server.set_debuglevel(0)
            code, msg = server.ehlo()
            if code != 250:
                return False, f"EHLO失败: {code} {msg.decode()}"
            
            if config.port != 465:
                if server.has_extn('STARTTLS'):
                    code, msg = server.starttls()
                    if code != 220:
                        return False, f"STARTTLS失败: {code} {msg.decode()}"
                    server.ehlo()
                else:
                    return False, "服务器不支持STARTTLS"
            
            server.login(config.sender_email, config.password)
            return True, None
        except smtplib.SMTPAuthenticationError as e:
            return False, f"认证失败: {e.smtp_error.decode() if isinstance(e.smtp_error, bytes) else e.smtp_error}"
        except smtplib.SMTPConnectError as e:
            return False, f"连接失败: {e}"
        except TimeoutError:
            return False, "连接超时，请检查网络或服务器地址"
        except Exception as e:
            return False, f"{type(e).__name__}: {str(e)}"
        finally:
            if server:
                try:
                    server.quit()
                except:
                    pass
