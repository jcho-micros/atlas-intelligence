from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Project(Base):
    __tablename__ = "projects"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    keywords = relationship("Keyword", back_populates="project", cascade="all, delete-orphan")


class Keyword(Base):
    __tablename__ = "keywords"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    keyword: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), default="General")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_researched_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    project = relationship("Project", back_populates="keywords")
    runs = relationship("ResearchRun", back_populates="keyword", cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="keyword", cascade="all, delete-orphan")
    opportunity = relationship("Opportunity", back_populates="keyword", uselist=False, cascade="all, delete-orphan")
    snapshots = relationship("KeywordSnapshot", back_populates="keyword", cascade="all, delete-orphan")
    product_ideas = relationship("ProductIdea", back_populates="keyword", cascade="all, delete-orphan")
    launch_plans = relationship("ProductLaunchPlan", back_populates="keyword", cascade="all, delete-orphan")
    product_projects = relationship("ProductProject", back_populates="keyword", cascade="all, delete-orphan")


class ResearchRun(Base):
    __tablename__ = "research_runs"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    connector: Mapped[str] = mapped_column(String(50), default="sample")
    status: Mapped[str] = mapped_column(String(50), default="started")
    listings_found: Mapped[int] = mapped_column(Integer, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    keyword = relationship("Keyword", back_populates="runs")
    listing_snapshots = relationship("ListingSnapshot", back_populates="research_run", cascade="all, delete-orphan")
    keyword_snapshot = relationship("KeywordSnapshot", back_populates="research_run", uselist=False, cascade="all, delete-orphan")


class Shop(Base):
    __tablename__ = "shops"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    marketplace: Mapped[str] = mapped_column(String(50), default="sample")
    external_shop_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shop_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    sales_count: Mapped[int] = mapped_column(Integer, default=0)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    listings = relationship("Listing", back_populates="shop")


class Listing(Base):
    __tablename__ = "listings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    shop_id: Mapped[int | None] = mapped_column(ForeignKey("shops.id"), nullable=True)
    marketplace: Mapped[str] = mapped_column(String(50), default="sample")
    external_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    currency: Mapped[str] = mapped_column(String(10), default="USD")
    shop_name: Mapped[str] = mapped_column(String(255), default="Unknown")
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    rating: Mapped[float] = mapped_column(Float, default=0.0)
    url: Mapped[str] = mapped_column(Text, default="")
    image_url: Mapped[str] = mapped_column(Text, default="")
    is_personalized: Mapped[bool] = mapped_column(Boolean, default=False)
    is_digital: Mapped[bool] = mapped_column(Boolean, default=False)
    shipping_price: Mapped[float] = mapped_column(Float, default=0.0)
    processing_time: Mapped[str | None] = mapped_column(String(120), nullable=True)
    num_favorers: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    tags: Mapped[str] = mapped_column(Text, default="")
    materials: Mapped[str] = mapped_column(Text, default="")
    processing_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    processing_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_timestamp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    updated_timestamp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    keyword = relationship("Keyword", back_populates="listings")
    shop = relationship("Shop", back_populates="listings")
    snapshots = relationship("ListingSnapshot", back_populates="listing", cascade="all, delete-orphan")


class Opportunity(Base):
    __tablename__ = "opportunities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), unique=True, nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    demand_score: Mapped[float] = mapped_column(Float, default=0.0)
    competition_score: Mapped[float] = mapped_column(Float, default=0.0)
    profit_score: Mapped[float] = mapped_column(Float, default=0.0)
    personalization_score: Mapped[float] = mapped_column(Float, default=0.0)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0)
    median_price: Mapped[float] = mapped_column(Float, default=0.0)
    listing_count: Mapped[int] = mapped_column(Integer, default=0)
    recommendation: Mapped[str] = mapped_column(String(50), default="WAIT")
    notes: Mapped[str] = mapped_column(Text, default="")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    keyword = relationship("Keyword", back_populates="opportunity")


class ListingSnapshot(Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = (UniqueConstraint("research_run_id", "listing_id", name="uq_run_listing_snapshot"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"), nullable=False)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id"), nullable=False)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    price: Mapped[float] = mapped_column(Float, default=0.0)
    num_favorers: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)
    quantity: Mapped[int] = mapped_column(Integer, default=0)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    research_run = relationship("ResearchRun", back_populates="listing_snapshots")
    listing = relationship("Listing", back_populates="snapshots")


class KeywordSnapshot(Base):
    __tablename__ = "keyword_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    research_run_id: Mapped[int] = mapped_column(ForeignKey("research_runs.id"), nullable=False, unique=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    listing_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_price: Mapped[float] = mapped_column(Float, default=0.0)
    median_price: Mapped[float] = mapped_column(Float, default=0.0)
    avg_views: Mapped[float] = mapped_column(Float, default=0.0)
    avg_favorites: Mapped[float] = mapped_column(Float, default=0.0)
    personalized_count: Mapped[int] = mapped_column(Integer, default=0)
    digital_count: Mapped[int] = mapped_column(Integer, default=0)
    opportunity_score: Mapped[float] = mapped_column(Float, default=0.0)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    research_run = relationship("ResearchRun", back_populates="keyword_snapshot")
    keyword = relationship("Keyword", back_populates="snapshots")


class ProductIdea(Base):
    __tablename__ = "product_ideas"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_customer: Mapped[str] = mapped_column(Text, default="")
    suggested_price_min: Mapped[float] = mapped_column(Float, default=0.0)
    suggested_price_max: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[int] = mapped_column(Integer, default=0)
    materials: Mapped[str] = mapped_column(Text, default="")
    features: Mapped[str] = mapped_column(Text, default="")
    differentiators: Mapped[str] = mapped_column(Text, default="")
    etsy_title: Mapped[str] = mapped_column(Text, default="")
    etsy_description: Mapped[str] = mapped_column(Text, default="")
    etsy_tags: Mapped[str] = mapped_column(Text, default="")
    faq: Mapped[str] = mapped_column(Text, default="")
    image_prompt: Mapped[str] = mapped_column(Text, default="")
    rationale: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="product_ideas")
    launch_plans = relationship("ProductLaunchPlan", back_populates="product_idea", cascade="all, delete-orphan")
    product_projects = relationship("ProductProject", back_populates="product_idea", cascade="all, delete-orphan")


class ProductProject(Base):
    __tablename__ = "product_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    product_idea_id: Mapped[int | None] = mapped_column(ForeignKey("product_ideas.id"), nullable=True)

    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active")
    stage: Mapped[str] = mapped_column(String(80), default="research")
    readiness_score: Mapped[int] = mapped_column(Integer, default=0)
    priority: Mapped[int] = mapped_column(Integer, default=5)

    research_status: Mapped[str] = mapped_column(String(50), default="complete")
    product_status: Mapped[str] = mapped_column(String(50), default="pending")
    manufacturing_status: Mapped[str] = mapped_column(String(50), default="pending")
    finance_status: Mapped[str] = mapped_column(String(50), default="pending")
    marketing_status: Mapped[str] = mapped_column(String(50), default="pending")
    customer_success_status: Mapped[str] = mapped_column(String(50), default="pending")
    launch_status: Mapped[str] = mapped_column(String(50), default="not_started")

    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="product_projects")
    product_idea = relationship("ProductIdea", back_populates="product_projects")
    tasks = relationship("AgentTask", back_populates="project", cascade="all, delete-orphan")
    events = relationship("AgentEvent", back_populates="project", cascade="all, delete-orphan")


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("product_projects.id"), nullable=False)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    task_name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    output: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project = relationship("ProductProject", back_populates="tasks")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("product_projects.id"), nullable=True)
    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), default="update")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("ProductProject", back_populates="events")


class ProductLaunchPlan(Base):
    __tablename__ = "product_launch_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    product_idea_id: Mapped[int] = mapped_column(ForeignKey("product_ideas.id"), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="draft")

    manufacturing_json: Mapped[str] = mapped_column(Text, default="")
    logistics_json: Mapped[str] = mapped_column(Text, default="")
    finance_json: Mapped[str] = mapped_column(Text, default="")
    customer_service_json: Mapped[str] = mapped_column(Text, default="")
    accounting_json: Mapped[str] = mapped_column(Text, default="")
    next_actions: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    keyword = relationship("Keyword", back_populates="launch_plans")
    product_idea = relationship("ProductIdea", back_populates="launch_plans")
