markdown

\# Zabbix AI Monitoring Assistant



An intelligent monitoring assistant that combines Zabbix with AI-powered alert analysis using RAG (Retrieval-Augmented Generation).



\## Features



\- \*\*Alert Explanation\*\* — Get AI-generated explanations of Zabbix alerts

\- \*\*Alert Correlation\*\* — Find related alerts on the same host

\- \*\*Daily Summary\*\* — Generate professional daily reports

\- \*\*Conversational Assistant\*\* — Chat with an AI about your infrastructure

\- \*\*Multilingual\*\* — Switch between French and English



\## Architecture



```

Zabbix API → Python (RAG) → Groq LLM → Streamlit UI

&#x20;               ↓

&#x20;          Chroma Vector DB

```



\## Project Structure



```

├── app.py                    # Streamlit web interface

├── explain\_alert.py          # Single alert explanation

├── daily\_summary.py          # Daily summary generator

├── alert\_correlation.py      # Alert correlation engine

├── build\_vectorstore.py      # Build Chroma DB

├── incidents.py              # Fake incident knowledge base

├── vm\_discovery.ps1          # PowerShell script for Hyper-V

├── zbx\_export\_templates.yaml # Zabbix template export

├── requirements.txt          # Python dependencies

└── README.md                 # This file

```



\## Setup



1\. Clone the repository:

&#x20;  ```bash

&#x20;  git clone https://github.com/malek-soui/zabbix-ai-assistant.git

&#x20;  cd zabbix-ai-assistant

&#x20;  ```



2\. Create a `.env` file with your credentials:

&#x20;  ```

&#x20;  ZABBIX\_URL=http://your-zabbix-server/api\_jsonrpc.php

&#x20;  ZABBIX\_API\_TOKEN=your\_zabbix\_api\_token

&#x20;  GROQ\_API\_KEY=your\_groq\_api\_key

&#x20;  ```



3\. Install dependencies:

&#x20;  ```bash

&#x20;  pip install -r requirements.txt

&#x20;  ```



4\. Build the vector store:

&#x20;  ```bash

&#x20;  python build\_vectorstore.py

&#x20;  ```



5\. Run the app:

&#x20;  ```bash

&#x20;  streamlit run app.py

&#x20;  ```



\## Prerequisites



\- Zabbix 7.4+ (with API access)

\- Groq API key (free tier available)

\- Python 3.10+



\## License



This project was created during an internship and is for demonstration purposes.

