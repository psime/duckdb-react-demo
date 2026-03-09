import json
from pathlib import Path
import pandas as pd
import numpy as np


def analyze_event_structure(data_path, match_id):
    """
    Detailed analysis of event data structure and mathematical properties.
    
    Parameters:
    data_path (str): Path to StatsBomb data
    match_id (int): Specific match identifier
    
    Returns:
    dict: Comprehensive event structure analysis
    """
    data_path = "/home/pete/dev/duckdb-react-demo/public/data/json/statsbomb"

    match_id = 315

    events_path = Path(data_path) / "data" / "events" / f"{match_id}.json"
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
        
        # Top 10 most frequent events
        for event_type, count in event_types.head(10).items():
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

def main():
    data_path = "/home/pete/dev/duckdb-react-demo/public/data/json/statsbomb"
    match_id = 53
    d53 = analyze_event_structure(data_path, match_id)
    print(d53)
if __name__ == "__main__":
    main()


