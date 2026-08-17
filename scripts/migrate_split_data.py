"""
One-time migration: splits the existing data.json into two files.

manual_data.json — small, stays hand-editable in GitHub's web UI forever.
  Fields: house_rules, champions, preseason, alltime, standings_by_year,
  playoffs, team_name_map, maxpf.

live_data.json — large, only ever touched by the automated scripts.
  Fields: meta, users, rosters, players, matchups, transactions,
  seasons_history, current_draft.

Run once, manually, from the Actions tab. After this runs successfully,
data.json is removed from the repo — update_data.py and backfill_history.py
both write to live_data.json going forward.
"""
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
OLD_PATH = REPO_ROOT / "data.json"
MANUAL_PATH = REPO_ROOT / "manual_data.json"
LIVE_PATH = REPO_ROOT / "live_data.json"

MANUAL_KEYS = [
    "house_rules",
    "champions",
    "preseason",
    "alltime",
    "standings_by_year",
    "playoffs",
    "team_name_map",
    "maxpf",
]

LIVE_KEYS = [
    "meta",
    "users",
    "rosters",
    "players",
    "matchups",
    "transactions",
    "seasons_history",
    "current_draft",
]


def main():
    if not OLD_PATH.exists():
        print("data.json not found — nothing to migrate. Exiting.")
        sys.exit(0)

    with open(OLD_PATH) as f:
        data = json.load(f)

    manual_data = {}
    for key in MANUAL_KEYS:
        manual_data[key] = data.get(key)

    # If maxpf wasn't added yet, default it from team_name_map's team names.
    if not manual_data.get("maxpf"):
        team_names = list((manual_data.get("team_name_map") or {}).values())
        manual_data["maxpf"] = {name: None for name in team_names}

    live_data = {}
    for key in LIVE_KEYS:
        live_data[key] = data.get(key)

    with open(MANUAL_PATH, "w") as f:
        json.dump(manual_data, f, indent=2)
    print(f"Wrote {MANUAL_PATH.name} ({MANUAL_PATH.stat().st_size} bytes)")

    with open(LIVE_PATH, "w") as f:
        json.dump(live_data, f, indent=2)
    print(f"Wrote {LIVE_PATH.name} ({LIVE_PATH.stat().st_size} bytes)")

    OLD_PATH.unlink()
    print("Removed old data.json")


if __name__ == "__main__":
    main()
