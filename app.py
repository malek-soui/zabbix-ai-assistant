import streamlit as st
import requests
import json
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from groq import Groq
import chromadb
from alert_correlation import get_all_correlations

load_dotenv()

# --- Configuration ---
ZABBIX_URL = os.getenv("ZABBIX_URL")
ZABBIX_TOKEN = os.getenv("ZABBIX_API_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

SEVERITY_MAP = {
    "0": "Not classified", "1": "Information", "2": "Warning",
    "3": "Average", "4": "High", "5": "Disaster"
}

SEVERITY_ICONS = {
    "Disaster": "🔴",
    "High": "🟠",
    "Average": "🟡",
    "Warning": "🔵",
    "Information": "🟢",
    "Not classified": "⚪"
}

# --- Language support ---
LANGUAGES = {
    "en": {
        "title": "🤖 AI Monitoring Assistant",
        "subtitle": "💬 Chat with your monitoring assistant",
        "sidebar_title": "📡 Active Alerts",
        "no_alerts": "✅ No active problems",
        "active_problems": "active problems",
        "clear_chat": "🗑️ Clear Chat",
        "daily_summary": "📊 Generate Daily Summary",
        "correlate": "🔗 Find Correlated Alerts",
        "chat_placeholder": "Ask about your infrastructure (e.g., 'What's the status of HV-HOST-01?')",
        "explain": "Explain this alert",
        "on": "on",
        "no_correlation": "No correlated alert groups found. All active alerts appear to be isolated issues.",
        "correlation_detected": "🔗 Correlation detected on",
        "time": "Time",
        "number_of_alerts": "Number of alerts",
        "highest_severity": "Highest severity",
        "alerts_in_group": "Alerts in this group",
        "analysis": "Analysis",
        "generating": "Generating explanation...",
        "thinking": "Thinking...",
        "analyzing": "Analyzing alert patterns...",
        "daily_summary_spinner": "Generating daily summary...",
        "footer": "Powered by Zabbix · Streamlit · Groq LLM · Chroma RAG",
        "switch_lang": "🌐 Switch to French",
        "no_problems_24h": "No problems recorded in the last 24 hours.",
        "stats_clear": "✅ All Clear",
        "stats_problems": "problems"
    },
    "fr": {
        "title": "🤖 Assistant de Supervision IA",
        "subtitle": "💬 Discutez avec votre assistant de supervision",
        "sidebar_title": "📡 Alertes Actives",
        "no_alerts": "✅ Aucun problème actif",
        "active_problems": "problèmes actifs",
        "clear_chat": "🗑️ Effacer la discussion",
        "daily_summary": "📊 Générer le résumé quotidien",
        "correlate": "🔗 Trouver des alertes corrélées",
        "chat_placeholder": "Posez une question sur votre infrastructure (ex: 'Quel est le statut de HV-HOST-01?')",
        "explain": "Expliquer cette alerte",
        "on": "sur",
        "no_correlation": "Aucun groupe d'alertes corrélées trouvé. Toutes les alertes actives semblent être des problèmes isolés.",
        "correlation_detected": "🔗 Corrélation détectée sur",
        "time": "Heure",
        "number_of_alerts": "Nombre d'alertes",
        "highest_severity": "Sévérité maximale",
        "alerts_in_group": "Alertes dans ce groupe",
        "analysis": "Analyse",
        "generating": "Génération de l'explication...",
        "thinking": "Réflexion en cours...",
        "analyzing": "Analyse des modèles d'alertes...",
        "daily_summary_spinner": "Génération du résumé quotidien...",
        "footer": "Propulsé par Zabbix · Streamlit · Groq LLM · Chroma RAG",
        "switch_lang": "🌐 Passer en Anglais",
        "no_problems_24h": "Aucun problème enregistré au cours des dernières 24 heures.",
        "stats_clear": "✅ Tout est clair",
        "stats_problems": "problèmes"
    }
}

# --- Initialize clients ---
groq_client = Groq(api_key=GROQ_API_KEY)
chroma_client = chromadb.PersistentClient(path="./chroma_db")
incident_collection = chroma_client.get_or_create_collection(name="incidents")

# --- Helper functions ---

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

def get_similar_incidents(alert_text, n=2):
    """Retrieve similar past incidents from Chroma vector store."""
    results = incident_collection.query(
        query_texts=[alert_text],
        n_results=n
    )
    return results["documents"][0] if results["documents"] else []

def explain_alert(alert, lang="en"):
    """Generate AI explanation for an alert using RAG."""
    severity_text = SEVERITY_MAP.get(alert["severity"], "Unknown")
    host_name = get_host_name(alert["objectid"])
    alert_time = datetime.fromtimestamp(int(alert["clock"])).strftime("%Y-%m-%d %H:%M:%S")
    
    # Retrieve similar past incidents
    similar_incidents = get_similar_incidents(alert['name'])
    incidents_text = "\n".join(f"- {inc}" for inc in similar_incidents) if similar_incidents else "No similar past incidents found."
    
    # Prompts in English and French
    prompts = {
        "en": f"""You are a monitoring assistant helping a system engineer understand an alert.

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

Keep it concise and practical.""",
        
        "fr": f"""Vous êtes un assistant de supervision aidant un ingénieur système à comprendre une alerte.

Hôte: {host_name}
Alerte: {alert['name']}
Sévérité: {severity_text}
Heure: {alert_time}

Incidents passés similaires dans l'historique:
{incidents_text}

En utilisant les détails de l'alerte et les incidents passés similaires pertinents, fournissez:
1. Une explication simple de ce que signifie cette alerte
2. Les causes possibles (référencez les incidents passés similaires si pertinent)
3. Les premières étapes recommandées à vérifier

Restez concis et pratique."""
    }
    
    prompt = prompts.get(lang, prompts["en"])
    
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def get_daily_summary(lang="en"):
    """Generate a daily summary report."""
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
    problems = response.json().get("result", [])
    
    text = LANGUAGES[lang]
    
    if not problems:
        return text["no_problems_24h"]
    
    lines = []
    for p in problems:
        severity_text = SEVERITY_MAP.get(p["severity"], "Unknown")
        host_name = get_host_name(p["objectid"])
        alert_time = datetime.fromtimestamp(int(p["clock"])).strftime("%Y-%m-%d %H:%M:%S")
        status = "RESOLVED" if p.get("r_eventid", "0") != "0" else "STILL ACTIVE"
        lines.append(f"- [{status}] Host: {host_name} | {p['name']} | Severity: {severity_text} | Time: {alert_time}")
    
    summary_text = "\n".join(lines)
    
    # Prompts in English and French
    prompts = {
        "en": f"""You are a monitoring assistant writing a daily summary report for a system engineer.

Here are all Zabbix problems from the last 24 hours:

{summary_text}

Write a concise daily summary report with:
1. Overall health snapshot (how many problems, how many still active vs resolved)
2. Which host(s) had the most issues, if any pattern stands out
3. The most severe or noteworthy problem(s) of the day
4. Any recommended follow-up actions

Keep it professional and concise.""",
        
        "fr": f"""Vous êtes un assistant de supervision rédigeant un rapport de résumé quotidien pour un ingénieur système.

Voici tous les problèmes Zabbix des dernières 24 heures:

{summary_text}

Rédigez un rapport de résumé quotidien concis avec:
1. Un aperçu global de la santé (combien de problèmes, combien sont encore actifs vs résolus)
2. Quel(s) hôte(s) ont eu le plus de problèmes, si un motif se dégage
3. Le(s) problème(s) le(s) plus grave(s) ou notable(s) de la journée
4. Toute action de suivi recommandée

Restez professionnel et concis."""
    }
    
    prompt = prompts.get(lang, prompts["en"])
    
    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

# --- Streamlit UI ---

st.set_page_config(page_title="AI Monitoring Assistant", layout="wide")

# Initialize language
if "lang" not in st.session_state:
    st.session_state.lang = "en"

lang = LANGUAGES[st.session_state.lang]

st.title(lang["title"])

# --- Stats Bar ---
problems = get_zabbix_problems()
severity_counts = {}
for p in problems:
    sev = SEVERITY_MAP.get(p["severity"], "Unknown")
    severity_counts[sev] = severity_counts.get(sev, 0) + 1

# Display stats in a row
cols = st.columns(len(severity_counts) if severity_counts else 1)
if severity_counts:
    for i, (sev, count) in enumerate(severity_counts.items()):
        cols[i].metric(f"{SEVERITY_ICONS.get(sev, '')} {sev}", count)
else:
    cols[0].metric(lang["stats_clear"], f"0 {lang['stats_problems']}")
st.divider()

# Sidebar - Active Alerts
with st.sidebar:
    # Language switcher
    if st.button(lang["switch_lang"], use_container_width=True):
        st.session_state.lang = "fr" if st.session_state.lang == "en" else "en"
        st.rerun()
    st.divider()
    
    st.header(lang["sidebar_title"])
    
    problems = get_zabbix_problems()
    
    if not problems:
        st.info(lang["no_alerts"])
    else:
        st.write(f"**{len(problems)} {lang['active_problems']}**")
        
        for p in problems:
            severity = SEVERITY_MAP.get(p["severity"], "Unknown")
            color = "🔴" if severity == "Disaster" else "🟠" if severity == "High" else "🟡" if severity == "Average" else "🔵" if severity == "Warning" else "🟢"
            
            host = get_host_name(p["objectid"])
            
            # Button for each alert - clicking it explains the alert
            label = f"{color} {host}: {p['name'][:50]}..."
            if st.button(label, key=p["eventid"], use_container_width=True):
                st.session_state.selected_alert = p
                st.session_state.chat_history.append({
                    "role": "user",
                    "content": f"{lang['explain']}: {p['name']} {lang['on']} {host}"
                })
                # Generate explanation
                with st.spinner(lang["generating"]):
                    explanation = explain_alert(p, st.session_state.lang)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": explanation
                    })
    
    st.divider()
    
    if st.button(lang["clear_chat"], use_container_width=True):
        st.session_state.chat_history = []
        st.rerun()
    
    st.divider()
    
    if st.button(lang["daily_summary"], use_container_width=True):
        with st.spinner(lang["daily_summary_spinner"]):
            summary = get_daily_summary(st.session_state.lang)
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": f"**{lang['daily_summary']}**\n\n{summary}"
            })
    
    st.divider()
    
    if st.button(lang["correlate"], use_container_width=True):
        with st.spinner(lang["analyzing"]):
            correlations = get_all_correlations()
            if not correlations:
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": lang["no_correlation"]
                })
            else:
                for c in correlations:
                    # Format the correlation group
                    alerts_summary = "\n".join([f"- {a['time_str']}: {a['name']}" for a in c['alerts']])
                    content = f"""**{lang['correlation_detected']} {c['host']}**
                    
**{lang['time']}:** {c['time_start']} - {c['time_end']}
**{lang['number_of_alerts']}:** {c['alert_count']}
**{lang['highest_severity']}:** {c['severity_text']}

**{lang['alerts_in_group']}:**
{alerts_summary}

**{lang['analysis']}:**
{c['explanation']}

---
"""
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": content
                    })

# Main Chat Area
st.subheader(lang["subtitle"])

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
    st.session_state.selected_alert = None

# Display chat history
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Chat input
if prompt := st.chat_input(lang["chat_placeholder"]):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    
    with st.chat_message("user"):
        st.markdown(prompt)
    
    with st.chat_message("assistant"):
        with st.spinner(lang["thinking"]):
            # System prompt in the selected language
            system_prompts = {
                "en": "You are a monitoring assistant helping with Zabbix infrastructure. You have access to real-time alert data. Answer questions based on the user's query.",
                "fr": "Vous êtes un assistant de supervision aidant avec l'infrastructure Zabbix. Vous avez accès aux données d'alertes en temps réel. Répondez aux questions en fonction de la requête de l'utilisateur."
            }
            system_prompt = system_prompts.get(st.session_state.lang, system_prompts["en"])
            
            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-120b",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response.choices[0].message.content
            st.markdown(answer)
            st.session_state.chat_history.append({"role": "assistant", "content": answer})

# --- Footer ---
st.divider()
st.caption(lang["footer"])