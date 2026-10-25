"""
PS-01: Intelligent Mule Account Detection & Fraud Investigation Platform
Python Data Science & Synthetic Fraud Generator
Modeled on IBM AML & PaySim banking benchmarks.
"""

import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

def generate_synthetic_banking_data(seed=42):
    random.seed(seed)
    np.random.seed(seed)

    banks = ["SBI", "HDFC", "ICICI", "Axis", "PNB", "Kotak", "Bank of Baroda"]
    
    # Base timestamp: 2026-10-25 10:00:00
    base_time = datetime(2026, 10, 25, 10, 0, 0)
    
    accounts = {}
    transactions = []
    complaints = []

    # 1. Generate 150 normal accounts (merchants, salaried individuals, retail savers)
    for i in range(1, 151):
        acc_id = f"ACC_NORM_{i:04d}"
        is_merchant = (i <= 20)
        kyc_days = random.randint(300, 2500) if is_merchant else random.randint(120, 1800)
        bank = random.choice(banks)
        device = f"DEV_NORM_{i:04d}"
        ip = f"192.168.1.{10 + (i % 200)}"
        total_bal = random.randint(50000, 1500000) if is_merchant else random.randint(5000, 200000)

        accounts[acc_id] = {
            "account_id": acc_id,
            "holder_name": f"Retail Client {i}" if not is_merchant else f"Merchant Outlet {i}",
            "bank": bank,
            "kyc_days": kyc_days,
            "device_id": device,
            "ip_address": ip,
            "total_balance": total_bal,
            "is_merchant": is_merchant,
            "account_type": "legitimate",
            "is_mule": False,
            "penny_drops": 0,
            "phone": f"+91-98{random.randint(10000000, 99999999)}",
            "pan": f"ABCDE{random.randint(1000, 9999)}Z"
        }

    # 2. Add Key Named Entities from Hackathon Blueprint
    # Victim 1: Ramesh Kumar (Victim of FIR-2026-104)
    accounts["ACC_VICTIM_01"] = {
        "account_id": "ACC_VICTIM_01",
        "holder_name": "Ramesh Kumar (Victim)",
        "bank": "SBI",
        "kyc_days": 1420,
        "device_id": "DEV_VICTIM_01",
        "ip_address": "10.0.1.15",
        "total_balance": 12500,
        "is_merchant": False,
        "account_type": "victim",
        "is_mule": False,
        "penny_drops": 0,
        "phone": "+91-9811223344",
        "pan": "BPLPK1234F"
    }

    # Honest Merchant: FreshMart Supermarket (Stress Test comparison)
    accounts["ACC_MERCHANT_OK"] = {
        "account_id": "ACC_MERCHANT_OK",
        "holder_name": "FreshMart Supermarket (Honest Merchant)",
        "bank": "SBI",
        "kyc_days": 2190,
        "device_id": "DEV_POS_FRESHMART",
        "ip_address": "10.10.4.55",
        "total_balance": 540000,
        "is_merchant": True,
        "account_type": "merchant",
        "is_mule": False,
        "penny_drops": 0,
        "phone": "+91-9877665544",
        "pan": "AAFCM9988K"
    }

    # Ring 1 & 2: Smurfing + 4-Hop Rapid Layering Mule Network
    # Layer 1 Mule: Sohan Lal (Rented Student Account)
    accounts["ACC_MULE_L1"] = {
        "account_id": "ACC_MULE_L1",
        "holder_name": "Sohan Lal (Rented Student Mule)",
        "bank": "HDFC",
        "kyc_days": 45,
        "device_id": "DEV_HERDER_99",  # Shared device
        "ip_address": "198.51.100.22",
        "total_balance": 104500,
        "is_merchant": False,
        "account_type": "mule",
        "is_mule": True,
        "penny_drops": 0,
        "phone": "+91-9812345678",
        "pan": "CPZPL5678M"
    }

    # Smurf Intermediate 1: Karan Verma
    accounts["ACC_SMURF_A"] = {
        "account_id": "ACC_SMURF_A",
        "holder_name": "Karan Verma (Smurf Mule A)",
        "bank": "ICICI",
        "kyc_days": 30,
        "device_id": "DEV_HERDER_99",  # Shared device
        "ip_address": "198.51.100.22",
        "total_balance": 11200,
        "is_merchant": False,
        "account_type": "mule",
        "is_mule": True,
        "penny_drops": 0,
        "phone": "+91-9823456789",
        "pan": "DKLPM6789N"
    }

    # Smurf Intermediate 2: Pooja Das
    accounts["ACC_SMURF_B"] = {
        "account_id": "ACC_SMURF_B",
        "holder_name": "Pooja Das (Smurf Mule B)",
        "bank": "Axis",
        "kyc_days": 22,
        "device_id": "DEV_HERDER_99",  # Shared device
        "ip_address": "198.51.100.22",
        "total_balance": 9800,
        "is_merchant": False,
        "account_type": "mule",
        "is_mule": True,
        "penny_drops": 0,
        "phone": "+91-9834567890",
        "pan": "EJMPN7890P"
    }

    # Smurf Intermediate 3: Vikram Singh
    accounts["ACC_SMURF_C"] = {
        "account_id": "ACC_SMURF_C",
        "holder_name": "Vikram Singh (Smurf Mule C)",
        "bank": "PNB",
        "kyc_days": 19,
        "device_id": "DEV_HERDER_99",  # Shared device
        "ip_address": "198.51.100.22",
        "total_balance": 10100,
        "is_merchant": False,
        "account_type": "mule",
        "is_mule": True,
        "penny_drops": 0,
        "phone": "+91-9845678901",
        "pan": "FKNPO8901Q"
    }

    # Aggregator Cashout Boss: Apex Crypto / Cashout Boss
    accounts["ACC_BOSS_AGG"] = {
        "account_id": "ACC_BOSS_AGG",
        "holder_name": "Apex Crypto / Cashout Boss",
        "bank": "Kotak",
        "kyc_days": 14,
        "device_id": "DEV_HERDER_BOSS_77",
        "ip_address": "198.51.100.99",
        "total_balance": 92000,
        "is_merchant": False,
        "account_type": "mule_boss",
        "is_mule": True,
        "penny_drops": 0,
        "phone": "+91-9856789012",
        "pan": "GLOQP9012R"
    }

    # Ring 3: Sleeper Mule Pre-Crime Staging
    # Neha Sharma (Dormant account suddenly receiving test transfers)
    accounts["ACC_SLEEPER_99"] = {
        "account_id": "ACC_SLEEPER_99",
        "holder_name": "Neha Sharma (Sleeper Mule)",
        "bank": "Bank of Baroda",
        "kyc_days": 180,
        "device_id": "DEV_HERDER_99",  # Shared with herder!
        "ip_address": "198.51.100.22",
        "total_balance": 9,
        "is_merchant": False,
        "account_type": "sleeper_mule",
        "is_mule": True,
        "penny_drops": 8,
        "phone": "+91-9899887766",
        "pan": "HMSPQ0123S"
    }

    # Generate 500 normal background transactions between legitimate accounts
    acc_keys = [k for k in accounts.keys() if k.startswith("ACC_NORM_")]
    for t_idx in range(1, 501):
        u = random.choice(acc_keys)
        v = random.choice([k for k in acc_keys if k != u])
        amt = random.randint(200, 15000)
        t_delta = timedelta(minutes=random.randint(5, 720))
        tx_time = base_time + t_delta
        transactions.append({
            "tx_id": f"TX_NORM_{t_idx:05d}",
            "from_account": u,
            "to_account": v,
            "amount": amt,
            "timestamp": tx_time.strftime("%Y-%m-%d %H:%M:%S"),
            "channel": random.choice(["UPI", "IMPS", "NEFT"]),
            "is_fraud": False,
            "ring": "normal"
        })

    # Normal transactions for FreshMart Supermarket (120 genuine transactions over the day)
    for fm_idx in range(1, 41):
        cust = random.choice(acc_keys)
        amt = random.randint(150, 3500)
        t_delta = timedelta(minutes=random.randint(10, 600))
        transactions.append({
            "tx_id": f"TX_FM_{fm_idx:04d}",
            "from_account": cust,
            "to_account": "ACC_MERCHANT_OK",
            "amount": amt,
            "timestamp": (base_time + t_delta).strftime("%Y-%m-%d %H:%M:%S"),
            "channel": "UPI",
            "is_fraud": False,
            "ring": "merchant_normal"
        })

    # Fraud Scenario 1: Placement (Initial victim theft)
    t0 = base_time + timedelta(hours=1)
    transactions.append({
        "tx_id": "TX_FRAUD_001",
        "from_account": "ACC_VICTIM_01",
        "to_account": "ACC_MULE_L1",
        "amount": 100000,
        "timestamp": t0.strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "UPI",
        "is_fraud": True,
        "ring": "smurfing_layering"
    })

    # Fraud Scenario 2: Smurfing Layering (10x split transfers to dodge ₹50k rule in 35-70 seconds)
    t_mule_out_1 = t0 + timedelta(seconds=35)
    t_mule_out_2 = t0 + timedelta(seconds=50)
    t_mule_out_3 = t0 + timedelta(seconds=68)

    transactions.append({
        "tx_id": "TX_FRAUD_002",
        "from_account": "ACC_MULE_L1",
        "to_account": "ACC_SMURF_A",
        "amount": 9500,
        "timestamp": t_mule_out_1.strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "IMPS",
        "is_fraud": True,
        "ring": "smurfing_layering"
    })
    transactions.append({
        "tx_id": "TX_FRAUD_003",
        "from_account": "ACC_MULE_L1",
        "to_account": "ACC_SMURF_B",
        "amount": 9500,
        "timestamp": t_mule_out_2.strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "IMPS",
        "is_fraud": True,
        "ring": "smurfing_layering"
    })
    transactions.append({
        "tx_id": "TX_FRAUD_004",
        "from_account": "ACC_MULE_L1",
        "to_account": "ACC_SMURF_C",
        "amount": 9500,
        "timestamp": t_mule_out_3.strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "IMPS",
        "is_fraud": True,
        "ring": "smurfing_layering"
    })

    # Fraud Scenario 3: Aggregator Cashout Convergence (105-120 seconds)
    t_agg_1 = t0 + timedelta(seconds=105)
    t_agg_2 = t0 + timedelta(seconds=120)
    transactions.append({
        "tx_id": "TX_FRAUD_005",
        "from_account": "ACC_SMURF_A",
        "to_account": "ACC_BOSS_AGG",
        "amount": 9400,
        "timestamp": t_agg_1.strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "IMPS",
        "is_fraud": True,
        "ring": "smurfing_layering"
    })
    transactions.append({
        "tx_id": "TX_FRAUD_006",
        "from_account": "ACC_SMURF_B",
        "to_account": "ACC_BOSS_AGG",
        "amount": 9400,
        "timestamp": t_agg_2.strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "IMPS",
        "is_fraud": True,
        "ring": "smurfing_layering"
    })

    # Smurf C buys groceries at FreshMart (Honest merchant receives scammed money)
    t_merchant = t0 + timedelta(seconds=140)
    transactions.append({
        "tx_id": "TX_FRAUD_007",
        "from_account": "ACC_SMURF_C",
        "to_account": "ACC_MERCHANT_OK",
        "amount": 9500,
        "timestamp": t_merchant.strftime("%Y-%m-%d %H:%M:%S"),
        "channel": "UPI",
        "is_fraud": True,
        "ring": "merchant_touch"
    })

    # Fraud Scenario 4: Sleeper Mule Penny Drops (₹1 micro-transfers to verify active state)
    for p_idx in range(1, 9):
        p_time = base_time + timedelta(hours=2, minutes=p_idx * 3)
        transactions.append({
            "tx_id": f"TX_PENNY_{p_idx:03d}",
            "from_account": "ACC_SMURF_A",
            "to_account": "ACC_SLEEPER_99",
            "amount": 1,
            "timestamp": p_time.strftime("%Y-%m-%d %H:%M:%S"),
            "channel": "UPI",
            "is_fraud": True,
            "ring": "penny_drop"
        })

    # Police Complaints / FIRs
    complaints.append({
        "fir_id": "FIR-2026-104",
        "victim_account": "ACC_VICTIM_01",
        "reported_time": (t0 + timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S"),
        "stolen_amount": 100000,
        "description": "UPI extortion / Phishing call by impersonating electricity board"
    })

    complaints.append({
        "fir_id": "FIR-2026-108",
        "victim_account": "ACC_NORM_0012",
        "reported_time": (t0 + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M:%S"),
        "stolen_amount": 75000,
        "description": "Digital arrest scam involving impersonation of law enforcement"
    })

    return accounts, transactions, complaints

if __name__ == "__main__":
    accs, txs, cmps = generate_synthetic_banking_data()
    print(f"Generated {len(accs)} accounts, {len(txs)} transactions, {len(cmps)} complaints.")
