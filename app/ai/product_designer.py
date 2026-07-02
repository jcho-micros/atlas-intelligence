from __future__ import annotations

import re
from collections import Counter

from app.ai.product_models import ProductIdeaDraft


class ProductDesigner:
    """Create deterministic product ideas from Atlas marketplace data.

    v0.6 intentionally avoids an external LLM call. The goal is to turn real
    marketplace metrics into a structured product brief that can later be handed
    to an LLM, image generator, or listing publisher.
    """

    def design(self, opportunity: dict, listings: list[dict]) -> ProductIdeaDraft:
        keyword = str(opportunity.get("keyword") or "product opportunity").lower()
        avg_price = float(opportunity.get("avg_price") or 0)
        avg_views = float(opportunity.get("avg_views") or 0)
        avg_favorites = float(opportunity.get("avg_favorites") or 0)
        listing_count = int(opportunity.get("listings") or opportunity.get("listing_count") or 0)
        personalized_count = int(opportunity.get("personalized_count") or 0)
        digital_count = int(opportunity.get("digital_count") or 0)

        personalized_rate = personalized_count / listing_count if listing_count else 0
        digital_rate = digital_count / listing_count if listing_count else 0

        profile = self._profile_for_keyword(keyword, digital_rate)
        tags = self._tags(keyword, listings)
        price_min, price_max = self._price_range(avg_price, digital_rate)
        confidence = self._confidence(avg_views, avg_favorites, personalized_rate, listing_count)

        product_name = profile["product_name"]
        features = profile["features"]
        materials = profile["materials"]
        differentiators = profile["differentiators"]
        target_customer = profile["target_customer"]

        title = self._etsy_title(product_name, keyword, tags)
        description = self._description(
            product_name=product_name,
            target_customer=target_customer,
            price_min=price_min,
            price_max=price_max,
            features=features,
            differentiators=differentiators,
            keyword=keyword,
            avg_views=avg_views,
            avg_favorites=avg_favorites,
        )
        faq = self._faq(product_name, digital_rate)
        image_prompt = self._image_prompt(product_name, materials, target_customer, keyword)
        rationale = self._rationale(avg_price, avg_views, avg_favorites, personalized_rate, digital_rate)

        return ProductIdeaDraft(
            keyword=keyword,
            product_name=product_name,
            target_customer=target_customer,
            price_min=price_min,
            price_max=price_max,
            confidence=confidence,
            materials=materials,
            features=features,
            differentiators=differentiators,
            etsy_title=title,
            etsy_description=description,
            etsy_tags=tags[:13],
            faq=faq,
            image_prompt=image_prompt,
            rationale=rationale,
        )

    def _profile_for_keyword(self, keyword: str, digital_rate: float) -> dict:
        if "lineup" in keyword:
            return {
                "product_name": "Premium Magnetic Baseball Lineup Board",
                "target_customer": "Little League coaches, travel baseball coaches, and team parents",
                "materials": ["birch plywood", "dry erase acrylic", "player magnets", "dugout hook"],
                "features": ["magnetic player cards", "dry erase surface", "personalized team name", "dugout-ready hanging design"],
                "differentiators": ["premium coach-focused design", "interchangeable player magnets", "team logo option", "game-day ready layout"],
            }
        if "dugout" in keyword or "sign" in keyword:
            return {
                "product_name": "Personalized Baseball Dugout Team Sign",
                "target_customer": "youth baseball teams, tournament teams, and team moms",
                "materials": ["weather-resistant acrylic", "UV printed design", "hanging hardware"],
                "features": ["custom team name", "team colors", "optional player names", "weather-resistant finish"],
                "differentiators": ["premium custom design", "fast personalization", "team color matching", "photo-ready dugout display"],
            }
        if "banner" in keyword:
            return {
                "product_name": "Custom Baseball Tournament Team Banner",
                "target_customer": "team parents, tournament organizers, and youth sports teams",
                "materials": ["vinyl banner", "metal grommets", "full-color print"],
                "features": ["custom team name", "player names", "coach names", "large photo backdrop size"],
                "differentiators": ["tournament-ready layout", "team photo optimized", "fast editing workflow", "premium sports design"],
            }
        if "senior" in keyword or digital_rate >= 0.6:
            return {
                "product_name": "Editable Baseball Senior Night Poster Template",
                "target_customer": "senior baseball parents, team moms, and school booster clubs",
                "materials": ["Canva template", "print-ready PDF", "editable PNG"],
                "features": ["editable player name", "jersey number", "photo placeholder", "instant download"],
                "differentiators": ["fast digital delivery", "easy Canva editing", "premium senior night style", "print-shop friendly files"],
            }
        if "coach" in keyword or "gift" in keyword:
            return {
                "product_name": "Personalized Baseball Coach Appreciation Gift Set",
                "target_customer": "team parents looking for end-of-season coach gifts",
                "materials": ["engraved wood", "gift card holder", "custom message card"],
                "features": ["coach name personalization", "team name", "thank-you message", "gift-ready format"],
                "differentiators": ["personalized keepsake", "end-of-season ready", "easy team gifting", "premium presentation"],
            }
        return {
            "product_name": f"Personalized {keyword.title()}",
            "target_customer": "niche buyers looking for personalized sports products",
            "materials": ["custom printed material", "personalized design", "gift-ready packaging"],
            "features": ["custom text", "team colors", "premium layout", "fast turnaround"],
            "differentiators": ["personalization", "premium design", "clear niche positioning", "bundle options"],
        }

    def _price_range(self, avg_price: float, digital_rate: float) -> tuple[float, float]:
        if avg_price <= 0:
            return (19.99, 29.99) if digital_rate >= 0.6 else (39.99, 59.99)
        if digital_rate >= 0.6:
            return (round(max(9.99, avg_price * 0.85), 2), round(max(14.99, avg_price * 1.15), 2))
        return (round(max(14.99, avg_price * 0.95), 2), round(avg_price * 1.2, 2))

    def _tags(self, keyword: str, listings: list[dict]) -> list[str]:
        counter: Counter[str] = Counter()
        for item in listings:
            for tag in str(item.get("tags") or "").split("|"):
                tag = self._clean_tag(tag)
                if tag:
                    counter[tag] += 1

        base = [self._clean_tag(part) for part in [keyword, "baseball gift", "baseball coach", "team gift", "personalized"]]
        ranked = [tag for tag, _ in counter.most_common(30)]
        combined = []
        for tag in base + ranked:
            if tag and tag not in combined and len(tag) <= 20:
                combined.append(tag)
        while len(combined) < 13:
            fallback = ["coach gift", "little league", "sports gift", "team mom", "dugout decor", "baseball team", "custom baseball"]
            for tag in fallback:
                if tag not in combined and len(tag) <= 20:
                    combined.append(tag)
                if len(combined) >= 13:
                    break
        return combined[:13]

    def _clean_tag(self, tag: str) -> str:
        tag = re.sub(r"\s+", " ", str(tag or "").strip().lower())
        return tag[:20]

    def _confidence(self, avg_views: float, avg_favorites: float, personalized_rate: float, listings: int) -> int:
        score = 45
        if avg_views >= 3000:
            score += 20
        elif avg_views >= 1000:
            score += 10
        if avg_favorites >= 100:
            score += 15
        elif avg_favorites >= 40:
            score += 8
        if personalized_rate >= 0.5:
            score += 10
        if listings >= 20:
            score += 10
        return max(0, min(95, score))

    def _etsy_title(self, product_name: str, keyword: str, tags: list[str]) -> str:
        bits = [product_name, keyword.title(), "Personalized Baseball Gift"]
        if tags:
            bits.append(tags[0].title())
        title = " | ".join(dict.fromkeys(bits))
        return title[:140]

    def _description(
        self,
        product_name: str,
        target_customer: str,
        price_min: float,
        price_max: float,
        features: list[str],
        differentiators: list[str],
        keyword: str,
        avg_views: float,
        avg_favorites: float,
    ) -> str:
        feature_text = "\n".join([f"- {feature}" for feature in features])
        diff_text = "\n".join([f"- {item}" for item in differentiators])
        return (
            f"Introducing the {product_name}, designed for {target_customer}.\n\n"
            f"Why this product fits the market:\n"
            f"- Atlas found strong engagement around '{keyword}' with average views near {round(avg_views):,} "
            f"and average favorites near {round(avg_favorites):,}.\n"
            f"- Suggested price range: ${price_min:.2f} - ${price_max:.2f}.\n\n"
            f"Key features:\n{feature_text}\n\n"
            f"Differentiators:\n{diff_text}\n\n"
            f"Personalize it with team names, player details, colors, or coach information depending on the final product format."
        )

    def _faq(self, product_name: str, digital_rate: float) -> list[str]:
        if digital_rate >= 0.6:
            return [
                f"Is the {product_name} editable? Yes, the concept should be delivered as an editable Canva or print-ready file.",
                "Can I print it locally? Yes, provide PDF and PNG exports sized for common print shops.",
                "Is this a physical item? This concept is best positioned as a digital template unless you add a print fulfillment option.",
            ]
        return [
            f"Can the {product_name} be personalized? Yes, team name, colors, and optional player details should be supported.",
            "How fast should it ship? Atlas recommends positioning around fast turnaround because team gifts are often time-sensitive.",
            "Can this be bundled? Yes, consider bundles with player cards, magnets, or matching coach gifts.",
        ]

    def _image_prompt(self, product_name: str, materials: list[str], target_customer: str, keyword: str) -> str:
        material_text = ", ".join(materials[:4])
        return (
            f"High-quality Etsy product mockup of a {product_name} for {target_customer}. "
            f"Show {material_text}. Clean premium sports design, baseball dugout or team setting, "
            f"natural lighting, realistic product photography, no logos, no trademarked team names. Keyword context: {keyword}."
        )

    def _rationale(self, avg_price: float, avg_views: float, avg_favorites: float, personalized_rate: float, digital_rate: float) -> str:
        return (
            f"Atlas selected this concept because the niche shows average price around ${avg_price:.2f}, "
            f"average views around {round(avg_views):,}, average favorites around {round(avg_favorites):,}, "
            f"personalization rate around {round(personalized_rate * 100, 1)}%, and digital mix around {round(digital_rate * 100, 1)}%."
        )
