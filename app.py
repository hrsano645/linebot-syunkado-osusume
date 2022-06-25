from dataclasses import dataclass
import random
import os
import re
import sys

import dotenv
from flask import Flask, abort, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    AudioSendMessage,
    ButtonsTemplate,
    CarouselColumn,
    CarouselTemplate,
    ConfirmTemplate,
    MessageAction,
    MessageEvent,
    SourceUser,
    TemplateSendMessage,
    TextMessage,
    TextSendMessage,
    URIAction,
)

# TODO: 2022/06/25 linebotのインスタンス作るのと順番後でどちらでもいいか試す
app = Flask(__name__)

dotenv.load_dotenv()

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv("LINE_CHANNEL_SECRET", None)
channel_access_token = os.getenv("LINE_CHANNEL_ACCESS_TOKEN", None)
if channel_secret is None:
    print("Specify LINE_CHANNEL_SECRET as environment variable.")
    sys.exit(1)
if channel_access_token is None:
    print("Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.")
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)


@dataclass
class SyunkadoOkasi:
    name: str
    bot_sentence: str
    season: str
    okasi_info: str = ""  # urlとしたい


# お菓子一覧: https://www.shunkado.co.jp/sweets/
syunkado_okasi_list = [
    SyunkadoOkasi(
        "うなぎパイ",
        "夜のお菓子と言ったら！",
        "通年",
    ),
    SyunkadoOkasi("うなぎパイVPOS", "ブランデーが入ってさらに美味しい！", "通年"),
    SyunkadoOkasi("うなぎサブレ", "隠れた名品！", "通年"),
]


# linebot側のcallbackチェック, Line側とのやり取り用
@app.route("/callback", methods=["POST"])
def callback():
    # get X-Line-Signature header value
    signature = request.headers["X-Line-Signature"]

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)

    return "callback OK!"


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):
    event_text = event.message.text

    match event_text:

        case "おかしのおすすめを教えて！":
            mode_name = "おかしのオススメモード！"
            print(mode_name)

            line_bot_api.push_message(
                event.source.user_id,
                [TextSendMessage(text=f"{mode_name}")],
            )
            # TODO: 2022/06/25 シードは毎回リセットでいい？
            random.seed()
            random_okasi: SyunkadoOkasi = random.choice(syunkado_okasi_list)

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(
                    text=f"""{random_okasi.bot_sentence} \n
                    『{random_okasi.name}』\n
                    {random_okasi.season}で買えるよ！"""
                ),
            )

        # debug用
        case "userinfo":
            print("debug: userinfo")
            if isinstance(event.source, SourceUser):
                profile = line_bot_api.get_profile(event.source.user_id)
                line_bot_api.reply_message(
                    event.reply_token,
                    [
                        TextSendMessage(text="Display name: " + profile.display_name),
                        TextSendMessage(
                            text="Status message: " + str(profile.status_message)
                        ),
                    ],
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text="Bot can't use profile API without user ID"),
                )
        case _:
            print("何も当たらなかった場合の最後")

            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text=f"返す言葉がありませんでした: {event_text}"),
            )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5500))
    app.run(host="0.0.0.0", port=port)
