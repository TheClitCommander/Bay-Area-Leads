"""
Data Manager for handling file organization and preventing duplicates
"""
import os
import shutil
import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union

class DataManager:
    def __init__(self, base_dir: str = None):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.base_dir = Path(base_dir or Path.home() / 'CascadeProjects/MidcoastLeads/data')
        self.structure = {
            'raw': {
                'commitment_books': {},
                'tax_maps': {},
                'sales_books': {},
                'gis_data': {}
            },
            'processed': {
                'properties': {},
                'assessments': {},
                'maps': {}
            },
            'temp': {}
        }
        self.manifest_file = self.base_dir / 'manifest.json'
        self.initialize_structure()
        
    def initialize_structure(self):
        """Initialize directory structure and manifest"""
        try:
            # Create base directory structure
            for category in self.structure:
                category_dir = self.base_dir / category
                category_dir.mkdir(parents=True, exist_ok=True)
                for subcategory in self.structure[category]:
                    (category_dir / subcategory).mkdir(exist_ok=True)
            
            # Initialize or load manifest
            if self.manifest_file.exists():
                with open(self.manifest_file, 'r') as f:
                    self.structure = json.load(f)
            else:
                self._save_manifest()
                
            self.logger.info(f"Initialized data structure at {self.base_dir}")
        except Exception as e:
            self.logger.error(f"Error initializing data structure: {str(e)}")
            raise
            
    def _save_manifest(self):
        """Save current structure to manifest file"""
        with open(self.manifest_file, 'w') as f:
            json.dump(self.structure, f, indent=2)
            
    def _compute_file_hash(self, file_path: Union[str, Path]) -> str:
        """Compute SHA-256 hash of file"""
        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
        
    def add_file(self, file_path: Union[str, Path], category: str, 
                 subcategory: str, metadata: Dict = None) -> Dict:
        """
        Add a file to the managed structure
        
        Args:
            file_path: Path to the file to add
            category: Main category (raw, processed, temp)
            subcategory: Subcategory within main category
            metadata: Additional metadata about the file
            
        Returns:
            Dict with file information including new path
        """
        try:
            file_path = Path(file_path)
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Compute file hash
            file_hash = self._compute_file_hash(file_path)
            
            # Check for duplicates
            for cat in self.structure:
                for subcat in self.structure[cat]:
                    for existing in self.structure[cat][subcat].values():
                        if existing.get('hash') == file_hash:
                            self.logger.warning(f"Duplicate file found: {existing['path']}")
                            return existing
            
            # Prepare new file location
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{file_path.name}"
            new_path = self.base_dir / category / subcategory / new_filename
            
            # Copy file to new location
            shutil.copy2(file_path, new_path)
            
            # Update manifest
            file_info = {
                'original_name': file_path.name,
                'path': str(new_path),
                'hash': file_hash,
                'added_date': datetime.now().isoformat(),
                'metadata': metadata or {}
            }
            
            self.structure[category][subcategory][new_filename] = file_info
            self._save_manifest()
            
            self.logger.info(f"Added file {file_path.name} to {category}/{subcategory}")
            return file_info
            
        except Exception as e:
            self.logger.error(f"Error adding file {file_path}: {str(e)}")
            raise
            
    def get_file(self, category: str, subcategory: str, filename: str) -> Optional[Dict]:
        """Get file information from the manifest"""
        try:
            return self.structure[category][subcategory].get(filename)
        except KeyError:
            return None
            
    def list_files(self, category: str = None, subcategory: str = None) -> List[Dict]:
        """List files in specified category/subcategory"""
        files = []
        if category and subcategory:
            return list(self.structure[category][subcategory].values())
        elif category:
            for subcat in self.structure[category]:
                files.extend(self.structure[category][subcat].values())
        else:
            for cat in self.structure:
                for subcat in self.structure[cat]:
                    files.extend(self.structure[cat][subcat].values())
        return files
        
    def cleanup_temp(self, hours: int = 24):
        """Clean up temporary files older than specified hours"""
        try:
            now = datetime.now()
            temp_files = self.list_files('temp')
            
            for file_info in temp_files:
                file_date = datetime.fromisoformat(file_info['added_date'])
                if (now - file_date).total_seconds() > hours * 3600:
                    file_path = Path(file_info['path'])
                    if file_path.exists():
                        file_path.unlink()
                    del self.structure['temp'][file_path.name]
                    
            self._save_manifest()
            self.logger.info(f"Cleaned up temporary files older than {hours} hours")
            
        except Exception as e:
            self.logger.error(f"Error cleaning up temp files: {str(e)}")
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup_temp()
