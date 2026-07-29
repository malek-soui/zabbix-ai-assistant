"""
Alert Correlation Module
Finds relationships between alerts that occur around the same time on the same host.
"""

import requests
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from groq import Groq

load_dotenv()

ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_API_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SEVERITY_MAP = {
    "0": "Not classified", "1": "Information", "2": "Warning",
    "3": "Average", "4": "High", "5": "Disaster"
}

client = Groq(api_key=GROQ_API_KEY)


def get_zabbix_problems():
    """Fetch active problems from Zabbix."""
    headers = {
        "Content-Type": "application/json-rpc",
        "Authorization": f"Bearer {ZABBIX_TOKEN}"
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
    return response.json().get("result", [])


def get_host_name(triggerid):
    """Get host name for a trigger."""
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


def enrich_alert(alert):
    """Add host_name and formatted time to an alert."""
    alert["host_name"] = get_host_name(alert["objectid"])
    alert["time_str"] = datetime.fromtimestamp(int(alert["clock"])).strftime("%H:%M:%S")
    alert["severity_text"] = SEVERITY_MAP.get(alert["severity"], "Unknown")
    alert["timestamp"] = int(alert["clock"])
    return alert


def find_correlated_alerts(alerts, time_window_seconds=300):
    """
    Group alerts by host and time window.
    
    Args:
        alerts: List of enriched alert dicts
        time_window_seconds: Alerts within this many seconds are considered correlated
    
    Returns:
        List of correlation groups, each containing:
        - host: The host name
        - time: The time window start
        - alerts: List of alerts in this group
        - severity: Highest severity in the group
    """
    # Only consider alerts that are still active
    active_alerts = [a for a in alerts if a.get("r_eventid", "0") == "0"]
    
    if not active_alerts:
        return []
    
    # Group by host
    by_host = defaultdict(list)
    for alert in active_alerts:
        by_host[alert["host_name"]].append(alert)
    
    correlations = []
    
    for host, host_alerts in by_host.items():
        # Sort alerts by time
        host_alerts.sort(key=lambda x: x["timestamp"])
        
        # Group alerts within the time window
        groups = []
        current_group = [host_alerts[0]]
        
        for alert in host_alerts[1:]:
            # If this alert is within the time window of the first alert in the group
            if alert["timestamp"] - current_group[0]["timestamp"] <= time_window_seconds:
                current_group.append(alert)
            else:
                # Start a new group
                if len(current_group) > 1:  # Only keep groups with 2+ alerts
                    groups.append(current_group)
                current_group = [alert]
        
        # Don't forget the last group
        if len(current_group) > 1:
            groups.append(current_group)
        
        for group in groups:
            # Determine highest severity in the group
            severity_nums = [int(a["severity"]) for a in group]
            max_severity = max(severity_nums)
            
            correlations.append({
                "host": host,
                "time_start": group[0]["time_str"],
                "time_end": group[-1]["time_str"],
                "alert_count": len(group),
                "alerts": group,
                "severity_text": SEVERITY_MAP.get(str(max_severity), "Unknown"),
                "severity_num": max_severity
            })
    
    # Sort correlations by severity (highest first)
    correlations.sort(key=lambda x: x["severity_num"], reverse=True)
    
    return correlations


def generate_correlation_explanation(correlation):
    """Generate an AI explanation for a correlated group of alerts."""
    
    # Build a description of the group
    alerts_text = []
    for a in correlation["alerts"]:
        alerts_text.append(f"- {a['time_str']}: {a['name']} (Severity: {a['severity_text']})")
    
    alerts_bullets = "\n".join(alerts_text)
    
    prompt = f"""
You are a monitoring assistant analyzing a group of correlated alerts on the same host.

**Host:** {correlation['host']}
**Time window:** {correlation['time_start']} to {correlation['time_end']}
**Number of alerts:** {correlation['alert_count']}
**Highest severity:** {correlation['severity_text']}

**Alerts in this group:**
{alerts_bullets}

These alerts occurred around the same time on the same host. They may be related to a single underlying issue.

Analyze this group and provide:
1. **Likely root cause**: What single problem might explain this pattern of alerts?
2. **Relationship between alerts**: How are these alerts connected? Which one might have triggered the others?
3. **Recommended actions**: What should an engineer check or fix first?

Be concise and practical — focus on actionable insights.
"""
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}]
    )
    
    return response.choices[0].message.content


def get_all_correlations():
    """Main function: fetch alerts, find correlations, generate explanations."""
    problems = get_zabbix_problems()
    
    # Enrich each alert with host info
    enriched = [enrich_alert(p) for p in problems]
    
    # Find correlated groups
    correlations = find_correlated_alerts(enriched)
    
    # Generate explanations for each correlation
    for c in correlations:
        c["explanation"] = generate_correlation_explanation(c)
    
    return correlations


# --- For testing directly ---
if __name__ == "__main__":
    correlations = get_all_correlations()
    
    if not correlations:
        print("No correlated alert groups found.")
    else:
        print(f"Found {len(correlations)} correlation groups.\n")
        
        for i, c in enumerate(correlations, 1):
            print(f"--- Correlation #{i}: {c['host']} ({c['alert_count']} alerts) ---")
            print(f"Time: {c['time_start']} - {c['time_end']}")
            print(f"Severity: {c['severity_text']}")
            print()
            print(c["explanation"])
            print("\n" + "-"*60 + "\n")