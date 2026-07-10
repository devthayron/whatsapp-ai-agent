from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship
from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=True)
    number = Column(String, unique=True, nullable=False, index=True)

    messages = relationship(
        "Message",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Message.sent_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    message_id = Column(String,unique=True,nullable=False,index=True)                                         
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    message_type = Column(String, nullable=False)
    sent_at = Column(DateTime, nullable=False, index=True)
    user = relationship("User", back_populates="messages")