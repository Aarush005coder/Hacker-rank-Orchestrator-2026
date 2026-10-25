# Evaluation Report

## 1. Case-Level Status Accuracy
- **Methodology**: Compared predicted `deletion_status` against the canonical answers.
- **Accuracy**: [Insert %]
- **Analysis**: [Discuss any discrepancies, e.g., edge cases where identity resolution missed a historical email].

## 2. Step-Level and Field-Level Accuracy
- **Methodology**: Validated each step in `steps_json` against the canonical steps. Checked `phase`, `operation`, `system_id`, `resource_id`, `state`, and `evidence_id`.
- **Accuracy**: [Insert %]
- **Analysis**: [Discuss common errors, e.g., missing `evidence_id` for COMPLETE verifications, or incorrect operation mapping].

## 3. Sequence Accuracy
- **Methodology**: Verified that steps are strictly ordered: FINDING -> REMEDIATION -> VERIFICATION, and within each phase, sorted by operation, then `system_id`, then `resource_id`.
- **Accuracy**: [Insert %]
- **Analysis**: [Discuss any sorting issues].

## 4. Custom Evaluation Cases
We created three custom cases to test edge cases:
1. **Case 997 (Tombstone Retention)**: User deleted, but account tombstone must be retained with redacted PII. Tests if `REDACT_RECORD` and `VERIFY_RECORD_REDACTED` are applied correctly.
2. **Case 998 (Active Sync Recreation)**: User deleted, but an active sync job recreates the data. Tests if `REPORT_ACTIVE_DATA_FLOW` and `DISABLE_DATA_FLOW` are correctly generated.
3. **Case 999 (Complex Identity Chain)**: User changed email 3 times and merged accounts. Tests if the identity graph correctly resolves all historical identifiers.

## 5. Failures Found and Improvements Made
- **Failure 1**: Initial identity resolver missed historical emails if `user_id` was null in the audit log.
  - **Improvement**: Added direct email-to-email linking in the graph when `user_id` is missing.
- **Failure 2**: OCR on low-resolution images failed to extract emails.
  - **Improvement**: Implemented image preprocessing (grayscale, thresholding) before passing to Tesseract.