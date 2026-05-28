import time
from functools import wraps

def ttl_cache(ttl_seconds: int = 3600):
    """
    A simple lightweight in-memory TTL cache decorator.
    Suitable for MVP caching of idempotent API service calls without needing Redis.
    """
    def decorator(func):
        cache = {}
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create a cache key from args and kwargs
            # Stringify to handle Pydantic models or dicts safely
            key_args = tuple(str(arg) for arg in args[1:]) if args and hasattr(args[0], '__class__') else tuple(str(arg) for arg in args)
            key = (key_args, str(kwargs))
            
            now = time.time()
            if key in cache:
                result, timestamp = cache[key]
                if now - timestamp < ttl_seconds:
                    return result
            
            # Cache miss or expired
            result = func(*args, **kwargs)
            cache[key] = (result, now)
            return result
        return wrapper
    return decorator
