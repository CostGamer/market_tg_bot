from logging import getLogger

from redis.asyncio import ConnectionPool, Redis

from .settings import RedisSettings, Settings

logger = getLogger(__name__)


class RedisBase:
    def __init__(self, redis_settings: RedisSettings):
        self._redis_settings = redis_settings
        self._pool: ConnectionPool | None = None
        self._redis_connection: Redis | None = None

    async def _initialize_pool(self) -> None:
        """Initialize the Redis connection pool"""
        if not self._pool:
            self._pool = ConnectionPool(
                host=self._redis_settings.redis_host,
                port=self._redis_settings.redis_port,
                db=self._redis_settings.redis_db,
                max_connections=self._redis_settings.redis_max_conn,
            )
            self._redis_connection = Redis(connection_pool=self._pool)
            logger.info("Redis connection pool created")

    async def get_redis_connection(self) -> Redis:
        """Return a Redis connection from the pool"""
        await self._initialize_pool()

        if self._redis_connection is None:
            raise RuntimeError("Redis connection is not initialized")

        return self._redis_connection

    async def close(self) -> None:
        """Close the Redis connection pool if it exists"""
        if self._pool:
            await self._pool.disconnect()
            logger.info("Redis connection pool closed")
            self._pool = None


async def get_redis_connection(all_settings: Settings) -> Redis:
    redis_base = RedisBase(all_settings.redis)
    try:
        redis_conn = await redis_base.get_redis_connection()
        return redis_conn
    except Exception as e:
        logger.error(f"Unexpected error while getting Redis connection: {e}")
        raise
