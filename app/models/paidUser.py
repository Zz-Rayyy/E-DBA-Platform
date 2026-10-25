from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class PaidUser(Base):
    __tablename__ = 'paidUser'
    userID = Column(Integer, ForeignKey('user.userID'), primary_key=True)

    def __init__(self, userID):
        super(PaidUser, self).__init__()
        self.userID = userID

#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)