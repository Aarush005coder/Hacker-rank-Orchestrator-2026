# evaluation/run_eval.py
import pandas as pd
import json
import os

def evaluate_output(output_path, ground_truth_path=None):
    if not os.path.exists(output_path):
        print(f"❌ Error: {output_path} not found.")
        print("💡 Tip: Make sure you have run 'python main.py' first to generate the output.csv file.")
        return
        
    df = pd.read_csv(output_path)
    
    print(f"📊 Total rows: {len(df)} (Expected: 518)")
    
    # Check for required columns
    required_cols = ['case_id', 'deletion_status', 'steps_json']
    for col in required_cols:
        if col not in df.columns:
            print(f"❌ Missing required column: {col}")
            return
            
    # Validate JSON and status values
    valid_json_count = 0
    valid_status_count = 0
    valid_statuses = {'COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE'}
    
    for idx, row in df.iterrows():
        # Check status
        if row['deletion_status'] in valid_statuses:
            valid_status_count += 1
            
        # Check JSON
        try:
            steps = json.loads(row['steps_json'])
            if isinstance(steps, list):
                valid_json_count += 1
                
                # Check NOT_APPLICABLE has empty array
                if row['deletion_status'] == 'NOT_APPLICABLE' and len(steps) != 0:
                    print(f"⚠️ Row {idx} ({row['case_id']}): NOT_APPLICABLE should have empty steps_json.")
            else:
                print(f"⚠️ Row {idx}: steps_json is not a list.")
        except json.JSONDecodeError:
            print(f"❌ Row {idx}: Invalid JSON in steps_json.")
            
    print(f"✅ Valid JSON rows: {valid_json_count}/{len(df)}")
    print(f"✅ Valid Status rows: {valid_status_count}/{len(df)}")
    
    # Check sorting
    if df['case_id'].is_monotonic_increasing:
        print("✅ Output is correctly sorted by case_id.")
    else:
        print("❌ Output is NOT sorted by case_id.")

if __name__ == "__main__":
    # Dynamically find the root directory (one level up from the evaluation folder)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(script_dir)
    output_path = os.path.join(root_dir, "output.csv")
    
    print(f"🔍 Checking file at: {output_path}\n")
    evaluate_output(output_path)