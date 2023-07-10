import os
import time

import redis
from flask import request, abort, current_app
from flask_restful import Resource
from linebot.v3 import WebhookHandler
from linebot.v3.exceptions import InvalidSignatureError
from linebot.v3.webhooks import MessageEvent, TextMessageContent
from linebot.v3.messaging import Configuration, ApiClient, MessagingApi, ReplyMessageRequest, TextMessage

from events import message_event
import utils
import config

handler = WebhookHandler(config.CHANNEL_SECRET)
configuration = Configuration(access_token=config.CHANNEL_ACCESS_TOKEN)
redis_server = redis.Redis(host="localhost", port=6379, decode_responses=True)
# os.getenv("REDIS_HOST")
# os.getenv("REDIS_PORT")


class Callback(Resource):
    def post(self) -> str:
        # get X-Line-Signature header value
        signature = request.headers["X-Line-Signature"]

        # get request body as text
        body = request.get_data(as_text=True)
        current_app.logger.info("Request body: " + body)

        # handle webhook body
        try:
            handler.handle(body, signature)
        except InvalidSignatureError:
            current_app.logger.info("Invalid signature. Please check your channel access token/channel secret.")
            abort(400)

        return "OK"


@handler.add(MessageEvent, message=TextMessageContent)
def handle_message(event) -> None:
    init_time = f"{time.strftime('%X')}"
    user_id = event.source.user_id
    user_message = event.message.text
    reply_token = event.reply_token

    utils.push_reply_token(user_id, reply_token, init_time, redis_server)
    utils.log_msg(reply_token, user_message, redis_server)

    with ApiClient(configuration) as api_client:
        reply_message = message_event.handle_message(
            user_id=user_id,
            reply_token=reply_token,
            user_message=user_message,
            redis_server=redis_server,
        )
        utils.update_reply_message(reply_token, reply_message, redis_server)
        utils.update_state(reply_token, redis_server)
        print("迴圈")
        while utils.check_state(user_id, reply_token, redis_server):
            reply_message, init_time = utils.get_reply_info(reply_token, redis_server)
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message_with_http_info(
                ReplyMessageRequest(
                    reply_token=reply_token,
                    messages=[TextMessage(text=f"{reply_message}\n{init_time}, {time.strftime('%X')}")],
                ),
            )
            reply_token = utils.get_next_reply_token(user_id, redis_server)
            
