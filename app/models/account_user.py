from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey
from app.models.base import Base, SQLAlchemy
from app.models.user import User
from app.models.bank_account import BankAccount
#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class AccountUser(Base):
    __tablename__ = 'accountUser'
    userID = Column(Integer, ForeignKey('user.userID'), primary_key=True)
    bankAccountID = Column(Integer, ForeignKey('bank_account.bankAccountID'), primary_key=True)

    def __init__(self, userID, bankAccountID):
        super(AccountUser, self).__init__()
        self.userID = userID
        self.bankAccountID = bankAccountID

#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)