import os
import time

from flask import request, abort, current_app
from flask_restful import Resource
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage

import utils
from events import message_event


handler = WebhookHandler(os.getenv("CHANNEL_SECRET"))
configuration = Configuration(access_token=os.getenv("CHANNEL_ACCESS_TOKEN"))

REPLY_MSG = "REPLY_MSG"
STATE = "STATE"
END_TIME = "END_TIME"


class Callback(Resource):
    def post(self) -> str:
        # get X-Line-Signature header value
        signature = request.headers["X-Line-Signature"]

        # get request body as text
        body = request.get_data(as_text=True)
        # current_app.logger.info("Request body: " + body)

        # handle webhook body
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            current_app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
            abort(400)

        return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event) -> None:
    start_time = f"{time.strftime('%X')}"
    user_id = event.source.user_id
    reply_token = event.reply_token
    user_message = event.message.text

    current_app.logger.info(f"[事件觸發] {user_id} | {reply_token} | {user_message}")

    utils.push_event(user_id, reply_token, user_message, start_time)

    with ApiClient(configuration) as api_client:
        try:
            reply_message = message_event.handle_message(
                user_id=user_id,
                reply_token=reply_token,
                user_message=user_message,
            )
        except Exception as e:
            current_app.logger.error(f"{type(e)}: {e}", exc_info=True)
            reply_message = "系統忙碌中，請您稍後再試試看。"

        utils.update_event(reply_token, REPLY_MSG=reply_message, STATE="True")

        while utils.check_state(user_id, reply_token):
            reply_message, start_time = utils.get_reply_info(reply_token)
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=f"{reply_message}\n{start_time}, {time.strftime('%X')}")],
                ),
            )
            utils.update_event(reply_token, END_TIME=time.strftime('%X'))
            reply_token = utils.get_next_reply_token(user_id)
