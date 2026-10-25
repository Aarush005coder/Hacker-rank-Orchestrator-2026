# src/step_generator.py
import json

class StepGenerator:
    def __init__(self):
        # Define the strict ordering of operations within each phase
        self.phase_order = {
            "FINDING": [
                "REPORT_REMAINING_RECORD",
                "REPORT_EXPOSED_PII",
                "REPORT_ACTIVE_DATA_FLOW",
                "REPORT_RESTORE_RISK"
            ],
            "REMEDIATION": [
                "DISABLE_DATA_FLOW",
                "BLOCK_RESTORE",
                "DELETE_RECORD",
                "REDACT_RECORD",
                "ANONYMIZE_RECORD"
            ],
            "VERIFICATION": [
                "VERIFY_RECORD_ABSENT",
                "VERIFY_RECORD_PRESENT",
                "VERIFY_RECORD_REDACTED",
                "VERIFY_RECORD_ANONYMIZED",
                "VERIFY_DATA_FLOW_DISABLED",
                "VERIFY_RESTORE_BLOCKED"
            ]
        }

    def generate(self, evaluation_result):
        """Generates the final steps_json array based on evaluation results."""
        status = evaluation_result['status']
        
        # NOT_APPLICABLE cases get an empty array
        if status == "NOT_APPLICABLE":
            return []
            
        steps = []
        
        if status == "INCOMPLETE":
            # Include findings, remediations, and verifications
            steps.extend(evaluation_result.get('findings', []))
            steps.extend(evaluation_result.get('remediations', []))
            steps.extend(evaluation_result.get('verifications', []))
            
            # Rule: Proposed remediation and future verification steps for INCOMPLETE cases use an empty evidence_id
            for step in steps:
                if step['phase'] in ['REMEDIATION', 'VERIFICATION']:
                    step['evidence_id'] = ""
                    
        elif status == "COMPLETE":
            # Rule: For COMPLETE, include only verification steps
            steps.extend(evaluation_result.get('verifications', []))
            
            # Rule: Findings and verification steps for COMPLETE cases must cite a file_id, activity_id, or audit_id
            # (Assuming state_evaluator already populated evidence_id for COMPLETE verifications)

        # Sort the steps according to the strict rules
        steps = self._sort_steps(steps)
        
        # Assign consecutive step_no starting at 1
        for i, step in enumerate(steps):
            step['step_no'] = i + 1
            
        return steps

    def _sort_steps(self, steps):
        """
        Sorts steps by:
        1. Phase (FINDING -> REMEDIATION -> VERIFICATION)
        2. Operation order within the phase
        3. system_id (ascending)
        4. resource_id (ascending)
        """
        def sort_key(step):
            phase = step.get('phase', '')
            operation = step.get('operation', '')
            system_id = step.get('system_id', '')
            resource_id = step.get('resource_id', '')
            
            # Get phase index
            phase_idx = list(self.phase_order.keys()).index(phase) if phase in self.phase_order else 99
            
            # Get operation index within phase
            op_idx = 99
            if phase in self.phase_order and operation in self.phase_order[phase]:
                op_idx = self.phase_order[phase].index(operation)
                
            return (phase_idx, op_idx, system_id, resource_id)
            
        return sorted(steps, key=sort_key)