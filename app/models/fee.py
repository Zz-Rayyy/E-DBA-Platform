from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Fee(Base):
    __tablename__ = 'fee'
    feeID = Column(Integer, primary_key=True, autoincrement=True)
    level1Fee = Column(Integer, nullable=False)
    level2Fee = Column(Integer, nullable=False)
    level3Fee = Column(Integer, nullable=False)

    def __init__(self, level1Fee, level2Fee, level3Fee):
        super(Fee, self).__init__()
        self.level1Fee = level1Fee
        self.level2Fee = level2Fee
        self.level3Fee = level3Fee
        
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)