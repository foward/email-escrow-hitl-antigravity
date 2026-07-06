import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel
import config

class EscrowRequest(BaseModel):
    id: str
    tool: str
    recipient: str
    subject: str
    body: str
    requested_at: str
    status: str  # 'pending_review', 'resolved', 'timeout'
    action: Optional[str] = None  # 'approve', 'edit', 'reject', 'timeout'
    edited_body: Optional[str] = None
    reason: Optional[str] = None
    resolved_by: Optional[str] = None

# Global in-memory DB for local development/mock mode
_mock_db: Dict[str, EscrowRequest] = {}

class EscrowDatabase:
    def __init__(self):
        self.use_mock = config.USE_MOCK
        self.firestore = None
        if not self.use_mock:
            if not config.FIRESTORE_PROJECT_ID:
                print("No FIRESTORE_PROJECT_ID found. Defaulting to in-memory Mock DB.")
                self.use_mock = True
                return
            try:
                from google.cloud import firestore
                self.firestore = firestore.AsyncClient(project=config.FIRESTORE_PROJECT_ID)
                print(f"Connected to Google Cloud Firestore (Project: {config.FIRESTORE_PROJECT_ID}).")
            except ImportError:
                print("WARNING: google-cloud-firestore not installed. Falling back to Mock DB.")
                self.use_mock = True

    async def create_pending_request(
        self, request_id: str, tool: str, recipient: str, subject: str, body: str
    ) -> str:
        requested_at = datetime.utcnow().isoformat()
        
        request = EscrowRequest(
            id=request_id,
            tool=tool,
            recipient=recipient,
            subject=subject,
            body=body,
            requested_at=requested_at,
            status="pending_review"
        )
        
        data = request.model_dump() if hasattr(request, "model_dump") else request.dict()
        
        if self.use_mock:
            _mock_db[request_id] = request
            print(f"\n[DB-MOCK] Created pending request: {request_id} to {recipient}")
        else:
            await self.firestore.collection("escrow_requests").document(request_id).set(data)
            print(f"\n[DB-FIRESTORE] Created pending request: {request_id} to {recipient}")
        
        return request_id

    async def get_request(self, request_id: str) -> Optional[EscrowRequest]:
        if self.use_mock:
            return _mock_db.get(request_id)
        
        doc = await self.firestore.collection("escrow_requests").document(request_id).get()
        if doc.exists:
            return EscrowRequest(**doc.to_dict())
        return None

    async def update_request(self, request_id: str, **kwargs) -> bool:
        if self.use_mock:
            if request_id not in _mock_db:
                return False
            req = _mock_db[request_id]
            for key, val in kwargs.items():
                if hasattr(req, key):
                    setattr(req, key, val)
            print(f"[DB-MOCK] Updated request {request_id}: {kwargs}")
            return True
        
        doc_ref = self.firestore.collection("escrow_requests").document(request_id)
        doc = await doc_ref.get()
        if doc.exists:
            await doc_ref.update(kwargs)
            print(f"[DB-FIRESTORE] Updated request {request_id}: {kwargs}")
            return True
        return False

    async def get_all_pending(self) -> List[EscrowRequest]:
        if self.use_mock:
            return [req for req in _mock_db.values() if req.status == "pending_review"]
        
        docs = self.firestore.collection("escrow_requests").where("status", "==", "pending_review").stream()
        results = []
        async for doc in docs:
            results.append(EscrowRequest(**doc.to_dict()))
        return results

# Singleton database client
db = EscrowDatabase()
