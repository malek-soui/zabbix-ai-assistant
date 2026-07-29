import requests
import json
from dotenv import load_dotenv
import os

load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
API_TOKEN = os.getenv("ZABBIX_API_TOKEN")

headers = {
    "Content-Type": "application/json-rpc",
    "Authorization": f"Bearer {API_TOKEN}"
}

payload = {
    "jsonrpc": "2.0",
    "method": "problem.get",
    "params": {
        "output": "extend",
        "sortfield": ["eventid"],
        "sortorder": "DESC"
    },
    "id": 1
}

response = requests.post(ZABBIX_URL, headers=headers, json=payload)
problems = response.json()["result"]

for p in problems:
    print(f"Event ID: {p['eventid']} | Name: {p['name']} | Severity: {p['severity']}")