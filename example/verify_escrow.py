import sys
import os
import asyncio
import threading
import urllib.request
import urllib.parse
import json

# Ensure script path is in Python environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
# Set dummy API key to bypass import check
config.GEMINI_API_KEY = "dummy-key"

from database import db
from escrow import escrow_handler
from server import app
import uvicorn

def start_server():
    # Run uvicorn on localhost
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

# Mock tool call structure
class TestToolCall:
    def __init__(self):
        self.args = {
            "to": "client@external.com",
            "subject": "Antigravity Support Response",
            "body": "Original body text drafted by the agent."
        }

async def simulate_human_reviewer():
    await asyncio.sleep(2)  # Give the server and request time to spin up
    
    print("\n[TEST] 1. Reviewer checking pending requests...")
    pending = await db.get_all_pending()
    if not pending:
        print("[TEST] ERROR: No pending requests in escrow!")
        return
        
    req = pending[0]
    print(f"[TEST] Found pending request ID: {req.id}")
    print(f"[TEST] Original body: '{req.body}'")
    
    # Simulate human editing and approving the request via the dashboard endpoint
    url = "http://localhost:8000/action"
    data = urllib.parse.urlencode({
        "request_id": req.id,
        "action": "edit",
        "edited_body": "This is the EDITED email content approved by the reviewer."
    }).encode("utf-8")
    
    print("[TEST] 2. Reviewer sending edits and approval via POST /action...")
    try:
        req_obj = urllib.request.Request(url, data=data, method="POST")
        response = urllib.request.urlopen(req_obj)
        res_data = json.loads(response.read().decode("utf-8"))
        print(f"[TEST] Dashboard response: {res_data}")
    except Exception as e:
        print(f"[TEST] ERROR sending POST request: {e}")

async def run_test():
    # 1. Start the FastAPI server in a background daemon thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    await asyncio.sleep(1)  # Let server boot
    
    # 2. Schedule the human reviewer simulator
    asyncio.create_task(simulate_human_reviewer())
    
    # 3. Execute the escrow handler (simulates the agent calling send_email under policy check)
    tool_call = TestToolCall()
    print("[TEST] Triggering escrow_handler (Agent turn pauses)...")
    result = await escrow_handler(tool_call)
    
    # 4. Check validation results
    print("\n" + "=" * 50)
    print("📋 INTEGRATION TEST VERIFICATION RESULTS")
    print("=" * 50)
    print(f"Escrow handler return value: {result} (Expected: True)")
    print(f"Final tool_call email body:  '{tool_call.args['body']}'")
    print("Expected final body:         'This is the EDITED email content approved by the reviewer.'")
    print("=" * 50)
    
    if result is True and tool_call.args["body"] == "This is the EDITED email content approved by the reviewer.":
        print("\n🎉 SUCCESS: The Email Escrow pipeline is verified and working perfectly!\n")
        # Exit successfully
        os._exit(0)
    else:
        print("\n❌ FAILURE: Escrow output did not match expected results.\n")
        os._exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nTest interrupted.")
        os._exit(1)
