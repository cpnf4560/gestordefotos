"""
Image scanner and comparison module.
Handles image hashing, metadata extraction, and duplicate detection.
"""

import os
import hashlib
import json
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import imagehash
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ImageInfo:
    """Stores image metadata and hashes."""
    path: str
    filename: str
    filesize: int
    md5: str
    phash: str
    resolution: Tuple[int, int]
    date_modified: str
    exif_date: Optional[str] = None
    
    def to_dict(self):
        return asdict(self)


class ImageScanner:
    """Scans and analyzes images in a directory."""
    
    SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    CACHE_FILE = '.image_cache.json'
    
    def __init__(self, folder_path: str):
        self.folder_path = Path(folder_path)
        self.images: List[ImageInfo] = []
        self.duplicates: Dict[str, List[ImageInfo]] = {}
        self.cache_path = self.folder_path / self.CACHE_FILE
        
    def scan(self, use_cache: bool = True) -> List[ImageInfo]:
        """
        Scan folder for images and extract metadata.
        
        Args:
            use_cache: Use cached hashes if available
            
        Returns:
            List of ImageInfo objects
        """
        if use_cache and self.cache_path.exists():
            logger.info("Loading from cache...")
            self.images = self._load_cache()
            return self.images
        
        self.images = []
        image_files = self._get_image_files()
        logger.info(f"Found {len(image_files)} images. Processing...")
        
        for idx, img_path in enumerate(image_files, 1):
            try:
                info = self._extract_image_info(img_path)
                self.images.append(info)
                logger.info(f"[{idx}/{len(image_files)}] {img_path.name}")
            except Exception as e:
                logger.error(f"Error processing {img_path}: {e}")
        
        self._save_cache()
        return self.images
    
    def find_duplicates(self, similarity_threshold: float = 0.9) -> Dict:
        """
        Find duplicate and similar images.
        
        Args:
            similarity_threshold: 0-1, threshold for considering images similar
            
        Returns:
            Dict with groups of duplicates
        """
        if not self.images:
            raise ValueError("No images scanned yet. Run scan() first.")
        
        groups = {}
        used = set()
        
        # First pass: exact MD5 matches
        for i, img1 in enumerate(self.images):
            if img1.md5 in used:
                continue
                
            group = [img1]
            for img2 in self.images[i+1:]:
                if img2.md5 == img1.md5:
                    group.append(img2)
            
            if len(group) > 1:
                key = f"exact_{img1.md5[:8]}"
                groups[key] = {
                    'type': 'exact',
                    'images': group,
                    'similarity': 1.0
                }
                used.update(img.md5 for img in group)
        
        # Second pass: perceptual hash matches
        phash_groups = {}
        for img in self.images:
            if img.md5 in used:
                continue
            
            found = False
            for existing_phash, group_data in phash_groups.items():
                similarity = self._phash_similarity(img.phash, existing_phash)
                if similarity >= similarity_threshold:
                    group_data['images'].append(img)
                    group_data['similarity'] = similarity
                    found = True
                    break
            
            if not found:
                phash_groups[img.phash] = {
                    'images': [img],
                    'similarity': 1.0
                }
        
        # Add to results
        for phash_val, group_data in phash_groups.items():
            if len(group_data['images']) > 1:
                key = f"similar_{phash_val[:8]}"
                group_data['type'] = 'similar'
                groups[key] = group_data
                used.update(img.md5 for img in group_data['images'])
        
        self.duplicates = groups
        return groups
    
    def _get_image_files(self) -> List[Path]:
        """Get all image files from folder (recursive)."""
        if not self.folder_path.exists():
            raise FileNotFoundError(f"Folder not found: {self.folder_path}")
        
        images = []
        for ext in self.SUPPORTED_FORMATS:
            images.extend(self.folder_path.rglob(f'*{ext}'))
            images.extend(self.folder_path.rglob(f'*{ext.upper()}'))
        
        return sorted(set(images))  # Remove duplicates from list
    
    def _extract_image_info(self, img_path: Path) -> ImageInfo:
        """Extract all relevant information from image."""
        # File stats
        filesize = img_path.stat().st_size
        mod_time = datetime.fromtimestamp(img_path.stat().st_mtime).isoformat()
        
        # MD5 hash
        md5 = self._calculate_md5(img_path)
        
        # Open image
        with Image.open(img_path) as img:
            # Perceptual hash
            phash = str(imagehash.phash(img))
            
            # Resolution
            resolution = img.size
            
            # EXIF date
            exif_date = self._extract_exif_date(img)
        
        return ImageInfo(
            path=str(img_path),
            filename=img_path.name,
            filesize=filesize,
            md5=md5,
            phash=phash,
            resolution=resolution,
            date_modified=mod_time,
            exif_date=exif_date
        )
    
    def _calculate_md5(self, file_path: Path) -> str:
        """Calculate MD5 hash of file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def _extract_exif_date(self, pil_image: Image.Image) -> Optional[str]:
        """Extract date taken from EXIF."""
        try:
            exif = pil_image._getexif()
            if not exif:
                return None
            
            for tag_id, value in exif.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == 'DateTime':
                    return str(value)
        except Exception:
            pass
        
        return None
    
    def _phash_similarity(self, phash1: str, phash2: str) -> float:
        """Calculate similarity between two perceptual hashes (0-1)."""
        if len(phash1) != len(phash2):
            return 0.0
        
        # Count differing bits
        diff_bits = sum(c1 != c2 for c1, c2 in zip(phash1, phash2))
        max_bits = len(phash1)
        
        # Convert to similarity score
        similarity = 1.0 - (diff_bits / max_bits)
        return similarity
    
    def _save_cache(self):
        """Save image info to cache file."""
        try:
            cache_data = [img.to_dict() for img in self.images]
            with open(self.cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            logger.info(f"Cache saved to {self.cache_path}")
        except Exception as e:
            logger.error(f"Failed to save cache: {e}")
    
    def _load_cache(self) -> List[ImageInfo]:
        """Load image info from cache file."""
        try:
            with open(self.cache_path, 'r') as f:
                data = json.load(f)
            
            images = []
            for item in data:
                # Verify file still exists
                if Path(item['path']).exists():
                    info = ImageInfo(**item)
                    images.append(info)
            
            logger.info(f"Loaded {len(images)} images from cache")
            return images
        except Exception as e:
            logger.error(f"Failed to load cache: {e}")
            return []
    
    def delete_images(self, file_paths: List[str]):
        """
        Safely delete images.
        
        Args:
            file_paths: List of file paths to delete
        """
        deleted = []
        errors = []
        
        for path in file_paths:
            try:
                Path(path).unlink()
                deleted.append(path)
                logger.info(f"Deleted: {path}")
                
                # Remove from cache
                self.images = [img for img in self.images if img.path != path]
            except Exception as e:
                errors.append((path, str(e)))
                logger.error(f"Failed to delete {path}: {e}")
        
        if deleted:
            self._save_cache()
        
        return deleted, errors
