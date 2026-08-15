import requests
import json
import os
from dotenv import load_dotenv
from groq import Groq
from datetime import datetime, timedelta

load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_API_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SEVERITY_MAP = {
    "0": "Not classified", "1": "Information", "2": "Warning",
    "3": "Average", "4": "High", "5": "Disaster"
}

client = Groq(api_key=GROQ_API_KEY)


def get_problems_last_24h():
    """Pull all problems from the last 24 hours, active or already resolved."""
    time_from = int((datetime.now() - timedelta(hours=24)).timestamp())

    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {ZABBIX_TOKEN}"
    }
    payload = {
        "jsonrpc": "2.0",
        "method": "problem.get",
        "params": {
            "output": "extend",
            "time_from": time_from,
            "recent": True,
            "sortfield": ["eventid"],
            "sortorder": "DESC"
        },
        "id": 1
    }
    response = requests.post(ZABBIX_URL, headers=headers, json=payload)
    return response.json()["result"]


def get_host_name(triggerid):
    """Look up which host a trigger belongs to (same trick as explain_alert.py)."""
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
def build_summary_text(problems):
    """Turn the raw problem list into a readable block for the LLM prompt."""
    if not problems:
        return "No problems were recorded in the last 24 hours."

    lines = []
    for p in problems:
        severity_text = SEVERITY_MAP.get(p["severity"], "Unknown")
        host_name = get_host_name(p["objectid"])
        alert_time = datetime.fromtimestamp(int(p["clock"])).strftime("%Y-%m-%d %H:%M:%S")
        status = "RESOLVED" if p.get("r_eventid", "0") != "0" else "STILL ACTIVE"
        lines.append(f"- [{status}] Host: {host_name} | {p['name']} | Severity: {severity_text} | Time: {alert_time}")

    return "\n".join(lines)


def generate_daily_summary():
    problems = get_problems_last_24h()
    summary_text = build_summary_text(problems)

    print("--- Raw Problems (last 24h) ---")
    print(summary_text)
    print()

    prompt = f"""You are a monitoring assistant writing a daily summary report for a system engineer.

Here are all Zabbix problems from the last 24 hours:

{summary_text}

Write a concise daily summary report with:
1. Overall health snapshot (how many problems, how many still active vs resolved)
2. Which host(s) had the most issues, if any pattern stands out
3. The most severe or noteworthy problem(s) of the day
4. Any recommended follow-up actions

Keep it professional and concise, like something you'd paste into a report or send in a status update."""

    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )

    print("--- Daily Summary ---")
    print(response.choices[0].message.content)


if __name__ == "__main__":
    generate_daily_summary()
