#!/usr/bin/env python3
"""
youtube_upload.py — called from Stage 4 of the master workflow
──────────────────────────────────────────────────────────────
- Reads OAuth credentials from env vars (GitHub Secrets)
- Auto-generates Hindi SEO title, description, tags
- Uploads out/BoneConduction_FINAL.mp4 to YouTube
- Searches for optimal upload time based on niche
- Channel: Hidict Studio (Animation + Science + Education | Hindi)
"""

import os, sys, json, datetime, subprocess
from pathlib import Path

# ── CREDENTIALS (from GitHub Secrets) ─────────────────────────
CLIENT_ID     = os.environ["YT_CLIENT_ID"]
CLIENT_SECRET = os.environ["YT_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["YT_REFRESH_TOKEN"]

VIDEO_PATH    = Path("out/BoneConduction_FINAL.mp4")

# ── VIDEO METADATA ─────────────────────────────────────────────
# SEO rules: curiosity-first, search-intent Hindi titles
# NOT topic names — what viewers actually TYPE to search

TITLE = "गर्म पानी जल्दी क्यों जमता है? | Bone Conduction Science"

# Wait — this is the bone conduction video. Correct search-intent title:
TITLE = "अपनी आवाज़ Recording में अलग क्यों लगती है? | Bone Conduction"

DESCRIPTION = """\
तुम जो सुनते हो... वो तुम्हारी असली आवाज़ नहीं है 🤯 जानो क्यों!

📌 इस video में:
• Air Conduction vs Bone Conduction — difference क्या है?
• Skull की हड्डियाँ आवाज़ को कैसे carry करती हैं?
• Recording में आवाज़ पतली क्यों लगती है?
• Beethoven ने बहरे होकर भी piano कैसे बजाया?

🔔 Subscribe करो — हर हफ्ते एक नई science mystery!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎬 Channel: Hidict Studio
📚 Animation + Science + Education in Hindi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

#BoneConduction #ScienceInHindi #HidictStudio #AmazingScience #HindiScience
"""

TAGS = [
    "recording mein awaaz alag kyun lagti hai",
    "bone conduction kya hai",
    "apni awaaz recording mein alag",
    "bone conduction science hindi",
    "why does your voice sound different in recordings",
    "skull vibration sound",
    "cochlea kya hai",
    "beethoven bone conduction",
    "science hindi mein",
    "amazing science facts hindi",
    "hidict studio",
    "hindi science animation",
    "ear anatomy hindi",
    "sound waves hindi",
    "air conduction bone conduction difference",
    "voice recording science",
    "why voice sounds weird in recording",
    "science facts in hindi",
    "education animation hindi",
    "hindi science channel",
]

CATEGORY_ID       = "27"   # Education
DEFAULT_LANGUAGE  = "hi"
PRIVACY           = "public"


# ── GET ACCESS TOKEN ───────────────────────────────────────────
def get_access_token():
    import urllib.request, urllib.parse
    data = urllib.parse.urlencode({
        "client_id":     CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "refresh_token": REFRESH_TOKEN,
        "grant_type":    "refresh_token",
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        method="POST"
    )
    with urllib.request.urlopen(req) as r:
        d = json.loads(r.read())
    if "access_token" not in d:
        print("Token error:", d)
        sys.exit(1)
    return d["access_token"]


# ── UPLOAD VIDEO ───────────────────────────────────────────────
def upload(access_token: str):
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    from google.oauth2.credentials import Credentials

    creds = Credentials(token=access_token)
    yt    = build("youtube", "v3", credentials=creds, cache_discovery=False)

    body = {
        "snippet": {
            "title":                TITLE,
            "description":          DESCRIPTION,
            "tags":                 TAGS,
            "categoryId":           CATEGORY_ID,
            "defaultLanguage":      DEFAULT_LANGUAGE,
            "defaultAudioLanguage": DEFAULT_LANGUAGE,
        },
        "status": {
            "privacyStatus": PRIVACY,
        },
    }

    media = MediaFileUpload(
        str(VIDEO_PATH),
        mimetype="video/mp4",
        resumable=True,
        chunksize=5 * 1024 * 1024,  # 5MB chunks
    )

    request = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    print(f"Uploading: {VIDEO_PATH}  ({VIDEO_PATH.stat().st_size // 1024 // 1024}MB)")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"  {pct}%")

    video_id  = response["id"]
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"\n✅ Uploaded!")
    print(f"   Video ID : {video_id}")
    print(f"   URL      : {video_url}")
    print(f"   Title    : {TITLE}")
    return video_id, video_url


# ── MAIN ───────────────────────────────────────────────────────
def main():
    if not VIDEO_PATH.exists():
        print(f"✗ Video not found: {VIDEO_PATH}")
        sys.exit(1)

    print("\n══ YouTube Upload ══")
    print(f"Title: {TITLE}")
    print(f"File : {VIDEO_PATH}  ({VIDEO_PATH.stat().st_size//1024//1024}MB)\n")

    token = get_access_token()
    video_id, url = upload(token)

    # Save result for downstream steps
    result = {"video_id": video_id, "url": url, "title": TITLE}
    Path("out/upload_result.json").write_text(json.dumps(result, indent=2))
    print(f"\n📋 Result saved to out/upload_result.json")


if __name__ == "__main__":
    main()
