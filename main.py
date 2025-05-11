from flask import Request

from chatbot import handle_line_webhook


def webhook(request: Request):
    """HTTP Cloud Function to handle LINE webhook events."""
    return handle_line_webhook(request)