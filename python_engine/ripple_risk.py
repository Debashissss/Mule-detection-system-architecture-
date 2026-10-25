"""
PS-01: Intelligent Mule Account Detection & Fraud Investigation Platform
USP 1: Dynamic "Ripple Risk" Propagation Engine
Executes decaying risk wave downstream from cybercrime complaint / FIR source.
"""

import networkx as nx

class RippleRiskEngine:
    def __init__(self, graph_engine):
        self.ge = graph_engine

    def propagate_complaint_risk(self, complaint_account_id, base_shock=85.0, decay_factor=0.65, max_hops=4):
        """
        Propagates risk wave downstream starting from the account linked to the complaint/FIR.
        Hop 1: Shock * 1.0
        Hop 2: Shock * 0.65
        Hop 3: Shock * 0.65^2 = ~0.42
        Hop 4: Shock * 0.65^3 = ~0.27
        """
        ripple_scores = {}
        queue = [(complaint_account_id, 0, base_shock)]
        visited_hops = {complaint_account_id: 0}

        while queue:
            curr_node, current_hop, current_shock = queue.pop(0)

            if current_hop > 0:
                ripple_scores[curr_node] = round(current_shock, 1)

            if current_hop >= max_hops:
                continue

            # Follow outgoing financial transactions downstream
            out_neighbors = list(self.ge.G.successors(curr_node))
            next_shock = current_shock * decay_factor

            for neighbor in out_neighbors:
                if neighbor not in visited_hops or visited_hops[neighbor] > current_hop + 1:
                    visited_hops[neighbor] = current_hop + 1
                    queue.append((neighbor, current_hop + 1, next_shock))

            # Also propagate through shadow edges (shared device) with a 0.85 multiplier
            for shadow_neighbor in self.ge.shadow_G.neighbors(curr_node):
                if shadow_neighbor not in visited_hops:
                    visited_hops[shadow_neighbor] = current_hop + 1
                    shadow_shock = current_shock * 0.85
                    queue.append((shadow_neighbor, current_hop + 1, shadow_shock))

        return ripple_scores
