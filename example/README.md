# Google Antigravity SDK — Human-in-the-Loop (HITL) Email Escrow

This is a complete, runnable example showcasing the **Email Escrow** pattern using the Google Antigravity SDK. 

It intercepts sensitive actions (like sending an email to an external customer) using a policy guardrail, halts agent execution, alerts a reviewer, and resumes the agent automatically with the reviewer's decision—even allowing the reviewer to edit the email draft before approving it.

## Architecture Flow

```
+---------------+      send_email()      +---------------+
|               | ---------------------> |               |
|  Antigravity  |                        | Antigravity   |
|     Agent     | <--------------------- | Policy Engine |
|               |      Return Value      |               |
+---------------+    (True/False/Edit)   +---------------+
        ^                                        |
        | poll_for_decision()                    | escrow_handler()
        v                                        v
+---------------+                        +---------------+
|   Firestore   | <--------------------- | Slack webhook |
|  (or Mock DB) |   Approve/Edit/Deny    |  (or Local)   |
+---------------+                        +---------------+
        ^                                        |
        | HTTP Post                              | Open browser
        v                                        v
+--------------------------------------------------------+
|              FastAPI Governance Dashboard              |
+--------------------------------------------------------+
```

## Features Demonstrated

1. **Deny-by-Default Security**: The agent runs under a strict policy framework where no tools are authorized unless whitelisted.
2. **Declarative Predicates (Whitelisting)**: Demonstrates whitelisting internal emails (e.g. `@mycompany.com`) using `when=lambda args: ...` while routing external emails to the approval queue.
3. **Escrow State Persistence**: Uses a database (Mock DB or Firestore) rather than volatile memory to make the approval flow resilient to process crashes.
4. **Interactive Editing**: Demonstrates how human reviewers can modify email content in flight and pass the updated parameters back into the agent's active execution frame.

---

## Getting Started (Local Mock Mode)

You can run this demo completely locally without configuring Slack or Firestore. It boots a local FastAPI server on a background thread that serves a visual approval dashboard.

### 1. Installation

Create a virtual environment and install the dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

*Note: The `google-antigravity` package is now listed in `requirements.txt`. Ensure your environment has access to the private package index where it is hosted.*

### 2. Configure environment

Create a `.env` file in this directory and add your Google AI Studio API key:

```env
GEMINI_API_KEY="your-api-key-here"
```

### 3. Run the Demo

Run the main script:

```bash
python main.py
```

1. You will see a terminal message showing that the **Approval Portal** is active at `http://localhost:8000`.
2. Open your web browser and navigate to `http://localhost:8000`.
3. In your terminal, chat with the agent and trigger an external email:
   * **Prompt**: `Please check our pricing and email it to client@external.com`
4. The agent will check the knowledge base, draft the email, and then print a **🚨 [MOCK SLACK ALERT]** in the terminal. The agent execution will pause.
5. Go to `http://localhost:8000` in your browser. You will see the pending email request card!
6. Modify the email body inside the dashboard (e.g. add a personal greeting or a discount code) and click **Apply Edits & Approve**.
7. Return to your terminal—the agent will instantly resume, print the modified email, and finalize the turn!

### 4. Running the Automated Integration Tests

You can also verify the entire flow (FastAPI backend, database updates, polling handler, and argument mutation) automatically using the integration test script:

```bash
python verify_escrow.py
```

---

## Production Setup (Real Slack & Firestore)

To move past mock mode and connect to Google Cloud Firestore and Slack:

1. In your `.env` file, toggle off mock mode:
   ```env
   USE_MOCK=False
   FIRESTORE_PROJECT_ID="your-gcp-project-id"
   SLACK_WEBHOOK_URL="https://hooks.slack.com/services/..."
   ```
2. Make sure your local terminal environment is authenticated with Google Cloud (e.g. via `gcloud auth application-default login`).
3. Deploy the FastAPI app (`server.py`) to a public server (like Cloud Run).
4. Point your Slack app's **Interactive Components** Request URL to `https://your-public-domain.com/slack/interactive`.
