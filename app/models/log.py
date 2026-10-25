from app.models.base import db
from datetime import datetime

class Log(db.Model):
    __tablename__ = 'log'
    
    logID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    organizationID = db.Column(db.Integer, db.ForeignKey('organization.organizationID'), nullable=False)
    userID = db.Column(db.Integer, db.ForeignKey('user.userID'), nullable=False)
    action = db.Column(db.String(255), nullable=False)  # 操作类型
    details = db.Column(db.Text)  # 详细信息
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)  # 操作时间
    
    # 关联关系
    organization = db.relationship('Organization', backref='logs')
    user = db.relationship('User', backref='logs') 