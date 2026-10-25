from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Organization(Base):
    __tablename__ = 'organization'
    organizationID = Column(Integer, primary_key=True, autoincrement=True)
    organizationNameInFull = Column(String(100), nullable=False)
    organizationNameInShort = Column(String(100), nullable=False)
    bankName = Column(String(100), nullable=False)
    accountNo = Column(String(100), nullable=False)
    accountName = Column(String(100), nullable=False)
    password = Column(String(100), nullable=False)
    

    def __init__(self, organizationNameInFull, organizationNameInShort, bankName, accountNo, accountName, password):
        super(Organization, self).__init__()
        self.organizationNameInFull = organizationNameInFull
        self.organizationNameInShort = organizationNameInShort
        self.bankName = bankName
        self.accountNo = accountNo
        self.accountName = accountName
        self.password = password

#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)