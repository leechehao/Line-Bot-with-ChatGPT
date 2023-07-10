import json
from typing import Tuple

import redis
import requests

import config

HEADERS = {"Content-Type": "application/json"}
USER_MSG = "USER_MSG"
LINE_USER_ID = "LINE_USER_ID"
REPLY_TOKEN = "REPLY_TOKEN"
HIS_DLG_ID = "HIS_DLG_ID"
HIS_USER_MSG = "HIS_USER_MSG"


def push_reply_token(
    user_id: str,
    reply_token: str,
    init_time: str,
    redis_server: redis.client.Redis,
) -> None:
    redis_server.rpush(f"user:{user_id}:reply_tokens", reply_token)
    redis_server.lpush(f"user:{user_id}:logs", reply_token)
    redis_server.hmset(f"reply_token:{reply_token}", {"init_time": init_time, "state": "False"})


def log_msg(
    reply_token: str,
    user_message: str,
    redis_server: redis.client.Redis,
) -> None:
    redis_server.hset(f"reply_token:{reply_token}", "user_message", user_message)


def log_docs(
    reply_token: str,
    response: dict,
    redis_server: redis.client.Redis,
) -> None:
    redis_server.hset(f"reply_token:{reply_token}", "documents", json.dumps(response, ensure_ascii=False))


def update_reply_message(reply_token: str, reply_message: str, redis_server: redis.client.Redis) -> None:
    redis_server.hset(f"reply_token:{reply_token}", "reply_message", reply_message)


def update_state(reply_token: str, redis_server: redis.client.Redis) -> None:
    redis_server.hset(f"reply_token:{reply_token}", "state", "True")


def check_state(
    user_id: str,
    reply_token: str,
    redis_server: redis.client.Redis,
) -> bool:
    reply_token_head = redis_server.lindex(f"user:{user_id}:reply_tokens", 0)
    if (
        reply_token_head is not None and
        redis_server.hget(f"reply_token:{reply_token_head}", "state") == "True" and
        reply_token == reply_token_head
    ):
        return True
    return False


def get_reply_info(reply_token: str, redis_server: redis.client.Redis) -> Tuple[str, str]:
    reply_message = redis_server.hget(f"reply_token:{reply_token}", "reply_message")
    init_time = redis_server.hget(f"reply_token:{reply_token}", "init_time")
    return reply_message, init_time


def get_next_reply_token(user_id: str, redis_server: redis.client.Redis) -> str:
    redis_server.lpop(f"user:{user_id}:reply_tokens")
    return redis_server.lindex(f"user:{user_id}:reply_tokens", 0)


def match_history_dialogue(user_message: str) -> dict:
    print("歷史對話")
    return requests.post(config.HISTORY_DIALOGUE_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def detect_intent(user_message: str) -> dict:
    print("意圖識別")
    return requests.post(config.DETECT_INTENT_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def search_relative_docs(
    user_id: str,
    user_message: str,
    redis_server: redis.client.Redis
) -> dict:
    print("資訊檢索")
    his_user_msg = redis_server.lrange(f"user:{user_id}:history_msg", 0, -2)
    return requests.post(config.INFORMATION_RETRIEVAL_URL, json={USER_MSG: user_message, HIS_USER_MSG: his_user_msg}, headers=HEADERS).json()


def get_chatgpt_response(
    user_id: str,
    reply_token: str,
    user_message: str,
    relative_docs: dict,
) -> dict:
    print("生成回覆")
    relative_docs[LINE_USER_ID] = user_id
    relative_docs[REPLY_TOKEN] = reply_token
    relative_docs[USER_MSG] = user_message
    return requests.post(config.CHATGPT_RESPONSE_URL, json=relative_docs, headers=HEADERS).json()


def postprocess_response(
    his_dlg_id: str,
    user_message: str,
    input_data: dict
) -> str:
    """後處理回覆訊息

    Args:
        user_message (str): 使用者訊息。
        his_dlg_id (str): 歷史對話 ID。
        input_data (dict): 有三個 key (`ANSWER`，`STATE`，`OTHERS`)。

    Returns:
        str: 已後處理的回覆訊息
    """
    print("後處理")
    input_data[HIS_DLG_ID] = his_dlg_id
    input_data[USER_MSG] = user_message
    return requests.post(config.POSTPROCESS_URL, json=input_data, headers=HEADERS).json()["ANSWER"]
