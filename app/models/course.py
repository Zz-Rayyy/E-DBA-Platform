from flask import Flask
from sqlalchemy import Column, String, Integer, orm, ForeignKey, LargeBinary
from app.models.base import Base, SQLAlchemy

#app = Flask(__name__)
#app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://USER:PASSWORD@127.0.0.1:3306/E-DBA"
#app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


class Course(Base):
    __tablename__ = 'course'
    cid = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(100), nullable=False)
    units = Column(Integer, nullable=False)
    description = Column(String(100), nullable=False)
    organizationID = Column(Integer, ForeignKey('organization.organizationID'), nullable=False)

    def __init__(self, title, units, description, organizationID):
        super(Course, self).__init__()
        self.title = title
        self.units = units
        self.description = description
        self.organizationID = organizationID
        
#if __name__=='__main__':
    #db.create_all()
    #db.session.commit()
    #app.run(debug=True)