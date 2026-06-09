from datetime import datetime
import time
from typing import List, Callable, Optional
from dataclasses import dataclass
from services.file_parser import FileParser, ParsedFile
from services.mail_sender import MailSender, SMTPConfig, MailTemplate
from models.recipient_mapping import RecipientMappingRepository
from models.category import CategoryRepository
from utils.template import TemplateRenderer
from db.database import db

# Delay in seconds between consecutive SMTP sends. Helps avoid rate limiting
# by mail servers (e.g. Aliyun) that may silently drop CC recipients on
# rapid-fire sends.
SEND_INTERVAL_SECONDS = 2


@dataclass
class SendResult:
    filename: str
    owner_name: str
    status: str  # "成功", "跳过", "失败"
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
        global_template = MailSender.get_template()  # For signature only
        
        if not config:
            if progress_callback:
                progress_callback("错误: 请先配置SMTP设置")
            return results
        
        mapping_cache = {}  # (category_id, owner_name) -> mapping
        
        for pf in parsed_files:
            # Skip files with parse errors
            if pf.status == "解析失败" or not pf.category_id:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner or "",
                    status="跳过",
                    error_message=pf.error_message or "无分类"
                )
                results.append(result)
                TaskService.log_send_result(result)
                if progress_callback:
                    progress_callback(f"[跳过] {pf.filename}: {pf.error_message or '无分类'}")
                continue
            
            # Skip files without owner
            if not pf.owner:
                result = SendResult(
                    filename=pf.filename,
                    owner_name="",
                    status="跳过",
                    error_message="无法从文件名提取owner"
                )
                results.append(result)
                TaskService.log_send_result(result)
                if progress_callback:
                    progress_callback(f"[跳过] {pf.filename}: 无法从文件名提取owner")
                continue
            
            # Look up mapping by category_id AND owner_name
            cache_key = (pf.category_id, pf.owner)
            if cache_key not in mapping_cache:
                mapping = RecipientMappingRepository.get_by_category_and_owner(pf.category_id, pf.owner)
                mapping_cache[cache_key] = mapping
            else:
                mapping = mapping_cache[cache_key]
            
            # Skip if no mapping found for this owner
            if not mapping:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner,
                    status="跳过",
                    error_message=f"分类 '{pf.category_name}' 下未找到 owner '{pf.owner}' 的收件人映射"
                )
                results.append(result)
                TaskService.log_send_result(result)
                if progress_callback:
                    progress_callback(f"[跳过] {pf.filename}: 分类 '{pf.category_name}' 下未找到 owner '{pf.owner}' 的收件人映射")
                continue
            
            recipient = mapping.recipient
            cc_emails = [c.email for c in mapping.cc_contacts]
            
            # Get category for templates
            category = CategoryRepository.get_by_id(pf.category_id)
            if category:
                subject = TemplateRenderer.render_subject(pf.owner or '', pf.month or '', category.subject_template)
                body = TemplateRenderer.render(
                    pf.owner or '', 
                    pf.month or '', 
                    category.body_template, 
                    global_template.signature
                )
            else:
                # Fallback to default
                subject = f"{pf.month}月绩效数据结果"
                body = TemplateRenderer.render(
                    pf.owner or '', 
                    pf.month or '', 
                    '@{owner} 这是{month}月的绩效数据结果，请查收。', 
                    global_template.signature
                )
            
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
                    owner_name=pf.owner or '',
                    status="成功"
                )
                if progress_callback:
                    progress_callback(f"[成功] {pf.filename} -> {recipient.email}")
            else:
                result = SendResult(
                    filename=pf.filename,
                    owner_name=pf.owner or '',
                    status="失败",
                    error_message=error
                )
                if progress_callback:
                    progress_callback(f"[失败] {pf.filename}: {error}")
            
            results.append(result)
            TaskService.log_send_result(result)

            # Add delay between sends to avoid rate limiting by mail servers
            # that may silently drop CC recipients on rapid-fire sends.
            if SEND_INTERVAL_SECONDS > 0:
                time.sleep(SEND_INTERVAL_SECONDS)
        
        return results
