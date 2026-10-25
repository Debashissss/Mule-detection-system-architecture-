"""
PS-01: Intelligent Mule Account Detection & Fraud Investigation Platform
FastAPI Microservice for Python Data Science & ML Engine
Port: 8000
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import json
from typing import Optional, List, Dict, Any

from synthetic_data import generate_synthetic_banking_data
from dataset_ingestor import ingest_soa_folder
from graph_engine import FinancialGraphEngine
from ripple_risk import RippleRiskEngine
from sleeper_mules import SleeperMuleDetector
from tainted_lien import TaintedLienCalculator
from ml_scorer import MLRiskScorer


app = FastAPI(
    title="MuleGuard Python Data Science & Graph ML Service",
    version="1.0.0",
    description="Backend microservice for temporal graph analytics, ML risk scoring, and USP implementations"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global in-memory state initialized with synthetic banking data
accounts, transactions, complaints = generate_synthetic_banking_data()
graph_engine = FinancialGraphEngine(accounts, transactions)
ripple_engine = RippleRiskEngine(graph_engine)
sleeper_detector = SleeperMuleDetector(accounts, transactions, graph_engine)
lien_calculator = TaintedLienCalculator(graph_engine)
features = graph_engine.compute_all_graph_features()
ml_scorer = MLRiskScorer(features)

class AnalyzeRequest(BaseModel):
    fir_id: Optional[str] = "FIR-2026-104"
    start_account: Optional[str] = "ACC_VICTIM_01"
    propagate_ripple: Optional[bool] = True

class PartialLienRequest(BaseModel):
    victim_account: str = "ACC_VICTIM_01"
    stolen_amount: float = 100000.0

class SimulateAttackRequest(BaseModel):
    attack_type: str  # "smurfing", "4hop_layering", "fir_ripple", "sleeper_mule", "reset"

@app.get("/health")
def health_check():
    return {
        "status": "ONLINE",
        "service": "MuleGuard Python ML Engine",
        "accounts_indexed": len(accounts),
        "transactions_indexed": len(transactions),
        "complaints_indexed": len(complaints)
    }

@app.get("/api/dataset/summary")
def get_dataset_summary():
    return {
        "total_accounts": len(accounts),
        "total_transactions": len(transactions),
        "total_complaints": len(complaints),
        "banks_involved": list(set(a["bank"] for a in accounts.values())),
        "complaints": complaints
    }

@app.post("/api/dataset/ingest-real-soa")
def ingest_real_soa(max_files: int = 10):
    soa_accs, soa_txs = ingest_soa_folder("datasets", max_files=max_files)
    return {
        "status": "SOA_DATASET_LOADED",
        "files_ingested": max_files,
        "accounts_parsed": len(soa_accs),
        "transactions_parsed": len(soa_txs),
        "sample_accounts": list(soa_accs.values())[:5]
    }

@app.get("/api/real-datasets/catalog")
def get_real_dataset_catalog():
    catalog_path = os.path.join(os.path.dirname(__file__), "real_dataset_catalog.json")
    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    return {"total_files": 0, "files": []}

@app.get("/api/real-datasets/file/{file_name}")
def get_real_dataset_file(file_name: str):
    catalog_path = os.path.join(os.path.dirname(__file__), "real_dataset_catalog.json")
    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as fp:
            cat = json.load(fp)
            for f in cat.get("files", []):
                if f["file_name"] == file_name:
                    return f
    raise HTTPException(status_code=404, detail="SOA file not found in catalog")

@app.get("/api/real-datasets/search")
def search_real_accounts(query: str):
    catalog_path = os.path.join(os.path.dirname(__file__), "real_dataset_catalog.json")
    results = []
    if os.path.exists(catalog_path):
        with open(catalog_path, "r", encoding="utf-8") as fp:
            cat = json.load(fp)
            q = query.lower().strip()
            for f in cat.get("files", []):
                for acc in f.get("accounts", []):
                    if q in acc["raw_account"].lower() or q in acc["holder_name"].lower():
                        results.append({
                            **acc,
                            "source_file": f["file_name"]
                        })
                        if len(results) >= 25: break
                if len(results) >= 25: break
    return {"query": query, "total_matches": len(results), "accounts": results}



@app.post("/api/graph/analyze")
def analyze_graph(req: AnalyzeRequest):
    trail_data = graph_engine.trace_money_trail(req.start_account, max_hops=5)
    
    # Calculate ripple risk if requested
    ripple_bonuses = {}
    if req.propagate_ripple:
        ripple_bonuses = ripple_engine.propagate_complaint_risk(req.start_account)

    scored_nodes = []
    for acc_id in trail_data["trail_nodes"]:
        meta = accounts.get(acc_id, {})
        r_bonus = ripple_bonuses.get(acc_id, 0.0)
        score_res = ml_scorer.score_account(acc_id, ripple_bonus=r_bonus)
        
        scored_nodes.append({
            "account_id": acc_id,
            "holder_name": meta.get("holder_name", "Unknown"),
            "bank": meta.get("bank", "Unknown"),
            "device_id": meta.get("device_id", "Unknown"),
            "ip_address": meta.get("ip_address", "Unknown"),
            "phone": meta.get("phone", "Unknown"),
            "pan": meta.get("pan", "Unknown"),
            "total_balance": meta.get("total_balance", 0),
            "account_type": meta.get("account_type", "normal"),
            "risk_score": score_res["risk_score"],
            "is_flagged_mule": score_res["is_flagged_mule"],
            "reasons": score_res["reasons"],
            "ripple_bonus": r_bonus
        })

    # Calculate smart tainted lien amounts
    lien_map = lien_calculator.calculate_tainted_balances(req.start_account, 100000.0)
    for n in scored_nodes:
        n["tainted_amount"] = lien_map.get(n["account_id"], {}).get("tainted_stolen_inr", 0.0)
        n["safe_balance"] = lien_map.get(n["account_id"], {}).get("safe_clean_balance_inr", n["total_balance"])

    return {
        "start_account": req.start_account,
        "fir_id": req.fir_id,
        "nodes": scored_nodes,
        "edges": trail_data["trail_edges"],
        "shadow_edges": trail_data["shadow_edges"],
        "lien_dossier": lien_map
    }

@app.post("/api/ripple/propagate")
def trigger_ripple_propagation(complaint_account: str = "ACC_VICTIM_01"):
    ripples = ripple_engine.propagate_complaint_risk(complaint_account)
    return {
        "status": "RIPPLE_PROPAGATED",
        "origin_victim": complaint_account,
        "affected_intermediaries": ripples
    }

@app.post("/api/mules/detect-sleeper")
def detect_sleeper_mules():
    sleepers = sleeper_detector.scan_for_sleeper_mules()
    return {
        "status": "SCAN_COMPLETE",
        "sleeper_mules_detected": sleepers,
        "total_detected": len(sleepers)
    }

@app.post("/api/lien/calculate")
def calculate_partial_lien(req: PartialLienRequest):
    result = lien_calculator.calculate_tainted_balances(req.victim_account, req.stolen_amount)
    return {
        "victim_account": req.victim_account,
        "stolen_amount": req.stolen_amount,
        "accounts_to_partially_freeze": result
    }

@app.get("/api/benchmark/evaluation")
def get_benchmark_evaluation():
    return ml_scorer.evaluate_ab_benchmark(transactions)

@app.post("/api/simulator/inject")
def simulate_attack(req: SimulateAttackRequest):
    global accounts, transactions, complaints, graph_engine, ripple_engine, sleeper_detector, lien_calculator, ml_scorer, features
    
    if req.attack_type == "reset":
        accounts, transactions, complaints = generate_synthetic_banking_data()
    elif req.attack_type == "smurfing":
        # Boost smurf scores
        for k in ["ACC_SMURF_A", "ACC_SMURF_B", "ACC_SMURF_C"]:
            if k in accounts:
                accounts[k]["total_balance"] += 9500
    elif req.attack_type == "fir_ripple":
        complaints.append({
            "fir_id": "FIR-2026-109",
            "victim_account": "ACC_MULE_L1",
            "reported_time": "2026-10-25 12:00:00",
            "stolen_amount": 100000,
            "description": "Secondary FIR linked directly to intermediary ring"
        })

    graph_engine = FinancialGraphEngine(accounts, transactions)
    ripple_engine = RippleRiskEngine(graph_engine)
    sleeper_detector = SleeperMuleDetector(accounts, transactions, graph_engine)
    lien_calculator = TaintedLienCalculator(graph_engine)
    features = graph_engine.compute_all_graph_features()
    ml_scorer = MLRiskScorer(features)

    return {
        "status": "SCENARIO_INJECTED",
        "scenario": req.attack_type,
        "total_accounts": len(accounts),
        "total_transactions": len(transactions)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
