import sys
import os
import asyncio
import threading
import uvicorn

# Ensure the current directory is in Python path for local imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
from escrow import escrow_handler
from server import app

# Verify dependencies and print welcome screen
if not config.GEMINI_API_KEY and not os.getenv("GEMINI_API_KEY"):
    print("🚨 ERROR: GEMINI_API_KEY environment variable is not set.")
    print("Please create a '.env' file in this folder and add: GEMINI_API_KEY=your-api-key")
    print("You can get a free key from Google AI Studio: https://aistudio.google.com/app/api-keys")
    sys.exit(1)

# Helper to start FastAPI in a background daemon thread
def run_api_server():
    # Run uvicorn server silently so it doesn't clutter the agent's CLI output
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

# Custom tool definitions
def search_knowledge_base(query: str) -> str:
    """Searches the internal business knowledge base for information.

    Args:
        query: The search query, e.g. "pricing" or "business hours".
    """
    q = query.lower()
    if "price" in q or "pricing" in q:
        return "Pricing details: Starter plan is $19/mo, Enterprise plan is $99/mo."
    elif "hours" in q or "schedule" in q:
        return "Office hours: Mon-Fri 9:00 AM - 6:00 PM CET."
    return f"Search results for '{query}': Found no specific matches. Default to standard refund policy."

def draft_email(recipient: str, content: str) -> str:
    """Drafts a draft email in process memory without sending it.

    Args:
        recipient: The email address of the recipient.
        content: The text content of the email draft.
    """
    return f"Draft saved in memory for {recipient}. Content: '{content[:40]}...'"

def send_email(to: str, subject: str, body: str) -> str:
    """Sends an email message to a customer.

    Args:
        to: The recipient's email address (e.g. customer@example.com).
        subject: The subject header of the email.
        body: The text body of the email.
    """
    print("\n📬 ================= EMAIL DISPATCHED =================")
    print(f"To:      {to}")
    print(f"Subject: {subject}")
    print(f"Body:\n{body}")
    print("========================================================\n")
    return f"Email to {to} sent successfully."

async def main():
    # 1. Start the FastAPI local approval dashboard server in background
    server_thread = threading.Thread(target=run_api_server, daemon=True)
    server_thread.start()
    
    print("=" * 70)
    print("🚀 Google Antigravity - Email Escrow HITL Demo Active")
    print("👉 Approval Portal active at: http://localhost:8000")
    print("=" * 70)
    
    # Delay imports of antigravity until runtime
    try:
        from google.antigravity import Agent, LocalAgentConfig, CapabilitiesConfig
        from google.antigravity.hooks import policy
    except ImportError:
        print("🚨 ERROR: google-antigravity SDK is not installed.")
        print("Install it using: pip install google-antigravity")
        sys.exit(1)

    # 2. Configure safety policies with domain whitelisting
    policies = [
        policy.deny_all(),                            # Deny everything else by default
        policy.allow("search_knowledge_base"),        # Safe read operations: allowed
        policy.allow("draft_email"),                  # Safe write in-memory operations: allowed
        
        # Policy: Escrow external emails (requiring human review)
        policy.ask_user(
            "send_email",
            when=lambda args: not args.get("to", "").endswith("@mycompany.com"),
            handler=escrow_handler
        ),
        
        # Policy: Auto-approve internal emails
        policy.allow("send_email")
    ]

    # 3. Create agent configuration
    config_obj = LocalAgentConfig(
        api_key=config.GEMINI_API_KEY,
        system_instructions=(
            "You are a helpful customer support agent for our company. "
            "You have access to 'search_knowledge_base', 'draft_email', and 'send_email'. "
            "If a customer asks a question, lookup details in the knowledge base and email them the reply. "
            "Our internal domain is '@mycompany.com'."
        ),
        tools=[search_knowledge_base, draft_email, send_email],
        policies=policies,
        capabilities=CapabilitiesConfig()  # Enables write/execution tools
    )

    # 4. Instantiate and run the agent in the interactive CLI loop
    async with Agent(config_obj) as agent:
        print("\nType your message below (e.g., 'Check pricing and email it to customer@external.com')")
        await agent.run_interactive_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down demo.")
