#!/usr/bin/env python3
"""Auto-poster whuland.ayunda — runs on GitHub Actions, no Muse approval.
Secrets needed in the repo: IG_ACCESS_TOKEN (Page token, never expires
if set up from a long-lived user token), IG_USER_ID is in this file.
Media is served by GitHub itself: raw.githubusercontent.com/<repo>/main/<path>
"""
import json, os, sys, time, urllib.request, urllib.parse, urllib.error
from datetime import datetime
from zoneinfo import ZoneInfo

GRAPH = "https://graph.facebook.com/v27.0"
IG_USER_ID = "17841479784382130"  # whuland.ayunda
TOKEN = os.environ["IG_ACCESS_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]  # owner/repo
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
QUEUE_PATH = "queue.json"
EST = ZoneInfo("America/New_York")

def raw_url(path):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{path}"

def api(path, params, method="POST"):
    data = urllib.parse.urlencode(params).encode() if method == "POST" else None
    url = GRAPH + path
    if method == "GET":
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method, data=data)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    if method == "POST":
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        print(f"HTTP {e.code} on {method} {path}: {body}")
        raise RuntimeError(f"Graph API HTTP {e.code}: {body}")

def poll_finished(cid):
    for _ in range(30):
        d = api(f"/{cid}", {"fields": "status_code"}, "GET")
        s = d.get("status_code")
        print(f"container {cid} status: {s}")
        if s == "FINISHED":
            return
        if s == "ERROR":
            raise RuntimeError(f"container error: {d}")
        time.sleep(10)
    raise RuntimeError(f"container {cid} not finished")

def post_item(item):
    if item["type"] == "video":
        url = raw_url(item["files"][0])
        params = {"media_type": "REELS", "video_url": url, "caption": item["caption"]}
        if item.get("cover"):
            params["cover_url"] = raw_url(item["cover"])
        cid = api(f"/{IG_USER_ID}/media", params)["id"]
    elif len(item["files"]) == 1:
        cid = api(f"/{IG_USER_ID}/media",
                  {"image_url": raw_url(item["files"][0]), "caption": item["caption"]})["id"]
    else:
        children = [api(f"/{IG_USER_ID}/media",
                        {"image_url": raw_url(f), "is_carousel_item": "true"})["id"]
                    for f in item["files"]]
        cid = api(f"/{IG_USER_ID}/media",
                  {"media_type": "CAROUSEL", "children": ",".join(children),
                   "caption": item["caption"]})["id"]
    print(f"container: {cid}")
    poll_finished(cid)
    res = api(f"/{IG_USER_ID}/media_publish", {"creation_id": cid})
    print(f"PUBLISHED {item['feed']}: {res}")
    return res

def main():
    queue = json.load(open(QUEUE_PATH))
    now = datetime.now(EST)
    changed = False
    for item in queue:
        if item.get("status") != "ready":
            continue
        due = datetime.strptime(item["publish_at_est"], "%Y-%m-%d %H:%M").replace(tzinfo=EST)
        if due <= now:
            post_item(item)
            item["status"] = "published"
            changed = True
    if changed:
        json.dump(queue, open(QUEUE_PATH, "w"), indent=2, ensure_ascii=False)
        print("queue updated")
    else:
        print("nothing due")

if __name__ == "__main__":
    main()
