# Database Design

## Tables

### keywords
Stores product search ideas.

Fields:
- id
- keyword
- category
- priority
- status
- source
- created_at
- updated_at

### research_runs
Tracks each research attempt.

Fields:
- id
- keyword_id
- connector
- status
- started_at
- finished_at
- error_message

### listings
Stores raw marketplace listings.

Fields:
- id
- keyword_id
- research_run_id
- marketplace
- listing_id
- title
- price
- currency
- shop_name
- rating
- review_count
- url
- image_url
- raw_json
- first_seen_at
- last_seen_at

### opportunities
Stores scored niche opportunities.

Fields:
- id
- keyword_id
- score
- demand_score
- competition_score
- profit_score
- difficulty_score
- personalization_score
- confidence_score
- recommendation
- explanation
- created_at

### notes
Stores analyst observations.

Fields:
- id
- related_type
- related_id
- note_type
- content
- created_at
