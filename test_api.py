"""Quick integration test - run from kasukabe root directory."""
import urllib.request, json, sys

BASE = 'http://localhost:8000'
TOKEN = 'DhbkH_qbZim774YrFJvk6B3i_Z8SbIPULONcW2Z7Cy0'

def req(method, path, body=None, token=None):
    url = BASE + path
    data = json.dumps(body).encode() if body else None
    headers = {'Content-Type': 'application/json'}
    if token:
        headers['X-Profile-Token'] = token
    r = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(r, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())

print("=== HEALTH ===")
s, d = req('GET', '/health')
print(f'  {s} -> {d}')

print("\n=== PROFILE ===")
s, d = req('GET', '/api/profile', token=TOKEN)
print(f'  {s} -> id={d.get("id")}, name={d.get("display_name")}')
print(f'  answers_keys={list((d.get("answers") or {}).keys())}')

print("\n=== MENTOR SESSIONS ===")
s, d = req('GET', '/api/mentor/sessions', token=TOKEN)
print(f'  {s} -> {len(d)} sessions')
for sess in d[:2]:
    print(f'  id={sess.get("id")} status={sess.get("status")} problem={sess.get("preview","")[:60]}')

if d:
    conv_id = d[0]['id']
    print(f"\n=== CONVERSATION DETAIL ({conv_id[:8]}...) ===")
    s2, d2 = req('GET', f'/api/mentor/{conv_id}', token=TOKEN)
    print(f'  {s2} -> status={d2.get("status")} msgs={len(d2.get("messages",[]))} rounds={len(d2.get("challenge_rounds",[]))}')
    for m in d2.get('messages', []):
        role = m['role']
        content = m.get('content', '')
        meta = list((m.get('metadata') or {}).keys())
        print(f'  [{role}] len={len(content)} meta={meta}')
        print(f'    {content[:200]}')

print("\n=== JOURNAL LIST ===")
s, d = req('GET', '/api/journal', token=TOKEN)
print(f'  {s} -> {len(d)} entries')
for e in d[:3]:
    ins = e.get('insight')
    print(f'  id={e.get("id")} analysis_status={e.get("analysis_status")} risk={e.get("risk_flag")}')
    if ins:
        print(f'    tags={ins.get("tags")}')
        print(f'    themes={ins.get("themes")}')
        print(f'    obs={ins.get("observation","")[:120]}')

print("\n=== GROWTH JOURNEY ===")
s, d = req('GET', '/api/growth-journey', token=TOKEN)
print(f'  {s} -> keys={list(d.keys())}')
print(f'  day_streak={d.get("day_streak")} total_reflections={d.get("total_reflections")}')
cards = d.get("factor_cards", [])
print(f'  factor_cards count={len(cards)}')
for c in cards:
    print(f'    {c.get("key")}: value={c.get("value")} change={c.get("change")}')
themes = d.get("reflection_themes_observed", [])
print(f'  reflection_themes count={len(themes)}')
for t in themes[:3]:
    print(f'    theme={t.get("theme")} total={t.get("total")}')
print(f'  weekly_report={d.get("weekly_report")}')
print(f'  weekly_anchor={d.get("weekly_anchor")}')

print("\n=== ALL TESTS DONE ===")
