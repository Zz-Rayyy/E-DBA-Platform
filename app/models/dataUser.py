from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey
from app.models.user import User
from app.models.base import Base, SQLAlchemy
from sqlalchemy.orm import relationship
#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class DataUser(Base):
    __tablename__ = 'dataUser'
    userID = Column(Integer, ForeignKey('user.userID'), primary_key=True)
    name = Column(String(100), nullable=False)
    accessRight = Column(Integer, nullable=False)
    account = Column(Integer, nullable=False)
    quota = Column(Integer, nullable=False)
    organizationID = Column(Integer, ForeignKey('organization.organizationID'), nullable=False)
    
    user = relationship("User", backref="data_user", uselist=False)

    def __init__(self, userID, name, accessRight, account, quota, organizationID):
        super(DataUser, self).__init__()
        self.userID = userID
        self.name = name
        self.accessRight = accessRight
        self.account = account
        self.quota = quota
        self.organizationID = organizationID
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)