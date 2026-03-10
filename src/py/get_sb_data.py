import json
import time
import random
import requests
from pathlib import Path

BASE_URL = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"

# competitions + seasons you want


COMP_SEASONS = [
    {
        "competition_id": 53,
        "season_id": 315,
        "competition_name": "Womens Euro 2025",
        "season_name": "2025"
    },
    {
        "competition_id": 2,
        "season_id": 44,
        "competition_name": "La Liga",
        "season_name": "2018/19"
    },
    {
        "competition_id": 55,
        "season_id": 282,
        "competition_name": "UEFA Euro",
        "season_name": "2024"
    }

]


ROOT = Path("/home/pete/dev/duckdb-react-demo/public/data/json") / "statsbomb"


# def download_json(url: str, dest: Path, allow_404=False):

#     if dest.exists():
#         return True

#     dest.parent.mkdir(parents=True, exist_ok=True)

#     try:
#         r = requests.get(url, timeout=30)

#         if r.status_code == 404 and allow_404:
#             return False

#         r.raise_for_status()

#         with open(dest, "w", encoding="utf-8") as f:
#             f.write(r.text)

#         time.sleep(0.2 + random.random() * 0.3)

#         return True

#     except requests.RequestException as e:
#         print(f"Failed: {url}")
#         raise e

def download_json(url, dest_path, allow_404=False):
    """
    Download a JSON file if it doesn't exist.
    
    Returns:
        "downloaded" - if a new file was downloaded
        "exists"     - if file already exists locally
        "missing"    - if the request 404'd and allow_404=True
    """
    dest_path.parent.mkdir(parents=True, exist_ok=True)

    if dest_path.exists():
        return "exists"

    import requests

    try:
        r = requests.get(url)
        if r.status_code == 404 and allow_404:
            return "missing"
        r.raise_for_status()  # raise error for other bad statuses
        dest_path.write_bytes(r.content)
        return "downloaded"
    except requests.RequestException as e:
        print(f"Failed to download {url}: {e}")
        return "missing"

# def download_json(url: str, dest: Path, allow_404=False):

#     if dest.exists():
#         return "exists"

#     dest.parent.mkdir(parents=True, exist_ok=True)

#     try:
#         r = requests.get(url, timeout=30)

#         if r.status_code == 404 and allow_404:
#             return "missing"

#         r.raise_for_status()

#         with open(dest, "w", encoding="utf-8") as f:
#             f.write(r.text)

#         time.sleep(0.2)

#         return "downloaded"

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
    print(f"Downloaded matches for {comp_id}-{season_id}")
    # print(f"{comp_name} {season_name} | comp {comp_id} | season {season_id}")
    with open(dest) as f:
        matches = json.load(f)

    return [m["match_id"] for m in matches]

def log_match_status(comp_name, season_name, comp_id, season_id, match_idx, total_matches, match_id, events, lineups, frames):
    """
    Print a clear, consistent status line for a match download.
    """
    print(
        f"{comp_name} {season_name} [{comp_id}-{season_id}] | "
        f"{match_idx}/{total_matches} | match {match_id} | "
        f"events:{events} lineups:{lineups} 360:{frames}"
    )



def download_match_files(match_ids, comp_id, season_id, comp_name, season_name):
    print(f"\nProcessing {comp_name} {season_name} ({comp_id}-{season_id})")

    count_360 = 0

    for i, mid in enumerate(match_ids, 1):
        events = download_json(
            f"{BASE_URL}/events/{mid}.json",
            ROOT / "events" / f"{mid}.json"
        )

        lineups = download_json(
            f"{BASE_URL}/lineups/{mid}.json",
            ROOT / "lineups" / f"{mid}.json"
        )

        frames = download_json(
            f"{BASE_URL}/three-sixty/{mid}.json",
            ROOT / "three-sixty" / f"{mid}.json",
            allow_404=True
        )

        if frames == "downloaded":
            count_360 += 1

        # Log status immediately inside the loop
        log_match_status(
            comp_name, season_name, comp_id, season_id,
            i, len(match_ids), mid,
            events, lineups, frames
        )

    print(f"\n{comp_name} {season_name} → new 360 files: {count_360}\n")

def main():

    download_competitions()

    total_matches = 0

    for cs in COMP_SEASONS:

        comp_id = cs["competition_id"]
        season_id = cs["season_id"]
        comp_name = cs["competition_name"]
        season_name = cs["season_name"]

        print(
            f"\nFetching matches for "
            f"{comp_name} {season_name} ({comp_id}-{season_id})"
        )

        match_ids = download_matches(comp_id, season_id)

        print(f"{len(match_ids)} matches found")

        total_matches += len(match_ids)

        download_match_files(
            match_ids,
            comp_id,
            season_id,
            comp_name,
            season_name
        )

    print("\n============================")
    print(f"Total matches processed: {total_matches}")
    print("============================\n")

    print("events:", len(list((ROOT / "events").glob("*.json"))))
    print("lineups:", len(list((ROOT / "lineups").glob("*.json"))))
    print("360:", len(list((ROOT / "three-sixty").glob("*.json"))))


if __name__ == "__main__":
    main()



