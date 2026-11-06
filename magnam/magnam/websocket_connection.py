import os

import redis

MAX_CONNECTIONS_PER_USER = 3

redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "127.0.0.1"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True,
)

_add_connection_script = redis_client.register_script("""
    local count = redis.call("SCARD", KEYS[1])

    if count >= tonumber(ARGV[1]) then
        return 0
    end

    redis.call("SADD", KEYS[1], ARGV[2])
    return 1
    """)


def user_connection_key(user_id):
    return f"ws_connections:user:{user_id}"


def add_connection(user_id, channel_name):
    key = user_connection_key(user_id)

    return bool(
        _add_connection_script(
            keys=[key], args=[MAX_CONNECTIONS_PER_USER, channel_name]
        )
    )


def remove_connection(user_id, channel_name):
    key = user_connection_key(user_id)

    redis_client.srem(key, channel_name)

    if redis_client.scard(key) == 0:
        redis_client.delete(key)
