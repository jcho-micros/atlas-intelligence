from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ProductIdeaDraft:
    keyword: str
    product_name: str
    target_customer: str
    price_min: float
    price_max: float
    confidence: int
    materials: list[str] = field(default_factory=list)
    features: list[str] = field(default_factory=list)
    differentiators: list[str] = field(default_factory=list)
    etsy_title: str = ""
    etsy_description: str = ""
    etsy_tags: list[str] = field(default_factory=list)
    faq: list[str] = field(default_factory=list)
    image_prompt: str = ""
    rationale: str = ""
