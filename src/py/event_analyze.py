import json
# from pathlib import Path
import pandas as pd
import numpy as np

# Statistical analysis and visualization
import matplotlib.pyplot as plt  # Publication-quality plotting
import seaborn as sns           # Statistical data visualization
from pathlib import Path       # Cross-platform file system operations
from scipy import stats       # Statistical distributions and tests

from mplsoccer import Pitch
from collections import defaultdict

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

def load_and_analyze_competitions(data_path: str) -> pd.DataFrame:
    """
    Load competition data and perform comprehensive statistical analysis.

    - Let C = {c₁, c₂, ..., cₙ} be the set of competitions
    - Each cᵢ has attributes: name, country, gender, seasons
    - We analyze |C|, geographical distribution, and temporal coverage
    """
    comp_path = Path(data_path) / "competitions.json"
    
    with open(comp_path, 'r', encoding='utf-8') as f:
        competitions_data = json.load(f)
    
    competitions = pd.DataFrame(competitions_data)
    
    # Statistical characterization
    print("COMPETITION DATA ANALYSIS")
    print("=" * 40)
    print(f"Total entries (|C × S|): {len(competitions)}")
    print(f"Unique competitions (|C|): {competitions['competition_name'].nunique()}")
    print(f"Geographic coverage: {competitions['country_name'].nunique()} countries")
    print(f"Temporal span: {competitions['season_name'].min()} to {competitions['season_name'].max()}")
    
    # Competition frequency distribution
    comp_counts = competitions['competition_name'].value_counts()
    print(f"\nFrequency Distribution Statistics:")
    print(f"  Mean seasons per competition: {comp_counts.mean():.2f}")
    print(f"  Standard deviation: {comp_counts.std():.2f}")
    print(f"  Coefficient of variation: {comp_counts.std()/comp_counts.mean():.3f}")
    
    return competitions

def analyze_laliga_2020_21(data_path: str) -> tuple:
    """
    Comprehensive analysis of La Liga 2020/21 season.
    
    Mathematical Framework:
    - Season S contains matches M = {m₁, m₂, ..., m₃₈₀}
    - Each match mᵢ has goals gᵢ = (home_goals, away_goals)
    - We analyze goal distributions, team performance, and temporal patterns
    """
    matches_path = Path(data_path) / "matches" / "2" / "44.json"
    
    with open(matches_path, 'r', encoding='utf-8') as f:
        matches_data = json.load(f)
    
    matches_df = pd.DataFrame(matches_data)
    
    # Extract match outcome variables
    home_scores = [match['home_score'] for match in matches_data]
    away_scores = [match['away_score'] for match in matches_data]
    total_goals = [h + a for h, a in zip(home_scores, away_scores)]
    
    # Statistical analysis
    print("LA LIGA 2020/21 STATISTICAL ANALYSIS")
    print("=" * 45)
    print(f"Sample size (n): {len(matches_df)} matches")
    print(f"Total goals: {sum(total_goals)}")
    print(f"Mean goals per match (μ): {np.mean(total_goals):.3f}")
    print(f"Standard deviation (σ): {np.std(total_goals):.3f}")
    print(f"Variance (σ²): {np.var(total_goals):.3f}")
    
    # Distributional analysis
    from scipy import stats
    
    # Test for Poisson distribution (common in football)
    lambda_est = np.mean(total_goals)
    ks_stat, p_value = stats.kstest(total_goals, 
                                   lambda x: stats.poisson.cdf(x, lambda_est))
    
    print(f"Poisson distribution test:")
    print(f"  Estimated λ: {lambda_est:.3f}")
    print(f"  KS statistic: {ks_stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    
    # Home advantage analysis
    home_wins = sum(1 for h, a in zip(home_scores, away_scores) if h > a)
    draws = sum(1 for h, a in zip(home_scores, away_scores) if h == a)
    away_wins = sum(1 for h, a in zip(home_scores, away_scores) if h < a)
    
    home_advantage = home_wins / len(matches_df)
    print(f"\nHome advantage analysis:")
    print(f"  Home win rate: {home_advantage:.3f}")
    print(f"  Expected (null hypothesis): 0.333")
    print(f"  Observed deviation: {(home_advantage - 0.333):.3f}")
    
    return matches_df, home_scores, away_scores, total_goals

def extract_shot_characteristics(events_df):
    """
    Extract shot characteristics for xG analysis from StatsBomb data.
    
    Parameters:
    - events_df: DataFrame containing StatsBomb event data
    
    Returns:
    - DataFrame with shot locations, xG values, outcomes, and derived metrics
    """
    
    # Filter for shot events
    shots = events_df[events_df['event_type'] == 'Shot'].copy()
    
    shot_analysis = []
    
    for idx, shot in shots.iterrows():
        shot_info = shot.get('shot', {})
        location = shot.get('location')
        
        if isinstance(shot_info, dict) and location and len(location) >= 2:
            # Extract basic shot data
            xg_value = shot_info.get('statsbomb_xg', 0)
            outcome = shot_info.get('outcome', {}).get('name', 'Unknown')
            
            # Calculate derived metrics
            goal_x, goal_y = 120, 40  # StatsBomb coordinate system
            distance = np.sqrt((location[0] - goal_x)**2 + (location[1] - goal_y)**2)
            
            # Calculate shot angle using goal width (7.32m = ~8 yards in coordinate system)
            goal_width = 8
            y_diff = abs(location[1] - goal_y)
            if location[0] < goal_x:
                angle_rad = np.arctan(goal_width / (2 * np.sqrt((goal_x - location[0])**2 + y_diff**2)))
                angle_deg = np.degrees(angle_rad)
            else:
                angle_deg = 0
            
            shot_analysis.append({
                'shot_id': idx,
                'x': location[0],
                'y': location[1],
                'xg': xg_value,
                'outcome': outcome,
                'distance_to_goal': distance,
                'shot_angle': angle_deg,
                'player': shot.get('player', {}).get('name', 'Unknown'),
                'team': shot.get('team', {}).get('name', 'Unknown'),
                'minute': shot.get('minute', 0)
            })
    
        return pd.DataFrame(shot_analysis)

def tryme2(events_df):
    def extract_name(obj):
        if isinstance(obj, dict):
            return obj.get('name', 'Unknown')
        return str(obj)

    # Clean up data structure
    events_df['team_name'] = events_df['team'].apply(extract_name)
    events_df['player_name'] = events_df['player'].apply(lambda x: extract_name(x) if x is not None else None)
    events_df['event_type'] = events_df['type'].apply(extract_name)

    # Filter team data
    team_name = events_df['team_name'].iloc[0]
    team_events = events_df[events_df['team_name'] == team_name]
    passes_df = team_events[team_events['event_type'] == 'Pass']

    # Calculate average positions
    player_positions = defaultdict(list)
    for idx, event in team_events.iterrows():
        player = event.get('player_name')
        location = event.get('location')
        if player and location and isinstance(location, list) and len(location) == 2:
            player_positions[player].append(location)

    # Get average positions for active players
    avg_positions = {}
    for player, positions in player_positions.items():
        if len(positions) >= 15:
            positions_array = np.array(positions)
            avg_x = np.mean(positions_array[:, 0])
            avg_y = np.mean(positions_array[:, 1])
            avg_positions[player] = (avg_x, avg_y)

    # Calculate pass connections
    pass_connections = defaultdict(int)
    for idx, pass_event in passes_df.iterrows():
        passer = pass_event.get('player_name')
        pass_info = pass_event.get('pass')

        if isinstance(pass_info, dict):
            recipient_info = pass_info.get('recipient')
            receiver = extract_name(recipient_info) if recipient_info else None

            # Check if pass was successful
            pass_outcome = pass_info.get('outcome')
            is_successful = not (isinstance(pass_outcome, dict) and pass_outcome.get('name') == 'Incomplete')

            if (passer and receiver and is_successful and
                passer in avg_positions and receiver in avg_positions):
                pass_connections[(passer, receiver)] += 1

    # Create visualization
    fig, ax = plt.subplots(figsize=(16, 11))
    pitch = Pitch(pitch_type='statsbomb', pitch_color='#2d5a2d', line_color='white', linewidth=3)
    pitch.draw(ax=ax)

    # Filter significant connections
    min_passes = 5
    significant_connections = {k: v for k, v in pass_connections.items() if v >= min_passes}
    max_passes = max(significant_connections.values()) if significant_connections else 1

    # Draw pass connections with thickness based on frequency
    for (passer, receiver), count in significant_connections.items():
        passer_pos = avg_positions[passer]
        receiver_pos = avg_positions[receiver]

        line_thickness = 1 + (count / max_passes) * 11
        alpha = 0.3 + (count / max_passes) * 0.6

        ax.plot([passer_pos[0], receiver_pos[0]], [passer_pos[1], receiver_pos[1]],
                color='white', linewidth=line_thickness, alpha=alpha, zorder=2)

    # Draw player nodes (top 11 most active)
    top_players = sorted(avg_positions.items(),
                        key=lambda x: len(player_positions[x[0]]), reverse=True)[:11]

    for i, (player, (x, y)) in enumerate(top_players):
        circle = plt.Circle((x, y), radius=3.5, color='#FF4444',
                            edgecolor='white', linewidth=3, zorder=5)
        ax.add_patch(circle)

        # Position abbreviation based on field coordinates
        position_abbr = "abbr" #get_position_abbrev(x, y)  # Custom function for position naming
        ax.text(x, y, position_abbr, color='white', fontweight='bold',
                ha='center', va='center', fontsize=11, zorder=6)

    print(locals())
    return None

def tryme(events_df):

    # # Load StatsBomb event data
    # events_df = pd.read_json(r'C:\Users\Lucas\Documents\Research\Datasets\StatsBombOpenData\data\events\15946.json')

    def extract_name(obj):
        """Extract names from StatsBomb nested dictionary structure"""
        if isinstance(obj, dict):
            name = obj.get('name', 'Unknown')
            try:
                return name.encode('ascii', 'ignore').decode('ascii')
            except:
                return 'Unknown'
        return str(obj) if obj is not None else 'Unknown'

    # Clean data structure
    events_df['team_name'] = events_df['team'].apply(extract_name)
    events_df['player_name'] = events_df['player'].apply(lambda x: extract_name(x) if x is not None else None)
    events_df['event_type'] = events_df['type'].apply(extract_name)

    print("Creating possession chain visualization...")

    def find_interesting_possession(events_df):
        """Find a long, interesting possession chain with multiple events"""
        
        # Group by possession and analyze
        possession_analysis = []
        
        for poss_id, poss_events in events_df.groupby('possession'):
            if len(poss_events) >= 8:  # Look for substantial possessions
                
                # Count different event types
                passes = (poss_events['event_type'] == 'Pass').sum()
                carries = (poss_events['event_type'] == 'Carry').sum()
                shots = (poss_events['event_type'] == 'Shot').sum()
                
                # Check for spatial progression
                locations = []
                for _, event in poss_events.iterrows():
                    location = event.get('location')
                    if isinstance(location, list) and len(location) >= 2:
                        locations.append(location)
                
                if len(locations) >= 5:  # Need enough spatial events
                    start_x = locations[0][0]
                    end_x = locations[-1][0]
                    progression = end_x - start_x
                    
                    possession_analysis.append({
                        'possession_id': poss_id,
                        'length': len(poss_events),
                        'passes': passes,
                        'carries': carries,
                        'shots': shots,
                        'progression': progression,
                        'team': poss_events['team_name'].iloc[0],
                        'events': poss_events
                    })
        
        # Sort by interesting criteria (length + progression + shots)
        if possession_analysis:
            possession_analysis.sort(key=lambda x: x['length'] + x['progression']/10 + x['shots']*5, reverse=True)
            return possession_analysis[0]
        
        return None

    # Find an interesting possession
    interesting_possession = find_interesting_possession(events_df)

    if interesting_possession is None:
        print("No suitable possession chains found. Using first available possession.")
        # Fall back to first possession with reasonable length
        for poss_id, poss_events in events_df.groupby('possession'):
            if len(poss_events) >= 5:
                interesting_possession = {
                    'possession_id': poss_id,
                    'events': poss_events,
                    'team': poss_events['team_name'].iloc[0],
                    'length': len(poss_events)
                }
                break

    if interesting_possession:
        possession_events = interesting_possession['events']
        team_name = interesting_possession['team']
        
        print(f"Visualizing possession chain: {interesting_possession['possession_id']}")
        print(f"Team: {team_name}")
        print(f"Length: {interesting_possession['length']} events")
        
        # Create the visualization
        fig, ax = plt.subplots(figsize=(18, 12))
        pitch = Pitch(pitch_type='statsbomb', pitch_color='#2d5a2d', line_color='white', linewidth=3)
        pitch.draw(ax=ax)
        
        # Extract events with locations
        sequence_events = []
        for idx, event in possession_events.iterrows():
            location = event.get('location')
            if isinstance(location, list) and len(location) >= 2:
                
                event_info = {
                    'x': location[0],
                    'y': location[1],
                    'event_type': event.get('event_type'),
                    'player': event.get('player_name', 'Unknown'),
                    'minute': event.get('minute', 0),
                    'second': event.get('second', 0),
                    'index': len(sequence_events)
                }
                
                # Add pass end location if available
                if event.get('event_type') == 'Pass' and isinstance(event.get('pass'), dict):
                    end_location = event['pass'].get('end_location')
                    if isinstance(end_location, list) and len(end_location) >= 2:
                        event_info['pass_end_x'] = end_location[0]
                        event_info['pass_end_y'] = end_location[1]
                
                # Add carry end location if available  
                elif event.get('event_type') == 'Carry' and isinstance(event.get('carry'), dict):
                    end_location = event['carry'].get('end_location')
                    if isinstance(end_location, list) and len(end_location) >= 2:
                        event_info['carry_end_x'] = end_location[0]
                        event_info['carry_end_y'] = end_location[1]
                
                sequence_events.append(event_info)
        
        print(f"Found {len(sequence_events)} events with locations")
        
        if len(sequence_events) > 0:
            # Define colors for different event types
            event_colors = {
                'Pass': '#4CAF50',      # Green
                'Carry': '#FF9800',     # Orange  
                'Ball Receipt*': '#2196F3',  # Blue
                'Shot': '#F44336',      # Red
                'Dribble': '#9C27B0',   # Purple
                'Pressure': '#795548',  # Brown
                'Ball Recovery': '#607D8B'  # Blue Grey
            }
            
            # Draw the possession sequence
            for i, event in enumerate(sequence_events):
                color = event_colors.get(event['event_type'], '#FFC107')  # Default yellow
                
                # Draw event location
                circle = plt.Circle((event['x'], event['y']), radius=2, 
                                color=color, alpha=0.8, zorder=5)
                ax.add_patch(circle)
                
                # Add sequence number
                ax.text(event['x'], event['y'], str(i+1), 
                    color='white', fontweight='bold', fontsize=10,
                    ha='center', va='center', zorder=6)
                
                # Draw connections between consecutive events
                if i > 0:
                    prev_event = sequence_events[i-1]
                    ax.plot([prev_event['x'], event['x']], 
                        [prev_event['y'], event['y']], 
                        color='white', linewidth=3, alpha=0.7, zorder=2)
                    
                    # Add arrow for direction
                    dx = event['x'] - prev_event['x']
                    dy = event['y'] - prev_event['y']
                    if abs(dx) > 1 or abs(dy) > 1:  # Only for meaningful distances
                        ax.annotate('', xy=(event['x'], event['y']), 
                                xytext=(prev_event['x'], prev_event['y']),
                                arrowprops=dict(arrowstyle='->', color='white', 
                                                alpha=0.8, lw=2), zorder=3)
                
                # Draw pass/carry trajectories
                if 'pass_end_x' in event:
                    ax.plot([event['x'], event['pass_end_x']], 
                        [event['y'], event['pass_end_y']], 
                        color='yellow', linewidth=2, linestyle='--', 
                        alpha=0.8, zorder=4)
                
                if 'carry_end_x' in event:
                    ax.plot([event['x'], event['carry_end_x']], 
                        [event['y'], event['carry_end_y']], 
                        color='orange', linewidth=3, alpha=0.9, zorder=4)
            
            # Add sequence information
            start_time = f"{int(sequence_events[0]['minute'])}:{int(sequence_events[0]['second']):02d}"
            end_time = f"{int(sequence_events[-1]['minute'])}:{int(sequence_events[-1]['second']):02d}"
            
            # Calculate total distance
            total_distance = 0
            for i in range(1, len(sequence_events)):
                dx = sequence_events[i]['x'] - sequence_events[i-1]['x']
                dy = sequence_events[i]['y'] - sequence_events[i-1]['y']
                total_distance += np.sqrt(dx**2 + dy**2)
            
            # Field progression
            field_progression = sequence_events[-1]['x'] - sequence_events[0]['x']
            
            # Add title and statistics
            title = f"Possession Chain Analysis: {team_name}\n"
            title += f"Sequence: {start_time} - {end_time} | "
            title += f"Events: {len(sequence_events)} | "
            title += f"Distance: {total_distance:.1f} yards | "
            title += f"Progression: {field_progression:+.1f} yards"
            
            ax.text(60, 85, title, ha='center', va='center', fontsize=14, 
                color='white', fontweight='bold',
                bbox=dict(boxstyle='round,pad=1', facecolor='black', alpha=0.8))
            
            # Create legend
            legend_elements = []
            used_events = set(event['event_type'] for event in sequence_events)
            for event_type in used_events:
                color = event_colors.get(event_type, '#FFC107')
                legend_elements.append(plt.Line2D([0], [0], marker='o', color='w',
                                                markerfacecolor=color, markersize=10,
                                                label=event_type, markeredgecolor='black'))
            
            if legend_elements:
                ax.legend(handles=legend_elements, loc='upper left', 
                        bbox_to_anchor=(0.02, 0.98), fontsize=11,
                        facecolor='black', edgecolor='white', labelcolor='white')
            
            # Add sequence details box
            details_text = "POSSESSION SEQUENCE BREAKDOWN:\n"
            for i, event in enumerate(sequence_events[:8]):  # Show first 8 events
                player_short = event['player'].split()[-1] if event['player'] != 'Unknown' else 'Player'
                details_text += f"{i+1}. {event['event_type']} - {player_short}\n"
            if len(sequence_events) > 8:
                details_text += f"... +{len(sequence_events)-8} more events"
            
            ax.text(5, 20, details_text, ha='left', va='top', fontsize=9,
                color='white', family='monospace',
                bbox=dict(boxstyle='round,pad=0.8', facecolor='black', alpha=0.9))
            
            plt.tight_layout()
            plt.savefig('Figure26_Possession_Chain.png', dpi=300, bbox_inches='tight', 
                    facecolor='#1a3d1a')
            plt.show()
            
            # Print detailed sequence information
            print(f"\nDETAILED POSSESSION SEQUENCE:")
            print(f"Team: {team_name}")
            print(f"Duration: {start_time} - {end_time}")
            print(f"Total events: {len(sequence_events)}")
            print(f"Total distance: {total_distance:.1f} yards")
            print(f"Field progression: {field_progression:+.1f} yards")
            print(f"\nEvent sequence:")
            
            for i, event in enumerate(sequence_events):
                player_name = event['player'] if event['player'] != 'Unknown' else 'Unknown Player'
                print(f"  {i+1:2d}. {event['event_type']:15} | {player_name:20} | "
                    f"({event['x']:5.1f}, {event['y']:5.1f}) | "
                    f"{int(event['minute']):2d}:{int(event['second']):02d}")
            
            print("\nPossession chain visualization saved as Figure26_Possession_Chain.png")
            
        else:
            print("No events with location data found in possession chain")
            
    else:
        print("No suitable possession chains found in dataset")

    return None



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
            print("TRY THIS")
            tryme(events_df)
            print("TRY THIS TOO")
            tryme2(events_df)

        # match_id, num_events = inspect_match(match_file)
        # print(f"{match_file.name} → match_id: {match_id}, events: {num_events}")
        load_and_analyze_competitions(data_path)
        analyze_laliga_2020_21(data_path)

if __name__ == "__main__":
    main()



