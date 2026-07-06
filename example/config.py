import os
from dotenv import load_dotenv

load_dotenv()

# Gemini API Key for Antigravity SDK
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Toggle to run completely locally (mocking Firestore and Slack)
# Default is True so the demo runs out-of-the-box without config
USE_MOCK = os.getenv("USE_MOCK", "True").lower() in ("true", "1", "yes")

# Slack configuration (used when USE_MOCK is False)
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")

# Firestore configuration (used when USE_MOCK is False)
FIRESTORE_PROJECT_ID = os.getenv("FIRESTORE_PROJECT_ID", "")
