from typing import List, Optional, Tuple
import os

import redis
import requests
from flask import current_app

import config


redis_server = redis.Redis(
    host=os.getenv("REDIS_HOST"),
    port=os.getenv("REDIS_PORT"),
    username=os.getenv("REDIS_ADMIN"),
    password=os.getenv("REDIS_ADMIN_PASSWORD"),
    ssl=True,
    ssl_certfile="/home/myuser/src/tls/client.crt",
    ssl_keyfile="/home/myuser/src/tls/client.key",
    ssl_ca_certs="/home/myuser/src/tls/ca.crt",
    decode_responses=True,
)


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
TOP_N_DOC = "TOP_N_DOC"
TOP_N_DOC_ID = "TOP_N_DOC_ID"


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


def match_history_dialogue(user_id: str, reply_token: str, user_message: str) -> dict:
    """歷史對話中使用者訊息的向量相似度搜尋。

    Args:
        user_id (str): 使用者 LINE ID。

        reply_token (str): 用於向此事件發送回覆訊息。只能使用一次且必須在收到 Webhook 後一分鐘內使用。使用超過一分鐘並不能保證有效。

        user_message (str): 使用者訊息。

    Returns:
        dict: 有兩種可能的輸出:
            (1) 輸出 -> LINE:
                    `ANSWER` (str): 回覆訊息(歷史對話的回覆訊息)。

                    `HIS_DLG_ID` (str): 歷史對話 ID。

                    `DISTANCE` (float): 使用者訊息之向量與歷史對話中問題之向量最相似的距離。
            (2) 輸出 -> 意圖識別:
                    `HIS_DLG_ID` (Optional[str]): 歷史對話 ID。

                    `DISTANCE` (float): 使用者訊息之向量與歷史對話中問題之向量最相似的距離。(如果 `HIS_DLG_ID` 為 None 則不會有此鍵)
    """
    response = requests.post(config.HISTORY_DIALOGUE_URL, json={USER_MSG: user_message}, headers=HEADERS, timeout=5).json()
    current_app.logger.info(f"[歷史對話] {user_id} | {reply_token} | {response}")
    return response


def detect_intent(user_id: str, reply_token: str, user_message: str) -> dict:
    """識別使用者意圖。

    Args:
        user_id (str): 使用者 LINE ID。

        reply_token (str): 用於向此事件發送回覆訊息。只能使用一次且必須在收到 Webhook 後一分鐘內使用。使用超過一分鐘並不能保證有效。

        user_message (str): 使用者訊息。

    Returns:
        dict: 有兩種可能的輸出:
            (1) 輸出 -> 資訊檢索:
                    `STATE` (str): 意圖的種類，此值為 `ASK`。
            (2) 輸出 -> 後處理:
                    `ANSWER` (None)

                    `STATE` (str): 意圖的種類，此值為 `HATE`/`CHAT`。

                    `OTHERS` (None)
    """
    response = requests.post(config.DETECT_INTENT_URL, json={USER_MSG: user_message}, headers=HEADERS, timeout=5).json()
    current_app.logger.info(f"[意圖識別] {user_id} | {reply_token} | {response}")
    return response


def search_relative_docs(user_id: str, reply_token: str, user_message: str) -> dict:
    """搜尋相關文件。

    Args:
        user_id (str): 使用者 LINE ID。

        reply_token (str): 用於向此事件發送回覆訊息。只能使用一次且必須在收到 Webhook 後一分鐘內使用。使用超過一分鐘並不能保證有效。

        user_message (str): 使用者訊息。

    Returns:
        dict: 有兩種可能的輸出:
            (1) 輸出 -> 生成回覆:
                    `TOP_N_DOC` (dict): 相關文件。

                    `TOP_N_DOC_ID` (List[dict]): 相關文件 ID。
            (2) 輸出 -> 後處理:
                    `ANSWER`(None)

                    `STATE` (str): 此值為 `INFO_NOT_FOUND`，表示查無相關文件。

                    `OTHERS`(None)
    """
    response = requests.post(
        config.INFORMATION_RETRIEVAL_URL,
        json={USER_MSG: user_message, "RETURN_LOG": True},
        headers=HEADERS,
        timeout=5,
    ).json()
    log_info = response[TOP_N_DOC_ID] if TOP_N_DOC_ID in response else response
    current_app.logger.info(f"[資訊檢索] {user_id} | {reply_token} | {log_info}")
    return response


def get_chatgpt_response(
    user_id: str,
    reply_token: str,
    user_message: str,
    relative_docs: List[dict],
) -> dict:
    """ChatGPT 生成回覆訊息。

    Args:
        user_id (str): 使用者 LINE ID。

        reply_token (str): 用於向此事件發送回覆訊息。只能使用一次且必須在收到 Webhook 後一分鐘內使用。使用超過一分鐘並不能保證有效。

        user_message (str): 使用者訊息。

        relative_docs (List[dict]): 資訊檢索系統搜尋的相關文件。

    Returns:
        dict:
            `ANSWER` (Optional[str]): ChatGPT 產生的回答，如果 `STATE` 是 `ERR` 則為 None。

            `STATE` (str): 回答的種類，包含 `ANS`/`ERR`/`UNANSWERABLE`/`POOR`/`ASK`(目前關閉)。

            `OTHERS` (Optional[dict]): 語意評分資訊，如果 `STATE` 是 `ERR` 則為 None ；如果 `STATE` 是 `ASK` 則會有 `REPHRASE` 的鍵(目前關閉)。
    """
    response = requests.post(
        config.CHATGPT_RESPONSE_URL,
        json={
            LINE_USER_ID: user_id,
            REPLY_TOKEN: reply_token,
            USER_MSG: user_message,
            TOP_N_DOC: relative_docs,
        },
        headers=HEADERS,
        timeout=40,
    ).json()
    current_app.logger.info(f"[生成回覆] {user_id} | {reply_token} | {response}")
    return response


def postprocess_response(
    user_id: str,
    reply_token: str,
    user_message: str,
    input_data: dict,
    his_dlg_id: Optional[str],
) -> str:
    """後處理回覆訊息。

    Args:
        user_message (str): 使用者訊息。

        input_data (dict):
            `ANSWER` (Optional[str]): 回覆訊息。

            `STATE` (str): 回覆訊息的種類，包含 `ANS`/`ASK`/`ERR`/`HATE`/`CHAT`/`INFO_NOT_FOUND`。

            `OTHERS` (Optional[dict]): 語意評分資訊，`STATE` 是 `ANS`/`ASK` 則不為 None。

        his_dlg_id (Optional[str]): 歷史對話 ID。

    Returns:
        str: 已後處理的回覆訊息。
    """
    input_data[USER_MSG] = user_message
    input_data[HIS_DLG_ID] = his_dlg_id
    response = requests.post(config.POSTPROCESS_URL, json=input_data, headers=HEADERS, timeout=5).json()
    current_app.logger.info(f"[已後處理] {user_id} | {reply_token} |")
    return response
