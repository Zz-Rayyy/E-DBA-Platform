from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Service(Base):
    __tablename__ = 'service'
    serviceID = Column(Integer, primary_key=True, autoincrement=True)
    serviceName = Column(String(100), nullable=False)
    use_status = Column(String(100), nullable=False)
    open_status = Column(String(100), nullable=False)
    organizationID = Column(Integer, ForeignKey('organization.organizationID'), nullable=False)

    def __init__(self, serviceName, use_status, open_status, organizationID):
        super(Service, self).__init__()
        self.serviceName = serviceName
        self.use_status = use_status
        self.open_status = open_status
        self.organizationID = organizationID
        
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)