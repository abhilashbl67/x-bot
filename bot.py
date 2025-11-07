import os
import time
import random
import pathlib
import tweepy

# ---------- Config ----------
DATA_FILE = "data/posts.txt"    # one post per line
POSTED_LOG = "data/posted.log"  # keeps track of what was already posted
MAX_LEN = 280

# ---------- Auth (from GitHub Actions Secrets) ----------
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
ACCESS_SECRET = os.getenv("ACCESS_SECRET")

if not all([API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET]):
    raise SystemExit("❌ Missing API credentials. Ensure API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET are set.")

auth = tweepy.OAuth1UserHandler(API_KEY, API_SECRET, ACCESS_TOKEN, ACCESS_SECRET)
api = tweepy.API(auth)


# ---------- Helpers ----------
def read_lines(path):
    with open(path, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def write_line(path, line):
    with open(path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

def smart_trim(text, limit=MAX_LEN):
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"

def pick_unposted(candidates, already_posted):
    pool = [l for l in candidates if l not in already_posted]
    if not pool:
        return None
    return random.choice(pool)


# ---------- Main ----------
def main():
    # Ensure data folder exists
    pathlib.Path("data").mkdir(parents=True, exist_ok=True)

    if not os.path.exists(DATA_FILE):
        raise SystemExit(f"❌ {DATA_FILE} not found. Create it and add some lines to post.")

    posted = read_lines(POSTED_LOG) if os.path.exists(POSTED_LOG) else []
    lines = read_lines(DATA_FILE)

    choice = pick_unposted(lines, posted)
    if not choice:
        print("✅ All lines already posted. Add more lines to data/posts.txt.")
        return

    text = smart_trim(choice)

    # Post with a tiny retry for transient errors
    for attempt in range(1, 4):
        try:
            api.update_status(status=text)  # Twitter API v1.1 write endpoint
            print("✅ Posted:", text)
            write_line(POSTED_LOG, choice)
            return
        except tweepy.TweepyException as e:
            print(f"⚠️ Attempt {attempt}/3 failed: {e}")
            time.sleep(5 * attempt)

    raise SystemExit("❌ Failed to post after 3 attempts.")


if __name__ == "__main__":
    main()
