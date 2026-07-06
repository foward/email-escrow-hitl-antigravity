from fastapi import FastAPI, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
import json
from database import db

app = FastAPI(title="Google Antigravity Email Escrow Dashboard")

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    pending_requests = await db.get_all_pending()
    
    # Premium UI CSS & layout in a single responsive HTML page
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Antigravity Email Escrow</title>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg-gradient: linear-gradient(135deg, #0d091e 0%, #150d30 50%, #06040e 100%);
                --card-bg: rgba(255, 255, 255, 0.03);
                --card-border: rgba(255, 255, 255, 0.06);
                --text-primary: #f0edf6;
                --text-secondary: #9c97b0;
                --accent-primary: #8257e5;
                --accent-cyan: #00f0ff;
                --danger: #ff2a5f;
                --success: #00ff87;
            }}
            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}
            body {{
                font-family: 'Outfit', sans-serif;
                background: var(--bg-gradient);
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                padding: 2.5rem 1rem;
                overflow-x: hidden;
            }}
            header {{
                width: 100%;
                max-width: 800px;
                margin-bottom: 2.5rem;
                text-align: center;
            }}
            header h1 {{
                font-size: 2.8rem;
                font-weight: 800;
                background: linear-gradient(90deg, #a885ff, var(--accent-cyan));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
                letter-spacing: -0.5px;
            }}
            header p {{
                color: var(--text-secondary);
                font-size: 1.15rem;
                font-weight: 300;
            }}
            main {{
                width: 100%;
                max-width: 800px;
                display: flex;
                flex-direction: column;
                gap: 2rem;
            }}
            .no-pending {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 20px;
                padding: 4rem 2rem;
                text-align: center;
                backdrop-filter: blur(20px);
                color: var(--text-secondary);
                font-size: 1.2rem;
                box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
            }}
            .card {{
                background: var(--card-bg);
                border: 1px solid var(--card-border);
                border-radius: 24px;
                padding: 2.2rem;
                backdrop-filter: blur(20px);
                box-shadow: 0 12px 40px 0 rgba(0, 0, 0, 0.5);
                display: flex;
                flex-direction: column;
                gap: 1.4rem;
                transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1), border-color 0.3s ease;
            }}
            .card:hover {{
                transform: translateY(-4px);
                border-color: rgba(255, 255, 255, 0.12);
            }}
            .card-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--card-border);
                padding-bottom: 1.2rem;
            }}
            .request-id {{
                background: rgba(130, 87, 229, 0.15);
                color: #c7b3ff;
                font-family: 'Courier New', Courier, monospace;
                padding: 0.35rem 0.8rem;
                border-radius: 8px;
                font-size: 0.9rem;
                font-weight: 600;
                border: 1px solid rgba(130, 87, 229, 0.2);
            }}
            .status-badge {{
                display: flex;
                align-items: center;
                gap: 0.6rem;
                color: var(--accent-cyan);
                font-size: 0.95rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }}
            .status-dot {{
                width: 9px;
                height: 9px;
                background-color: var(--accent-cyan);
                border-radius: 50%;
                box-shadow: 0 0 12px var(--accent-cyan);
                animation: pulse 2s infinite;
            }}
            @keyframes pulse {{
                0% {{ transform: scale(0.95); opacity: 0.8; }}
                50% {{ transform: scale(1.3); opacity: 1; }}
                100% {{ transform: scale(0.95); opacity: 0.8; }}
            }}
            .field-row {{
                display: grid;
                grid-template-columns: 90px 1fr;
                gap: 0.5rem;
                font-size: 1.05rem;
            }}
            .field-name {{
                color: var(--text-secondary);
                font-weight: 600;
            }}
            .field-val {{
                color: var(--text-primary);
            }}
            .body-container {{
                display: flex;
                flex-direction: column;
                gap: 0.6rem;
            }}
            textarea {{
                width: 100%;
                height: 180px;
                background: rgba(0, 0, 0, 0.4);
                border: 1px solid var(--card-border);
                border-radius: 12px;
                color: var(--text-primary);
                padding: 1.2rem;
                font-family: inherit;
                font-size: 1rem;
                line-height: 1.5;
                resize: vertical;
                outline: none;
                transition: border-color 0.25s ease, box-shadow 0.25s ease;
            }}
            textarea:focus {{
                border-color: var(--accent-primary);
                box-shadow: 0 0 0 3px rgba(130, 87, 229, 0.2);
            }}
            .btn-group {{
                display: flex;
                gap: 1rem;
                margin-top: 0.6rem;
            }}
            button {{
                flex: 1;
                padding: 0.95rem;
                border-radius: 12px;
                border: none;
                font-weight: 600;
                font-size: 1.02rem;
                cursor: pointer;
                transition: filter 0.2s ease, transform 0.1s ease, box-shadow 0.2s ease;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            button:active {{
                transform: scale(0.98);
            }}
            .btn-approve {{
                background: linear-gradient(90deg, var(--accent-primary), #6d39e3);
                color: #fff;
                box-shadow: 0 4px 15px rgba(130, 87, 229, 0.3);
            }}
            .btn-edit {{
                background: linear-gradient(90deg, var(--accent-cyan), #00c8d7);
                color: #0d091e;
                box-shadow: 0 4px 15px rgba(0, 240, 255, 0.25);
            }}
            .btn-reject {{
                background: rgba(255, 42, 95, 0.1);
                color: #ff527b;
                border: 1px solid rgba(255, 42, 95, 0.3);
            }}
            .btn-reject:hover {{
                background: rgba(255, 42, 95, 0.2);
                box-shadow: 0 4px 15px rgba(255, 42, 95, 0.1);
            }}
            button:hover {{
                filter: brightness(1.15);
            }}
            footer {{
                margin-top: auto;
                padding: 3rem 0 1rem 0;
                color: var(--text-secondary);
                font-size: 0.95rem;
                text-align: center;
            }}
            footer a {{
                color: var(--accent-cyan);
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <header>
            <h1>Google Antigravity</h1>
            <p>HITL Email Escrow Governance Portal</p>
        </header>
        <main id="requests-container">
            {"" if pending_requests else '<div class="no-pending">🎉 No pending emails in the escrow queue! Your agent is running or idle.</div>'}
            {"".join(f'''
            <div class="card" id="card-{req.id}">
                <div class="card-header">
                    <span class="request-id">Request ID: {req.id}</span>
                    <div class="status-badge">
                        <span class="status-dot"></span>
                        Pending Review
                    </div>
                </div>
                <div class="field-row">
                    <span class="field-name">To:</span>
                    <span class="field-val">{req.recipient}</span>
                </div>
                <div class="field-row">
                    <span class="field-name">Subject:</span>
                    <span class="field-val">{req.subject}</span>
                </div>
                <div class="body-container">
                    <span class="field-name">Email Draft:</span>
                    <textarea id="body-{req.id}">{req.body}</textarea>
                </div>
                <div class="btn-group">
                    <button class="btn-approve" onclick="resolveEscrow('{req.id}', 'approve')">Approve (As Is)</button>
                    <button class="btn-edit" onclick="resolveEscrow('{req.id}', 'edit')">Apply Edits & Approve</button>
                    <button class="btn-reject" onclick="resolveEscrow('{req.id}', 'reject')">Reject</button>
                </div>
            </div>
            ''' for req in pending_requests)}
        </main>
        
        <footer>
            Email Escrow Local Dashboard &bull; Powered by Google Antigravity SDK
        </footer>

        <script>
            async function resolveEscrow(requestId, action) {{
                const bodyText = document.getElementById('body-' + requestId).value;
                const card = document.getElementById('card-' + requestId);
                
                try {{
                    const response = await fetch('/action', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/x-www-form-urlencoded',
                        }},
                        body: new URLSearchParams({{
                            'request_id': requestId,
                            'action': action,
                            'edited_body': bodyText
                        }})
                    }});
                    
                    if (response.ok) {{
                        // Smooth scale & fade animation
                        card.style.opacity = '0';
                        card.style.transform = 'scale(0.95)';
                        card.style.transition = 'all 0.3s cubic-bezier(0.16, 1, 0.3, 1)';
                        setTimeout(() => {{
                            card.remove();
                            if (document.querySelectorAll('.card').length === 0) {{
                                document.getElementById('requests-container').innerHTML = 
                                    '<div class="no-pending">🎉 No pending emails in the escrow queue! Your agent is running or idle.</div>';
                            }}
                        }}, 300);
                    }} else {{
                        alert('Error resolving request.');
                    }}
                }} catch (e) {{
                    console.error(e);
                    alert('Network error.');
                }}
            }}
        </script>
    </body>
    </html>
    """
    return html_content

@app.post("/action")
async def action_endpoint(
    request_id: str = Form(...),
    action: str = Form(...),
    edited_body: str = Form("")
):
    success = await db.update_request(
        request_id=request_id,
        status="resolved",
        action=action,
        edited_body=edited_body,
        resolved_by="Dashboard Reviewer"
    )
    if not success:
        raise HTTPException(status_code=404, detail="Request not found")
    return {"status": "ok"}

@app.post("/slack/interactive")
async def slack_interactive(payload: str = Form(...)):
    """
    Slack Interactivity Webhook Endpoint. Slack posts webhook events here
    containing a JSON 'payload' form parameter.
    """
    try:
        data = json.loads(payload)
        action_id = data["actions"][0]["action_id"]  # Matches "approve" or "reject"
        request_id = data["actions"][0]["value"]      # The request ID in database
        
        await db.update_request(
            request_id=request_id,
            status="resolved",
            action=action_id,
            resolved_by=data["user"]["name"]
        )
        return JSONResponse(content={"text": f"Request {request_id} has been {action_id}d."})
    except Exception as e:
        print(f"Error handling Slack callback: {e}")
        raise HTTPException(status_code=400, detail="Invalid Slack interactive payload")
