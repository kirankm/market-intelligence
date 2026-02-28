"""SQLAlchemy models for the Market Intelligence News Feed."""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import (
    String, Text, Integer, Boolean, Date, DateTime, ForeignKey,
    Index, CheckConstraint, UniqueConstraint, func, JSON, Numeric
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB
from .database import Base

# ── Users & Roles ───────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    email: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    roles: Mapped[list["Role"]] = relationship(secondary="user_roles", back_populates="users")
    lists: Mapped[list["ArticleList"]] = relationship(back_populates="owner")
    stars: Mapped[list["ArticleStar"]] = relationship(back_populates="user")

class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    users: Mapped[list["User"]] = relationship(secondary="user_roles", back_populates="roles")

class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), primary_key=True)

# ── Sources ─────────────────────────────────────────────────

class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    last_success: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_failure: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    articles: Mapped[list["Article"]] = relationship(back_populates="source")

# ── Tags Taxonomy ───────────────────────────────────────────

class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, unique=True, nullable=False)

    article_tags: Mapped[list["ArticleTag"]] = relationship(back_populates="tag")

# ── Articles ────────────────────────────────────────────────

class Article(Base):
    __tablename__ = "articles"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    date: Mapped[Optional[date]] = mapped_column(Date)
    date_raw: Mapped[Optional[str]] = mapped_column(Text)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(Text)
    content_raw: Mapped[Optional[str]] = mapped_column(Text)
    content: Mapped[Optional[str]] = mapped_column(Text)
    content_hash: Mapped[Optional[str]] = mapped_column(Text)
    jina_title: Mapped[Optional[str]] = mapped_column(Text)
    jina_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="draft")
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=func.now())

    source: Mapped["Source"] = relationship(back_populates="articles")
    summaries: Mapped[list["ArticleSummary"]] = relationship(back_populates="article")
    tags: Mapped[list["ArticleTag"]] = relationship(back_populates="article")
    stars: Mapped[list["ArticleStar"]] = relationship(back_populates="article")

    __table_args__ = (
        Index("idx_articles_date", "date", postgresql_using="btree"),
        Index("idx_articles_source", "source_id"),
        Index("idx_articles_content_hash", "content_hash"),
        CheckConstraint("status IN ('draft', 'approved', 'rejected')", name="ck_articles_status"),
    )

# ── Summaries ───────────────────────────────────────────────

class ArticleSummary(Base):
    __tablename__ = "article_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    subtitle: Mapped[Optional[str]] = mapped_column(Text)
    bullets: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["Article"] = relationship(back_populates="summaries")

    __table_args__ = (
        UniqueConstraint("article_id", "version", name="uq_article_summaries_version"),
        Index("idx_article_summaries_article", "article_id"),
    )

# ── Article Tags ────────────────────────────────────────────

class ArticleTag(Base):
    __tablename__ = "article_tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="RESTRICT"), nullable=False)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=True)
    added_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    removed: Mapped[bool] = mapped_column(Boolean, default=False)
    removed_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["Article"] = relationship(back_populates="tags")
    tag: Mapped["Tag"] = relationship(back_populates="article_tags")

    __table_args__ = (
        UniqueConstraint("article_id", "tag_id", "is_auto", name="uq_article_tags"),
        Index("idx_article_tags_article", "article_id"),
        Index("idx_article_tags_tag", "tag_id"),
    )

# ── Tag Edits (audit log for training) ──────────────────────

class TagEdit(Base):
    __tablename__ = "tag_edits"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="RESTRICT"), nullable=False)
    action: Mapped[str] = mapped_column(Text, nullable=False)  # 'add' or 'remove'
    free_text: Mapped[Optional[str]] = mapped_column(Text)  # for "Other" tags
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["Article"] = relationship()
    tag: Mapped["Tag"] = relationship()

    __table_args__ = (
        CheckConstraint("action IN ('add', 'remove')", name="ck_tag_edits_action"),
        Index("idx_tag_edits_article", "article_id"),
        Index("idx_tag_edits_user", "user_id"),
    )

# ── Stars ───────────────────────────────────────────────────

class ArticleStar(Base):
    __tablename__ = "article_stars"

    id: Mapped[int] = mapped_column(primary_key=True)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    starred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    article: Mapped["Article"] = relationship(back_populates="stars")
    user: Mapped["User"] = relationship(back_populates="stars")

    __table_args__ = (
        UniqueConstraint("article_id", "user_id", name="uq_article_stars"),
        Index("idx_article_stars_article", "article_id"),
        Index("idx_article_stars_user", "user_id"),
    )

# ── Lists ───────────────────────────────────────────────────

class ArticleList(Base):
    __tablename__ = "article_lists"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped["User"] = relationship(back_populates="lists")
    items: Mapped[list["ArticleListItem"]] = relationship(back_populates="list_")

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_article_lists_owner_name"),
    )

class ArticleListItem(Base):
    __tablename__ = "article_list_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    list_id: Mapped[int] = mapped_column(ForeignKey("article_lists.id", ondelete="CASCADE"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    list_: Mapped["ArticleList"] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("list_id", "article_id", name="uq_article_list_items"),
        Index("idx_article_list_items_list", "list_id"),
    )

# ── Digests ─────────────────────────────────────────────────

class Digest(Base):
    __tablename__ = "digests"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(Text)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    status: Mapped[str] = mapped_column(Text, default="draft")
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list["DigestItem"]] = relationship(back_populates="digest")
    summaries: Mapped[list["DigestSummary"]] = relationship(back_populates="digest")

    __table_args__ = (
        CheckConstraint("date_from <= date_to", name="ck_digests_dates"),
        CheckConstraint("status IN ('draft', 'sent')", name="ck_digests_status"),
    )

class DigestItem(Base):
    __tablename__ = "digest_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    digest_id: Mapped[int] = mapped_column(ForeignKey("digests.id", ondelete="CASCADE"), nullable=False)
    article_id: Mapped[int] = mapped_column(ForeignKey("articles.id", ondelete="CASCADE"), nullable=False)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer)

    digest: Mapped["Digest"] = relationship(back_populates="items")

    __table_args__ = (
        UniqueConstraint("digest_id", "article_id", name="uq_digest_items"),
        Index("idx_digest_items_digest", "digest_id"),
    )

# ── Category Summaries ──────────────────────────────────────

class CategorySummary(Base):
    __tablename__ = "category_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id", ondelete="RESTRICT"), nullable=False)
    date_from: Mapped[date] = mapped_column(Date, nullable=False)
    date_to: Mapped[date] = mapped_column(Date, nullable=False)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tag_id", "date_from", "date_to", name="uq_category_summaries"),
        CheckConstraint("date_from <= date_to", name="ck_category_summaries_dates"),
    )

# ── Failures ────────────────────────────────────────────────

class Failure(Base):
    __tablename__ = "failures"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    source_id: Mapped[Optional[int]] = mapped_column(ForeignKey("sources.id", ondelete="SET NULL"))
    article_id: Mapped[Optional[int]] = mapped_column(ForeignKey("articles.id", ondelete="SET NULL"))
    step: Mapped[Optional[str]] = mapped_column(Text)
    error: Mapped[Optional[str]] = mapped_column(Text)
    retries: Mapped[int] = mapped_column(Integer, default=0)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        CheckConstraint("step IN ('fetch', 'cleanup', 'summarize', 'tag')", name="ck_failures_step"),
        Index("idx_failures_resolved", "resolved", postgresql_where="resolved = false"),
    )

# ── Pipeline Runs ───────────────────────────────────────────

class PipelineRun(Base):
    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="RESTRICT"), nullable=False)
    articles_fetched: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    cost: Mapped[float] = mapped_column(Numeric(10, 6), default=0)
    run_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    source: Mapped["Source"] = relationship()

    __table_args__ = (
        Index("idx_pipeline_runs_source", "source_id"),
        Index("idx_pipeline_runs_date", "run_at"),
    )

# ── App Settings ────────────────────────────────────────────

class AppSetting(Base):
    __tablename__ = "app_settings"

    key: Mapped[str] = mapped_column(Text, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)

# ── Keyword Summaries ──────────────────────────────────────

class KeywordSummary(Base):
    __tablename__ = "keyword_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    date_from: Mapped[Optional[date]] = mapped_column(Date)
    date_to: Mapped[Optional[date]] = mapped_column(Date)
    article_count: Mapped[Optional[int]] = mapped_column(Integer)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text, default="pending")
    requested_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    __table_args__ = (
        CheckConstraint("status IN ('pending', 'complete', 'failed')", name="ck_keyword_summaries_status"),
        Index("idx_keyword_summaries_status", "status", postgresql_where="status = 'pending'"),
        Index("idx_keyword_summaries_user", "requested_by"),
    )

class DigestSummary(Base):
    __tablename__ = "digest_summaries"

    id: Mapped[int] = mapped_column(primary_key=True)
    digest_id: Mapped[int] = mapped_column(ForeignKey("digests.id", ondelete="CASCADE"), nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1)
    content: Mapped[Optional[str]] = mapped_column(Text)
    is_auto: Mapped[bool] = mapped_column(Boolean, default=True)
    created_by: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    digest: Mapped["Digest"] = relationship(back_populates="summaries")

    __table_args__ = (
        UniqueConstraint("digest_id", "version", name="uq_digest_summaries_version"),
        Index("idx_digest_summaries_digest", "digest_id"),
    )
