from sqlalchemy import Boolean, Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    url = Column(String(1024), nullable=False, default="")
    parent_id = Column(Integer, ForeignKey("menu_items.id"), nullable=True, index=True)
    order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)
    type = Column(String(50), nullable=False, default="page")

    children = relationship(
        "MenuItem",
        back_populates="parent",
        remote_side=[id],
        order_by="MenuItem.order",
        cascade="all, delete-orphan",
    )

    parent = relationship(
        "MenuItem",
        back_populates="children",
        remote_side=[parent_id],
        uselist=False,
    )
