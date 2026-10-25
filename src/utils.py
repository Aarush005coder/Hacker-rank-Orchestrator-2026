# src/utils.py
import os
import pandas as pd
from datetime import datetime

# Base directories
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")
EVIDENCE_DIR = os.path.join(DATASET_DIR, "evidence")
EVAL_DIR = os.path.join(BASE_DIR, "evaluation")

def load_csv(filename):
    """Load a CSV file from the dataset directory with robust error handling."""
    filepath = os.path.join(DATASET_DIR, filename)
    
    # 1. Check if file exists
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"❌ File not found: {filepath}\n"
            f"Please ensure the 'dataset' folder is in the root directory and contains the challenge files."
        )
    
    # 2. Check if file is physically empty (0 bytes)
    file_size = os.path.getsize(filepath)
    if file_size == 0:
        raise ValueError(
            f"❌ File is empty (0 bytes): {filepath}\n"
            f"Please check your dataset download. The file exists but contains no data."
        )

    # 3. Try reading with different encodings to handle Windows/Mac formatting quirks
    for encoding in ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']:
        try:
            df = pd.read_csv(filepath, encoding=encoding)
            
            # If it parsed but resulted in 0 columns, it might be a weird delimiter issue
            if len(df.columns) == 0:
                continue 
                
            return df
        except pd.errors.EmptyDataError:
            # File has bytes but pandas sees no columns (might be only whitespace)
            continue
        except UnicodeDecodeError:
            # Wrong encoding, try the next one
            continue
        except Exception as e:
            raise ValueError(f"❌ Unexpected error reading {filepath}: {e}")

    raise ValueError(
        f"❌ Could not parse {filepath}. \n"
        f"The file has {file_size} bytes but contains no valid CSV data. "
        f"It might be corrupted, contain only whitespace, or use an unsupported delimiter."
    )

def parse_timestamp(ts):
    """Parse a timestamp string into a datetime object."""
    if pd.isna(ts):
        return None
    try:
        return pd.to_datetime(ts)
    except Exception:
        return None

def get_evidence_filepath(filename):
    """Get the full path for an evidence file."""
    return os.path.join(EVIDENCE_DIR, filename)

def ensure_output_dir():
    """Ensure the evaluation directory exists."""
    os.makedirs(EVAL_DIR, exist_ok=True)

def save_output(df, filename="output.csv"):
    """Save the final output dataframe to CSV."""
    filepath = os.path.join(BASE_DIR, filename)
    df.to_csv(filepath, index=False)
    print(f"✅ Output saved to {filepath}")