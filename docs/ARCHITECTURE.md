# Architecture

Atlas follows a local-first modular architecture.

Research flow:

Keyword -> Connector -> MarketplaceListing -> ListingService -> SQLite -> OpportunityService -> Dashboard

AI is intentionally not part of data collection. AI analysis will be added later as an explanation layer over stored data.
