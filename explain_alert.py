import requests
import json
import os
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime
import chromadb

load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_API_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SEVERITY_MAP = {
    "0": "Not classified", "1": "Information", "2": "Warning",
    "3": "Average", "4": "High", "5": "Disaster"
}

client = Groq(api_key=GROQ_API_KEY)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
incident_collection = chroma_client.get_or_create_collection(name="incidents")


def get_similar_incidents(alert_text, n=2):
    results = incident_collection.query(
        query_texts=[alert_text],
        n_results=n
    )
    return results["documents"][0]


def get_zabbix_problems():
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {ZABBIX_TOKEN}"
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": "extend",
            "selectAcknowledges": "extend",
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        },
        "id": 1
    }
    response = requests.post(ZABBIX_URL, headers=headers, json=payload)
    return response.json()["result"]


def get_host_name(triggerid):
    """Look up which host a trigger belongs to."""
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {ZABBIX_TOKEN}"
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "trigger.get",
        "params": {
            "triggerids": [triggerid],
            "selectHosts": ["host"]
        },
        "id": 1
    }
    response = requests.post(ZABBIX_URL, headers=headers, json=payload)
    result = response.json().get("result", [])
    if result and result[0].get("hosts"):
        return result[0]["hosts"][0]["host"]
    return "Unknown host"


def explain_alert(alert):
    severity_text = SEVERITY_MAP.get(alert["severity"], "Unknown")
    host_name = get_host_name(alert["objectid"])
    alert_time = datetime.fromtimestamp(int(alert["clock"])).strftime("%Y-%m-%d %H:%M:%S")

    print("--- Raw Alert ---")
    print(f"Host: {host_name}")
    print(f"Name: {alert['name']}")
    print(f"Severity: {severity_text}")
    print(f"Time: {alert_time}")
    print()

    similar_incidents = get_similar_incidents(alert['name'])
    incidents_text = "\n".join(f"- {inc}" for inc in similar_incidents)

    print("--- Similar Past Incidents (retrieved) ---")
    print(incidents_text)
    print()

    prompt = f"""You are a monitoring assistant helping a system engineer understand an infrastructure alert.

Host: {host_name}
Alert: {alert['name']}
Severity: {severity_text}
Time: {alert_time}

Similar past incidents from history:
{incidents_text}

Using the alert details and any relevant similar past incidents, provide:
1. A simple explanation of what this alert means
2. Possible causes (reference similar past incidents if relevant)
3. Recommended first steps to check

Keep it concise and practical."""
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    print("--- AI Explanation ---")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    problems = get_zabbix_problems()

    if not problems:
        print("No active problems found.")
        exit()

    # Try to find the "Test High CPU Alert" specifically, otherwise use the most recent
    target = next((p for p in problems if "CPU" in p["name"]), problems[0])
    explain_alert(target)