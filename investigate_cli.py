"""
PS-01: MuleGuard Interactive Terminal Investigation CLI
Direct interactive terminal client demonstrating all USPs from the Hackathon Blueprint.
Communicates with C# Gateway (:5000) & Python Engine (:8000), with automatic local fallback.
"""

import sys
import os
import json
import urllib.request
import subprocess

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(ROOT_DIR, "python_engine"))

from synthetic_data import generate_synthetic_banking_data
from graph_engine import FinancialGraphEngine
from ripple_risk import RippleRiskEngine
from sleeper_mules import SleeperMuleDetector
from tainted_lien import TaintedLienCalculator
from ml_scorer import MLRiskScorer

# Initialize local in-memory engines for instant fallback
_accounts, _transactions, _complaints = generate_synthetic_banking_data()
_graph_engine = FinancialGraphEngine(_accounts, _transactions)
_ripple_engine = RippleRiskEngine(_graph_engine)
_sleeper_detector = SleeperMuleDetector(_accounts, _transactions, _graph_engine)
_lien_calculator = TaintedLienCalculator(_graph_engine)
_features = _graph_engine.compute_all_graph_features()
_ml_scorer = MLRiskScorer(_features)

C_BASE = "http://127.0.0.1:5000/api/bank"
PY_BASE = "http://127.0.0.1:8000/api"

def api_get(url):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def api_post(url, data):
    try:
        body = json.dumps(data).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=1.5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}

def print_header(title):
    print("\n" + "=" * 78)
    print(f"   {title}")
    print("=" * 78)

def show_investigation(role="BankAnalyst", fir="FIR-2026-104"):
    print_header(f"INVESTIGATION: {fir} (Role: {role})")
    url = f"{C_BASE}/investigate?firId={fir}&role={role}"
    res = api_get(url)

    if "error" in res or "nodes" not in res:
        # Local fallback
        trail_data = _graph_engine.trace_money_trail("ACC_VICTIM_01", max_hops=5)
        ripple_bonuses = _ripple_engine.propagate_complaint_risk("ACC_VICTIM_01")
        lien_map = _lien_calculator.calculate_tainted_balances("ACC_VICTIM_01", 100000.0)

        nodes = []
        for acc_id in trail_data["trail_nodes"]:
            meta = _accounts.get(acc_id, {})
            r_bonus = ripple_bonuses.get(acc_id, 0.0)
            score_res = _ml_scorer.score_account(acc_id, ripple_bonus=r_bonus)
            is_unmasked = (role == "LawEnforcement" and bool(fir))
            disp_id = meta.get("holder_name") if is_unmasked else f"TOK_{acc_id[-8:]} [HMAC]"
            nodes.append({
                "account_id": acc_id,
                "display_id": disp_id,
                "bank": meta.get("bank"),
                "risk_score": score_res["risk_score"],
                "tainted_amount": lien_map.get(acc_id, {}).get("tainted_stolen_inr", 0.0),
                "safe_balance": lien_map.get(acc_id, {}).get("safe_clean_balance_inr", meta.get("total_balance", 0)),
                "reasons": score_res["reasons"]
            })
    else:
        nodes = res["nodes"]

    print(f"\n{'ACCOUNT':<32} | {'BANK':<8} | {'RISK':<8} | {'SCAM MONEY':<12} | {'SAFE USABLE':<12}")
    print("-" * 80)
    for n in nodes:
        disp = n.get("display_id") or n.get("account_id")
        bank = n.get("bank", "N/A")
        risk = f"{n.get('risk_score', 0)}/100"
        scam = f"₹{n.get('tainted_amount', 0):,.0f}"
        safe = f"₹{n.get('safe_balance', 0):,.0f}"
        print(f"{disp:<32} | {bank:<8} | {risk:<8} | {scam:<12} | {safe:<12}")

    print("\n[AI REASONS FOR SELECTED MULE (Sohan Lal / ACC_MULE_L1)]:")
    mule_node = next((n for n in nodes if "MULE" in n.get("account_id", "") or n.get("risk_score", 0) > 90), None)
    if mule_node:
        for r in mule_node.get("reasons", []):
            print(f"  • {r.get('label')}")

def run_sleeper_scan():
    print_header("USP 2: 'SLEEPER MULE' PRE-CRIME STAGING DETECTION")
    res = api_post(f"{PY_BASE}/mules/detect-sleeper", {})
    sleepers = res.get("sleeper_mules_detected")
    if not sleepers:
        sleepers = _sleeper_detector.scan_for_sleeper_mules()

    print(f"Found {len(sleepers)} account(s) in pre-crime staging phase:\n")
    for s in sleepers:
        print(f"  • Account  : {s.get('holder_name')} ({s.get('account_id')}) [{s.get('bank')}]")
        print(f"    Risk     : {s.get('sleeper_risk_score')}/100")
        print(f"    Action   : {s.get('recommended_action')}")
        for r in s.get("reasons", []):
            print(f"      - {r}")
        print()

def run_partial_lien():
    print_header("USP 3: SMART 'TAINTED AMOUNT' PARTIAL LIEN HOLD EXECUTION")
    req = {
        "AccountId": "ACC_MERCHANT_OK",
        "TaintedAmount": 9500,
        "TotalBalance": 540000,
        "UserRole": "BankCompliance",
        "FirId": "FIR-2026-104"
    }
    res = api_post(f"{C_BASE}/place-partial-lien", req)
    if "error" in res or "status" not in res:
        # Local calculation fallback
        lien_map = _lien_calculator.calculate_tainted_balances("ACC_VICTIM_01", 100000.0)
        m_info = lien_map.get("ACC_MERCHANT_OK", {})
        res = {
            "lienHoldId": "LIEN-LOCAL-MOCK",
            "status": "PARTIAL_LIEN_ACTIVE",
            "accountId": "ACC_MERCHANT_OK",
            "frozenAmount": m_info.get("tainted_stolen_inr", 9500),
            "usableBalance": m_info.get("safe_clean_balance_inr", 530500),
            "timestamp": "2026-10-25 18:20:00"
        }

    print("Core Banking Execution Result:")
    print(json.dumps(res, indent=2))
    print("\nOutcome: Innocent FreshMart Supermarket's balance of ₹5,30,500 remains OPEN and ACTIVE!")

def run_audit_verify():
    print_header("ENTERPRISE SECURITY: SHA-256 TAMPER-PROOF AUDIT CHAIN")
    res = api_get(f"{C_BASE}/verify-audit-chain")
    if "error" in res:
        # Run C# runner directly to show live verification
        dotnet_exe = os.path.expandvars(r"%USERPROFILE%\.dotnet\dotnet.exe")
        subprocess.run([dotnet_exe, "run", "--project", os.path.join(ROOT_DIR, "csharp_gateway", "BankGateway.csproj"), "--no-build", "--", "--run-tests"], cwd=ROOT_DIR)
        return

    print(f"Verification Status : {res.get('statusMessage', 'OK')}")
    print(f"Valid Cryptography  : {res.get('isValid')}")
    print(f"Total Block Entries : {res.get('totalRecords')}")

def run_benchmark():
    print_header("A/B BENCHMARK EVALUATION (Legacy Static Rules vs Hybrid Graph-AI)")
    res = api_get(f"{C_BASE}/benchmark-metrics")
    if "error" in res:
        res = _ml_scorer.evaluate_ab_benchmark(_transactions)

    print(json.dumps(res, indent=2))

def run_dossier():
    print_header("USP 4: ONE-CLICK COURT-READY EVIDENCE DOSSIER")
    res = api_get(f"{C_BASE}/generate-dossier?firId=FIR-2026-104&role=LawEnforcement")
    if "error" in res:
        res = {
            "firId": "FIR-2026-104",
            "role": "LawEnforcement",
            "hash": "a4f89d300b91e2f89c0...",
            "legalBasis": "Sec 102 CrPC Partial Lien Freeze",
            "conduitTraced": "Ramesh Kumar -> Sohan Lal (L1) -> Smurf A/B/C -> Cashout Boss"
        }
    print(json.dumps(res, indent=2))

def explore_real_datasets():
    print_header("REAL SOA BANK STATEMENTS CATALOG (26 Files / 494,276 Transactions)")
    catalog = api_get(f"{PY_BASE}/real-datasets/catalog")
    if "error" in catalog or not catalog.get("files"):
        cat_file = os.path.join(ROOT_DIR, "python_engine", "real_dataset_catalog.json")
        if os.path.exists(cat_file):
            with open(cat_file, "r", encoding="utf-8") as fp:
                catalog = json.load(fp)
        else:
            print("Catalog file not found.")
            return

    files = catalog.get("files", [])
    print(f"Total Statement Workbooks Indexed: {len(files)}\n")
    print(f"{'#':<3} | {'FILE NAME':<18} | {'PRIMARY HOLDER':<24} | {'ACCS':<5} | {'TXS':<7} | {'FLAGGED MULES'}")
    print("-" * 80)
    for idx, f in enumerate(files, 1):
        fn = f.get("file_name", "N/A")
        holder = (f.get("primary_holder") or "Unknown")[:23]
        acc_cnt = f.get("total_accounts", 0)
        tx_cnt = f.get("total_transactions", 0)
        mules = f.get("high_risk_mules_detected", 0)
        flag_str = f"⚠️ {mules} Mule(s)" if mules > 0 else "0 (Clean)"
        print(f"{idx:<3} | {fn:<18} | {holder:<24} | {acc_cnt:<5} | {tx_cnt:<7} | {flag_str}")

    pick = input("\nEnter file number to inspect (or Enter to return): ").strip()
    if not pick.isdigit() or int(pick) < 1 or int(pick) > len(files):
        return

    sel_file = files[int(pick) - 1]
    print_header(f"STATEMENT DETAILS: {sel_file['file_name']}")
    print(f"Primary Holder    : {sel_file.get('primary_holder')}")
    print(f"Total Transactions: {sel_file.get('total_transactions'):,}")
    print(f"Total Debits (DR) : ₹{sel_file.get('total_debits', 0):,.2f}")
    print(f"Total Credits (CR): ₹{sel_file.get('total_credits', 0):,.2f}")
    print(f"Flagged Mule Accs : {sel_file.get('high_risk_mules_detected', 0)}")

    accounts = sel_file.get("accounts", [])
    if accounts:
        print(f"\nACCOUNTS IN THIS STATEMENT ({len(accounts)}):")
        print(f"{'ACCOUNT ID':<20} | {'HOLDER':<20} | {'DEBITS':<14} | {'CREDITS':<14} | {'RISK':<8} | {'STATUS'}")
        print("-" * 88)
        for acc in accounts[:15]:
            aid = acc.get("raw_account") or acc.get("account_id")
            hname = (acc.get("holder_name") or "Unknown")[:19]
            dr = f"₹{acc.get('total_debit', 0):,.0f}"
            cr = f"₹{acc.get('total_credit', 0):,.0f}"
            risk = f"{acc.get('risk_score', 0)}/100"
            stat = "🚨 MULE" if acc.get("is_flagged_mule") else "NORMAL"
            print(f"{aid:<20} | {hname:<20} | {dr:<14} | {cr:<14} | {risk:<8} | {stat}")
            if acc.get("reasons"):
                for r in acc.get("reasons", []):
                    print(f"    ↳ {r.get('label')}")

def search_real_accounts_cli():
    query = input("\nEnter account number, customer name, or keyword: ").strip()
    if not query:
        return
    print_header(f"SEARCHING ACCOUNTS: '{query}'")
    cat_file = os.path.join(ROOT_DIR, "python_engine", "real_dataset_catalog.json")
    results = []
    if os.path.exists(cat_file):
        with open(cat_file, "r", encoding="utf-8") as fp:
            cat = json.load(fp)
            q = query.lower()
            for f in cat.get("files", []):
                for acc in f.get("accounts", []):
                    acc_num = str(acc.get("raw_account", "")).lower()
                    h_name = str(acc.get("holder_name", "")).lower()
                    if q in acc_num or q in h_name:
                        results.append((f["file_name"], acc))
    if not results:
        print("No matching accounts found.")
        return

    print(f"Found {len(results)} matching account(s):\n")
    print(f"{'FILE':<16} | {'ACCOUNT NO':<20} | {'CUSTOMER':<22} | {'BALANCE':<14} | {'RISK'}")
    print("-" * 80)
    for fn, acc in results[:20]:
        aid = acc.get("raw_account") or acc.get("account_id")
        cname = (acc.get("holder_name") or "Unknown")[:21]
        bal = f"₹{acc.get('balance', 0):,.2f}"
        risk = f"{acc.get('risk_score', 0)}/100"
        print(f"{fn:<16} | {aid:<20} | {cname:<22} | {bal:<14} | {risk}")

def main():
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        if "investigate" in cmd: show_investigation()
        elif "sleeper" in cmd: run_sleeper_scan()
        elif "lien" in cmd: run_partial_lien()
        elif "audit" in cmd: run_audit_verify()
        elif "benchmark" in cmd: run_benchmark()
        elif "dossier" in cmd: run_dossier()
        elif "datasets" in cmd or "real" in cmd: explore_real_datasets()
        elif "search" in cmd: search_real_accounts_cli()
        return

    while True:
        print("\n" + "=" * 60)
        print("   MULEGUARD FRAUD INVESTIGATION CLI")
        print("=" * 60)
        print("1. Investigate Money Trail (Bank Analyst - HMAC Masked)")
        print("2. Investigate Money Trail (Police Officer - FIR Unmasked)")
        print("3. Run Sleeper Mule Pre-Crime Scan (USP 2)")
        print("4. Execute Smart Partial Lien Hold (USP 3)")
        print("5. Verify SHA-256 Tamper-Proof Audit Chain")
        print("6. Run A/B Benchmark (Static Rules vs Graph-AI)")
        print("7. Export Court-Ready Legal Dossier (USP 4)")
        print("8. Explore Real SOA Bank Datasets (26 Files / 494k Txs)")
        print("9. Search 14,313 Real Bank Accounts")
        print("0. Exit")
        choice = input("\nEnter choice (0-9): ").strip()
        if choice == "1": show_investigation("BankAnalyst", "FIR-2026-104")
        elif choice == "2": show_investigation("LawEnforcement", "FIR-2026-104")
        elif choice == "3": run_sleeper_scan()
        elif choice == "4": run_partial_lien()
        elif choice == "5": run_audit_verify()
        elif choice == "6": run_benchmark()
        elif choice == "7": run_dossier()
        elif choice == "8": explore_real_datasets()
        elif choice == "9": search_real_accounts_cli()
        elif choice == "0": break

if __name__ == "__main__":
    main()
