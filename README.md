# ATS Integration

## What ATS Integration Means

- Your platform is the AI screening/scoring service.
- Workable (or another ATS) is the system where candidates apply.
- The integration allows candidate data to flow from the ATS to your AI engine automatically.

## Why ATS Integrations Exist

- Many companies already use ATS platforms.
- They don't want to switch to a new ATS.
- They want to add AI screening to their existing workflow.
- Integration lets them keep their ATS while using your AI capabilities.

## What Happens When a Candidate Applies

1. Candidate applies on Workable.
2. Workable creates the candidate record.
3. Workable sends a webhook event to your platform.
4. Your platform receives candidate and job data.
5. Your AI analyzes the resume.
6. Your platform generates:
   - Match score
   - Strengths
   - Missing skills
   - Recommendations
7. Results are returned to Workable or shown in your dashboard.

## What a Webhook Does

- A webhook is an automatic notification between systems.
- Workable "pushes" candidate data to your platform.
- No manual export/import is required.

### Example events

- `candidate_created`
- `candidate_moved`

## What Data You Receive

- Candidate ID
- Candidate name
- Resume URL
- Job ID
- Job title

Your AI uses this information to perform scoring.

## What You Do NOT Receive

You only receive candidates from companies that:

- Sign up for your service
- Authorize the integration
- Connect their Workable account

## Business Models

1. Candidate → Your ATS → Your AI Scoring
2. Candidate → Workable → Your AI Platform

- Companies continue using Workable.
- Your platform provides AI screening.

## What You'll Build During Integration

### On Your Platform

- ATS integration settings page
- API key management
- Webhook endpoint
- Resume analysis pipeline
- Candidate scoring engine
- Results dashboard
- Callback endpoint (optional)

### On Workable

- Configure webhook
- Send candidate events
- Authenticate requests
- Receive scoring results (if supported)
