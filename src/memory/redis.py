import redis
import zlib
import pickle
from src.core.config import REDIS_DB, REDIS_HOST, REDIS_PORT, REDIS_TTL

# Connect to Redis
redis_client = redis.Redis(host=REDIS_HOST, port=int(REDIS_PORT), db=int(REDIS_DB))

def store_messages_in_redis(key, message, ttl=int(REDIS_TTL)):
    """Compresses a message using gzip and stores it in Redis."""
    redis_key = f"msg_{key}"
    serialized_json = pickle.dumps(message)
    compressed_data = zlib.compress(serialized_json)
    redis_client.setex(redis_key, ttl, compressed_data)

def read_messages_from_redis(key):
    """Retrieves a compressed message from Redis and decompresses it."""
    redis_key = f"msg_{key}"
    compressed_data = redis_client.get(redis_key)
    if compressed_data:
        decompressed_data = zlib.decompress(compressed_data)
        return pickle.loads(decompressed_data)
    else:
        return []  # Handle the case where the key doesn't exist
