# 🚀 Zabbix AI Monitoring Assistant

> An intelligent monitoring assistant that combines **Zabbix** with **AI-powered alert analysis** using RAG (Retrieval-Augmented Generation).

---

## 📌 Overview

This project was developed during an internship to enhance infrastructure monitoring by adding an AI layer that explains alerts, correlates incidents, and generates daily reports.

The system connects to the Zabbix API, retrieves active alerts, enriches them with historical context from a vector database, and uses an LLM to provide **actionable, human-readable explanations**.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔍 **Alert Explanation** | Get AI-generated explanations of Zabbix alerts with possible causes and recommended actions |
| 🔗 **Alert Correlation** | Automatically detect related alerts on the same host within a time window |
| 📊 **Daily Summary** | Generate professional daily reports summarizing all problems from the last 24 hours |
| 💬 **Conversational Assistant** | Ask natural language questions about your infrastructure |
| 🌍 **Multilingual** | Full support for **French** and **English** — switch with one click |
| 📡 **Real-time Alerts** | Sidebar shows live Zabbix alerts with severity color coding |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  Zabbix API ──► Python (RAG) ──► Groq LLM ──► Streamlit UI │
│                     │                                       │
│                     ▼                                       │
│              Chroma Vector DB                              │
│         (Similar Past Incidents)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
📂 zabbix-ai-assistant/
├── 📄 app.py                    # Streamlit web interface
├── 📄 explain_alert.py          # Single alert explanation
├── 📄 daily_summary.py          # Daily summary report
├── 📄 alert_correlation.py      # Alert correlation engine
├── 📄 build_vectorstore.py      # Build Chroma vector database
├── 📄 incidents.py              # Fake incident knowledge base
├── 📄 vm_discovery.ps1          # PowerShell script for Hyper-V VM discovery
├── 📄 zbx_export_templates.yaml # Zabbix template export (ready to import)
├── 📄 requirements.txt          # Python dependencies
├── 📄 .gitignore                # Ignore secrets
└── 📄 README.md                 # Project documentation
```

---

## 🚀 Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/malek-soui/zabbix-ai-assistant.git
cd zabbix-ai-assistant
```

### 2. Create a `.env` file with your credentials

```
ZABBIX_URL=http://localhost/api_jsonrpc.php
ZABBIX_API_TOKEN=your_zabbix_api_token
GROQ_API_KEY=your_groq_api_key
```

> **Note:** If your Zabbix server is running on a different host, replace `localhost` with the appropriate IP or hostname.

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Build the vector store

```bash
python build_vectorstore.py
```

### 5. Run the application

```bash
streamlit run app.py
```

The app will open automatically at [http://localhost:8501](http://localhost:8501)

---

## 📋 Prerequisites

| Requirement | Details |
|-------------|---------|
| **Zabbix** | Version 7.4+ with API access enabled |
| **Groq API** | Free tier available at [groq.com](https://groq.com) |
| **Python** | Version 3.10 or higher |
| **Docker** | For running the Zabbix containers (optional) |

---

## 🛠️ Technologies Used

| Technology | Purpose |
|------------|---------|
| 🐍 **Python** | Core programming language |
| 📊 **Zabbix** | Monitoring infrastructure and data source |
| 🤖 **Groq LLM** | AI model for generating explanations |
| 📚 **Chroma DB** | Vector database for RAG (similar past incidents) |
| 🎨 **Streamlit** | Web interface framework |
| 🔧 **PowerShell** | Hyper-V VM discovery script |

---

## 📬 Contact

**Malek Soui**  
[LinkedIn]([[https://www.linkedin.com/in/malek-soui-88b8a9388/]) 

---

## ⭐ Show Your Support

If you found this project useful, give it a ⭐ on GitHub!
