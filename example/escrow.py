import uuid
import asyncio
from datetime import datetime
import urllib.request
import json
import config
from database import db

class Decision:
    def __init__(self, action: str, edited_body: str = None, reason: str = None):
        self.action = action
        self.edited_body = edited_body
        self.reason = reason

async def notify_reviewer(request_id: str, recipient: str, subject: str, body_preview: str):
    dashboard_url = "http://localhost:8000"
    
    if config.USE_MOCK:
        # Visual console representation of Slack notification block
        print("\n" + "=" * 60)
        print("  🚨 [MOCK SLACK ALERT]")
        print("  Channel: #support-approvals")
        print(f"  Request ID: {request_id}")
        print(f"  To:         {recipient}")
        print(f"  Subject:    {subject}")
        print(f"  Preview:    {body_preview}")
        print("-" * 60)
        print(f"  👉 APPROVE OR EDIT HERE: {dashboard_url}")
        print("=" * 60 + "\n")
        return

    # Real Slack Webhook (Production Mode)
    if not config.SLACK_WEBHOOK_URL:
        print("WARNING: USE_MOCK is False but SLACK_WEBHOOK_URL is not set.")
        return

    # Slack Block Kit Payload
    payload = {
        "text": f"🚨 *Email Escrow Approval Required*",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"🚨 *Email Escrow Approval Required*\n*To:* {recipient}\n*Subject:* {subject}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Body Preview:*\n```{body_preview}```"
                }
            },
            {
                "type": "actions",
                "block_id": "escrow_actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Approve"},
                        "style": "primary",
                        "action_id": "approve",
                        "value": request_id
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Reject"},
                        "style": "danger",
                        "action_id": "reject",
                        "value": request_id
                    }
                ]
            }
        ]
    }
    
    try:
        req = urllib.request.Request(
            config.SLACK_WEBHOOK_URL,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: urllib.request.urlopen(req).read())
        print(f"Slack webhook sent successfully for request: {request_id}")
    except Exception as e:
        print(f"Failed to post to Slack webhook: {e}")

async def poll_for_decision(request_id: str, timeout_seconds: int) -> Decision:
    start_time = datetime.utcnow()
    while (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
        req = await db.get_request(request_id)
        if req and req.status == "resolved":
            return Decision(
                action=req.action,
                edited_body=req.edited_body,
                reason=req.reason
            )
        await asyncio.sleep(2)  # Check Firestore/mock DB every 2 seconds
    return Decision(action="timeout", reason="Reviewer did not respond in time")

async def escrow_handler(tool_call):
    """
    Antigravity safety policy handler.
    Returns True to allow the execution, and False to block it.
    """
    request_id = str(uuid.uuid4())[:8]  # Short user-friendly ID
    recipient = tool_call.args.get("to", "customer@example.com")
    subject = tool_call.args.get("subject", "Your Support Request")
    body = tool_call.args.get("body", "")
    
    # 1. Persist the request in database (State: pending_review)
    await db.create_pending_request(
        request_id=request_id,
        tool="send_email",
        recipient=recipient,
        subject=subject,
        body=body
    )
    
    # 2. Trigger notification
    await notify_reviewer(
        request_id=request_id,
        recipient=recipient,
        subject=subject,
        body_preview=body[:280] + ("..." if len(body) > 280 else "")
    )
    
    # 3. Poll until decision is returned or timeout triggers
    print(f"Agent execution paused. Waiting for review on request '{request_id}'...")
    decision = await poll_for_decision(request_id, timeout_seconds=600)  # 10 minute timeout
    
    if decision.action == "approve":
        print(f"Request '{request_id}' APPROVED. Resuming tool call.")
        return True
    elif decision.action == "edit":
        print(f"Request '{request_id}' EDITED & APPROVED. Overriding body arguments.")
        # Modify the argument dynamically before running the tool
        tool_call.args["body"] = decision.edited_body
        return True
    elif decision.action == "reject":
        print(f"Request '{request_id}' REJECTED. Blocking tool call. Reason: {decision.reason}")
        return False
    else:
        print(f"Request '{request_id}' TIMED OUT. Blocking tool call.")
        return False
