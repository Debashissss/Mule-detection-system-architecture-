"""
PS-01: Intelligent Mule Account Detection & Fraud Investigation Platform
Graph Analytics & Temporal Flow Engine (NetworkX)
Implements:
- Time-Delta Velocity Weighting (Delta-t Pass-Through Detection)
- Non-Financial Shadow Edges (Device ID & IP Fusion)
- Directed MultiGraph Topological Analytics
"""

import networkx as nx
from datetime import datetime
from collections import defaultdict

class FinancialGraphEngine:
    def __init__(self, accounts_dict, transactions_list):
        self.accounts = accounts_dict
        self.transactions = transactions_list
        self.G = nx.MultiDiGraph()
        self.shadow_G = nx.Graph()
        self._build_graphs()

    def _build_graphs(self):
        # 1. Add all accounts as nodes
        for acc_id, meta in self.accounts.items():
            self.G.add_node(acc_id, **meta)
            self.shadow_G.add_node(acc_id, **meta)

        # 2. Add transaction edges with timestamp and amount
        for tx in self.transactions:
            t_obj = datetime.strptime(tx["timestamp"], "%Y-%m-%d %H:%M:%S")
            self.G.add_edge(
                tx["from_account"],
                tx["to_account"],
                key=tx["tx_id"],
                amount=tx["amount"],
                timestamp=t_obj,
                channel=tx.get("channel", "UPI"),
                is_fraud=tx.get("is_fraud", False),
                ring=tx.get("ring", "normal")
            )

        # 3. Add Non-Financial Shadow Edges (Device ID, IP Subnet clustering)
        device_map = defaultdict(list)
        ip_map = defaultdict(list)
        for acc_id, meta in self.accounts.items():
            dev = meta.get("device_id")
            if dev and not dev.startswith("DEV_NORM_"):
                device_map[dev].append(acc_id)
            ip = meta.get("ip_address")
            if ip and not ip.startswith("192.168."):
                ip_map[ip].append(acc_id)

        # Connect accounts that share a suspicious Device ID or IP
        for dev, group in device_map.items():
            if len(group) > 1:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        self.shadow_G.add_edge(group[i], group[j], reason="Shared Device", identifier=dev)

        for ip, group in ip_map.items():
            if len(group) > 1:
                for i in range(len(group)):
                    for j in range(i + 1, len(group)):
                        if not self.shadow_G.has_edge(group[i], group[j]):
                            self.shadow_G.add_edge(group[i], group[j], reason="Shared IP Subnet", identifier=ip)

    def compute_temporal_velocity_features(self, account_id):
        """
        Calculates Time-Delta Velocity Weighting:
        - How quickly incoming funds are pushed out (Delta-t)
        - Drain velocity ratio (out_flow / in_flow within 180 seconds)
        """
        in_edges = sorted(self.G.in_edges(account_id, data=True), key=lambda x: x[2]["timestamp"])
        out_edges = sorted(self.G.out_edges(account_id, data=True), key=lambda x: x[2]["timestamp"])

        total_in = sum(e[2]["amount"] for e in in_edges)
        total_out = sum(e[2]["amount"] for e in out_edges)

        fast_drain_amount = 0
        min_delta_t_seconds = 999999

        # For every incoming payment, find outgoing transfers that occurred within 180 seconds
        for in_u, in_v, in_d in in_edges:
            in_time = in_d["timestamp"]
            for out_u, out_v, out_d in out_edges:
                out_time = out_d["timestamp"]
                delta_t = (out_time - in_time).total_seconds()
                if 0 <= delta_t <= 180:
                    fast_drain_amount += out_d["amount"]
                    if delta_t < min_delta_t_seconds:
                        min_delta_t_seconds = delta_t

        drain_ratio_fast = (fast_drain_amount / total_in) if total_in > 0 else 0.0
        drain_ratio_fast = min(1.0, drain_ratio_fast)

        return {
            "total_inflow": total_in,
            "total_outflow": total_out,
            "fast_drain_amount": fast_drain_amount,
            "drain_ratio_fast": round(drain_ratio_fast, 3),
            "min_delta_t_seconds": min_delta_t_seconds if min_delta_t_seconds < 999999 else -1
        }

    def compute_all_graph_features(self):
        """
        Computes both structural graph metrics and behavioral velocity metrics.
        """
        features = {}

        # PageRank centrality
        simple_di = nx.DiGraph()
        for u, v, d in self.G.edges(data=True):
            if simple_di.has_edge(u, v):
                simple_di[u][v]["weight"] += d["amount"]
            else:
                simple_di.add_edge(u, v, weight=d["amount"])

        pagerank = nx.pagerank(simple_di, alpha=0.85, weight="weight") if len(simple_di) > 0 else {}

        for acc_id, meta in self.accounts.items():
            in_deg = self.G.in_degree(acc_id)
            out_deg = self.G.out_degree(acc_id)
            fan_ratio = (out_deg / in_deg) if in_deg > 0 else (out_deg * 2.0)
            
            # Shadow edge links (how many accounts share device/IP)
            shadow_degree = self.shadow_G.degree(acc_id)

            # Temporal velocity
            velocity = self.compute_temporal_velocity_features(acc_id)

            features[acc_id] = {
                "account_id": acc_id,
                "in_degree": in_deg,
                "out_degree": out_deg,
                "fan_ratio": round(fan_ratio, 2),
                "pagerank": round(pagerank.get(acc_id, 0.0), 6),
                "shadow_links": shadow_degree,
                "total_inflow": velocity["total_inflow"],
                "total_outflow": velocity["total_outflow"],
                "drain_ratio_fast": velocity["drain_ratio_fast"],
                "min_delta_t_seconds": velocity["min_delta_t_seconds"],
                "penny_drops": meta.get("penny_drops", 0),
                "kyc_days": meta.get("kyc_days", 365),
                "is_merchant": 1 if meta.get("is_merchant") else 0,
                "is_mule_label": 1 if meta.get("is_mule") else 0
            }

        return features

    def trace_money_trail(self, start_account_id, max_hops=5):
        """
        BFS/DFS Multi-Hop Trail Extraction from victim or seed account.
        Returns nodes and edges traversed in the chain.
        """
        visited_nodes = {start_account_id}
        queue = [(start_account_id, 0)]
        trail_edges = []

        while queue:
            curr, depth = queue.pop(0)
            if depth >= max_hops:
                continue

            for _, next_node, k, d in self.G.out_edges(curr, keys=True, data=True):
                trail_edges.append({
                    "tx_id": k,
                    "from_account": curr,
                    "to_account": next_node,
                    "amount": d["amount"],
                    "timestamp": d["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    "hop": depth + 1
                })
                if next_node not in visited_nodes:
                    visited_nodes.add(next_node)
                    queue.append((next_node, depth + 1))

        # Also collect shadow edges among visited nodes
        shadow_links = []
        for u in visited_nodes:
            for v in self.shadow_G.neighbors(u):
                if v in visited_nodes and u < v:
                    edge_data = self.shadow_G.get_edge_data(u, v)
                    shadow_links.append({
                        "from_account": u,
                        "to_account": v,
                        "reason": edge_data.get("reason", "Shared Device"),
                        "identifier": edge_data.get("identifier", "")
                    })

        return {
            "trail_nodes": list(visited_nodes),
            "trail_edges": trail_edges,
            "shadow_edges": shadow_links
        }
