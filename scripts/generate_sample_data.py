"""
Generate sample Coinbase data for replay
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_sample_data(num_records=600, output_file=None):
    """
    Generate sample Coinbase trade data
    
    Args:
        num_records: Number of records to generate (600 = ~1 per second for 10 min)
        output_file: Output CSV file path (defaults to data/replay_10min.csv)
    """
    # Determine output file path
    if output_file is None:
        # Get project root (parent of scripts directory)
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        output_file = os.path.join(project_root, "data", "replay_10min.csv")
    
    # Ensure data directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    # Start time
    start_time = datetime(2025, 1, 1, 10, 0, 0)
    
    # Generate timestamps (1 per second)
    timestamps = [start_time + timedelta(seconds=i) for i in range(num_records)]
    
    # Generate price data (random walk)
    base_price = 50000.0
    prices = [base_price]
    for i in range(1, num_records):
        # Random walk with slight upward trend
        change = np.random.normal(0, 50)  # Volatility
        new_price = prices[-1] + change
        prices.append(max(new_price, 1000.0))  # Floor price
    
    # Generate volume data
    volumes = np.random.lognormal(10, 0.5, num_records)
    
    # Create DataFrame
    df = pd.DataFrame({
        'timestamp': timestamps,
        'price': prices,
        'volume': volumes,
        'side': np.random.choice(['buy', 'sell'], num_records)
    })
    
    # Save to CSV
    df.to_csv(output_file, index=False)
    print(f"Generated {num_records} records to {output_file}")
    print(f"Time range: {timestamps[0]} to {timestamps[-1]}")
    print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")

if __name__ == "__main__":
    import os
    generate_sample_data()

