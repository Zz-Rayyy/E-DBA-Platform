from flask import Flask
from sqlalchemy import Column, String, Integer, orm
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class User(Base):
    __tablename__ = 'user'
    userID = Column(Integer, primary_key=True, autoincrement=True)
    #name = Column(String(100), nullable=False)
    email = Column(String(100), nullable=False)
    #address = Column(String(100), nullable=False)
    userType = Column(String(100), nullable=False)

    def __init__(self, email, userType):
        super(User, self).__init__()
        self.email = email
        self.userType = userType

#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)