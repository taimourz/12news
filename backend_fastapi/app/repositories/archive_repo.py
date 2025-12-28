from pathlib import Path
from typing import Optional
from datetime import datetime
import aiofiles
from app.models.archive import DayArchive
from app.config import settings

class ArchiveRepository:
    def __init__(self):
        self.data_dir = settings.DATA_DIR
        self.data_dir.mkdir(exist_ok=True)
    
    async def save(self, archive: DayArchive) -> None:
        file_path = self.data_dir / f"{archive.date}.json"
        async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
            await f.write(archive.model_dump_json(indent=2))
    
    async def load(self, date_string: str) -> Optional[DayArchive]:
        file_path = self.data_dir / f"{date_string}.json"
        if not file_path.exists():
            return None
        
        async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
            content = await f.read()
            return DayArchive.model_validate_json(content)
    
    async def delete_old_files(self, before_date: str) -> int:
        try:
            cutoff_date = datetime.strptime(before_date, '%Y-%m-%d')
        except ValueError:
            raise ValueError(f"Invalid date format: {before_date}. Expected YYYY-MM-DD")
        
        deleted_count = 0
        
        if not self.data_dir.exists():
            return deleted_count
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                file_date_str = file_path.stem
                file_date = datetime.strptime(file_date_str, '%Y-%m-%d')
                
                if file_date < cutoff_date:
                    file_path.unlink()
                    deleted_count += 1
                    print(f"Deleted old file: {file_path.name}")
                    
            except ValueError:
                print(f"Skipping non-date file: {file_path.name}")
                continue
            except Exception as e:
                print(f"Error deleting {file_path.name}: {e}")
                continue
        
        return deleted_count
    
    async def delete_all_files(self) -> tuple[int, list[dict]]:
        deleted_count = 0
        errors = []
        
        if not self.data_dir.exists():
            return deleted_count, errors
        
        for file_path in self.data_dir.glob("*.json"):
            try:
                file_path.unlink()
                deleted_count += 1
            except Exception as e:
                errors.append({
                    "file": file_path.name,
                    "error": str(e)
                })
        
        return deleted_count, errors
    
    async def list_all_dates(self) -> list[str]:
        if not self.data_dir.exists():
            return []
        
        dates = []
        for file_path in self.data_dir.glob("*.json"):
            try:
                datetime.strptime(file_path.stem, '%Y-%m-%d')
                dates.append(file_path.stem)
            except ValueError:
                continue
        
        return sorted(dates)
    
    async def file_exists(self, date_string: str) -> bool:
        file_path = self.data_dir / f"{date_string}.json"
        return file_path.exists()
    
    async def get_file_size(self, date_string: str) -> int | None:
        file_path = self.data_dir / f"{date_string}.json"
        if not file_path.exists():
            return None
        return file_path.stat().st_size