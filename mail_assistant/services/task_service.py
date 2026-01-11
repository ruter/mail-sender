from datetime import datetime
from typing import List, Callable, Optional
from dataclasses import dataclass
from services.file_parser import FileParser, ParsedFile
from services.mail_sender import MailSender, SMTPConfig, MailTemplate
from models.contact import ContactRepository
from models.cc_mapping import CCMappingRepository
from utils.template import TemplateRenderer
from db.database import db


@dataclass
class SendResult:
    filename: str
    owner_name: str
    status: str
    error_message: Optional[str] = None


class TaskService:
    @staticmethod
    def log_send_result(result: SendResult) -> None:
        conn = db.get_connection()
        try:
            conn.execute(
                """INSERT INTO send_logs (filename, owner_name, status, error_message, created_at) 
                   VALUES (?, ?, ?, ?, ?)""",
                (result.filename, result.owner_name, result.status, result.error_message, datetime.now())
            )
            conn.commit()
        finally:
            conn.close()
    
    @staticmethod
    def process_files(
        parsed_files: List[ParsedFile],
        progress_callback: Optional[Callable[[str], None]] = None
    ) -> List[SendResult]:
        results = []
        config = MailSender.get_config()
        template = MailSender.get_template()
        
        if not config:
            if progress_callback:
                progress_callback("错误: 请先配置SMTP设置")
            return results
        
        for pf in parsed_files:
            if pf.status == "解析失败":
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner or "",
                    status="失败",
                    error_message=pf.error_message
                )
                results.append(result)
                TaskService.log_send_result(result)
                if progress_callback:
                    progress_callback(f"[跳过] {pf.filename}: {pf.error_message}")
                continue
            
            contact = ContactRepository.get_by_name(pf.owner)
            if not contact:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner,
                    status="失败",
                    error_message=f"未找到联系人: {pf.owner}"
                )
                results.append(result)
                TaskService.log_send_result(result)
                if progress_callback:
                    progress_callback(f"[失败] {pf.filename}: 未找到联系人 {pf.owner}")
                continue
            
            cc_contacts = CCMappingRepository.get_cc_contacts(pf.owner)
            cc_emails = [c.email for c in cc_contacts]
            
            subject = f"{pf.month}月绩效数据结果"
            body = TemplateRenderer.render(pf.owner, pf.month, template.body_template, template.signature)
            
            success, error = MailSender.send_email(
                to_email=contact.email,
                cc_emails=cc_emails,
                subject=subject,
                body=body,
                attachment_path=pf.filepath,
                config=config
            )
            
            if success:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner,
                    status="成功"
                )
                if progress_callback:
                    progress_callback(f"[成功] {pf.filename} -> {contact.email}")
            else:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner,
                    status="失败",
                    error_message=error
                )
                if progress_callback:
                    progress_callback(f"[失败] {pf.filename}: {error}")
            
            results.append(result)
            TaskService.log_send_result(result)
        
        return results
