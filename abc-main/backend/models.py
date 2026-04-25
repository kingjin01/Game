from sqlalchemy import Column, Integer, String, Text
from database import Base


class Game(Base):
    __tablename__ = "games"

    id = Column(Integer, primary_key=True, index=True)
    rawg_id = Column(Integer, unique=True, index=True)
    title = Column(String(255), nullable=False)
    platforms = Column(Text, default="")
    release_date = Column(String(50), default="")
    genre = Column(String(255), default="Unknown")
    status = Column(String(50), default="Coming Soon")
    description = Column(Text, default="")
    image = Column(Text, default="")