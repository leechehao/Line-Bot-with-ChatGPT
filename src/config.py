import os

from secret import SERVER_HOST


HISTORY_DIALOGUE_URL = f"http://{SERVER_HOST}:{os.getenv('HISTORY_DIALOGUE_PORT')}"
DETECT_INTENT_URL = f"http://{SERVER_HOST}:{os.getenv('DETECT_INTENT_PORT')}/intent_detection"
INFORMATION_RETRIEVAL_URL = f"http://{SERVER_HOST}:{os.getenv('INFORMATION_RETRIEVAL_PORT')}/doc-search-sys/health-insurance/search"
CHATGPT_RESPONSE_URL = f"http://{SERVER_HOST}:{os.getenv('CHATGPT_RESPONSE_PORT')}/get_chatgpt_response"
POSTPROCESS_URL = f"http://{SERVER_HOST}:{os.getenv('POSTPROCESS_PORT')}"
