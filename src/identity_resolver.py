# src/identity_resolver.py
import pandas as pd
from collections import defaultdict, deque
from .utils import load_csv

class IdentityResolver:
    def __init__(self):
        self.identities_df = load_csv("user_identities.csv")
        self.audit_log_df = load_csv("user_audit_log.csv")
        
        self.graph = defaultdict(set)
        self._build_graph()

    def _build_graph(self):
        # 1. Link current user_ids to their current identifiers
        for _, row in self.identities_df.iterrows():
            user_id = str(row.get('user_id', '')).strip()
            email = str(row.get('email', '')).strip().lower()
            phone = str(row.get('phone', '')).strip()
            email_hash = str(row.get('email_hash', '')).strip()
            
            if user_id and user_id != 'nan':
                if email and email != 'nan':
                    self.graph[user_id].add(email)
                    self.graph[email].add(user_id)
                if phone and phone != 'nan':
                    self.graph[user_id].add(phone)
                    self.graph[phone].add(user_id)
                if email_hash and email_hash != 'nan':
                    self.graph[user_id].add(email_hash)
                    self.graph[email_hash].add(user_id)

        # 2. Link historical identifiers from the audit log
        for _, row in self.audit_log_df.iterrows():
            user_id = str(row.get('user_id', '')).strip()
            field_name = str(row.get('field_name', '')).strip().lower()
            old_value = str(row.get('old_value', '')).strip().lower()
            new_value = str(row.get('new_value', '')).strip().lower()
            
            if user_id and user_id != 'nan':
                if old_value and old_value != 'nan':
                    self.graph[user_id].add(old_value)
                    self.graph[old_value].add(user_id)
                if new_value and new_value != 'nan':
                    self.graph[user_id].add(new_value)
                    self.graph[new_value].add(user_id)
            
            # Link old and new values directly if user_id is missing
            if (not user_id or user_id == 'nan') and old_value != 'nan' and new_value != 'nan':
                self.graph[old_value].add(new_value)
                self.graph[new_value].add(old_value)

    def resolve(self, target_identifier):
        target = str(target_identifier).strip().lower()
        if target not in self.graph:
            return {"emails": {target}, "user_ids": set(), "phones": set(), "hashes": set()}

        visited = set()
        queue = deque([target])
        visited.add(target)

        emails = set()
        user_ids = set()
        phones = set()
        hashes = set()

        while queue:
            current = queue.popleft()
            
            if current.startswith("user_"):
                user_ids.add(current)
            elif current.startswith("+") or current.isdigit():
                phones.add(current)
            elif len(current) == 64: # SHA-256 hash length
                hashes.add(current)
            else:
                emails.add(current)

            for neighbor in self.graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return {"emails": emails, "user_ids": user_ids, "phones": phones, "hashes": hashes}

    def get_all_resolved_identities(self, requests_df):
        resolved_map = {}
        for _, row in requests_df.iterrows():
            case_id = row['case_id']
            email = row['email']
            resolved_map[case_id] = self.resolve(email)
        return resolved_map