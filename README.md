# C.L.I.O.S.

**CLI-based OSPF Simulator** — An interactive network simulation tool that models OSPF routing behaviors through a terminal interface, powered by AI reasoning and RFC 2328 knowledge retrieval.

```
   _____ _      _____  ____   _____
  / ____| |    |_   _|/ __ \ / ____|
 | |    | |      | | | |  | | (___
 | |    | |      | | | |  | |\___ \
 | |____| |____ _| |_| |__| |____) |
  \_____|______|_____|_____/|_____/
```

---

## Features

- **Topology Mode** — Build and configure OSPF network topologies via CLI commands (routers, interfaces, IP addressing, area configuration, etc.)
- **Ask Mode** — Ask natural language questions about OSPF behavior and get AI-powered answers grounded in your current topology and RFC 2328 knowledge
- **Agent Mode** — Describe a network in plain English and let AI automatically generate and execute the CLI commands to build it
- **Live Visualization** — Auto-generated topology diagrams via Graphviz
- **Real-time Validation** — Detects OSPF area ID/type mismatches between connected peers

---

## Architecture

```
chat.py              → Main entry point & mode controller
cli_engine.py        → Command parser & Graphviz visualization
network_state.py     → In-memory topology data model
llm_engine.py        → Typhoon LLM API integration
rag/
├── retriever.py     → FAISS vector search over RFC chunks
└── embedder.py      → Text embedding via Ollama
```

---

## Prerequisites

| Tool | Purpose |
|------|---------|
| **Python 3.10+** | Runtime |
| **[Ollama](https://ollama.com)** | Local embedding model server |
| **[Graphviz](https://graphviz.org/download/)** | Topology diagram rendering (must be on PATH) |
| **Typhoon API Key** | LLM for Q&A and agent modes |

---

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/<your-username>/CLIOS.git
cd CLIOS
```

### 2. Create and activate a virtual environment

```bash
python -m venv env_CLIOS

# Windows
.\env_CLIOS\Scripts\activate

# macOS / Linux
source env_CLIOS/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
TYPHOON_API_KEY=your_api_key_here
```

### 5. Start Ollama and pull the embedding model

```bash
ollama pull nomic-embed-text
```

### 6. Install Graphviz

Download and install from [graphviz.org](https://graphviz.org/download/), and make sure the `dot` executable is on your system PATH.

---

## Usage

```bash
python chat.py
```

### Mode Switching

| Command | Description |
|---------|-------------|
| `mode topology` | Build and configure network topology |
| `mode ask` | Ask AI questions about OSPF behavior |
| `mode agent` | AI builds topology from natural language |
| `q` | Exit |

### Topology Commands

| Command | Description |
|---------|-------------|
| `router <name>` | Create a router |
| `no router <name>` | Delete a router |
| `interface <router> <name>` | Add an interface to a router |
| `ip address <router> <intf> <ip/subnet>` | Assign an IP address |
| `connect <r1> <i1> <r2> <i2>` | Connect two interfaces |
| `ospf enable <router>` | Enable OSPF on a router |
| `area <router> <interface> <area_id>` | Assign an OSPF area |
| `areatype <id> <stub\|totally-stub\|nssa\|normal>` | Set area type |
| `external <router> <domain>` | Mark a router as external domain |
| `show topology` | Display topology + open Graphviz diagram |
| `?` | Show help |

### Example Session

```
[topology]# router R1
Router R1 created
[topology]# router R2
Router R2 created
[topology]# interface R1 e0
Interface e0 created on R1
[topology]# interface R2 e0
Interface e0 created on R2
[topology]# ip address R1 e0 10.0.0.1/24
R1 e0 IP set to 10.0.0.1/24
[topology]# ip address R2 e0 10.0.0.2/24
R2 e0 IP set to 10.0.0.2/24
[topology]# connect R1 e0 R2 e0
R1:e0 connected to R2:e0
[topology]# ospf enable R1
OSPF enabled on R1
[topology]# ospf enable R2
OSPF enabled on R2
[topology]# area R1 e0 0
Area 0 configured on R1 e0
[topology]# area R2 e0 0
Area 0 configured on R2 e0
[topology]# show topology
```

---

## Project Structure

```
CLIOS/
├── chat.py              # App entry point & CLI loop
├── cli_engine.py        # Command parser & Graphviz rendering
├── network_state.py     # Router/Interface/Network data model
├── llm_engine.py        # Typhoon LLM API calls
├── rag/
│   ├── retriever.py     # FAISS-based semantic search
│   └── embedder.py      # Ollama embedding client
├── faiss.index          # Pre-built vector index (RFC 2328)
├── chunks.pkl           # Chunked RFC text data
├── requirements.txt     # Python dependencies
├── .env                 # API keys (not committed)
└── .gitignore
```

---

## Tech Stack

- **[Typhoon API](https://opentyphoon.ai)** — LLM for OSPF reasoning & agent command generation
- **[Ollama](https://ollama.com)** + `nomic-embed-text` — Local text embeddings
- **[FAISS](https://github.com/facebookresearch/faiss)** — Vector similarity search
- **[Graphviz](https://graphviz.org)** — Network topology visualization
- **[python-dotenv](https://github.com/theskumar/python-dotenv)** — Environment variable management
