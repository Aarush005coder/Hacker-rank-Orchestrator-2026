# generate_mock_data.py
import os
import pandas as pd
import numpy as np
import random
import json
from datetime import datetime, timedelta

# Create directories
os.makedirs("dataset/evidence", exist_ok=True)

print("🧪 Generating mock dataset for testing...")

# 1. Generate User Identities
num_users = 600
user_ids = [f"user_{i:04d}" for i in range(1, num_users + 1)]
emails = [f"user{i}@northstar.com" for i in range(1, num_users + 1)]
user_identities_df = pd.DataFrame({"user_id": user_ids, "email": emails})
user_identities_df.to_csv("dataset/user_identities.csv", index=False)

# 2. Generate User Audit Log (Historical email changes)
audit_logs = []
for i in range(1, 101):
    uid = f"user_{i:04d}"
    old_email = f"old_user{i}@northstar.com"
    new_email = f"user{i}@northstar.com"
    audit_logs.append({
        "audit_id": f"audit_{i:04d}",
        "user_id": uid,
        "old_email": old_email,
        "new_email": new_email,
        "changed_at": "2025-01-15T10:00:00Z"
    })
user_audit_log_df = pd.DataFrame(audit_logs)
user_audit_log_df.to_csv("dataset/user_audit_log.csv", index=False)

# 3. Generate Deletion Rules
rules_data = [
    {"data_category": "account_profile", "system_id": "account_service", "required_treatment": "DELETE", "retention_period_days": 0},
    {"data_category": "order_history", "system_id": "billing_service", "required_treatment": "ANONYMIZE", "retention_period_days": 2555},
    {"data_category": "support_tickets", "system_id": "support_system", "required_treatment": "REDACT", "retention_period_days": 365},
    {"data_category": "analytics_events", "system_id": "analytics_db", "required_treatment": "DELETE", "retention_period_days": 0},
    {"data_category": "marketing_list", "system_id": "marketing_service", "required_treatment": "DELETE", "retention_period_days": 0}
]
deletion_rules_df = pd.DataFrame(rules_data)
deletion_rules_df.to_csv("dataset/deletion_rules.csv", index=False)

# 4. Generate System Activity (Syncs, Backups, Deletions)
activities = []
# Some successful deletions
for i in range(1, 201):
    activities.append({
        "activity_id": f"act_{i:04d}",
        "system_id": "account_service",
        "resource_id": f"account_{i:04d}",
        "activity_type": "DELETE_USER",
        "timestamp": "2026-10-20T12:00:00Z",
        "details": f"Deleted user_{i:04d}"
    })
# Some active syncs that recreate data
for i in range(201, 211):
    activities.append({
        "activity_id": f"act_{i:04d}",
        "system_id": "sync_job_01",
        "resource_id": f"account_{i:04d}",
        "activity_type": "SYNC_RECREATE",
        "timestamp": "2026-10-24T08:00:00Z",
        "details": f"Sync recreated user_{i:04d}"
    })
# Some backups
for i in range(211, 221):
    activities.append({
        "activity_id": f"act_{i:04d}",
        "system_id": "backup_vault",
        "resource_id": f"backup_daily_{i:04d}",
        "activity_type": "BACKUP_CREATE",
        "timestamp": "2026-10-23T02:00:00Z",
        "details": f"Backup contains user_{i:04d}"
    })
system_activity_df = pd.DataFrame(activities)
system_activity_df.to_csv("dataset/system_activity.csv", index=False)

# 5. Generate Evidence Files Manifest & Dummy Files
evidence_manifest = []
for i in range(1, 51):
    filename = f"evidence_{i:02d}.txt"
    filepath = f"dataset/evidence/{filename}"
    
    # Write some dummy text containing user emails
    with open(filepath, "w") as f:
        f.write(f"Log entry for user{i}@northstar.com\n")
        f.write(f"Action: Purchase completed.\n")
        if i <= 10:
            f.write(f"Status: DELETION COMPLETE\n")
        else:
            f.write(f"Status: ACTIVE\n")
            
    evidence_manifest.append({
        "evidence_id": f"evidence_{i:02d}",
        "filename": filename,
        "file_type": "text",
        "system_id": "support_system" if i % 2 == 0 else "account_service"
    })
evidence_files_df = pd.DataFrame(evidence_manifest)
evidence_files_df.to_csv("dataset/evidence_files.csv", index=False)

# 6. Generate Deletion Requests (Exactly 518 rows)
requests = []
statuses = ["COMPLETE", "PARTIALLY_COMPLETE", "NOT_STARTED"]
for i in range(1, 519):
    email = f"user{i}@northstar.com" if i <= num_users else f"ghost_user{i}@northstar.com"
    status = random.choice(statuses)
    
    # Make some explicitly NOT_APPLICABLE
    req_text = "Please delete my account and all associated data."
    if i % 50 == 0:
        req_text = "I just want to update my password, not delete my account."
        status = "NOT_STARTED"
        
    requests.append({
        "case_id": f"case_{i:03d}",
        "email": email,
        "requested_at": "2026-10-01T10:00:00Z",
        "reported_status": status,
        "reported_at": "2026-10-02T10:00:00Z",
        "audit_at": "2026-10-25T00:00:00Z",
        "request_text": req_text
    })
deletion_requests_df = pd.DataFrame(requests)
deletion_requests_df.to_csv("dataset/deletion_requests.csv", index=False)

print("✅ Mock dataset generated successfully!")
print("📂 Files created in ./dataset/")
print("🚀 You can now run 'python main.py' to test the pipeline.")