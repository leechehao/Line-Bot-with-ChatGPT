from typing import Tuple
import os
import json

import redis
import requests

import config

redis_server = redis.Redis(host="localhost", port=6379, decode_responses=True)
# os.getenv("REDIS_HOST")
# os.getenv("REDIS_PORT")

HEADERS = {"Content-Type": "application/json"}
LINE_USER_ID = "LINE_USER_ID"
HIS_DLG_ID = "HIS_DLG_ID"
REPLY_TOKEN = "REPLY_TOKEN"
USER_MSG = "USER_MSG"
HIS_USER_MSG = "HIS_USER_MSG"
ANSWER = "ANSWER"
START_TIME = "START_TIME"
STATE = "STATE"
REPLY_MSG = "REPLY_MSG"
DOCUMENTS = "DOCUMENTS"


def push_event(
    user_id: str,
    reply_token: str,
    user_message: str,
    start_time: str,
) -> None:
    redis_server.rpush(f"user:{user_id}:reply_tokens", reply_token)
    redis_server.lpush(f"user:{user_id}:logs", reply_token)
    redis_server.hmset(
        f"reply_token:{reply_token}",
        {
            START_TIME: start_time,
            USER_MSG: user_message,
            STATE: "False",
        },
    )


def log_docs(reply_token: str, response: dict) -> None:
    redis_server.hset(f"reply_token:{reply_token}", DOCUMENTS, json.dumps(response, ensure_ascii=False))


def update_event(reply_token: str, **kwargs) -> None:
    redis_server.hmset(f"reply_token:{reply_token}", {key: value for key, value in kwargs.items()})


def check_state(user_id: str, reply_token: str) -> bool:
    reply_token_head = redis_server.lindex(f"user:{user_id}:reply_tokens", 0)
    if (
        reply_token_head == reply_token and
        redis_server.hget(f"reply_token:{reply_token_head}", STATE) == "True"
    ):
        return True
    return False


def get_reply_info(reply_token: str) -> Tuple[str, str]:
    reply_message = redis_server.hget(f"reply_token:{reply_token}", REPLY_MSG)
    start_time = redis_server.hget(f"reply_token:{reply_token}", START_TIME)
    return reply_message, start_time


def get_next_reply_token(user_id: str) -> str:
    redis_server.lpop(f"user:{user_id}:reply_tokens")
    return redis_server.lindex(f"user:{user_id}:reply_tokens", 0)


def match_history_dialogue(user_message: str) -> dict:
    print("歷史對話", user_message)
    return requests.post(config.HISTORY_DIALOGUE_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def detect_intent(user_message: str) -> dict:
    print("意圖識別", user_message)
    return requests.post(config.DETECT_INTENT_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def search_relative_docs(user_message: str) -> dict:
    print("資訊檢索", user_message)
    return requests.post(config.INFORMATION_RETRIEVAL_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def get_chatgpt_response(
    user_id: str,
    reply_token: str,
    user_message: str,
    relative_docs: dict,
) -> dict:
    print("生成回覆", user_message)
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
    print("後處理", user_message)
    input_data[HIS_DLG_ID] = his_dlg_id
    input_data[USER_MSG] = user_message
    return requests.post(config.POSTPROCESS_URL, json=input_data, headers=HEADERS).json()[ANSWER]
