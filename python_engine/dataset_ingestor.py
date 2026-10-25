"""
PS-01: Intelligent Mule Account Detection & Fraud Investigation Platform
Dataset Ingestor for Hackathon Statements of Account (SOA Workbooks)
Parses real bank statements (.xlsx and .xls) from datasets/ folder
"""

import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def excel_date_to_datetime(val):
    if isinstance(val, (int, float)):
        # Excel serial date: 44921 -> datetime
        return datetime(1899, 12, 30) + timedelta(days=float(val))
    elif isinstance(val, str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                return datetime.strptime(val.strip(), fmt)
            except Exception:
                pass
    return datetime(2026, 1, 1)

def ingest_soa_folder(folder_path="datasets", max_files=10):
    files = [f for f in glob.glob(os.path.join(folder_path, "*.*")) if not os.path.basename(f).startswith("~$")]
    files = sorted(files)

    accounts = {}
    transactions = []
    
    print(f"Ingesting up to {max_files} SOA files from {folder_path}...")

    for fpath in files[:max_files]:
        fname = os.path.basename(fpath)
        try:
            # Read first 1000 rows per file for fast processing
            if fpath.endswith(".xlsx"):
                df = pd.read_excel(fpath, sheet_name=0, nrows=1000)
            elif fpath.endswith(".xls"):
                df = pd.read_excel(fpath, nrows=1000)
            else:
                continue

            # Standardize column names
            col_map = {c: str(c).strip() for c in df.columns}
            df.rename(columns=col_map, inplace=True)

            ac_col = next((c for c in df.columns if c.lower() in ["ac_no", "account_no", "acc_no"]), None)
            name_col = next((c for c in df.columns if c.lower() in ["ac_name", "account_name", "name"]), None)
            dr_col = next((c for c in df.columns if c.lower() in ["dr_amt", "debit", "dr"]), None)
            cr_col = next((c for c in df.columns if c.lower() in ["cr_amt", "credit", "cr"]), None)
            bal_col = next((c for c in df.columns if c.lower() in ["balance", "bal"]), None)
            date_col = next((c for c in df.columns if c.lower() in ["tran_date", "date", "tx_date"]), None)
            tx_id_col = next((c for c in df.columns if c.lower() in ["tran_id", "tx_id", "ref_no"]), None)
            narr_col = next((c for c in df.columns if c.lower() in ["narration", "remarks", "rmks"]), None)

            if not ac_col:
                continue

            for idx, row in df.iterrows():
                raw_ac = str(row[ac_col]).strip()
                if not raw_ac or raw_ac.lower() == "nan":
                    continue

                acc_id = f"ACC_{raw_ac}"
                holder = str(row.get(name_col, f"Customer {raw_ac[-4:]}")).strip()
                if holder.lower() == "nan": holder = f"Customer {raw_ac[-4:]}"

                dr = float(row.get(dr_col, 0) or 0)
                cr = float(row.get(cr_col, 0) or 0)
                bal = float(row.get(bal_col, 0) or 0)
                dt_raw = row.get(date_col)
                dt = excel_date_to_datetime(dt_raw)
                tx_id = str(row.get(tx_id_col, f"TX_{fname}_{idx}"))
                narr = str(row.get(narr_col, ""))

                # Index account
                if acc_id not in accounts:
                    accounts[acc_id] = {
                        "account_id": acc_id,
                        "raw_account_no": raw_ac,
                        "holder_name": holder,
                        "bank": "Bank of Baroda" if "bob" in fname.lower() else "Partner Bank",
                        "total_balance": bal,
                        "total_debits": 0.0,
                        "total_credits": 0.0,
                        "tx_count": 0,
                        "penny_drops": 0,
                        "source_file": fname
                    }

                accounts[acc_id]["total_balance"] = bal
                accounts[acc_id]["tx_count"] += 1
                if dr > 0: accounts[acc_id]["total_debits"] += dr
                if cr > 0: accounts[acc_id]["total_credits"] += cr
                if 0 < cr <= 10: accounts[acc_id]["penny_drops"] += 1

                # Record transaction
                amt = dr if dr > 0 else cr
                if amt > 0:
                    transactions.append({
                        "tx_id": tx_id,
                        "account_id": acc_id,
                        "amount": amt,
                        "is_debit": (dr > 0),
                        "timestamp": dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "balance_after": bal,
                        "narration": narr,
                        "source_file": fname
                    })

        except Exception as ex:
            print(f"Skipping {fname} due to: {ex}")

    print(f"Ingestion complete: {len(accounts)} accounts, {len(transactions)} transactions parsed.")
    return accounts, transactions

if __name__ == "__main__":
    accs, txs = ingest_soa_folder()
    print("Sample Account:", list(accs.values())[0] if accs else "None")
