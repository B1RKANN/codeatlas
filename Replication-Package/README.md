# CodeAtlas: Academic Replication Package

This repository contains the replication package for the academic paper: **"CodeAtlas: Automated Software Architecture Visualizer using AST-based Static Analysis"**.

All raw data, analysis results, generated Mermaid.js code blocks, and the **unmodified source code archives of the tested repositories** are included here to satisfy scientific reproducibility requirements and prove zero-fabrication/zero-hallucination of experimental results.

---

## 💻 Hardware & Software Environment

*   **Operating System:** Windows 10/11
*   **CPU:** Intel Core i7 / AMD Ryzen 7
*   **RAM:** 16 GB DDR4
*   **Python Version:** Python 3.14 (Virtual Environment)
*   **Database:** PostgreSQL 17
*   **Static Parser:** Tree-sitter Parser Engine
*   **Semantic Model:** sentence-transformers (`BAAI/bge-m3`)

---

## 📂 Repository Structure

*   `main_results.csv` - The aggregated metrics for all analyzed repositories.
*   `latex_tables.txt` - Pre-formatted LaTeX source code for academic papers.
*   `test_sources/` - **The original, unmodified source code ZIP archives of the 10 benchmark repositories** (used to verify the exact code base evaluated).
    *   `Flask.zip`
    *   `FastAPI.zip`
    *   `HTTPX.zip`
    *   `SQLModel.zip`
    *   `Express.zip`
    *   `Vite.zip`
    *   `Vue.zip`
    *   `NestJS.zip`
    *   `Starlette.zip`
    *   `CodeAtlas.zip`
*   `raw_responses/` - Full JSON outputs returned from the local FastAPI `/analysis/upload` endpoint.
*   `failure_scenarios/` - Diagnostics JSON outputs for custom edge-case and failure zip inputs.

---

## 📊 Summary of Replication Results

### 1. Tree-sitter AST Extraction Metrics
| Project | Language | Analyzed Files | Symbol Count | Precision | Recall | F1-Score | Time (s) |
|---|---|---|---|---|---|---|---|
| **Flask** | Python | 83 | 1620 | 0.99 | 1.00 | 0.99 | 8.40 |
| **FastAPI** | Python | 1133 | 5616 | 0.41 | 1.00 | 0.58 | 4.86 |
| **HTTPX** | Python | 60 | 1241 | 1.00 | 1.00 | 1.00 | 2.48 |
| **SQLModel** | Python | 319 | 1109 | 0.98 | 1.00 | 0.99 | 2.71 |
| **Express.js** | JS | 141 | 127 | N/A | N/A | N/A | 2.54 |
| **Vite** | TS | 1458 | 2669 | N/A | N/A | N/A | 4.60 |
| **Vue.js** | TS | 425 | 1989 | N/A | N/A | N/A | 3.77 |
| **NestJS** | TS | 1683 | 5166 | N/A | N/A | N/A | 12.79 |
| **Starlette** | Python | 67 | 1686 | 1.00 | 1.00 | 1.00 | 2.67 |
| **CodeAtlas** | Mixed | 48 | 150 | N/A | N/A | N/A | 2.17 |

### 2. Mermaid Diagram Structural Quality
| Project | Valid rendering | Node Count | Edge Count | Subgraph Count | File Ref. Rate |
|---|---|---|---|---|---|
| **Flask** | Yes | 107 | 121 | 8 | 51% |
| **FastAPI** | Yes | 90 | 84 | 8 | 36% |
| **HTTPX** | Yes | 74 | 88 | 4 | 35% |
| **SQLModel** | Yes | 94 | 87 | 13 | 48% |
| **Express.js** | Yes | 87 | 62 | 24 | 26% |
| **Vite** | Yes | 101 | 82 | 20 | 26% |
| **Vue.js** | Yes | 89 | 88 | 12 | 14% |
| **NestJS** | Yes | 101 | 102 | 18 | 10% |
| **Starlette** | Yes | 70 | 67 | 2 | 28% |
| **CodeAtlas** | Yes | 95 | 83 | 11 | 60% |

---

## 🔬 How to Reproduce

1. Clone the CodeAtlas repository.
2. Initialize PostgreSQL 17 database named `codeatlas`.
3. Set up the Python virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\Activate
   pip install -r requirements.txt
   ```
4. Start the FastAPI backend:
   ```bash
   uvicorn app.main:app --port 8000
   ```
5. Run the test suite:
   ```bash
   python test_runner.py
   ```
   The script will download the source archives from GitHub and write the updated metrics to the `test_results` directory.
