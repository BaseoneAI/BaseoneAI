from fastapi import FastAPI, Depends, HTTPException
import httpx
import os

app = FastAPI()

DMA_API_URL = "https://api.linkedin.com/rest/dmaPosts"
ACCESS_TOKEN = "AQX6G_ucy0RfxZB-BeWrkHCBPhTv6jxv6Wie0mKNX3F-D32b5o7S9nXiqACzK7tAffnFOksQPwdenkWXcCQaQ4L-FND755QaGKitX6_f9QHiCPV-DZykDxH5C_nBMLH7BkpH46WMKg9Ac1_y089YP0sI4WNap7FvqA5NacWut7ZiUzfAxip-88Mdda_cyjRK-nhtwWDnDP20XdL2mDEwVwUew9JsPNWhLjm31KQ1WSguFHQKl7GnzN3sCq71xY9zoHxb5lDYrlc3EGXl4uodqBAMU6hpgjvIugrmBAkVh9pDUDUJyMkhf4XTGNio8E8XMqBbW0xxLX91K-1J5rjMwEJikQkaIw"  # Use OAuth 3-legged token

async def fetch_recent_posts():
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
        "Content-Type": "application/json",
        "LinkedIn-Version": "202401"  # REQUIRED for LinkedIn API
    }
    params = {
        "operation": "BATCH_GET",
        "fields": "r_dma_admin_pages_content",
        "limit": 5
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.get(DMA_API_URL, headers=headers, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        return response.json()


@app.get("/recent-posts")
async def get_recent_posts():
    return await fetch_recent_posts()
