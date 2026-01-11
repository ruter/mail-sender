import os
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple
from pathlib import Path


@dataclass
class ParsedFile:
    filepath: str
    filename: str
    owner: Optional[str]
    month: Optional[str]
    category_id: Optional[int]
    category_name: Optional[str]
    status: str
    error_message: Optional[str] = None


class FileParser:
    @staticmethod
    def parse_filename_with_pattern(filename: str, pattern: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        try:
            regex = re.compile(pattern)
            match = regex.match(filename)
            if match:
                groups = match.groups()
                owner = groups[0].strip() if len(groups) > 0 else None
                month = groups[1] if len(groups) > 1 else None
                return owner, month, None
        except re.error:
            pass
        return None, None, "文件名格式不匹配"
    
    @staticmethod
    def scan_directory(directory: str) -> List[ParsedFile]:
        from models.category import CategoryRepository
        
        results = []
        path = Path(directory)
        
        if not path.exists():
            return results
        
        xlsx_files = list(path.glob("*.xlsx"))
        categories = CategoryRepository.get_all()
        
        for file_path in xlsx_files:
            filename = file_path.name
            matched = False
            
            for category in categories:
                owner, month, error = FileParser.parse_filename_with_pattern(filename, category.pattern)
                if not error:
                    results.append(ParsedFile(
                        filepath=str(file_path),
                        filename=filename,
                        owner=owner,
                        month=month,
                        category_id=category.id,
                        category_name=category.name,
                        status="待发送"
                    ))
                    matched = True
                    break
            
            if not matched:
                results.append(ParsedFile(
                    filepath=str(file_path),
                    filename=filename,
                    owner=None,
                    month=None,
                    category_id=None,
                    category_name=None,
                    status="解析失败",
                    error_message="没有匹配的分类规则"
                ))
        
        return results
