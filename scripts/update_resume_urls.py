#!/usr/bin/env python3
import sqlite3
import json
import pathlib

p = pathlib.Path('ats_integration.db')
if not p.exists():
    print('DB not found', p)
    raise SystemExit(1)

conn = sqlite3.connect(p)
cur = conn.cursor()
cur.execute('SELECT event_id,payload FROM webhook_events')
rows = cur.fetchall()
print('total_rows=', len(rows))
found = []
for eid, payload in rows:
    try:
        data = json.loads(payload)
    except Exception:
        continue
    candidate = data.get('data', {}).get('candidate', {})
    url = candidate.get('resume_url')
    print(eid, url)
    if url == 'https://canva.link/rqzak898ih41znd':
        found.append(eid)

if not found:
    print('No updates needed')
else:
    for eid in found:
        cur.execute('SELECT payload FROM webhook_events WHERE event_id=?', (eid,))
        pjson = cur.fetchone()[0]
        data = json.loads(pjson)
        data['data']['candidate']['resume_url'] = (
            'https://canva.link/rqzak898ih41znd'
        )
        cur.execute('UPDATE webhook_events SET payload=? WHERE event_id=?', (json.dumps(data), eid))
    conn.commit()
    print('updated', found)

conn.close()
