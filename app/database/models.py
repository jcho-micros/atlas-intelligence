from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


##############################################################################
# Enterprise Foundation Models
##############################################################################


class Organization(Base):
    __tablename__ = "organizations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    timezone: Mapped[str] = mapped_column(String(80), default="America/New_York")
    settings_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    identities = relationship("UserIdentity", back_populates="organization", cascade="all, delete-orphan")
    roles = relationship("AccessRole", back_populates="organization", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="organization", cascade="all, delete-orphan")
    audit_events = relationship("AuditEvent", back_populates="organization", cascade="all, delete-orphan")


class UserIdentity(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        UniqueConstraint("organization_id", "email", name="uq_org_identity_email"),
        UniqueConstraint("employee_id", name="uq_identity_employee"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    employee_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    system_name: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160), nullable=False)
    identity_type: Mapped[str] = mapped_column(String(50), default="human")
    status: Mapped[str] = mapped_column(String(50), default="active")
    department: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("user_identities.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="identities")
    employee = relationship("Employee", back_populates="identity", uselist=False)
    manager = relationship("UserIdentity", remote_side=[id], foreign_keys=[manager_id])
    role_assignments = relationship("UserRole", back_populates="identity", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="recipient")


class AccessRole(Base):
    __tablename__ = "access_roles"
    __table_args__ = (UniqueConstraint("organization_id", "name", name="uq_org_role_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    organization = relationship("Organization", back_populates="roles")
    permission_links = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")
    user_assignments = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    code: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    role_links = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("access_roles.id"), nullable=False)
    permission_id: Mapped[int] = mapped_column(ForeignKey("permissions.id"), nullable=False)

    role = relationship("AccessRole", back_populates="permission_links")
    permission = relationship("Permission", back_populates="role_links")


class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = (UniqueConstraint("identity_id", "role_id", name="uq_identity_role"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    identity_id: Mapped[int] = mapped_column(ForeignKey("user_identities.id"), nullable=False)
    role_id: Mapped[int] = mapped_column(ForeignKey("access_roles.id"), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    identity = relationship("UserIdentity", back_populates="role_assignments")
    role = relationship("AccessRole", back_populates="user_assignments")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("user_identities.id"), nullable=True, index=True)
    notification_type: Mapped[str] = mapped_column(String(80), default="info")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    severity: Mapped[str] = mapped_column(String(30), default="info")
    status: Mapped[str] = mapped_column(String(30), default="unread")
    resource_type: Mapped[str | None] = mapped_column(String(80), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    organization = relationship("Organization", back_populates="notifications")
    recipient = relationship("UserIdentity", back_populates="notifications")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(ForeignKey("organizations.id"), nullable=False, index=True)
    actor_identity_id: Mapped[int | None] = mapped_column(ForeignKey("user_identities.id"), nullable=True)
    actor_name: Mapped[str] = mapped_column(String(160), default="system")
    action: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_id: Mapped[str | None] = mapped_column(String(120), nullable=True)
    outcome: Mapped[str] = mapped_column(String(30), default="success")
    details_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

    organization = relationship("Organization", back_populates="audit_events")
    actor = relationship("UserIdentity")


##############################################################################
# Core Project / Research Models
##############################################################################


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
    opportunity = relationship(
        "Opportunity",
        back_populates="keyword",
        uselist=False,
        cascade="all, delete-orphan",
    )
    snapshots = relationship("KeywordSnapshot", back_populates="keyword", cascade="all, delete-orphan")
    product_ideas = relationship("ProductIdea", back_populates="keyword", cascade="all, delete-orphan")
    launch_plans = relationship("ProductLaunchPlan", back_populates="keyword", cascade="all, delete-orphan")
    product_projects = relationship("ProductProject", back_populates="keyword", cascade="all, delete-orphan")
    candidate_projects = relationship("CandidateProject", back_populates="keyword", cascade="all, delete-orphan")


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
    listing_snapshots = relationship(
        "ListingSnapshot",
        back_populates="research_run",
        cascade="all, delete-orphan",
    )
    keyword_snapshot = relationship(
        "KeywordSnapshot",
        back_populates="research_run",
        uselist=False,
        cascade="all, delete-orphan",
    )


##############################################################################
# Marketplace Models
##############################################################################


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


##############################################################################
# Analytics Models
##############################################################################


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
    candidate_projects = relationship("CandidateProject", back_populates="opportunity")


class ListingSnapshot(Base):
    __tablename__ = "listing_snapshots"
    __table_args__ = (
        UniqueConstraint("research_run_id", "listing_id", name="uq_run_listing_snapshot"),
    )

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


##############################################################################
# Product Development / Launch Models
##############################################################################


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


class CandidateProject(Base):
    __tablename__ = "candidate_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True)
    opportunity_id: Mapped[int | None] = mapped_column(ForeignKey("opportunities.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_margin: Mapped[float] = mapped_column(Float, default=0.0)
    priority: Mapped[int] = mapped_column(Integer, default=5)
    reason: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    keyword = relationship("Keyword", back_populates="candidate_projects")
    opportunity = relationship("Opportunity", back_populates="candidate_projects")


class ProductProject(Base):
    __tablename__ = "product_projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    keyword_id: Mapped[int] = mapped_column(ForeignKey("keywords.id"), nullable=False)
    product_idea_id: Mapped[int | None] = mapped_column(ForeignKey("product_ideas.id"), nullable=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), nullable=True)
    product_id: Mapped[int | None] = mapped_column(ForeignKey("products.id"), nullable=True)

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
    business = relationship("Business", back_populates="product_projects")
    product = relationship("Product", back_populates="product_projects")
    tasks = relationship("AgentTask", back_populates="project", cascade="all, delete-orphan")
    events = relationship("AgentEvent", back_populates="project", cascade="all, delete-orphan")
    manufacturing_options = relationship("ManufacturingOption", back_populates="project", cascade="all, delete-orphan")
    finance_analyses = relationship("FinanceAnalysis", back_populates="project", cascade="all, delete-orphan")
    design_concepts = relationship("DesignConcept", back_populates="project", cascade="all, delete-orphan")
    sourcing_assignments = relationship("SourcingAssignment", back_populates="project", cascade="all, delete-orphan")
    supplier_recommendations = relationship("SupplierRecommendation", back_populates="project", cascade="all, delete-orphan")


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


##############################################################################
# Business Engine Models
##############################################################################


class BusinessOpportunity(Base):
    __tablename__ = "business_opportunities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    candidate_project_id: Mapped[int | None] = mapped_column(ForeignKey("candidate_projects.id"), nullable=True)
    keyword_id: Mapped[int | None] = mapped_column(ForeignKey("keywords.id"), nullable=True)

    title: Mapped[str] = mapped_column(String(255), nullable=False)
    market: Mapped[str] = mapped_column(String(120), default="General")
    summary: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_monthly_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_margin: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(50), default="candidate")
    reason: Mapped[str] = mapped_column(Text, default="")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class Business(Base):
    __tablename__ = "businesses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    brand_name: Mapped[str] = mapped_column(String(255), default="")
    market: Mapped[str] = mapped_column(String(120), default="General")
    status: Mapped[str] = mapped_column(String(50), default="active")
    vision: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_monthly_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_margin: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    brand = relationship("Brand", back_populates="business", uselist=False, cascade="all, delete-orphan")
    products = relationship("Product", back_populates="business", cascade="all, delete-orphan")
    metrics = relationship("BusinessMetric", back_populates="business", cascade="all, delete-orphan")
    product_projects = relationship("ProductProject", back_populates="business")
    finance_analyses = relationship("FinanceAnalysis", back_populates="business", cascade="all, delete-orphan")


class Brand(Base):
    __tablename__ = "brands"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    positioning: Mapped[str] = mapped_column(Text, default="")
    voice: Mapped[str] = mapped_column(String(120), default="premium helpful coach-focused")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="brand")


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    product_idea_id: Mapped[int | None] = mapped_column(ForeignKey("product_ideas.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="concept")
    category: Mapped[str] = mapped_column(String(120), default="General")
    target_customer: Mapped[str] = mapped_column(Text, default="")
    suggested_price_min: Mapped[float] = mapped_column(Float, default=0.0)
    suggested_price_max: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    summary: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="products")
    product_idea = relationship("ProductIdea")
    product_projects = relationship("ProductProject", back_populates="product")


class BusinessMetric(Base):
    __tablename__ = "business_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int] = mapped_column(ForeignKey("businesses.id"), nullable=False)
    product_count: Mapped[int] = mapped_column(Integer, default=0)
    active_project_count: Mapped[int] = mapped_column(Integer, default=0)
    avg_confidence: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_monthly_revenue: Mapped[float] = mapped_column(Float, default=0.0)
    estimated_margin: Mapped[float] = mapped_column(Float, default=0.0)
    launch_readiness: Mapped[float] = mapped_column(Float, default=0.0)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="metrics")



##############################################################################
# Atlas Enterprise Employee Models
##############################################################################


class Department(Base):
    __tablename__ = "departments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employees = relationship(
        "Employee",
        back_populates="department",
        foreign_keys="Employee.department_id",
    )


class Employee(Base):
    __tablename__ = "employees"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    department_id: Mapped[int | None] = mapped_column(ForeignKey("departments.id"), nullable=True)
    manager_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)

    name: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(160), nullable=False)
    avatar_emoji: Mapped[str] = mapped_column(String(16), default="🤖")
    status: Mapped[str] = mapped_column(String(50), default="available")
    current_task: Mapped[str] = mapped_column(Text, default="")

    mission: Mapped[str] = mapped_column(Text, default="")
    personality: Mapped[str] = mapped_column(Text, default="")
    goals: Mapped[str] = mapped_column(Text, default="")

    performance_score: Mapped[float] = mapped_column(Float, default=0.0)
    workload: Mapped[float] = mapped_column(Float, default=0.0)
    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    department = relationship(
        "Department",
        back_populates="employees",
        foreign_keys=[department_id],
    )
    identity = relationship("UserIdentity", back_populates="employee", uselist=False)
    manager = relationship(
        "Employee",
        remote_side=[id],
        back_populates="direct_reports",
        foreign_keys=[manager_id],
    )
    direct_reports = relationship(
        "Employee",
        back_populates="manager",
        foreign_keys="Employee.manager_id",
    )
    skills = relationship("EmployeeSkill", back_populates="employee", cascade="all, delete-orphan")
    tools = relationship("EmployeeTool", back_populates="employee", cascade="all, delete-orphan")
    memories = relationship("EmployeeMemory", back_populates="employee", cascade="all, delete-orphan")
    kpis = relationship("EmployeeKPI", back_populates="employee", cascade="all, delete-orphan")
    goals_owned = relationship("EmployeeGoal", back_populates="employee", cascade="all, delete-orphan")
    thoughts = relationship("EmployeeThought", back_populates="employee", cascade="all, delete-orphan")
    decisions = relationship("EmployeeDecision", back_populates="employee", cascade="all, delete-orphan")
    reflections = relationship("EmployeeReflection", back_populates="employee", cascade="all, delete-orphan")
    sent_messages = relationship(
        "EmployeeMessage",
        foreign_keys="EmployeeMessage.sender_id",
        back_populates="sender",
        cascade="all, delete-orphan",
    )
    received_messages = relationship(
        "EmployeeMessage",
        foreign_keys="EmployeeMessage.recipient_id",
        back_populates="recipient",
        cascade="all, delete-orphan",
    )


class EmployeeSkill(Base):
    __tablename__ = "employee_skills"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    skill: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    proficiency: Mapped[float] = mapped_column(Float, default=0.8)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="skills")


class EmployeeTool(Base):
    __tablename__ = "employee_tools"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    tool_name: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    access_level: Mapped[str] = mapped_column(String(80), default="standard")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="tools")


class EmployeeMessage(Base):
    __tablename__ = "employee_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    recipient_id: Mapped[int | None] = mapped_column(ForeignKey("employees.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="unread")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    read_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sender = relationship("Employee", foreign_keys=[sender_id], back_populates="sent_messages")
    recipient = relationship("Employee", foreign_keys=[recipient_id], back_populates="received_messages")


class EmployeeMemory(Base):
    __tablename__ = "employee_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(80), default="general")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    importance: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="memories")


class EmployeeKPI(Base):
    __tablename__ = "employee_kpis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    metric_name: Mapped[str] = mapped_column(String(120), nullable=False)
    metric_value: Mapped[float] = mapped_column(Float, default=0.0)
    target_value: Mapped[float] = mapped_column(Float, default=0.0)
    captured_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="kpis")


class EmployeeGoal(Base):
    __tablename__ = "employee_goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    goal_type: Mapped[str] = mapped_column(String(80), default="employee")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="active")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="goals_owned")


class EmployeeThought(Base):
    __tablename__ = "employee_thoughts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    thought_type: Mapped[str] = mapped_column(String(80), default="work_cycle")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.75)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="thoughts")


class EmployeeDecision(Base):
    __tablename__ = "employee_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    decision_type: Mapped[str] = mapped_column(String(100), default="runtime")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, default="")
    outcome: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.75)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="decisions")


class EmployeeReflection(Base):
    __tablename__ = "employee_reflections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    employee_id: Mapped[int] = mapped_column(ForeignKey("employees.id"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    lesson: Mapped[str] = mapped_column(Text, default="")
    importance: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", back_populates="reflections")


##############################################################################
# Communications Hub Models
##############################################################################


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    subject: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    conversation_type: Mapped[str] = mapped_column(String(80), default="internal")
    context_type: Mapped[str] = mapped_column(String(80), default="company")
    context_name: Mapped[str] = mapped_column(String(255), default="Atlas Enterprise", index=True)
    summary: Mapped[str] = mapped_column(Text, default="")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    status: Mapped[str] = mapped_column(String(50), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    participants = relationship("ConversationParticipant", back_populates="conversation", cascade="all, delete-orphan")
    messages = relationship("ConversationMessage", back_populates="conversation", cascade="all, delete-orphan")
    actions = relationship("CommunicationAction", back_populates="conversation", cascade="all, delete-orphan")


class ConversationParticipant(Base):
    __tablename__ = "conversation_participants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    participant_type: Mapped[str] = mapped_column(String(80), default="employee")
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(120), default="participant")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="participants")


class ConversationMessage(Base):
    __tablename__ = "conversation_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    sender_name: Mapped[str] = mapped_column(String(255), nullable=False)
    message_type: Mapped[str] = mapped_column(String(80), default="note")
    body: Mapped[str] = mapped_column(Text, nullable=False)
    requires_response: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class CommunicationAction(Base):
    __tablename__ = "communication_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    owner_name: Mapped[str] = mapped_column(String(255), default="Mia Stone")
    action_type: Mapped[str] = mapped_column(String(120), default="follow_up")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="open")
    due_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    conversation = relationship("Conversation", back_populates="actions")


##############################################################################
# Vendor Intelligence Models
##############################################################################


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(120), default="Manufacturing")
    relationship_status: Mapped[str] = mapped_column(String(80), default="prospect")
    location: Mapped[str] = mapped_column(String(255), default="")
    website: Mapped[str] = mapped_column(Text, default="")
    contact_name: Mapped[str] = mapped_column(String(255), default="")
    contact_email: Mapped[str] = mapped_column(String(255), default="")
    capabilities: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    trust_score: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    communication_score: Mapped[float] = mapped_column(Float, default=0.0)
    pricing_score: Mapped[float] = mapped_column(Float, default=0.0)
    delivery_score: Mapped[float] = mapped_column(Float, default=0.0)
    average_lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    minimum_order_quantity: Mapped[int] = mapped_column(Integer, default=0)
    average_margin: Mapped[float] = mapped_column(Float, default=0.0)
    projects_completed: Mapped[int] = mapped_column(Integer, default=0)
    risk_level: Mapped[str] = mapped_column(String(80), default="medium")
    recommendation: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    contacts = relationship("VendorContact", back_populates="vendor", cascade="all, delete-orphan")
    quotes = relationship("VendorQuote", back_populates="vendor", cascade="all, delete-orphan")
    events = relationship("VendorEvent", back_populates="vendor", cascade="all, delete-orphan")


class VendorContact(Base):
    __tablename__ = "vendor_contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(160), default="")
    email: Mapped[str] = mapped_column(String(255), default="")
    phone: Mapped[str] = mapped_column(String(80), default="")
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="contacts")


class VendorQuote(Base):
    __tablename__ = "vendor_quotes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    landed_cost: Mapped[float] = mapped_column(Float, default=0.0)
    moq: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    quote_status: Mapped[str] = mapped_column(String(80), default="draft")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="quotes")


class VendorEvent(Base):
    __tablename__ = "vendor_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vendor_id: Mapped[int] = mapped_column(ForeignKey("vendors.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(160), default="Atlas")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    vendor = relationship("Vendor", back_populates="events")


class ManufacturingOption(Base):
    __tablename__ = "manufacturing_options"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("product_projects.id"), nullable=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    supplier_type: Mapped[str] = mapped_column(String(120), default="manufacturer")
    country: Mapped[str] = mapped_column(String(120), default="")
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    setup_cost: Mapped[float] = mapped_column(Float, default=0.0)
    moq: Mapped[int] = mapped_column(Integer, default=0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    shipping_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    landed_cost: Mapped[float] = mapped_column(Float, default=0.0)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0)
    risk_score: Mapped[float] = mapped_column(Float, default=0.0)
    margin_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    vendor_score: Mapped[float] = mapped_column(Float, default=0.0)
    recommendation: Mapped[str] = mapped_column(String(80), default="review")
    notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(80), default="candidate")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("ProductProject", back_populates="manufacturing_options")



##############################################################################
# Design & Manufacturing Execution Models
##############################################################################


class DesignConcept(Base):
    __tablename__ = "design_concepts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("product_projects.id"), nullable=False)
    designer_name: Mapped[str] = mapped_column(String(160), default="Noah Reed")
    concept_name: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_version: Mapped[int] = mapped_column(Integer, default=1)
    design_rationale: Mapped[str] = mapped_column(Text, default="")
    materials: Mapped[str] = mapped_column(Text, default="")
    dimensions: Mapped[str] = mapped_column(String(255), default="")
    target_customer: Mapped[str] = mapped_column(Text, default="")
    suggested_price: Mapped[float] = mapped_column(Float, default=0.0)
    image_prompt: Mapped[str] = mapped_column(Text, default="")
    mockup_svg: Mapped[str] = mapped_column(Text, default="")
    designer_notes: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(80), default="review")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project = relationship("ProductProject", back_populates="design_concepts")
    events = relationship("DesignEvent", back_populates="concept", cascade="all, delete-orphan")


class DesignEvent(Base):
    __tablename__ = "design_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    concept_id: Mapped[int] = mapped_column(ForeignKey("design_concepts.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    actor: Mapped[str] = mapped_column(String(160), default="Noah Reed")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    concept = relationship("DesignConcept", back_populates="events")


class SourcingAssignment(Base):
    __tablename__ = "sourcing_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("product_projects.id"), nullable=False)
    design_concept_id: Mapped[int | None] = mapped_column(ForeignKey("design_concepts.id"), nullable=True)
    owner_name: Mapped[str] = mapped_column(String(160), default="David")
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    requirements: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(80), default="assigned")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project = relationship("ProductProject", back_populates="sourcing_assignments")
    design_concept = relationship("DesignConcept")


class SupplierRecommendation(Base):
    __tablename__ = "supplier_recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("product_projects.id"), nullable=False)
    vendor_id: Mapped[int | None] = mapped_column(ForeignKey("vendors.id"), nullable=True)
    supplier_name: Mapped[str] = mapped_column(String(255), nullable=False)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    reason: Mapped[str] = mapped_column(Text, default="")
    landed_cost: Mapped[float] = mapped_column(Float, default=0.0)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0)
    moq: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(80), default="recommended")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project = relationship("ProductProject", back_populates="supplier_recommendations")
    vendor = relationship("Vendor")


##############################################################################
# Finance Intelligence Models
##############################################################################


class FinanceAnalysis(Base):
    __tablename__ = "finance_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    business_id: Mapped[int | None] = mapped_column(ForeignKey("businesses.id"), nullable=True)
    project_id: Mapped[int | None] = mapped_column(ForeignKey("product_projects.id"), nullable=True)
    scenario_name: Mapped[str] = mapped_column(String(120), default="base")
    selling_price: Mapped[float] = mapped_column(Float, default=0.0)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    packaging_cost: Mapped[float] = mapped_column(Float, default=0.0)
    outbound_shipping_cost: Mapped[float] = mapped_column(Float, default=0.0)
    marketplace_fee: Mapped[float] = mapped_column(Float, default=0.0)
    payment_fee: Mapped[float] = mapped_column(Float, default=0.0)
    ad_cost: Mapped[float] = mapped_column(Float, default=0.0)
    reserve_cost: Mapped[float] = mapped_column(Float, default=0.0)
    total_variable_cost: Mapped[float] = mapped_column(Float, default=0.0)
    gross_profit: Mapped[float] = mapped_column(Float, default=0.0)
    gross_margin: Mapped[float] = mapped_column(Float, default=0.0)
    break_even_units: Mapped[int] = mapped_column(Integer, default=0)
    target_price: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_units_estimate: Mapped[int] = mapped_column(Integer, default=0)
    monthly_profit_estimate: Mapped[float] = mapped_column(Float, default=0.0)
    approval_status: Mapped[str] = mapped_column(String(80), default="review")
    recommendation: Mapped[str] = mapped_column(Text, default="")
    assumptions: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="finance_analyses")
    project = relationship("ProductProject", back_populates="finance_analyses")
    scenarios = relationship("FinanceScenario", back_populates="analysis", cascade="all, delete-orphan")
    events = relationship("FinanceEvent", back_populates="analysis", cascade="all, delete-orphan")


class FinanceScenario(Base):
    __tablename__ = "finance_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("finance_analyses.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    selling_price: Mapped[float] = mapped_column(Float, default=0.0)
    unit_cost: Mapped[float] = mapped_column(Float, default=0.0)
    gross_margin: Mapped[float] = mapped_column(Float, default=0.0)
    monthly_units: Mapped[int] = mapped_column(Integer, default=0)
    monthly_profit: Mapped[float] = mapped_column(Float, default=0.0)
    risk_level: Mapped[str] = mapped_column(String(80), default="medium")
    notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis = relationship("FinanceAnalysis", back_populates="scenarios")


class FinanceEvent(Base):
    __tablename__ = "finance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    analysis_id: Mapped[int] = mapped_column(ForeignKey("finance_analyses.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    actor: Mapped[str] = mapped_column(String(160), default="Michael")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    analysis = relationship("FinanceAnalysis", back_populates="events")


##############################################################################
# Agent Framework Models
##############################################################################


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("product_projects.id"), nullable=False)

    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    task_type: Mapped[str] = mapped_column(String(120), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(50), default="pending")
    priority: Mapped[int] = mapped_column(Integer, default=5)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    project = relationship("ProductProject", back_populates="tasks")


class AgentEvent(Base):
    __tablename__ = "agent_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("product_projects.id"), nullable=False)

    agent_name: Mapped[str] = mapped_column(String(120), nullable=False)
    event_type: Mapped[str] = mapped_column(String(120), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project = relationship("ProductProject", back_populates="events")
