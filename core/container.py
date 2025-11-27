from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider

from core.environment.providers import EnvironmentProvider
from blockchain.providers import BlockchainProvider
from core.redis.providers import RedisProvider, CacheProvider
from core.logging.providers import LoggerProvider

container = make_async_container(
    FastapiProvider(),
    EnvironmentProvider(),
    LoggerProvider(),
    BlockchainProvider(),
    RedisProvider(),
    CacheProvider()
)

