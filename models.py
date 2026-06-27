"""
SQLAlchemy ORM models for the Free API Directory.
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(64), nullable=False, unique=True, comment="Category display name")
    slug = Column(String(64), nullable=False, unique=True, index=True, comment="URL-friendly name")
    icon = Column(String(32), nullable=False, default="folder", comment="Icon identifier")
    description = Column(String(256), nullable=True, comment="Short description")
    sort_order = Column(Integer, nullable=False, default=0, comment="Display order (lower first)")

    apis = relationship("ApiEntry", back_populates="category", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Category {self.name}>"


class ApiEntry(Base):
    __tablename__ = "api_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category_id = Column(Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(128), nullable=False, comment="API name")
    provider = Column(String(128), nullable=False, comment="Provider / company name")
    url = Column(String(512), nullable=False, comment="Official documentation URL")
    description = Column(Text, nullable=False, comment="Detailed description (Markdown)")
    tags = Column(String(256), nullable=True, comment="Comma-separated tags for search")
    is_free = Column(Boolean, nullable=False, default=True, comment="Free tier available")
    auth_type = Column(String(32), nullable=False, default="api_key", comment="api_key / no_auth / oauth")
    request_example = Column(Text, nullable=True, comment="Example request code")
    status = Column(String(16), nullable=False, default="active", comment="active / deprecated")
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    category = relationship("Category", back_populates="apis")

    def tag_list(self):
        """Return tags as a list of strings."""
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def __repr__(self):
        return f"<ApiEntry {self.name}>"
