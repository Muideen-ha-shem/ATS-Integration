Purpose

Receives candidate events from Workable.

API
POST /api/webhooks/workable
Receives
{
  "event":"candidate_created",
  "data":{
    "candidate":{
      "id":"123",
      "name":"Jane Doe",
      "resume_url":"..."
    }
  }
}


Responsibilities:

Validate

Check API key
Check company ID
Save Event
webhook_events
event_id
provider
payload
status

Trigger AI Processing
queue_resume_for_scoring()


Next is the

Resume Analysis Pipeline

This is the heart of the system.

Which my ATS already has 