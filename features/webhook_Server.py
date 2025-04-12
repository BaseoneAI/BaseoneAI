from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/webhook")
async def receive_webhook(request: Request):
    payload = await request.json()
    print("Webhook Received:", payload)
    return {"status": "received"}
