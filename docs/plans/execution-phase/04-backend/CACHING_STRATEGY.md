# Caching Strategy

**Last Updated:** 2026-01-15
**Related Documents:**
- [Service Layer](./SERVICE_LAYER.md)
- [Infrastructure](../01-architecture/INFRASTRUCTURE.md)
- [API Endpoints](./API_ENDPOINTS.md)

---

## Table of Contents

1. [Overview](#overview)
2. [Cache Layers](#cache-layers)
3. [Redis Setup](#redis-setup)
4. [Caching Patterns](#caching-patterns)
5. [Cache Keys](#cache-keys)
6. [Cache Invalidation](#cache-invalidation)
7. [Performance Metrics](#performance-metrics)
8. [Related Documentation](#related-documentation)

---

## Overview

The PDP Automation v.3 system implements a multi-layer caching strategy to optimize performance and reduce costs. Caching is particularly important for:
- **Anthropic API responses** - Expensive and rate-limited (70-90% cost savings)
- **Prompt library** - Frequently accessed, rarely changes
- **Project metadata** - High read volume
- **Template configurations** - Static data

**Caching Goals:**
1. **Reduce API costs** - Cache expensive Anthropic API calls
2. **Improve response times** - Serve cached data in <10ms
3. **Reduce database load** - Cache frequently accessed data
4. **Handle rate limits** - Serve cached responses when APIs throttle

**Cache Technology:** Redis (Cloud Memorystore or self-hosted)

---

## Cache Layers

```
┌─────────────────────────────────────────────────────┐
│           Layer 1: In-Memory Cache                  │
│  - Application-level (per instance)                 │
│  - Very fast (<1ms)                                 │
│  - Limited scope (single instance)                  │
│  - TTL: 1-5 minutes                                 │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│           Layer 2: Redis Cache                      │
│  - Shared across all instances                      │
│  - Fast (<10ms)                                     │
│  - Global scope                                     │
│  - TTL: 5 minutes - 30 days                        │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│           Layer 3: Database / API                   │
│  - Source of truth                                  │
│  - Slower (50-500ms)                                │
│  - Always consistent                                │
└─────────────────────────────────────────────────────┘
```

---

## Cache Layers

### Layer 1: Anthropic Response Cache

**Purpose:** Cache expensive Anthropic API responses

**TTL:** 30 days
**Keys:** `anthropic:{prompt_hash}:{content_hash}`
**Cost Savings:** 70-90%

**Why Cache Anthropic?**
- API calls are expensive ($10-30 per 1M tokens)
- Same PDF + same prompt = same result
- Rate limits (60-5000 req/min depending on tier)

**Example:**
```python
# Cache key
prompt = "Extract structured data from this PDF..."
content = "<pdf_text_here>"
cache_key = f"anthropic:{hash_string(prompt)}:{hash_string(content)}"

# Check cache first
cached_result = await redis.get(cache_key)
if cached_result:
    return json.loads(cached_result)

# Cache miss - call API
result = await anthropic_service.extract_data(content, prompt)

# Store in cache (30 days)
await redis.setex(cache_key, 2592000, json.dumps(result))
```

---

### Layer 2: Prompt Cache

**Purpose:** Cache frequently accessed prompts

**TTL:** 1 hour
**Keys:** `prompt:{id}`
**Hit Rate:** >95%

**Why Cache Prompts?**
- Accessed on every job
- Rarely change (version controlled)
- Database query avoided

**Example:**
```python
cache_key = f"prompt:{prompt_id}"

# Check cache
cached_prompt = await redis.get(cache_key)
if cached_prompt:
    return Prompt(**json.loads(cached_prompt))

# Cache miss - query database
prompt = await db.prompts.find_one({"id": prompt_id})

# Store in cache (1 hour)
await redis.setex(cache_key, 3600, json.dumps(prompt.dict()))
```

---

### Layer 3: Project Metadata Cache

**Purpose:** Cache project list and metadata

**TTL:** 5 minutes
**Keys:** `project:{id}:meta`, `projects:list:{filters_hash}`
**Hit Rate:** 60-80%

**Why Cache Projects?**
- Dashboard loads project list frequently
- Metadata rarely changes
- Reduce database load

**Example:**
```python
cache_key = f"project:{project_id}:meta"

# Check cache
cached_project = await redis.get(cache_key)
if cached_project:
    return Project(**json.loads(cached_project))

# Cache miss - query database
project = await db.projects.find_one({"id": project_id})

# Store in cache (5 minutes)
await redis.setex(cache_key, 300, json.dumps(project.dict()))
```

---

### Layer 4: Template Cache

**Purpose:** Cache website templates

**TTL:** 24 hours
**Keys:** `templates:list`, `template:{id}`
**Hit Rate:** >99%

**Why Cache Templates?**
- Rarely change
- Accessed on every job
- Static data

**Example:**
```python
cache_key = "templates:list"

# Check cache
cached_templates = await redis.get(cache_key)
if cached_templates:
    return [Template(**t) for t in json.loads(cached_templates)]

# Cache miss - query database
templates = await db.templates.find({"is_active": True}).to_list()

# Store in cache (24 hours)
await redis.setex(cache_key, 86400, json.dumps([t.dict() for t in templates]))
```

---

## Redis Setup

### Cloud Memorystore

**Why Cloud Memorystore?**
- Fully managed Redis
- High availability (99.9% SLA)
- Automatic failover
- No maintenance

**Configuration:**
```bash
# Create Redis instance
gcloud redis instances create pdp-automation-cache \
  --size=1 \
  --region=us-central1 \
  --redis-version=redis_7_0 \
  --tier=basic

# Get connection info
gcloud redis instances describe pdp-automation-cache \
  --region=us-central1 \
  --format="value(host,port)"
```

**Connection String:**
```
redis://10.0.0.3:6379
```

### Python Client Setup

```python
# app/config/cache.py

from redis import asyncio as aioredis
import json

class CacheService:
    def __init__(self):
        self.redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=50
        )

    async def get(self, key: str) -> Any:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: int):
        """Set value in cache with TTL (seconds)."""
        await self.redis.setex(key, ttl, json.dumps(value))

    async def delete(self, key: str):
        """Delete key from cache."""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str):
        """Delete all keys matching pattern."""
        keys = []
        async for key in self.redis.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            await self.redis.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        return await self.redis.exists(key) > 0

    async def ttl(self, key: str) -> int:
        """Get time-to-live for key."""
        return await self.redis.ttl(key)

    async def close(self):
        """Close Redis connection."""
        await self.redis.close()


# Singleton instance
cache_service = CacheService()
```

---

## Caching Patterns

### Pattern 1: Cache-Aside (Lazy Loading)

**Most Common Pattern**

```python
async def get_project(project_id: str) -> Project:
    """Get project with cache-aside pattern."""
    cache_key = f"project:{project_id}"

    # 1. Check cache
    cached = await cache_service.get(cache_key)
    if cached:
        logger.debug(f"Cache hit: {cache_key}")
        return Project(**cached)

    # 2. Cache miss - query database
    logger.debug(f"Cache miss: {cache_key}")
    project = await db.projects.find_one({"id": project_id})

    if not project:
        raise NotFoundError("project", project_id)

    # 3. Store in cache
    await cache_service.set(cache_key, project.dict(), ttl=300)

    return project
```

---

### Pattern 2: Write-Through Cache

**Update cache when data changes**

```python
async def update_project(
    project_id: str,
    updates: dict,
    user: User
) -> Project:
    """Update project and cache."""
    # 1. Update database
    await db.projects.update_one(
        {"id": project_id},
        {"$set": updates}
    )

    # 2. Get updated project
    project = await db.projects.find_one({"id": project_id})

    # 3. Update cache
    cache_key = f"project:{project_id}"
    await cache_service.set(cache_key, project.dict(), ttl=300)

    # 4. Invalidate list cache
    await cache_service.delete_pattern("projects:list:*")

    return project
```

---

### Pattern 3: Cache with Function Decorator

**Reusable caching decorator**

```python
# app/utils/cache_decorator.py

from functools import wraps
import hashlib
import inspect

def cache(ttl: int = 300, key_prefix: str = None):
    """
    Cache decorator for async functions.

    Args:
        ttl: Time-to-live in seconds
        key_prefix: Optional key prefix

    Usage:
        @cache(ttl=3600, key_prefix="user")
        async def get_user(user_id: str):
            return await db.users.find_one({"id": user_id})
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            func_name = func.__name__
            prefix = key_prefix or func_name

            # Hash arguments
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            args_str = json.dumps(bound_args.arguments, sort_keys=True)
            args_hash = hashlib.md5(args_str.encode()).hexdigest()[:8]

            cache_key = f"{prefix}:{args_hash}"

            # Check cache
            cached = await cache_service.get(cache_key)
            if cached:
                logger.debug(f"Cache hit: {cache_key}")
                return cached

            # Cache miss - call function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_service.set(cache_key, result, ttl=ttl)

            return result

        return wrapper
    return decorator


# Usage example
@cache(ttl=3600, key_prefix="prompt")
async def get_prompt(prompt_id: str) -> Prompt:
    return await db.prompts.find_one({"id": prompt_id})
```

---

### Pattern 4: Get or Fetch

**Simplified cache-aside with callback**

```python
async def get_or_fetch(
    cache_key: str,
    fetch_func: Callable,
    ttl: int = 300
) -> Any:
    """
    Get from cache or fetch from source.

    Args:
        cache_key: Cache key
        fetch_func: Async function to fetch data if cache miss
        ttl: Time-to-live in seconds

    Returns:
        Cached or fetched data
    """
    # Check cache
    cached = await cache_service.get(cache_key)
    if cached:
        return cached

    # Cache miss - fetch from source
    data = await fetch_func()

    # Store in cache
    await cache_service.set(cache_key, data, ttl=ttl)

    return data


# Usage example
project = await get_or_fetch(
    cache_key=f"project:{project_id}",
    fetch_func=lambda: db.projects.find_one({"id": project_id}),
    ttl=300
)
```

---

## Cache Keys

### Key Naming Convention

**Format:** `{namespace}:{identifier}:{subkey}`

**Examples:**
- `anthropic:abc123def:xyz789` - Anthropic response
- `prompt:550e8400-e29b-41d4-a716-446655440000` - Prompt by ID
- `project:770e8400-e29b-41d4-a716-446655440002:meta` - Project metadata
- `projects:list:dev=emaar&status=published` - Filtered project list
- `templates:list` - All templates
- `user:550e8400-e29b-41d4-a716-446655440000:permissions` - User permissions

### Key Hashing

For long keys, use MD5 hash:

```python
import hashlib

def hash_string(s: str) -> str:
    """Hash string to fixed-length identifier."""
    return hashlib.md5(s.encode()).hexdigest()[:16]

# Example
prompt_text = "Very long prompt text here..."
content = "Very long PDF content here..."
cache_key = f"anthropic:{hash_string(prompt_text)}:{hash_string(content)}"
```

---

## Cache Invalidation

### When to Invalidate

**Immediate Invalidation:**
- Project updated → Invalidate `project:{id}:*`
- Prompt updated → Invalidate `prompt:{id}:*`
- Template updated → Invalidate `templates:*`

**Pattern-Based Invalidation:**
- Delete by prefix: `projects:list:*` (all project lists)
- Delete by pattern: `project:*:meta` (all project metadata)

### Invalidation Strategies

**1. Time-Based (TTL)**
```python
# Set TTL when caching
await cache_service.set(cache_key, data, ttl=300)  # 5 minutes
```

**2. Event-Based**
```python
# Invalidate on update
async def update_project(project_id: str, updates: dict):
    # Update database
    await db.projects.update_one({"id": project_id}, {"$set": updates})

    # Invalidate cache
    await cache_service.delete(f"project:{project_id}")
    await cache_service.delete_pattern("projects:list:*")
```

**3. Version-Based**
```python
# Include version in cache key
cache_key = f"prompt:{prompt_id}:v{version}"
```

---

## Performance Metrics

### Cache Hit Rates

**Target Hit Rates:**
- Anthropic responses: 70-80%
- Prompts: >95%
- Templates: >99%
- Project metadata: 60-80%

### Cache Performance Monitoring

```python
# app/middleware/cache_metrics.py

from functools import wraps
import time

def track_cache_performance(func):
    """Track cache hit/miss metrics."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        duration = time.time() - start_time

        # Determine hit/miss based on duration
        is_hit = duration < 0.01  # <10ms = cache hit

        # Record metric
        metrics_client.record_metric(
            "cache_access",
            1,
            labels={
                "function": func.__name__,
                "status": "hit" if is_hit else "miss",
                "duration_ms": duration * 1000
            }
        )

        return result

    return wrapper
```

### Cost Savings

**Anthropic API Cache:**
```
Without Cache:
- 1000 jobs/month
- Average 100K tokens per job
- $10 per 1M input tokens
- Cost: 1000 * 100K / 1M * $10 = $1,000/month

With 80% Cache Hit Rate:
- 800 cached (free)
- 200 API calls
- Cost: 200 * 100K / 1M * $10 = $200/month

Savings: $800/month (80%)
```

---

## Related Documentation

- [Service Layer](./SERVICE_LAYER.md) - Services using caching
- [Infrastructure](../01-architecture/INFRASTRUCTURE.md) - Redis setup
- [API Endpoints](./API_ENDPOINTS.md) - Cached endpoints

---

**Last Updated:** 2026-01-15
