# RAG – "Chat with my PC" troubleshooter

Ask plain-English questions about your Windows PC, such as *"Why did my game crash last night?"*, and get an answer based on your own event logs, crash reports and system info.

It's a retrieval-augmented generation (RAG) project:

1. **Collect:** export Windows Event Logs, crash dumps / error reports and system info.
2. **Index:** turn them into documents and store them in a local vector database (Chroma).
3. **Retrieve:** find the events relevant to your question, filtered by time.
4. **Answer:** an LLM explains what happened, citing the events it used.

The build plan is tracked step by step in the [issues](https://github.com/TriangulumAustrale/RAG/issues).

## Requirements

- Windows 10/11
- Python 3.10+
- Some logs (e.g. crash dumps) need an **administrator** terminal to read

## Install

```powershell
git clone https://github.com/TriangulumAustrale/RAG.git
cd RAG
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```powershell
python -m rag.cli --help
```

Planned commands:

| Command | What it does |
|---|---|
| `collect` | Gather system info, event logs and crash reports |
| `index` | Build the searchable index |
| `refresh` | Collect and index only what's new |
| `search "<question>"` | Show the evidence found, without calling an LLM |
| `ask "<question>"` | Answer a question about your PC |

These get built in issues #2–#10. So far, `collect` saves a system snapshot (OS, CPU, RAM, GPU and driver, uptime) to `data/raw/system_info.json`.

## Project layout

```
rag/
  collect/     # gathers raw data from the PC
  index/       # turns data into searchable documents + vectors
  retrieve/    # finds relevant documents for a question
  answer/      # sends context to the LLM and formats the reply
  cli.py       # entry point
data/          # collected data + vector store (git-ignored, stays on your PC)
tests/
```

## Privacy

Everything collected stays in `data/` on your machine and is never committed. Only the events relevant to a question are sent to the LLM.
