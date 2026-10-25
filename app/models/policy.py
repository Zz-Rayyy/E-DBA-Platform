from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Policy(Base):
    __tablename__ = 'policy'
    policyID = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    file_data = Column(LargeBinary, nullable=False)

    def __init__(self, title, file_data):
        super(Policy, self).__init__()
        self.title = title
        self.file_data = file_data
        
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)