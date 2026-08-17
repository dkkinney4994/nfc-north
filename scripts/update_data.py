"""
Pulls current-season data from the Sleeper API and merges it into data.json.
Only touches: users, rosters, players, matchups, transactions, meta.last_updated.
Everything else in data.json (history, rules, rankings) is left untouched —
edit those fields by hand in the repo.
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

LEAGUE_ID = "1310099274612080640"
BASE = f"https://api.sleeper.app/v1/league/{LEAGUE_ID}"
DATA_PATH = Path(__file__).resolve().parent.parent / "live_data.json"


def get_json(url):
    with urlopen(url, timeout=30) as resp:
        return json.loads(resp.read().decode())


def try_get_json(url):
    try:
        return get_json(url)
    except HTTPError as e:
        print(f"  skip {url}: HTTP {e.code}")
        return None
    except Exception as e:
        print(f"  skip {url}: {e}")
        return None


def main():
    if not DATA_PATH.exists():
        print(f"data.json not found at {DATA_PATH}")
        sys.exit(1)

    with open(DATA_PATH) as f:
        data = json.load(f)

    print("Fetching users...")
    users = try_get_json(f"{BASE}/users")
    if users:
        data["users"] = users

    print("Fetching rosters...")
    rosters = try_get_json(f"{BASE}/rosters")
    if rosters:
        data["rosters"] = rosters

    # Player lookup only needs fetching once — it's large (~5MB) and rarely changes.
    if not data.get("players"):
        print("Fetching player lookup (one-time, this is large)...")
        players_raw = try_get_json("https://api.sleeper.app/v1/players/nfl")
        if players_raw:
            trimmed = {}
            for pid, p in players_raw.items():
                if p and p.get("full_name"):
                    trimmed[pid] = {
                        "full_name": p.get("full_name"),
                        "position": p.get("position"),
                        "team": p.get("team"),
                    }
            data["players"] = trimmed
            print(f"  saved {len(trimmed)} players")

    print("Fetching matchups and transactions, weeks 1-17...")
    data.setdefault("matchups", {})
    data.setdefault("transactions", {})
    for week in range(1, 18):
        mus = try_get_json(f"{BASE}/matchups/{week}")
        if mus:
            data["matchups"][str(week)] = mus
        txs = try_get_json(f"{BASE}/transactions/{week}")
        if txs:
            data["transactions"][str(week)] = txs

    print("Checking for this season's draft...")
    league_info = try_get_json(BASE)
    draft_id = league_info.get("draft_id") if league_info else None
    data.setdefault("current_draft", {"draft_id": None, "picks": []})
    if draft_id:
        picks = try_get_json(f"https://api.sleeper.app/v1/draft/{draft_id}/picks")
        if picks:
            data["current_draft"] = {"draft_id": draft_id, "picks": picks}
            print(f"  saved {len(picks)} draft picks")

    data.setdefault("meta", {})
    data["meta"]["league_id"] = LEAGUE_ID
    data["meta"]["last_updated"] = datetime.now(timezone.utc).isoformat()

    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print("Done. data.json updated.")


if __name__ == "__main__":
    main()
    main()
