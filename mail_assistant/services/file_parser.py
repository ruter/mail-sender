import os
import re
from dataclasses import dataclass
from typing import List, Optional
from pathlib import Path


@dataclass
class ParsedFile:
    filepath: str
    filename: str
    owner: Optional[str]
    month: Optional[str]
    status: str
    error_message: Optional[str] = None


class FileParser:
    FILENAME_PATTERN = re.compile(r'^(.+?)\s*-\s*(\d+)月绩效考勤系数&名单\.xlsx$')
    
    @staticmethod
    def parse_filename(filename: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        match = FileParser.FILENAME_PATTERN.match(filename)
        if match:
            owner = match.group(1).strip()
            month = match.group(2)
            return owner, month, None
        return None, None, "文件名格式不匹配"
    
    @staticmethod
    def scan_directory(directory: str) -> List[ParsedFile]:
        results = []
        path = Path(directory)
        
        if not path.exists():
            return results
        
        xlsx_files = list(path.glob("*.xlsx"))
        
        for file_path in xlsx_files:
            filename = file_path.name
            owner, month, error = FileParser.parse_filename(filename)
            
            if error:
                results.append(ParsedFile(
                    filepath=str(file_path),
                    filename=filename,
                    owner=None,
                    month=None,
                    status="解析失败",
                    error_message=error
                ))
            else:
                results.append(ParsedFile(
                    filepath=str(file_path),
                    filename=filename,
                    owner=owner,
                    month=month,
                    status="待发送"
                ))
        
        return results
