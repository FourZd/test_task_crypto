from dishka import Provider, Scope, provide, FromComponent
from typing import Annotated, AsyncIterable
from core.environment.config import Settings
from redis.asyncio import Redis
import json


class RedisProvider(Provider):
    """
    Provider for Redis client.
    """
    
    scope = Scope.APP
    component = "redis"
    
    @provide(scope=Scope.APP)
    async def provide_redis_client(
        self,
        settings: Annotated[Settings, FromComponent("environment")]
    ) -> AsyncIterable[Redis]:
        """
        Create Redis client for the application.
        
        Parameters
        ----------
        settings : Settings
            Application settings
            
        Yields
        ------
        Redis
            Redis client instance
        """
        redis_client = Redis(
            host=settings.redis_host,
            port=settings.redis_port,
            db=settings.redis_db,
            password=settings.redis_password if settings.redis_password else None,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        
        try:
            await redis_client.ping()
            yield redis_client
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Redis: {e}")
        finally:
            await redis_client.aclose()


class CacheService:
    """
    Service for caching data in Redis.
    
    Parameters
    ----------
    redis_client : Redis
        Redis client instance
    """
    
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
    
    async def get(self, key: str) -> dict | None:
        """
        Get cached value.
        
        Parameters
        ----------
        key : str
            Cache key
            
        Returns
        -------
        dict | None
            Cached value or None
        """
        try:
            value = await self.redis.get(key)
            if value:
                return json.loads(value)
        except Exception:
            pass
        return None
    
    async def set(self, key: str, value: dict, ttl: int = 3600) -> bool:
        """
        Set cached value.
        
        Parameters
        ----------
        key : str
            Cache key
        value : dict
            Value to cache
        ttl : int
            Time to live in seconds
            
        Returns
        -------
        bool
            Success status
        """
        try:
            await self.redis.setex(
                key,
                ttl,
                json.dumps(value)
            )
            return True
        except Exception:
            return False


class CacheProvider(Provider):
    """
    Provider for cache service.
    """
    
    component = "cache"
    scope = Scope.APP
    
    @provide(scope=Scope.APP)
    def provide_cache_service(
        self,
        redis_client: Annotated[Redis, FromComponent("redis")]
    ) -> CacheService:
        """
        Provide cache service.
        
        Parameters
        ----------
        redis_client : Redis
            Redis client instance
            
        Returns
        -------
        CacheService
            Cache service instance
        """
        return CacheService(redis_client)

