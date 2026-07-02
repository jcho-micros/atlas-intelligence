from __future__ import annotations

import pandas as pd


def _pct(part: float, whole: float) -> float:
    return round((part / whole) * 100, 1) if whole else 0.0


def competition_label(listings: int) -> str:
    if listings >= 100:
        return "High"
    if listings >= 40:
        return "Medium"
    return "Low"


def momentum_label(avg_views: float, avg_favorites: float) -> str:
    if avg_views >= 3000 or avg_favorites >= 100:
        return "Strong"
    if avg_views >= 1000 or avg_favorites >= 40:
        return "Moderate"
    return "Early"


def build_opportunity_insight(row: pd.Series) -> str:
    keyword = row.get("keyword", "This niche")
    score = float(row.get("score") or 0)
    avg_price = float(row.get("avg_price") or 0)
    avg_views = float(row.get("avg_views") or 0)
    avg_favorites = float(row.get("avg_favorites") or 0)
    listings = int(row.get("listings") or 0)
    personalized = int(row.get("personalized_count") or 0)
    digital = int(row.get("digital_count") or 0)

    personalization_rate = _pct(personalized, listings)
    digital_rate = _pct(digital, listings)
    competition = competition_label(listings)
    momentum = momentum_label(avg_views, avg_favorites)

    if score >= 75:
        action = "Build candidate"
    elif score >= 45:
        action = "Watch and validate"
    else:
        action = "Wait"

    if avg_price >= 45:
        price_note = "premium pricing"
    elif avg_price >= 25:
        price_note = "mid-market pricing"
    else:
        price_note = "lower-ticket pricing"

    return (
        f"{keyword} shows {momentum.lower()} demand with {price_note}. "
        f"Competition is currently {competition.lower()} based on the collected sample. "
        f"Personalization appears in {personalization_rate}% of listings and digital products represent {digital_rate}%. "
        f"Recommendation: {action}."
    )


def opportunity_badges(row: pd.Series) -> list[str]:
    badges: list[str] = []
    avg_price = float(row.get("avg_price") or 0)
    avg_views = float(row.get("avg_views") or 0)
    avg_favorites = float(row.get("avg_favorites") or 0)
    listings = int(row.get("listings") or 0)
    personalized = int(row.get("personalized_count") or 0)
    digital = int(row.get("digital_count") or 0)

    if avg_price >= 45:
        badges.append("Premium price")
    if avg_views >= 3000:
        badges.append("High views")
    if avg_favorites >= 100:
        badges.append("High favorites")
    if _pct(personalized, listings) >= 60:
        badges.append("Personalization-heavy")
    if 10 <= _pct(digital, listings) <= 55:
        badges.append("Digital mix")
    if listings <= 30:
        badges.append("Focused sample")
    return badges


def suggested_price_range(avg_price: float) -> str:
    if not avg_price:
        return "$0"
    low = max(4.99, avg_price * 0.9)
    high = avg_price * 1.15
    return f"${low:.2f} - ${high:.2f}"
