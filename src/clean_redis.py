import os
import re

import redis

redis_server = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), decode_responses=True)


reserve_reply_tokens = []
for user_log in redis_server.keys("user:*:logs"):
    redis_server.ltrim(user_log, 0, 100)
    reserve_reply_tokens.extend(redis_server.lrange(user_log, 0, -1))

for reply_token in redis_server.keys("reply_token:*"):
    if re.sub(r"reply_token:", "", reply_token) not in reserve_reply_tokens:
        redis_server.delete(reply_token)
