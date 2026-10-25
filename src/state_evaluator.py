# src/state_evaluator.py
import pandas as pd
from .utils import parse_timestamp

class StateEvaluator:
    def __init__(self, rules_df, activity_df, evidence_manifest_df):
        self.rules = rules_df.set_index('data_category') if 'data_category' in rules_df.columns else rules_df
        self.activity = activity_df.copy()
        self.evidence_manifest = evidence_manifest_df.copy()
        
        if 'timestamp' in self.activity.columns:
            self.activity['timestamp'] = self.activity['timestamp'].apply(parse_timestamp)

    def evaluate(self, case_id, identities, extracted_evidence, audit_at_str, request_text=""):
        audit_at = parse_timestamp(audit_at_str)
        
        request_lower = str(request_text).lower()
        if any(phrase in request_lower for phrase in ["not a deletion", "cancel request", "update password", "change email only", "do not delete", "close my account but keep"]):
            return self._build_result(case_id, "NOT_APPLICABLE", identities, extracted_evidence, audit_at, [], [], [])

        findings = []
        remediations = []
        verifications = []
        
        for file_id, content in extracted_evidence.items():
            # Robustly find the manifest row
            manifest_row = self.evidence_manifest[
                (self.evidence_manifest.get('file_id') == file_id) | 
                (self.evidence_manifest.get('evidence_id') == file_id)
            ]
            if manifest_row.empty:
                continue
                
            origin = str(manifest_row.iloc[0].get('origin', manifest_row.iloc[0].get('system_id', 'unknown_system'))).lower()
            data_category = self._infer_category(content, origin)
            
            if data_category in self.rules.index:
                rule = self.rules.loc[data_category]
                action_required = str(rule.get('required_action', 'DELETE')).upper()
                
                content_lower = str(content).lower()
                is_deleted = "deleted" in content_lower or "absent" in content_lower or "purged" in content_lower
                is_redacted = "redacted" in content_lower or "[redacted]" in content_lower
                is_anonymized = "anonymized" in content_lower or "anonymised" in content_lower or "user_****" in content_lower
                is_retained = "retained" in content_lower or "audit" in content_lower or "security" in content_lower
                
                if action_required == "DELETE":
                    if not is_deleted:
                        findings.append(self._make_step("FINDING", "REPORT_REMAINING_RECORD", "PRESENT", origin, file_id, file_id))
                        remediations.append(self._make_step("REMEDIATION", "DELETE_RECORD", "ABSENT", origin, file_id, ""))
                        verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT", origin, file_id, ""))
                    else:
                        verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT", origin, file_id, file_id))
                        
                elif action_required == "REDACT":
                    if not is_redacted:
                        findings.append(self._make_step("FINDING", "REPORT_EXPOSED_PII", "PRESENT", origin, file_id, file_id))
                        remediations.append(self._make_step("REMEDIATION", "REDACT_RECORD", "REDACTED", origin, file_id, ""))
                        verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED", origin, file_id, ""))
                    else:
                        verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_REDACTED", "REDACTED", origin, file_id, file_id))
                        
                elif action_required == "ANONYMIZE":
                    if not is_anonymized:
                        findings.append(self._make_step("FINDING", "REPORT_EXPOSED_PII", "PRESENT", origin, file_id, file_id))
                        remediations.append(self._make_step("REMEDIATION", "ANONYMIZE_RECORD", "ANONYMIZED", origin, file_id, ""))
                        verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", origin, file_id, ""))
                    else:
                        verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_ANONYMIZED", "ANONYMIZED", origin, file_id, file_id))
                        
                elif action_required == "RETAIN":
                    verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_PRESENT", "PRESENT", origin, file_id, file_id))

        search_terms = list(identities.get('emails', [])) + list(identities.get('user_ids', [])) + list(identities.get('phones', [])) + list(identities.get('hashes', []))
        search_terms = [str(t).lower() for t in search_terms if t]
        
        for _, act in self.activity.iterrows():
            details = str(act.get('details', '')).lower()
            action = str(act.get('action', act.get('activity_type', ''))).upper()
            status = str(act.get('status', 'SUCCESS')).upper()
            
            if any(term in details for term in search_terms):
                sys_id = str(act.get('target_system', act.get('origin_system', act.get('system_id', 'unknown'))))
                res_id = str(act.get('resource_id', 'unknown'))
                act_id = str(act.get('activity_id', act.get('id', 'unknown')))
                
                if "SYNC" in action or "CHECK_DATA_FLOW" in action:
                    if status == "SUCCESS":
                        findings.append(self._make_step("FINDING", "REPORT_ACTIVE_DATA_FLOW", "ACTIVE", sys_id, res_id, act_id))
                        remediations.append(self._make_step("REMEDIATION", "DISABLE_DATA_FLOW", "DISABLED", sys_id, res_id, ""))
                        verifications.append(self._make_step("VERIFICATION", "VERIFY_DATA_FLOW_DISABLED", "DISABLED", sys_id, res_id, ""))
                        
                elif "BACKUP" in sys_id or "ARCHIVE" in sys_id or "EXPORT" in action:
                    findings.append(self._make_step("FINDING", "REPORT_RESTORE_RISK", "ACTIVE", sys_id, res_id, act_id))
                    remediations.append(self._make_step("REMEDIATION", "BLOCK_RESTORE", "BLOCKED", sys_id, res_id, ""))
                    verifications.append(self._make_step("VERIFICATION", "VERIFY_RESTORE_BLOCKED", "BLOCKED", sys_id, res_id, ""))

        status = "INCOMPLETE" if findings else "COMPLETE"
        
        if not findings and not extracted_evidence:
            verifications.append(self._make_step("VERIFICATION", "VERIFY_RECORD_ABSENT", "ABSENT", "global_search", "no_records_found", "audit_log_check"))

        return self._build_result(case_id, status, identities, extracted_evidence, audit_at, findings, remediations, verifications)

    def _infer_category(self, content, origin):
        content_lower = str(content).lower()
        origin_lower = str(origin).lower()
        
        if "support" in origin_lower or "ticket" in content_lower:
            return "SUPPORT_MESSAGE"
        elif "attachment" in origin_lower or "document" in origin_lower:
            return "SUPPORT_ATTACHMENT"
        elif "analytics" in origin_lower or "telemetry" in content_lower:
            return "ANALYTICS_PROFILE"
        elif "export" in origin_lower or "download" in content_lower:
            return "USER_EXPORT"
        elif "marketing" in origin_lower or "campaign" in content_lower:
            return "MARKETING_PROFILE"
        elif "email" in origin_lower or "delivery" in content_lower:
            return "EMAIL_DELIVERY_LOG"
        elif "security" in origin_lower or "audit" in content_lower:
            return "SECURITY_AUDIT_LOG"
        elif "backup" in origin_lower or "archive" in content_lower:
            return "BACKUP_ARCHIVE"
        elif "tombstone" in origin_lower or "identity" in origin_lower:
            return "ACCOUNT_TOMBSTONE"
        elif "search" in origin_lower or "index" in content_lower:
            return "SEARCH_INDEX_ENTRY"
        else:
            return "USER_PROFILE"

    def _make_step(self, phase, operation, state, system_id, resource_id, evidence_id):
        return {
            "step_no": 0,
            "phase": phase,
            "system_id": system_id,
            "resource_id": resource_id,
            "operation": operation,
            "state": state,
            "evidence_id": evidence_id
        }

    def _build_result(self, case_id, status, identities, evidence, audit_at, findings, remediations, verifications):
        return {
            "case_id": case_id,
            "status": status,
            "identities": identities,
            "evidence": evidence,
            "findings": findings,
            "remediations": remediations,
            "verifications": verifications,
            "audit_at": audit_at
        }