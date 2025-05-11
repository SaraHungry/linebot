from flask import Request  # Import Flask's Request for type hinting

from chatbot import handle_line_webhook


def webhook(request: Request):
    """HTTP Cloud Function to handle LINE webhook events."""
    return handle_line_webhook(request)