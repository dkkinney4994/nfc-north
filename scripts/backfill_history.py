"""
One-time backfill: walks the league's previous_league_id chain back through
past seasons and pulls rosters, matchups, transactions, and draft picks for
each into data.json under "seasons_history". Run manually, once — past
seasons are frozen and don't need to be re-pulled on a schedule.
"""
import json
import sys
from pathlib import Path
from urllib.request import urlopen
from urllib.error import HTTPError

CURRENT_LEAGUE_ID = "1310099274612080640"
DATA_PATH = Path(__file__).resolve().parent.parent / "data.json"


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

    data.setdefault("seasons_history", {})

    print("Fetching current league to find previous_league_id chain...")
    current = try_get_json(f"https://api.sleeper.app/v1/league/{CURRENT_LEAGUE_ID}")
    if not current:
        print("Could not fetch current league. Aborting.")
        sys.exit(1)

    league_id = current.get("previous_league_id")
    seasons_pulled = []

    while league_id:
        print(f"\nFetching league {league_id}...")
        league = try_get_json(f"https://api.sleeper.app/v1/league/{league_id}")
        if not league:
            print("  could not fetch league info, stopping chain here")
            break

        season = league.get("season")
        print(f"  season: {season}")

        base = f"https://api.sleeper.app/v1/league/{league_id}"

        rosters = try_get_json(f"{base}/rosters") or []

        matchups = {}
        transactions = {}
        for week in range(1, 18):
            mus = try_get_json(f"{base}/matchups/{week}")
            if mus:
                matchups[str(week)] = mus
            txs = try_get_json(f"{base}/transactions/{week}")
            if txs:
                transactions[str(week)] = txs

        draft_picks = []
        draft_id = league.get("draft_id")
        if draft_id:
            picks = try_get_json(f"https://api.sleeper.app/v1/draft/{draft_id}/picks")
            if picks:
                draft_picks = picks

        data["seasons_history"][season] = {
            "rosters": rosters,
            "matchups": matchups,
            "transactions": transactions,
            "draft_picks": draft_picks,
        }
        seasons_pulled.append(season)

        league_id = league.get("previous_league_id")

    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=2)

    print(f"\nDone. Backfilled seasons: {seasons_pulled}")


if __name__ == "__main__":
    main()
