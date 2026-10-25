# main.py
import os
import pandas as pd
from tqdm import tqdm
import json

from src.utils import load_csv, save_output, ensure_output_dir
from src.identity_resolver import IdentityResolver
from src.evidence_parser import EvidenceParser
from src.state_evaluator import StateEvaluator
from src.step_generator import StepGenerator

def main():
    print("🚀 Starting Northstar Shop Deletion Audit Agent...")
    
    # 1. Load core datasets
    print("📂 Loading datasets...")
    requests_df = load_csv("deletion_requests.csv")
    rules_df = load_csv("deletion_rules.csv")
    activity_df = load_csv("system_activity.csv")
    
    # 2. Resolve Identities
    print("🔗 Resolving user identities (building identity graph)...")
    resolver = IdentityResolver()
    resolved_identities = resolver.get_all_resolved_identities(requests_df)
    
    # 3. Initialize Parsers and Evaluators
    print("🔍 Initializing evidence parser and state evaluator...")
    evidence_parser = EvidenceParser()
    evidence_manifest_df = load_csv("evidence_files.csv")
    state_evaluator = StateEvaluator(rules_df, activity_df, evidence_manifest_df)
    step_generator = StepGenerator()
    
    # 4. Process each case
    results = []
    print(f"⚙️ Processing {len(requests_df)} cases...")
    
    for _, row in tqdm(requests_df.iterrows(), total=len(requests_df)):
        case_id = row['case_id']
        email = row['email']
        audit_at = row['audit_at']
        
        # Get resolved identifiers for this case
        identities = resolved_identities[case_id]
        
        # Parse evidence for these identifiers
        extracted_evidence = evidence_parser.extract_for_identities(identities)
        
        # Evaluate state and determine if deletion is complete
        evaluation_result = state_evaluator.evaluate(
            case_id, 
            identities, 
            extracted_evidence, 
            audit_at,
            row.get('request_text', '')
        )
        
        # Generate steps JSON
        steps_json = step_generator.generate(evaluation_result)
        
        results.append({
            "case_id": case_id,
            "deletion_status": evaluation_result['status'],
            "steps_json": json.dumps(steps_json)
        })
        
    # 5. Save output
    print("💾 Saving output...")
    ensure_output_dir()
    output_df = pd.DataFrame(results)
    
    # FIX: Sort numerically by extracting the number from case_id
    output_df['sort_key'] = output_df['case_id'].str.extract(r'(\d+)').astype(int)
    output_df = output_df.sort_values(by='sort_key').drop(columns=['sort_key']).reset_index(drop=True)
    
    save_output(output_df)
    print("✅ Audit complete. output.csv generated with numerical sorting.")

if __name__ == "__main__":
    main()