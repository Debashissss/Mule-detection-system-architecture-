"""
PS-01: Intelligent Mule Account Detection & Fraud Investigation Platform
USP 3: Smart "Tainted Amount" Partial Lien Calculator
Proportional flow tracking to compute exact illicit rupees in downstream accounts,
preventing blanket freezes on innocent merchants.
"""

from collections import defaultdict

class TaintedLienCalculator:
    def __init__(self, graph_engine):
        self.ge = graph_engine

    def calculate_tainted_balances(self, source_victim_account, initial_stolen_amount):
        """
        Traces downstream transfers originating from the victim's payment.
        Calculates exact tainted rupee amount per account, protecting innocent merchant balance.
        """
        tainted_rupees = defaultdict(float)
        tainted_rupees[source_victim_account] = 0.0  # Victim's own balance is clean

        # BFS downstream
        queue = [(source_victim_account, float(initial_stolen_amount))]
        visited = set()

        while queue:
            curr_acc, curr_tainted = queue.pop(0)
            if curr_acc in visited and curr_acc != source_victim_account:
                continue
            visited.add(curr_acc)

            out_edges = list(self.ge.G.out_edges(curr_acc, data=True))
            total_out = sum(e[2]["amount"] for e in out_edges)

            for _, next_acc, d in out_edges:
                edge_amt = d["amount"]
                # Calculate proportion of tainted money in this transfer
                if total_out > 0:
                    transfer_tainted = min(edge_amt, curr_tainted * (edge_amt / total_out))
                else:
                    transfer_tainted = min(edge_amt, curr_tainted)

                tainted_rupees[next_acc] += transfer_tainted
                queue.append((next_acc, transfer_tainted))

        # Build clean summary for each touched account
        lien_dossier = {}
        for acc_id, tainted_val in tainted_rupees.items():
            if tainted_val <= 0 or acc_id == source_victim_account:
                continue

            acc_meta = self.ge.accounts.get(acc_id, {})
            total_balance = acc_meta.get("total_balance", tainted_val)
            safe_spendable = max(0.0, total_balance - tainted_val)

            lien_dossier[acc_id] = {
                "account_id": acc_id,
                "holder_name": acc_meta.get("holder_name", "Unknown"),
                "bank": acc_meta.get("bank", "Unknown"),
                "total_balance_inr": total_balance,
                "tainted_stolen_inr": round(tainted_val, 2),
                "safe_clean_balance_inr": round(safe_spendable, 2),
                "recommended_action": "EXECUTE_PARTIAL_LIEN",
                "blanket_freeze_prevented": acc_meta.get("is_merchant", False) or safe_spendable > 0
            }

        return lien_dossier
