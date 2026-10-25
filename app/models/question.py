from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Question(Base):
    __tablename__ = 'question'
    questionID = Column(Integer, primary_key=True, autoincrement=True)
    answered = Column(String(100), nullable=False)
    response = Column(String(100), nullable=False)
    userID = Column(Integer, ForeignKey('user.userID'), nullable=False)
    
    def __init__(self, answered, response, userID):
        super(Question, self).__init__()
        self.answered = answered
        self.response = response
        self.userID = userID
        
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)