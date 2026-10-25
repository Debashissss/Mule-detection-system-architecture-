import urllib.request
import json
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def test():
    # 1. Investigate as Bank Analyst
    req = urllib.request.Request("http://127.0.0.1:5000/api/bank/investigate?firId=FIR-2026-104&role=BankAnalyst")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read().decode())
        print("=== C# INVESTIGATE (Bank Analyst) ===")
        print("Total nodes:", len(data["nodes"]))
        print("Total edges:", len(data["edges"]))
        print("Shadow edges:", len(data["shadow_edges"]))
        for n in data["nodes"][:3]:
            print(f"  Node: {n['display_id']} | Bank: {n['bank']} | Risk: {n['risk_score']} | Scam: INR {n['tainted_amount']}")

    # 2. Investigate as Police (Unmasked)
    req2 = urllib.request.Request("http://127.0.0.1:5000/api/bank/investigate?firId=FIR-2026-104&role=LawEnforcement")
    with urllib.request.urlopen(req2) as resp:
        data2 = json.loads(resp.read().decode())
        print("\n=== C# INVESTIGATE (Police Officer - FIR-2026-104) ===")
        print("PII Unmasked?", data2["is_pii_unmasked"])
        for n in data2["nodes"][:3]:
            print(f"  Unmasked: {n['display_id']} | Real Name: {n['real_name']}")

    # 3. Partial Lien
    lien_req = {
        "AccountId": "ACC_MULE_L1",
        "TaintedAmount": 100000,
        "TotalBalance": 104500,
        "UserRole": "BankCompliance",
        "FirId": "FIR-2026-104"
    }
    req3 = urllib.request.Request(
        "http://127.0.0.1:5000/api/bank/place-partial-lien",
        data=json.dumps(lien_req).encode("utf-8"),
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req3) as resp:
        print("\n=== C# EXECUTE PARTIAL LIEN ===")
        print(json.loads(resp.read().decode()))

    # 4. Verify Audit Chain
    req4 = urllib.request.Request("http://127.0.0.1:5000/api/bank/verify-audit-chain")
    with urllib.request.urlopen(req4) as resp:
        print("\n=== C# AUDIT CHAIN VERIFY ===")
        print(json.loads(resp.read().decode()))

    # 5. Court Dossier
    req5 = urllib.request.Request("http://127.0.0.1:5000/api/bank/generate-dossier?firId=FIR-2026-104&role=LawEnforcement")
    with urllib.request.urlopen(req5) as resp:
        print("\n=== C# COURT-READY EVIDENCE DOSSIER ===")
        print(json.loads(resp.read().decode()))

if __name__ == "__main__":
    test()
