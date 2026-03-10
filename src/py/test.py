import json
from pathlib import Path
import pandas as pd


def load_competitions(repo_root: str | Path) -> tuple[pd.DataFrame, dict]:
    """
    Load StatsBomb Open Data competitions.json and return:
      (1) competitions dataframe
      (2) a small summary dict you can print or log

    Parameters
    ----------
    repo_root : str | Path
        Path to the *root* of the statsbomb/open-data repository clone.

    Returns
    -------
    competitions_df : pd.DataFrame
    summary : dict
    """
    repo_root = Path('/home/pete/dev/duckdb-react-demo')
    comp_path = repo_root / "public" / "data" / "competitions.json"
    # sb_path = repo_root / "public" / "data"
    print(repo_root);
    print(comp_path);
    # print(locals());

    if not comp_path.exists():
        raise FileNotFoundError(
            f"Could not find {comp_path}. "
            "Make sure repo_root points to the cloned statsbomb/open-data directory."
        )

    competitions_data = json.loads(comp_path.read_text(encoding="utf-8"))
    competitions_df = pd.DataFrame(competitions_data)

    # These column names are stable in the open-data schema (gender was added in v1.1). :contentReference[oaicite:5]{index=5}
    summary = {
        "entries_competitions_json": len(competitions_df),  # competition-season entries
        "unique_competitions": competitions_df["competition_name"].nunique(),
        "unique_seasons": competitions_df["season_name"].nunique(),
        "countries": competitions_df["country_name"].nunique(),
        "genders": competitions_df["competition_gender"].value_counts(dropna=False).to_dict(),
    }

    return competitions_df, summary

# print(repo_root);
# print(comp_path);
# print(locals())
# print(locals());
# print(__name__)


# Example usage
competitions_df, summary = load_competitions(r"/home/pete/dev/duckdb-react-demo/public/data")
print(competitions_df.head())

print("=== DATASET SCOPE (local copy) ===")
for k, v in summary.items():
    print(f"{k}: {v}")

# Quick look at what fields you have
print("\nColumns:", sorted(competitions_df.columns))
print("\nSample rows:")
print(competitions_df.head(3))