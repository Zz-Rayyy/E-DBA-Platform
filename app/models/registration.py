from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Registration(Base):
    __tablename__ = 'registration'
    registrationID = Column(Integer, primary_key=True, autoincrement=True)
    userID = Column(Integer, ForeignKey('user.userID'))
    organizationNameInFull = Column(String(100), nullable=False)
    organizationNameInShort = Column(String(100), nullable=False)
    convenerEmail = Column(String(100), nullable=False)
    proofFile = Column(LargeBinary, nullable=False)
    status = Column(String(100), nullable=False)
    organizationID = Column(Integer, ForeignKey('organization.organizationID'))

    def __init__(self, userID, organizationNameInFull, organizationNameInShort, convenerEmail, proofFile, status, organizationID):
        super(Registration, self).__init__()
        self.userID = userID
        self.organizationNameInFull = organizationNameInFull
        self.organizationNameInShort = organizationNameInShort
        self.convenerEmail = convenerEmail
        self.proofFile = proofFile
        self.status = status
        self.organizationID = organizationID
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)