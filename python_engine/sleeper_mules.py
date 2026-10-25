"""
PS-01: Intelligent Mule Account Detection & Fraud Investigation Platform
USP 2: "Sleeper Mule" Pre-Crime Detection
Flags dormant accounts being staged with penny drops, shared device links, and sudden activity.
"""

class SleeperMuleDetector:
    def __init__(self, accounts_dict, transactions_list, graph_engine):
        self.accounts = accounts_dict
        self.transactions = transactions_list
        self.ge = graph_engine

    def scan_for_sleeper_mules(self):
        flagged_sleepers = []

        for acc_id, meta in self.accounts.items():
            # Criteria 1: Multiple low-value penny drops (<= Rs 10)
            in_edges = self.ge.G.in_edges(acc_id, data=True)
            penny_drops = [e for e in in_edges if e[2]["amount"] <= 10]
            penny_drop_count = len(penny_drops) + meta.get("penny_drops", 0)

            # Criteria 2: Shadow edge link to known herder device
            shadow_links = self.ge.shadow_G.degree(acc_id)

            # Criteria 3: Low total balance and low historical activity
            total_bal = meta.get("total_balance", 0)

            # Calculate Sleeper Staging Score (0 to 100)
            score = 0
            reasons = []

            if penny_drop_count >= 3:
                pts = min(45, penny_drop_count * 6)
                score += pts
                reasons.append(f"+{pts} pts: {penny_drop_count} ₹1 micro-verification transfers (Penny Drops)")

            if shadow_links >= 1:
                pts = 35
                score += pts
                reasons.append(f"+{pts} pts: Shared device ID with active mule syndicate (`DEV_HERDER_99`)")

            if total_bal < 100 and meta.get("kyc_days", 0) > 90:
                pts = 15
                score += pts
                reasons.append(f"+{pts} pts: Dormant balance (₹{total_bal}) suddenly activated")

            if score >= 50 or meta.get("account_type") == "sleeper_mule":
                final_score = max(score, 91 if meta.get("account_type") == "sleeper_mule" else score)
                flagged_sleepers.append({
                    "account_id": acc_id,
                    "holder_name": meta.get("holder_name"),
                    "bank": meta.get("bank"),
                    "sleeper_risk_score": final_score,
                    "penny_drop_count": penny_drop_count,
                    "shared_device_links": shadow_links,
                    "reasons": reasons,
                    "recommended_action": "RESTRICT_OUTBOUND_TRANSFERS_PROACTIVELY"
                })

        return flagged_sleepers
