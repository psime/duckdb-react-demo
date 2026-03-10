import json
from pathlib import Path
import pandas as pd
import numpy as np


def analyze_match_structure(data_path, competition_id=55, season_id=282):
    """
    Analyze match-level data structure for a specific competition-season pair.
    
    Parameters:
    data_path (str): Path to StatsBomb data
    competition_id (int): Competition identifier
    season_id (int): Season identifier
    
    Returns:
    dict: Match structure analysis with schema information
    """
    matches_path = Path(data_path)  / "matches" / str(competition_id) / f"{season_id}.json"
    
    if not matches_path.exists():
        return {"error": f"Matches file not found: {matches_path}"}
    
    with open(matches_path, 'r', encoding='utf-8') as f:
        matches_data = json.load(f)
    
    matches_df = pd.DataFrame(matches_data)
    
    print("=== MATCH STRUCTURE ANALYSIS ===")
    print(f"Competition ID: {competition_id}, Season ID: {season_id}")
    print(f"Total matches: {len(matches_df)}")
    print(f"Schema columns: {list(matches_df.columns)}")
    
    # Analyze match metadata
    if len(matches_df) > 0:
        sample_match = matches_df.iloc[0]
        print(f"\nSample Match Metadata:")
        print(f"  Match ID: {sample_match.get('match_id')}")
        print(f"  Date: {sample_match.get('match_date')}")
        print(f"  Kick-off: {sample_match.get('kick_off')}")
        
        # Extract team information
        home_team = sample_match.get('home_team', {})
        away_team = sample_match.get('away_team', {})
        print(f"  Home team: {home_team.get('home_team_name', 'Unknown')}")
        print(f"  Away team: {away_team.get('away_team_name', 'Unknown')}")
        
        # Temporal analysis
        if 'match_date' in matches_df.columns:
            dates = pd.to_datetime(matches_df['match_date'])
            print(f"\nTemporal Coverage:")
            print(f"  Date range: {dates.min().date()} to {dates.max().date()}")
            print(f"  Duration: {(dates.max() - dates.min()).days} days")
    
    return {
        "matches_df": matches_df,
        "total_matches": len(matches_df),
        "schema_columns": list(matches_df.columns)
    }

def analyze_data_structure(data_path):
    """
    Analyze the file structure and organizational hierarchy of StatsBomb data.
    
    Parameters:
    data_path (str): Path to StatsBomb data directory
    
    Returns:
    dict: Structural analysis with file counts and organization metrics
    """
    from pathlib import Path
    
    data_dir = Path(data_path)
    
    # Analyze directory structure
    structure_analysis = {
        'competitions_file': (data_dir / "competitions.json").exists(),
        'events_dir': (data_dir / "events").exists(),
        'matches_dir': (data_dir / "matches").exists(),
        'lineups_dir': (data_dir / "lineups").exists(),
        'three_sixty_dir': (data_dir / "three-sixty").exists()
    }
    
    print("=== DATA STRUCTURE VALIDATION ===")
    for component, exists in structure_analysis.items():
        status = "✓" if exists else "✗"
        print(f"{status} {component.replace('_', ' ').title()}: {'Found' if exists else 'Missing'}")
    
    # Count files in each directory
    if structure_analysis['events_dir']:
        events_count = len(list((data_dir / "events").glob("*.json")))
        print(f"\nFile Counts:")
        print(f"  Event files: {events_count}")
        
        if structure_analysis['lineups_dir']:
            lineups_count = len(list((data_dir / "lineups").glob("*.json")))
            print(f"  Lineup files: {lineups_count}")
            
        if structure_analysis['three_sixty_dir']:
            three_sixty_count = len(list((data_dir / "three-sixty").glob("*.json")))
            print(f"  360 tracking files: {three_sixty_count}")
    
    return structure_analysis


def analyze_360_coverage(competitions_df):
    """
    Analyze StatsBomb 360 data availability and coverage patterns.
    
    Returns:
    dict: 360 data coverage statistics and patterns
    """
    # Identify competitions with 360 data
    has_360 = competitions_df[competitions_df['match_available_360'].notna()]
    
    print("=== STATSBOMB 360 DATA COVERAGE ===")
    print(f"Competitions with 360 data: {len(has_360)} / {len(competitions_df)} ({100*len(has_360)/len(competitions_df):.1f}%)")
    
    if len(has_360) > 0:
        print("\nCompetitions with 360 data:")
        for _, row in has_360.iterrows():
            print(f"  {row['competition_name']} {row['season_name']}")
        
        # Temporal analysis of 360 data availability
        has_360['year'] = has_360['season_name'].str.extract('(\d{4})', expand=False).astype(float)
        year_analysis = has_360.groupby('year').size()
        
        print(f"\n360 Data Temporal Distribution:")
        for year, count in year_analysis.items():
            if not np.isnan(year):
                print(f"  {int(year)}: {count} competitions")
    
    return {
        'total_360_competitions': len(has_360),
        'coverage_percentage': 100 * len(has_360) / len(competitions_df),
        '360_competitions': has_360[['competition_name', 'season_name', 'match_available_360']]
    }


def analyze_competition_hierarchy(competitions_df: pd.DataFrame) -> dict:
    """
    Summarize the competition→season hierarchy encoded in competitions.json.

    Returns a dict so you can log it, print it, or reuse it in later sections.
    """
    comp_counts = competitions_df["competition_name"].value_counts()

    seasons_per_comp = comp_counts.to_numpy()

    summary = {
        "top_competitions_by_seasons": comp_counts.head(10),
        "seasons_per_competition": {
            "mean": float(np.mean(seasons_per_comp)),
            "median": float(np.median(seasons_per_comp)),
            "std": float(np.std(seasons_per_comp, ddof=0)),
            "min": int(np.min(seasons_per_comp)),
            "max": int(np.max(seasons_per_comp)),
        }
    }

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
    repo_root = Path(repo_root)
    comp_path = repo_root / "competitions.json"

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



def analyze_event_structure(data_path, match_id):
    """
    Detailed analysis of event data structure and mathematical properties.
    
    Parameters:
    data_path (str): Path to StatsBomb data
    match_id (int): Specific match identifier
    
    Returns:
    dict: Comprehensive event structure analysis
    """
    events_path = Path(data_path) / "events" / f"{match_id}.json"
    print(events_path)
    
    if not events_path.exists():
        return {"error": f"Events file not found for match {match_id}"}
    
    with open(events_path, 'r', encoding='utf-8') as f:
        events_data = json.load(f)
    
    events_df = pd.DataFrame(events_data)
    
    print("=== EVENT DATA STRUCTURE ANALYSIS ===")
    print(f"Match ID: {match_id}")
    print(f"Total events: {len(events_df)} = n_m")
    print(f"Event schema dimensions: {events_df.shape}")
    print(f"Column count: {len(events_df.columns)}")
    
    # Event type distribution analysis
    if 'type' in events_df.columns:
        event_types = events_df['type'].apply(
            lambda x: x['name'] if isinstance(x, dict) else str(x)
        ).value_counts()
        
        print(f"\nEvent Type Distribution (|E_type|):")
        print(f"Unique event types: {len(event_types)}")

        print("Top 10 most frequent events")        
        # Top 10 most frequent events

        for event_type, count in event_types.head(15).items():
            percentage = (count / len(events_df)) * 100
            print(f"  {event_type}: {count} ({percentage:.1f}%)")
        
        # Statistical analysis of event frequencies
        frequencies = event_types.values
        print(f"\nFrequency Statistics:")
        print(f"  Mean events per type: {np.mean(frequencies):.1f}")
        print(f"  Median events per type: {np.median(frequencies):.1f}")
        print(f"  Standard deviation: {np.std(frequencies):.1f}")
    
    # Spatial data availability analysis
    spatial_events = events_df[events_df['location'].notna()]
    spatial_coverage = len(spatial_events) / len(events_df) * 100
    
    print(f"\nSpatial Data Coverage:")
    print(f"  Events with location: {len(spatial_events)} / {len(events_df)} ({spatial_coverage:.1f}%)")
    
    # Temporal structure analysis
    if 'minute' in events_df.columns and 'second' in events_df.columns:
        temporal_analysis = {
            'min_minute': events_df['minute'].min(),
            'max_minute': events_df['minute'].max(),
            'periods': events_df['period'].nunique() if 'period' in events_df.columns else 'Unknown'
        }
        
        print(f"\nTemporal Structure:")
        print(f"  Time range: {temporal_analysis['min_minute']}' to {temporal_analysis['max_minute']}'")
        print(f"  Periods: {temporal_analysis['periods']}")
    
    return {
        "events_df": events_df,
        "total_events": len(events_df),
        "event_types": event_types if 'type' in events_df.columns else {},
        "spatial_coverage": spatial_coverage,
        "schema_columns": list(events_df.columns)
    }

def analyze_coordinate_system(events_df):
    """
    Analyze the StatsBomb coordinate system and spatial data properties.
    
    Parameters:
    events_df (pd.DataFrame): Events data with location information
    
    Returns:
    dict: Spatial coordinate analysis with mathematical properties
    """
    # Extract location data
    locations = []
    for _, event in events_df.iterrows():
        location = event.get('location')
        if location and isinstance(location, list) and len(location) >= 2:
            locations.append([location[0], location[1]])
    
    if not locations:
        return {"error": "No valid location data found"}
    
    locations_array = np.array(locations)
    x_coords = locations_array[:, 0]
    y_coords = locations_array[:, 1]
    
    print("=== COORDINATE SYSTEM ANALYSIS ===")
    print("Pitch Dimensions: 120 × 80 units")
    
    # Statistical analysis of coordinates
    print(f"\nX-Coordinate Statistics:")
    print(f"  Range: [{np.min(x_coords):.1f}, {np.max(x_coords):.1f}]")
    print(f"  Mean: {np.mean(x_coords):.1f}")
    print(f"  Standard deviation: {np.std(x_coords):.1f}")
    
    print(f"\nY-Coordinate Statistics:")
    print(f"  Range: [{np.min(y_coords):.1f}, {np.max(y_coords):.1f}]")
    print(f"  Mean: {np.mean(y_coords):.1f}")
    print(f"  Standard deviation: {np.std(y_coords):.1f}")
    
    # Boundary validation
    x_valid = np.all((x_coords >= 0) & (x_coords <= 120))
    y_valid = np.all((y_coords >= 0) & (y_coords <= 80))
    
    print(f"\nBoundary Validation:")
    print(f"  X-coordinates within [0, 120]: {x_valid}")
    print(f"  Y-coordinates within [0, 80]: {y_valid}")
    
    # Spatial density analysis
    pitch_area = 120 * 80  # Total pitch area
    events_per_unit = len(locations) / pitch_area
    
    print(f"\nSpatial Density:")
    print(f"  Total events with location: {len(locations)}")
    print(f"  Events per unit area: {events_per_unit:.4f}")
    
    return {
        "total_locations": len(locations),
        "x_stats": {"min": np.min(x_coords), "max": np.max(x_coords), 
                   "mean": np.mean(x_coords), "std": np.std(x_coords)},
        "y_stats": {"min": np.min(y_coords), "max": np.max(y_coords), 
                   "mean": np.mean(y_coords), "std": np.std(y_coords)},
        "boundary_valid": x_valid and y_valid,
        "spatial_density": events_per_unit
    }

def analyze_statistical_properties(events_df):
    """
    Analyze statistical properties and mathematical characteristics of event data.
    
    Parameters:
    events_df (pd.DataFrame): Events data for statistical analysis
    
    Returns:
    dict: Statistical analysis with distribution characteristics
    """
    print("=== STATISTICAL PROPERTIES ANALYSIS ===")
    
    # Event type frequency distribution
    if 'type' in events_df.columns:
        event_types = events_df['type'].apply(
            lambda x: x['name'] if isinstance(x, dict) else str(x)
        ).value_counts()
        
        frequencies = event_types.values
        
        # Distribution statistics
        print(f"Event Frequency Distribution:")
        print(f"  Number of event types: {len(event_types)}")
        print(f"  Mean frequency: {np.mean(frequencies):.2f}")
        print(f"  Median frequency: {np.median(frequencies):.2f}")
        print(f"  Standard deviation: {np.std(frequencies):.2f}")
        print(f"  Skewness: {pd.Series(frequencies).skew():.2f}")
        print(f"  Kurtosis: {pd.Series(frequencies).kurtosis():.2f}")
        
        # Power law analysis
        log_ranks = np.log(np.arange(1, len(frequencies) + 1))
        log_frequencies = np.log(frequencies)
        correlation = np.corrcoef(log_ranks, log_frequencies)[0, 1]
        
        print(f"  Log-log correlation: {correlation:.3f}")
        
        # Gini coefficient for frequency inequality
        sorted_freq = np.sort(frequencies)
        n = len(sorted_freq)
        cumsum = np.cumsum(sorted_freq)
        gini = (n + 1 - 2 * np.sum(cumsum) / cumsum[-1]) / n
        
        print(f"  Gini coefficient: {gini:.3f}")
    
    # Temporal distribution analysis
    if 'minute' in events_df.columns:
        minute_dist = events_df['minute'].value_counts().sort_index()
        
        print(f"\nTemporal Distribution:")
        print(f"  Events per minute (mean): {len(events_df) / 90:.1f}")
        print(f"  Peak minute: {minute_dist.idxmax()} ({minute_dist.max()} events)")
        print(f"  Temporal variance: {events_df['minute'].var():.2f}")
    
    return {
        "event_type_stats": {
            "mean_frequency": np.mean(frequencies) if 'type' in events_df.columns else None,
            "frequency_std": np.std(frequencies) if 'type' in events_df.columns else None,
            "gini_coefficient": gini if 'type' in events_df.columns else None
        },
        "temporal_stats": {
            "mean_events_per_minute": len(events_df) / 90 if 'minute' in events_df.columns else None,
            "temporal_variance": events_df['minute'].var() if 'minute' in events_df.columns else None
        }
    }


def main():
    data_path = "/home/pete/dev/duckdb-react-demo/public/data/json/statsbomb"
    sb_path = "/home/pete/dev/duckdb-react-demo/public/data/json"
    match_id = 4020846
    # d4020846 = analyze_event_structure(data_path, match_id)

    # print("Analyse event structure")
    # print(d4020846)

    # Example usage
    # competitions_df, summary = load_competitions(r"/path/to/statsbomb/open-data")
    competitions_df, summary = load_competitions(data_path)
    print("Competition Summary")
    print(summary)
    dfsum = pd.DataFrame.from_dict(summary, orient='index').reset_index()
    dfsum.columns = ['Competition', 'Value']  # optional, rename columns
    print(dfsum)

    coverage_360 = analyze_360_coverage(competitions_df)
    print(coverage_360)    
    # print("Competitions df:")
    # print(competitions_df.head())

    hierarchy_summary = analyze_competition_hierarchy(competitions_df)

    structure_validation = analyze_data_structure("/home/pete/dev/duckdb-react-demo/public/data/json/statsbomb")
    print(structure_validation)
    match_structure = analyze_match_structure(data_path, 55, 282)
        # "competition_id": 55,
        # "season_id": 282,

    print(match_structure)
    # print("hierarchy_summary")
    # print(hierarchy_summary)
    num_matches_to_preview = 5  # adjust as needed

    events_dir = Path(data_path) / "events"
    event_files = sorted(events_dir.glob("*.json"))[:num_matches_to_preview]

    def inspect_match(match_json_path):
        with open(match_json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Put your two lines for extracting match details here
        match_id = data[0]["match_id"] if data else "unknown"
        num_events = len(data)
        return match_id, num_events

    for match_file in event_files:
        # print(match_file)
        print("#"*350)
        print("MATCH ANALYSIS")
        print("#"*350)
        print(match_id)
        out = analyze_event_structure(data_path, match_id)
        # print(out)

        events_path = Path(data_path) / "events" / f"{match_id}.json"
        
        if not events_path.exists():
            return {"error": f"Events file not found for match {match_id}"}
        
        with open(events_path, 'r', encoding='utf-8') as f:
            events_data = json.load(f)
            events_df = pd.DataFrame(events_data)
            # print(events_df)
            print("CO ORDINATES ANALYSIS")
            coords = analyze_coordinate_system(events_df)
            print("STAT PROPS")
            analyze_statistical_properties(events_df)
        # match_id, num_events = inspect_match(match_file)
        # print(f"{match_file.name} → match_id: {match_id}, events: {num_events}")

if __name__ == "__main__":
    main()


