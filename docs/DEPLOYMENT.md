# Deployment and Scaling Guide

## System Requirements

### Hardware Requirements
- CPU: 4+ cores recommended for parallel processing
- RAM: 16GB+ recommended for large datasets
- Storage: 100GB+ for data and model storage
- GPU: Optional, but recommended for deep learning models

### Software Requirements
- Python 3.8+
- PostgreSQL 13+
- Redis (optional, for caching)
- Docker (optional, for containerization)
- CUDA Toolkit (if using GPU)

## Installation

### 1. Basic Installation
```bash
# Clone repository
git clone https://github.com/yourusername/MidcoastLeads.git
cd MidcoastLeads

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install system dependencies
# On macOS:
brew install wkhtmltopdf
brew install postgresql
brew install redis  # Optional

# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install -y wkhtmltopdf
sudo apt-get install -y postgresql
sudo apt-get install -y redis-server  # Optional
```

### 2. Docker Installation
```dockerfile
# Dockerfile
FROM python:3.8-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run application
CMD ["python", "main.py"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DB_HOST=db
      - DB_PORT=5432
      - DB_NAME=midcoast_leads
      - DB_USER=user
      - DB_PASSWORD=password
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=midcoast_leads
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:6
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

## Configuration

### 1. Environment Variables
```bash
# .env
# API Keys
PROPERTY_API_KEY=your_api_key
TAX_API_KEY=your_api_key
PERMIT_API_KEY=your_api_key

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=midcoast_leads
DB_USER=user
DB_PASSWORD=password

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Processing
MAX_WORKERS=4
BATCH_SIZE=100
CACHE_TTL=3600

# Analysis
MIN_CONFIDENCE_SCORE=0.7
MAX_CLUSTER_DISTANCE=0.5
SIMILARITY_THRESHOLD=0.8

# Paths
DATA_DIR=/path/to/data
CACHE_DIR=/path/to/cache
MODEL_DIR=/path/to/models
```

### 2. Application Configuration
```python
# config/default.py
config = {
    'processing': {
        'max_workers': 4,
        'batch_size': 100,
        'cache_ttl': 3600
    },
    'analysis': {
        'min_confidence': 0.7,
        'max_distance': 0.5,
        'similarity_threshold': 0.8
    },
    'visualization': {
        'map_zoom': 12,
        'chart_height': 600,
        'chart_width': 800
    }
}
```

## Scaling Strategies

### 1. Horizontal Scaling
- Deploy multiple application instances
- Use load balancer for request distribution
- Implement session management
- Use distributed caching
- Implement database replication

Example Kubernetes configuration:
```yaml
# kubernetes/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: midcoast-leads
spec:
  replicas: 3
  selector:
    matchLabels:
      app: midcoast-leads
  template:
    metadata:
      labels:
        app: midcoast-leads
    spec:
      containers:
      - name: midcoast-leads
        image: midcoast-leads:latest
        resources:
          requests:
            memory: "1Gi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: midcoast-config
              key: db_host
```

### 2. Vertical Scaling
- Increase CPU cores
- Add more RAM
- Use faster storage
- Optimize database indexes
- Implement caching

Example Redis caching:
```python
import redis
from functools import lru_cache

# Initialize Redis
redis_client = redis.Redis(
    host=os.getenv('REDIS_HOST'),
    port=int(os.getenv('REDIS_PORT')),
    db=int(os.getenv('REDIS_DB'))
)

def cache_key(*args, **kwargs):
    """Generate cache key"""
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}:{v}" for k, v in sorted(kwargs.items()))
    return ":".join(key_parts)

def redis_cache(ttl=3600):
    """Redis cache decorator"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            key = cache_key(func.__name__, *args, **kwargs)
            
            # Try to get from cache
            result = redis_client.get(key)
            if result:
                return json.loads(result)
            
            # Calculate result
            result = func(*args, **kwargs)
            
            # Store in cache
            redis_client.setex(
                key,
                ttl,
                json.dumps(result)
            )
            
            return result
        return wrapper
    return decorator
```

### 3. Data Partitioning
- Implement database sharding
- Use time-based partitioning
- Implement geographic partitioning
- Use content-based partitioning
- Implement custom partitioning strategies

Example database sharding:
```python
class ShardedDatabase:
    def __init__(self, shard_count=3):
        self.shard_count = shard_count
        self.shards = [
            Database(f"shard_{i}")
            for i in range(shard_count)
        ]
    
    def get_shard(self, key):
        """Get appropriate shard for key"""
        shard_index = hash(key) % self.shard_count
        return self.shards[shard_index]
    
    def insert(self, key, data):
        """Insert data into appropriate shard"""
        shard = self.get_shard(key)
        return shard.insert(key, data)
    
    def query(self, key):
        """Query data from appropriate shard"""
        shard = self.get_shard(key)
        return shard.query(key)
```

## Performance Optimization

### 1. Database Optimization
- Create appropriate indexes
- Optimize queries
- Implement connection pooling
- Use database specific optimizations
- Monitor and tune performance

Example index creation:
```sql
-- Create indexes for common queries
CREATE INDEX idx_property_location ON properties (latitude, longitude);
CREATE INDEX idx_property_value ON properties (total_value);
CREATE INDEX idx_property_type ON properties (property_type);
CREATE INDEX idx_transaction_date ON transactions (date);
```

### 2. Caching Strategies
- Implement multiple cache levels
- Use appropriate cache invalidation
- Monitor cache hit rates
- Optimize cache sizes
- Implement preemptive caching

Example multi-level cache:
```python
class MultiLevelCache:
    def __init__(self):
        self.memory_cache = {}
        self.redis_cache = redis.Redis()
        self.disk_cache = DiskCache()
    
    def get(self, key):
        # Try memory cache
        if key in self.memory_cache:
            return self.memory_cache[key]
        
        # Try Redis cache
        value = self.redis_cache.get(key)
        if value:
            self.memory_cache[key] = value
            return value
        
        # Try disk cache
        value = self.disk_cache.get(key)
        if value:
            self.memory_cache[key] = value
            self.redis_cache.set(key, value)
            return value
        
        return None
    
    def set(self, key, value):
        self.memory_cache[key] = value
        self.redis_cache.set(key, value)
        self.disk_cache.set(key, value)
```

### 3. Code Optimization
- Use appropriate data structures
- Implement parallel processing
- Optimize algorithms
- Use profiling tools
- Monitor memory usage

Example parallel processing:
```python
from concurrent.futures import ThreadPoolExecutor
import threading

class ParallelProcessor:
    def __init__(self, max_workers=4):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.lock = threading.Lock()
    
    def process_batch(self, items):
        results = []
        futures = []
        
        # Submit tasks
        for item in items:
            future = self.executor.submit(self.process_item, item)
            futures.append(future)
        
        # Collect results
        for future in futures:
            try:
                result = future.result()
                with self.lock:
                    results.append(result)
            except Exception as e:
                logging.error(f"Error processing item: {str(e)}")
        
        return results
```

## Monitoring and Maintenance

### 1. Logging
- Implement structured logging
- Use appropriate log levels
- Rotate log files
- Monitor log patterns
- Set up alerts

Example logging configuration:
```python
import logging
import logging.handlers
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        if record.exc_info:
            log_record['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # File handler
    file_handler = logging.handlers.RotatingFileHandler(
        'app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
```

### 2. Monitoring
- Monitor system resources
- Track performance metrics
- Monitor error rates
- Set up alerting
- Implement health checks

Example monitoring setup:
```python
from prometheus_client import Counter, Histogram, start_http_server

# Define metrics
REQUEST_COUNT = Counter(
    'request_count',
    'Number of requests processed',
    ['endpoint']
)
PROCESSING_TIME = Histogram(
    'processing_time_seconds',
    'Time spent processing request',
    ['endpoint']
)
ERROR_COUNT = Counter(
    'error_count',
    'Number of errors encountered',
    ['type']
)

def monitor_request(endpoint):
    """Monitor request processing"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            REQUEST_COUNT.labels(endpoint=endpoint).inc()
            
            with PROCESSING_TIME.labels(endpoint=endpoint).time():
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    ERROR_COUNT.labels(type=type(e).__name__).inc()
                    raise
        return wrapper
    return decorator
```

### 3. Backup and Recovery
- Implement regular backups
- Test recovery procedures
- Monitor backup success
- Implement point-in-time recovery
- Document recovery procedures

Example backup script:
```python
import subprocess
from datetime import datetime

def backup_database():
    """Backup PostgreSQL database"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backup_{timestamp}.sql"
    
    try:
        # Create backup
        subprocess.run([
            'pg_dump',
            '-h', os.getenv('DB_HOST'),
            '-U', os.getenv('DB_USER'),
            '-d', os.getenv('DB_NAME'),
            '-f', backup_file
        ], check=True)
        
        # Compress backup
        subprocess.run([
            'gzip',
            backup_file
        ], check=True)
        
        # Upload to storage
        upload_to_storage(f"{backup_file}.gz")
        
        logging.info(f"Backup completed: {backup_file}.gz")
        
    except Exception as e:
        logging.error(f"Backup failed: {str(e)}")
        raise
```
