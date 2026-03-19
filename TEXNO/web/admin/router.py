from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict, List
from web.admin.auth import verify_token
from bot.database import Database
import json

router = APIRouter()
db = Database()

@router.post("/login")
async def login(data: dict):
    token = data.get('token')
    admin_token = "max_bot_admin_secret_2024"
    if token == admin_token:
        return {"status": "ok", "token": token}
    raise HTTPException(status_code=401, detail="Invalid token")

@router.get("/links")
async def get_links(user=Depends(verify_token)):
    links = db.get_all_links()
    stats = db.get_link_stats()
    stats_dict = {s['code']: s['clicks'] for s in stats}
    
    for link in links:
        link['clicks'] = stats_dict.get(link['code'], 0)
    
    return links

@router.post("/links")
async def create_link(link_data: dict, user=Depends(verify_token)):
    try:
        db.add_link(
            code=link_data['code'],
            menu_code=link_data['menu_code'],
            name=link_data['name'],
            url=link_data['url'],
            category=link_data.get('category'),
            parent_category=link_data.get('parent_category')
        )
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/links/{code}")
async def delete_link(code: str, user=Depends(verify_token)):
    try:
        db.delete_link(code)
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/users")
async def get_users(user=Depends(verify_token)):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users ORDER BY last_seen DESC LIMIT 100')
    users = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return users

@router.get("/users/stats")
async def get_user_stats(user=Depends(verify_token)):
    return db.get_user_stats()

@router.get("/stats/clicks")
async def get_click_stats(user=Depends(verify_token)):
    links = db.get_all_links()
    stats = db.get_link_stats()
    
    by_category = {'finance': 0, 'development': 0, 'infrastructure': 0}
    total_clicks = 0
    top_5 = []
    
    for stat in stats:
        total_clicks += stat['clicks']
        link = next((l for l in links if l['code'] == stat['code']), None)
        if link:
            by_category[link['category']] = by_category.get(link['category'], 0) + stat['clicks']
            top_5.append({
                'code': stat['code'],
                'name': link['name'],
                'clicks': stat['clicks']
            })
    
    top_5.sort(key=lambda x: x['clicks'], reverse=True)
    
    return {
        'total': total_clicks,
        'by_category': by_category,
        'top_5': top_5[:5]
    }

@router.get("/settings")
async def get_settings(user=Depends(verify_token)):
    return {
        'welcome_message': db.get_setting('welcome_message'),
        'bot_name': db.get_setting('bot_name'),
        'admin_ids': db.get_setting('admin_ids', [])
    }

@router.post("/settings")
async def update_settings(settings: dict, user=Depends(verify_token)):
    for key, value in settings.items():
        db.set_setting(key, value)
    return {"status": "ok"}