id
company_id
provider
status
api_key
callback_url
created_at

- Example

1
company_123
workable
active
sk_live_xxx
https://...

Generate API key
Authenticates requests between your platform and external ATS systems.

id
company_id
key_hash
status
expires_at
created_at

Never store plain keys.

sha256(api_key)

## Backend Logic

When webhook arrives:

if api_key_valid():
    continue
else:
    reject()