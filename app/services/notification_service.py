from sqlalchemy.orm import Session
from ..models.notification import Notification
from ..websocket.manager import manager
import json

class NotificationService:
    
    @staticmethod
    def create_notification(db: Session, user_id: int, title: str, message: str, type: str = "info"):
        """Create a new notification and send via WebSocket"""
        
        notification = Notification(
            user_id=user_id,
            title=title,
            message=message,
            type=type
        )
        db.add(notification)
        db.commit()
        db.refresh(notification)
        
        notification_data = {
            "id": notification.id,
            "title": title,
            "message": message,
            "type": type,
            "created_at": notification.created_at.isoformat() if notification.created_at else None
        }
        
        import asyncio
        try:
            asyncio.create_task(manager.send_to_user(user_id, notification_data))
        except Exception as e:
            print(f"Error sending WebSocket notification: {e}")
        
        return notification
    
    @staticmethod
    def get_user_notifications(db: Session, user_id: int, limit: int = 50):
        """Get notifications for a user"""
        return db.query(Notification).filter(
            Notification.user_id == user_id
        ).order_by(Notification.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_unread_count(db: Session, user_id: int):
        """Get unread notification count"""
        return db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).count()
    
    @staticmethod
    def mark_as_read(db: Session, notification_id: int, user_id: int):
        """Mark a notification as read"""
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user_id
        ).first()
        if notification:
            notification.is_read = True
            db.commit()
            return notification
        return None
    
    @staticmethod
    def mark_all_as_read(db: Session, user_id: int):
        """Mark all notifications as read for a user"""
        db.query(Notification).filter(
            Notification.user_id == user_id,
            Notification.is_read == False
        ).update({"is_read": True})
        db.commit()