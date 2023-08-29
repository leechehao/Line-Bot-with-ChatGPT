import json

import utils


ANSWER = "ANSWER"
HIS_DLG_ID = "HIS_DLG_ID"
STATE = "STATE"
ASK = "ASK"
TOP_N_DOC = "TOP_N_DOC"


def handle_message(
    user_id: str,
    reply_token: str,
    user_message: str,
) -> str:
    topic_class = None
    # ===== Ken 歷史對話 =====
    match_output = utils.match_history_dialogue(user_id, reply_token, user_message)
    if ANSWER in match_output:
        reply_message = match_output[ANSWER]
    else:
        his_dlg_id = match_output[HIS_DLG_ID]
        # ===== Clay 意圖識別 =====
        response = utils.detect_intent(user_id, reply_token, user_message)
        if response[STATE] == ASK:
            # ===== Lulu 資訊檢索 =====
            response = utils.search_relative_docs(user_id, reply_token, user_message)
            if TOP_N_DOC in response:
                utils.update_event(reply_token, DOCUMENTS=json.dumps({TOP_N_DOC: response[TOP_N_DOC]}, ensure_ascii=False))
                # ===== Clay 生成回覆 =====
                response = utils.get_chatgpt_response(user_id, reply_token, user_message, response[TOP_N_DOC])
                topic_class = response["OTHERS"]["TRIGGER_FUNCTION_CALL"]

        # ===== Ken 後處理 =====
        reply_message = utils.postprocess_response(user_id, reply_token, user_message, response, his_dlg_id)

    return reply_message, topic_class
