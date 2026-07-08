from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import relationship

from database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String,
        nullable=True,
    )

    number = Column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )


    conversations = relationship(
        "Conversation",
        back_populates="user",
        cascade="all, delete-orphan",
        order_by="Conversation.timestamp",
    )



class Conversation(Base):
    __tablename__ = "conversations"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "role",
            "content",
            "timestamp",
            name="uq_conversation_message",
        ),
    )


    id = Column(
        Integer,
        primary_key=True,
    )


    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )


    role = Column(
        String,
        nullable=False,
    )
    # user | assistant


    content = Column(
        String,
        nullable=False,
    )


    message_type = Column(
        String,
        nullable=False,
    )
    # text | image | audio | document


    timestamp = Column(
        DateTime,
        nullable=False,
        index=True,
    )


    user = relationship(
        "User",
        back_populates="conversations",
    )