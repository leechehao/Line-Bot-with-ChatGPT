import utils

ANSWER = "ANSWER"
HIS_DLG_ID = "HIS_DLG_ID"
STATE = "STATE"
ASK = "ASK"
TOP_N_DOC = "TOP_N_DOC"


def handle_message(user_id: str, user_message: str) -> str:
    # ===== Ken 歷史對話 =====
    match_output = utils.match_history_dialogue(user_message)
    if ANSWER in match_output:
        reply_message = match_output[ANSWER]
    else:
        his_dlg_id = match_output[HIS_DLG_ID]
        # ===== Clay 任務識別 =====
        response = utils.detect_intent(user_message)
        if response[STATE] == ASK:
            # ===== Lulu 資訊檢索 =====
            response = utils.search_relative_docs(user_message)
            if TOP_N_DOC in response:
                # ===== Clay 生成回覆 =====
                response = utils.get_chatgpt_response(user_message, user_id, response)
        # ===== Ken 後處理 =====
        reply_message = utils.postprocess_response(user_message, his_dlg_id, response)

    return reply_message
