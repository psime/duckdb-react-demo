import json
import time
import random
import requests
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

# competitions + seasons you want
COMP_SEASONS = [
    {"competition_id": 53, "season_id": 315},   # Womens Euro 2025
    {"competition_id": 2, "season_id": 44},   # La Liga 2018/19
]

ROOT = Path("/home/pete/dev/duckdb-react-demo/public/data/json") / "statsbomb"


def download_json(url: str, dest: Path, allow_404=False):

    if dest.exists():
        return True

    dest.parent.mkdir(parents=True, exist_ok=True)

    try:
        r = requests.get(url, timeout=30)

        if r.status_code == 404 and allow_404:
            return False

        r.raise_for_status()

        with open(dest, "w", encoding="utf-8") as f:
            f.write(r.text)

        time.sleep(0.2 + random.random() * 0.3)

        return True

    except requests.RequestException as e:
        print(f"Failed: {url}")
        raise e


def download_competitions():
    url = f"{BASE_URL}/competitions.json"
    dest = ROOT / "competitions.json"

    download_json(url, dest)
    print("Downloaded competitions.json")


def download_matches(comp_id: int, season_id: int):

    url = f"{BASE_URL}/matches/{comp_id}/{season_id}.json"
    dest = ROOT / "matches" / str(comp_id) / f"{season_id}.json"

    download_json(url, dest)
    print(f"Downloaded matches {comp_id}/{season_id}")

    with open(dest) as f:
        matches = json.load(f)

    return [m["match_id"] for m in matches]


def download_match_files(match_ids):

    count_360 = 0

    for mid in match_ids:

        events_url = f"{BASE_URL}/events/{mid}.json"
        events_dest = ROOT / "events" / f"{mid}.json"
        download_json(events_url, events_dest)

        lineup_url = f"{BASE_URL}/lineups/{mid}.json"
        lineup_dest = ROOT / "lineups" / f"{mid}.json"
        download_json(lineup_url, lineup_dest)

        # attempt 360
        three_sixty_url = f"{BASE_URL}/three-sixty/{mid}.json"
        three_sixty_dest = ROOT / "three-sixty" / f"{mid}.json"

        got_360 = download_json(
            three_sixty_url,
            three_sixty_dest,
            allow_404=True
        )

        if got_360:
            count_360 += 1

        print(f"Downloaded match {mid}")

    print(f"\n360 files downloaded: {count_360}")


def main():

    download_competitions()

    all_match_ids = []

    for cs in COMP_SEASONS:

        comp_id = cs["competition_id"]
        season_id = cs["season_id"]

        match_ids = download_matches(comp_id, season_id)

        print(f"{len(match_ids)} matches found")

        all_match_ids.extend(match_ids)

    download_match_files(all_match_ids)

    print(f"\nTotal matches processed: {len(all_match_ids)}")


if __name__ == "__main__":
    main()



