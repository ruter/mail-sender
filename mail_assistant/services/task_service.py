from datetime import datetime
from typing import List, Callable, Optional
from dataclasses import dataclass
from services.file_parser import FileParser, ParsedFile
from services.mail_sender import MailSender, SMTPConfig, MailTemplate
from models.recipient_mapping import RecipientMappingRepository
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
        
        mapping_cache = {}
        
        for pf in parsed_files:
            if pf.status == "解析失败" or not pf.category_id:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner or "",
                    status="失败",
                    error_message=pf.error_message or "无分类"
                )
                results.append(result)
                TaskService.log_send_result(result)
                if progress_callback:
                    progress_callback(f"[跳过] {pf.filename}: {pf.error_message or '无分类'}")
                continue
            
            if pf.category_id not in mapping_cache:
                mapping = RecipientMappingRepository.get_by_category_id(pf.category_id)
                mapping_cache[pf.category_id] = mapping
            else:
                mapping = mapping_cache[pf.category_id]
            
            if not mapping:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner or "",
                    status="失败",
                    error_message=f"未配置分类 '{pf.category_name}' 的收件人映射"
                )
                results.append(result)
                TaskService.log_send_result(result)
                if progress_callback:
                    progress_callback(f"[跳过] {pf.filename}: 未配置分类 '{pf.category_name}' 的收件人映射")
                continue
            
            recipient = mapping.recipient
            cc_emails = [c.email for c in mapping.cc_contacts]
            
            subject = f"{pf.month}月绩效数据结果"
            body = TemplateRenderer.render(pf.owner, pf.month, template.body_template, template.signature)
            
            success, error = MailSender.send_email(
                to_email=recipient.email,
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
                    progress_callback(f"[成功] {pf.filename} -> {recipient.email}")
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
