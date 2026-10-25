import urllib.request
import json

def test():
    py_url = "http://127.0.0.1:8000/api/real-datasets/catalog"
    cs_url = "http://127.0.0.1:5000/api/bank/datasets"
    
    print("Testing Python /api/real-datasets/catalog...")
    try:
        with urllib.request.urlopen(py_url, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"SUCCESS: Python Catalog has {data.get('total_files')} files.")
            first = data.get('files', [])[0]
            print("File item keys:", list(first.keys()))
            print("First file:", first.get("file_name"), "Accounts count:", len(first.get("accounts", [])))
    except Exception as e:
        print("ERROR querying Python:", e)

    print("\nTesting C# /api/bank/datasets...")
    try:
        with urllib.request.urlopen(cs_url, timeout=3) as resp:
            data = json.loads(resp.read().decode())
            print(f"SUCCESS: C# Gateway Catalog has {data.get('total_files')} files.")
    except Exception as e:
        print("ERROR querying C#:", e)

if __name__ == "__main__":
    test()
