import os
from functools import lru_cache

from flask import Request

from agent import Agent
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextSendMessage
from tools.dad_joke import DadJokeTool


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

    agent = Agent() # Initialize your agent with the defined tools
    agent.register_tool(DadJokeTool())

    for event in events:
        if isinstance(event, MessageEvent):
            if event.message.type == 'text':
                user_message = event.message.text
                reply_token = event.reply_token

                # Pass the user message to the agent and get the response
                agent_response = agent.run(user_message)

                # Send the response back to LINE using the SDK
                try:
                    line_bot_api.reply_message(
                        reply_token,
                        TextSendMessage(text=agent_response)
                    )
                except Exception as e:
                    print(f"Error sending reply message: {e}")

    return 'OK', 200

if __name__ == '__main__':
    # Local testing with Flask remains the same


    from flask import Flask
    from flask import request as flask_request

    from linebot.models import TextSendMessage

    app = Flask(__name__)

    @app.route('/', methods=['POST'])
    def local_test_webhook():
        return handle_line_webhook(flask_request)

    # Set environment variables for local testing
    os.environ["LINE_CHANNEL_ACCESS_TOKEN"] = "YOUR_CHANNEL_ACCESS_TOKEN"
    os.environ["LINE_CHANNEL_SECRET"] = "YOUR_CHANNEL_SECRET"

    app.run(host='0.0.0.0', port=8080, debug=True)