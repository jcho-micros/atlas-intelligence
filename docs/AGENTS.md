# Atlas Agent Contracts

## CEO Agent

Owns prioritization and decision support.

Consumes:
- CandidateProjectCreated
- ProjectHealthChanged
- LaunchReady

Emits:
- CandidateApproved
- CandidateRejected
- CandidateParked
- ProjectPrioritized

## COO Agent

Owns operational coordination.

Consumes:
- CandidateApproved
- ProductProjectCreated

Emits:
- WorkflowStarted
- DepartmentTaskCreated
- ProjectBlocked

## Research Agent

Owns market discovery and opportunity creation.

Skills:
- Research marketplace keywords
- Analyze competitors
- Score opportunities
- Create candidate projects

## Product Agent

Owns product concept and listing draft creation.

Skills:
- Generate product brief
- Generate Etsy title
- Generate description
- Generate tags
- Generate FAQ
- Generate image prompt

## Manufacturing Agent

Owns supplier and production feasibility.

Skills:
- Find vendors
- Estimate costs
- Compare quotes
- Analyze MOQ
- Identify production risks

## Finance Agent

Owns unit economics and financial viability.

Skills:
- Calculate margin
- Estimate fees
- Estimate shipping impact
- Break-even analysis
- ROI analysis

## Marketing Agent

Owns go-to-market materials.

Skills:
- Etsy SEO
- Pinterest content
- Instagram copy
- Email launch copy
- Keyword positioning

## Customer Success Agent

Owns customer-facing operations.

Skills:
- FAQ
- Return policy
- Support macros
- Personalization response templates
