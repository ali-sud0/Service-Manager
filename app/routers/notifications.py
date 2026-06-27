import json

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from ..core.database import SessionLocal, get_db
from ..core.dependencies import get_current_active_user
from ..models.user import User
from ..services.notification_service import NotificationService
from ..websocket.manager import manager

router = APIRouter(prefix="/notifications", tags=["notifications"])

@router.get("/")
async def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notifications = NotificationService.get_user_notifications(db, current_user.id)
    unread_count = NotificationService.get_unread_count(db, current_user.id)
    
    return {
        "notifications": notifications,
        "unread_count": unread_count
    }

@router.put("/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    notification = NotificationService.mark_as_read(db, notification_id, current_user.id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

@router.put("/read-all")
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    NotificationService.mark_all_as_read(db, current_user.id)
    return {"message": "All notifications marked as read"}


@router.websocket("/ws/{user_id}")
async def websocket_endpoint(
    websocket: WebSocket, 
    user_id: int
):
    """WebSocket endpoint for real-time notifications with authentication"""
    
    token = websocket.query_params.get("token")
    
    if not token:
        await websocket.close(code=1008, reason="Authentication required")
        return
    
    payload = decode_access_token(token)
    if not payload:
        await websocket.close(code=1008, reason="Invalid token")
        return
    
    token_user_id = payload.get("sub")
    if not token_user_id or int(token_user_id) != user_id:
        await websocket.close(code=1008, reason="User ID mismatch")
        return
    
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            await websocket.close(code=1008, reason="User not found")
            return
        
        if not user.is_active:
            await websocket.close(code=1008, reason="User is inactive")
            return
    finally:
        db.close()
    
    await manager.connect(websocket, user_id)
    
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(json.dumps({"status": "ok", "timestamp": __import__('time').time()}))
    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)