"""
Performance optimization utilities for property data extraction
"""
from typing import Dict, List, Set, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import lru_cache
import re
from datetime import datetime
import logging
from collections import defaultdict

class PerformanceOptimizer:
    def __init__(self, max_workers: int = 4, cache_size: int = 1000):
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.cache_size = cache_size
        self.stats = defaultdict(list)
        
        # Initialize thread pool
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        
    def process_pages_parallel(self, pages: List[str], process_func) -> List[Dict]:
        """Process PDF pages in parallel"""
        futures = []
        results = []
        
        try:
            # Submit tasks
            for page in pages:
                future = self.executor.submit(process_func, page)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.extend(result)
                except Exception as e:
                    self.logger.error(f"Error processing page: {str(e)}")
                    
        except Exception as e:
            self.logger.error(f"Error in parallel processing: {str(e)}")
            
        return results
        
    @lru_cache(maxsize=1000)
    def parse_text_cached(self, text: str) -> Dict:
        """Cached text parsing to avoid redundant processing"""
        # This is a placeholder for the actual parsing logic
        return {}
        
    def batch_process(self, items: List[Dict], process_func, batch_size: int = 100) -> List[Dict]:
        """Process items in batches for better memory management"""
        results = []
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            try:
                batch_results = process_func(batch)
                results.extend(batch_results)
            except Exception as e:
                self.logger.error(f"Error processing batch {i//batch_size}: {str(e)}")
                
        return results
        
    def optimize_regex(self, patterns: Dict[str, str]) -> Dict[str, re.Pattern]:
        """Optimize regex patterns for better performance"""
        optimized = {}
        for name, pattern in patterns.items():
            try:
                # Add common optimizations
                if pattern.startswith('^'):
                    # Pattern matches start, can use match() instead of search()
                    optimized[name] = re.compile(pattern, re.MULTILINE)
                else:
                    # Add word boundary if helpful
                    if not pattern.startswith('\\b') and not pattern.startswith('.*'):
                        pattern = '\\b' + pattern
                    optimized[name] = re.compile(pattern)
            except Exception as e:
                self.logger.error(f"Error optimizing pattern {name}: {str(e)}")
                optimized[name] = re.compile(pattern)  # Use original as fallback
                
        return optimized
        
    def track_performance(self, operation: str, start_time: datetime):
        """Track performance metrics for operations"""
        elapsed = (datetime.now() - start_time).total_seconds()
        self.stats[operation].append(elapsed)
        
    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        stats = {}
        for operation, times in self.stats.items():
            if times:
                stats[operation] = {
                    'min': min(times),
                    'max': max(times),
                    'avg': sum(times) / len(times),
                    'count': len(times)
                }
        return stats
        
    def cleanup(self):
        """Cleanup resources"""
        self.executor.shutdown(wait=True)
        self.parse_text_cached.cache_clear()
        
class PropertyTextChunker:
    """Efficient text chunking for property data"""
    
    def __init__(self, chunk_size: int = 1000):
        self.chunk_size = chunk_size
        self.chunks = []
        
    def chunk_text(self, text: str) -> List[str]:
        """Split text into manageable chunks while preserving property boundaries"""
        chunks = []
        current_chunk = []
        current_size = 0
        
        for line in text.split('\n'):
            line_size = len(line)
            
            # Check if adding this line would exceed chunk size
            if current_size + line_size > self.chunk_size and current_chunk:
                chunks.append('\n'.join(current_chunk))
                current_chunk = []
                current_size = 0
                
            current_chunk.append(line)
            current_size += line_size
            
        # Add final chunk
        if current_chunk:
            chunks.append('\n'.join(current_chunk))
            
        return chunks
        
    def find_property_boundaries(self, text: str) -> List[tuple]:
        """Find property record boundaries in text"""
        boundaries = []
        start = 0
        
        # Simple property boundary detection
        # This should be customized based on actual format
        for match in re.finditer(r'(?m)^(?:\d{5,7}|PROPERTY\s+RECORD)', text):
            if start != match.start():
                boundaries.append((start, match.start()))
            start = match.start()
            
        # Add final boundary
        if start != len(text):
            boundaries.append((start, len(text)))
            
        return boundaries
        
    def extract_properties(self, text: str) -> List[str]:
        """Extract individual property records"""
        boundaries = self.find_property_boundaries(text)
        return [text[start:end].strip() for start, end in boundaries]
