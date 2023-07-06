import redis
import requests

import config

HEADERS = {"Content-Type": "application/json"}
USER_MSG = "USER_MSG"
LINE_USER_ID = "LINE_USER_ID"
HIS_DLG_ID = "HIS_DLG_ID"


def keep_latest_100_dialogue(
    user_id: str,
    message: str,
    reply_message: str,
    redis_server: redis.client.Redis,
) -> None:
    redis_server.lpush(f"user:{user_id}:history_dlg", f"{message}|*_*|{reply_message}")
    redis_server.ltrim(f"user:{user_id}:history_dlg", 0, 99)


def match_history_dialogue(user_message: str) -> dict:
    print("歷史對話")
    return requests.post(config.HISTORY_DIALOGUE_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def detect_intent(user_message: str) -> dict:
    print("意圖識別")
    return requests.post(config.DETECT_INTENT_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def search_relative_docs(user_message: str) -> dict:
    print("資訊檢索")
    return requests.post(config.INFORMATION_RETRIEVAL_URL, json={USER_MSG: user_message}, headers=HEADERS).json()


def get_chatgpt_response(
    user_message: str,
    user_id: str,
    relative_docs: dict,
) -> dict:
    print("生成回覆")
    relative_docs[USER_MSG] = user_message
    relative_docs[LINE_USER_ID] = user_id
    return requests.post(config.CHATGPT_RESPONSE_URL, json=relative_docs, headers=HEADERS).json()


def postprocess_response(
    user_message: str,
    his_dlg_id: str,
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
    input_data[USER_MSG] = user_message
    input_data[HIS_DLG_ID] = his_dlg_id
    return requests.post(config.POSTPROCESS_URL, json=input_data, headers=HEADERS).json()["ANSWER"]
