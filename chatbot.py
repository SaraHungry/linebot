import os
from functools import lru_cache

from flask import Request

from agent import Agent
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage
from tools.dad_joke import DadJokeTool

BOTNAME = "TinyRo"

@lru_cache(maxsize=1)
def get_line_config():
    """Loads and caches LINE configuration from environment variables."""
    channel_access_token = os.environ.get("LINE_CHANNEL_ACCESS_TOKEN")
    channel_secret = os.environ.get("LINE_CHANNEL_SECRET")
    if not channel_access_token or not channel_secret:
        raise ValueError(
            "LINE_CHANNEL_ACCESS_TOKEN and LINE_CHANNEL_SECRET environment variables must be set."
        )
    return channel_access_token, channel_secret
    

# TODO: make handle general request (framework agnostic)
def handle_line_webhook(request: Request):
    """Handles the incoming LINE webhook request (specifically for Flask-like requests)."""
    
    channel_access_token, channel_secret = get_line_config()
    line_bot_api = LineBotApi(channel_access_token)
    parser = WebhookParser(channel_secret)

    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)

    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        print("Invalid signature")
        return 'Invalid signature', 401
    except Exception as e:
        print(f"Error parsing webhook: {e}")
        return 'Error parsing webhook', 400

    agent = Agent()
    agent.register_tool(DadJokeTool())

    for event in events:
        if isinstance(event, MessageEvent):
            if event.message.type == 'text':
                user_message = event.message.text
                reply_token = event.reply_token

                if f"@{BOTNAME}" not in user_message:
                    return

                try:
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=agent.generate_response([user_message]))
                    )
                except Exception as e:
                    print(f"Error sending reply message: {e}")

    return 'OK', 200