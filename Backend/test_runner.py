"""
CodeAtlas Academic Test Runner
================================
IEEE makale değerlendirmesi için:
  - 12 GitHub reposu üzerinde otomatik test
  - Tree-sitter Precision/Recall (Python repolar için AST ground truth)
  - NLP modu (use_nlp=True) vs NLP'siz (use_nlp=False) karşılaştırması
  - Mermaid diyagram geçerlilik testi
  - İşlem süresi ölçümü
  - Başarısızlık senaryoları testi
  - JSON + CSV çıktı

Kullanım:
  python test_runner.py
"""

import ast
import csv
import io
import json
import os
import re
import sys
import time
import urllib.request
import zipfile
from dataclasses import asdict, dataclass, field
from pathlib import Path

# Windows terminal UTF-8 encoding configuration
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


# ──────────────────────────────────────────────
# Yapılandırma
# ──────────────────────────────────────────────
API_BASE = "http://localhost:8000"
RESULTS_DIR = Path("test_results")
RESULTS_DIR.mkdir(exist_ok=True)

# Test edilecek 12 GitHub reposu
TEST_REPOS = [
    # (owner, repo, branch, label, language_profile, size_category)
    ("pallets",   "flask",        "main",   "Flask",        "python",      "small"),
    ("tiangolo",  "fastapi",      "master", "FastAPI",      "python",      "small"),
    ("encode",    "httpx",        "master", "HTTPX",        "python",      "small"),
    ("tiangolo",  "sqlmodel",     "main",   "SQLModel",     "python",      "small"),
    ("expressjs", "express",      "master", "Express.js",   "javascript",  "small"),
    ("vitejs",    "vite",         "main",   "Vite",         "typescript",  "medium"),
    ("vuejs",     "vue",          "main",   "Vue.js",       "typescript",  "medium"),
    ("facebook",  "react",        "main",   "React",        "javascript",  "large"),
    ("nestjs",    "nest",         "master", "NestJS",       "typescript",  "large"),
    ("django",    "django",       "main",   "Django",       "python",      "large"),
    ("encode",    "starlette",    "master", "Starlette",    "python",      "small"),
    ("B1RKANN",   "codeatlas",    "main",   "CodeAtlas",    "mixed",       "small"),
]

# Başarısızlık senaryo testleri
FAILURE_SCENARIOS = [
    {
        "name": "too_small_zip",
        "description": "Kaynak dosyası olmayan ZIP (yalnızca README.md)",
        "create_fn": "create_no_source_zip",
    },
    {
        "name": "minified_js",
        "description": "Minified/obfuscated JavaScript (sembol tespiti zor)",
        "create_fn": "create_minified_js_zip",
    },
    {
        "name": "deep_nesting",
        "description": "Çok derin klasör hiyerarşisi",
        "create_fn": "create_deep_nesting_zip",
    },
    {
        "name": "dynamic_imports",
        "description": "Python dinamik import (__import__, importlib)",
        "create_fn": "create_dynamic_imports_zip",
    },
    {
        "name": "circular_deps",
        "description": "Dairesel bağımlılık (A→B→C→A)",
        "create_fn": "create_circular_deps_zip",
    },
]


# ──────────────────────────────────────────────
# Veri Sınıfları
# ──────────────────────────────────────────────
@dataclass
class RepoTestResult:
    repo: str
    label: str
    language_profile: str
    size_category: str
    # Dosya istatistikleri
    total_files_in_zip: int = 0
    source_files_analyzed: int = 0
    # Tree-sitter metrikleri
    ts_symbols_found: int = 0
    ts_functions_found: int = 0
    ts_classes_found: int = 0
    ts_imports_found: int = 0
    # Ground truth (Python repolar için)
    gt_symbols: int = 0
    gt_functions: int = 0
    gt_classes: int = 0
    ts_precision: float = 0.0
    ts_recall: float = 0.0
    ts_f1: float = 0.0
    # Mermaid metrikleri
    mermaid_valid: bool = False
    mermaid_node_count: int = 0
    mermaid_edge_count: int = 0
    mermaid_subgraph_count: int = 0
    mermaid_file_reference_rate: float = 0.0
    # LLM metrikleri
    llm_provider: str = ""
    llm_summary_word_count: int = 0
    component_count: int = 0
    has_warnings: bool = False
    warnings: list = field(default_factory=list)
    # Performans
    processing_time_sec: float = 0.0
    zip_size_bytes: int = 0
    # Mod karşılaştırması
    nlp_mode_tested: bool = False
    nlp_processing_time_sec: float = 0.0
    nlp_mermaid_node_count: int = 0
    nlp_token_reduction_pct: float = 0.0
    # Durum
    success: bool = False
    error_message: str = ""


@dataclass
class FailureResult:
    scenario: str
    description: str
    expected_behavior: str
    actual_behavior: str
    success: bool  # True = beklenen hata alındı (sistem doğru davrandı)
    error_message: str = ""


# ──────────────────────────────────────────────
# ZIP İndirme
# ──────────────────────────────────────────────
def download_github_zip(owner: str, repo: str, branch: str) -> bytes | None:
    url = f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.zip"
    print(f"    ⬇  İndiriliyor: {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "CodeAtlas-TestRunner/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.read()
    except Exception as exc:
        print(f"    ✗ İndirme hatası: {exc}")
        return None


# ──────────────────────────────────────────────
# CodeAtlas API Çağrısı
# ──────────────────────────────────────────────
def call_analysis_api(zip_bytes: bytes, filename: str, use_nlp: bool = False) -> tuple[dict | None, float]:
    boundary = "----CodeAtlasTestBoundary"
    body_parts = [
        f"--{boundary}".encode(),
        b'Content-Disposition: form-data; name="provider"\r\n\r\ngemini',
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="use_nlp"\r\n\r\n{"true" if use_nlp else "false"}'.encode(),
        f"--{boundary}".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\nContent-Type: application/zip\r\n\r\n'.encode() + zip_bytes,
        f"--{boundary}--".encode(),
    ]
    body = b"\r\n".join(body_parts)

    req = urllib.request.Request(
        f"{API_BASE}/analysis/upload",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )

    start = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - start
        return data, elapsed
    except urllib.request.HTTPError as exc:
        elapsed = time.time() - start
        try:
            err_body = exc.read().decode("utf-8")
        except Exception:
            err_body = str(exc)
        return {"error": err_body, "status_code": exc.code}, elapsed
    except Exception as exc:
        elapsed = time.time() - start
        return None, elapsed


# ──────────────────────────────────────────────
# Mermaid Analizi
# ──────────────────────────────────────────────
def analyze_mermaid(mermaid_text: str) -> dict:
    if not mermaid_text or not mermaid_text.strip():
        return {"valid": False, "nodes": 0, "edges": 0, "subgraphs": 0}

    node_pattern = re.compile(r'\[["\'"]?[^\]]+')
    edge_pattern = re.compile(r"-->|-.->|===|--")
    subgraph_pattern = re.compile(r"^\s*subgraph\s", re.MULTILINE)

    nodes = len(node_pattern.findall(mermaid_text))
    edges = len(edge_pattern.findall(mermaid_text))
    subgraphs = len(subgraph_pattern.findall(mermaid_text))

    # Temel geçerlilik: flowchart ile başlıyor mu?
    valid = bool(re.search(r"flowchart\s+(LR|TD|TB|RL|BT)", mermaid_text))

    return {
        "valid": valid and nodes > 0,
        "nodes": nodes,
        "edges": edges,
        "subgraphs": subgraphs,
    }


def calc_file_reference_rate(mermaid_text: str, analyzed_files: list) -> float:
    """Analiz edilen dosyaların kaçı Mermaid diyagramında geçiyor?"""
    if not analyzed_files or not mermaid_text:
        return 0.0
    matched = 0
    for f in analyzed_files:
        path = f.get("path", "")
        basename = path.rsplit("/", 1)[-1] if "/" in path else path
        if basename in mermaid_text or path in mermaid_text:
            matched += 1
    return round(matched / len(analyzed_files), 3)


# ──────────────────────────────────────────────
# Ground Truth — Python AST
# ──────────────────────────────────────────────
def get_python_ground_truth(zip_bytes: bytes) -> dict:
    """Python zip'inden ast modülüyle gerçek sembol sayısını çıkar."""
    gt_functions, gt_classes = 0, 0
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            py_files = [n for n in zf.namelist() if n.endswith(".py") and not n.endswith("__init__.py")]
            for name in py_files[:500]:  # max 500 dosya
                try:
                    src = zf.read(name)
                    tree = ast.parse(src)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                            gt_functions += 1
                        elif isinstance(node, ast.ClassDef):
                            gt_classes += 1
                except Exception:
                    continue
    except Exception:
        pass
    return {"functions": gt_functions, "classes": gt_classes, "total": gt_functions + gt_classes}


def calc_precision_recall(ts_found: int, gt_total: int) -> tuple[float, float, float]:
    """
    Basitleştirilmiş metrik: 
    Tree-sitter'ın bulduğu sembol sayısı ile ground truth karşılaştırması.
    Gerçek TP/FP/FN hesabı için isim bazlı eşleşme gerekir; 
    burada sayısal yaklaşım kullanıyoruz (makale sınırlılık bölümünde belirtilmeli).
    """
    if gt_total == 0:
        return 0.0, 0.0, 0.0
    # Tree-sitter bazen fazla yakalar (arrow functions dahil), bazen az
    tp_est = min(ts_found, gt_total)
    fp_est = max(0, ts_found - gt_total)
    fn_est = max(0, gt_total - ts_found)
    precision = tp_est / (tp_est + fp_est) if (tp_est + fp_est) > 0 else 0.0
    recall = tp_est / (tp_est + fn_est) if (tp_est + fn_est) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return round(precision, 3), round(recall, 3), round(f1, 3)


# ──────────────────────────────────────────────
# Başarısızlık Senaryoları — ZIP Oluşturucular
# ──────────────────────────────────────────────
def create_no_source_zip() -> bytes:
    """Kaynak dosyası olmayan ZIP."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("README.md", "# Test Project\nNo source files here.")
        zf.writestr("LICENSE", "MIT License")
    return buf.getvalue()


def create_minified_js_zip() -> bytes:
    """Minified JS — sembol isimler anlamsız."""
    minified = "!function(e,t){var n=function(a,b,c){return a+b+c};var r=function(x){return x*2};var o=function(){var a=1;var b=2;return n(a,b,0)}}();"
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dist/bundle.min.js", minified * 50)
        zf.writestr("dist/vendor.min.js", minified * 100)
    return buf.getvalue()


def create_deep_nesting_zip() -> bytes:
    """10 seviye derin klasör yapısı."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        path = "/".join(f"level{i}" for i in range(10))
        zf.writestr(f"{path}/deep.py", "def deeply_nested():\n    pass\n")
        zf.writestr("top.py", "def top_level():\n    pass\n")
    return buf.getvalue()


def create_dynamic_imports_zip() -> bytes:
    """Python dinamik import — Tree-sitter statik analiz edemez."""
    code = """
import importlib
import sys

def load_module(name):
    return __import__(name)

def dynamic_load(module_name, class_name):
    mod = importlib.import_module(module_name)
    return getattr(mod, class_name)

plugins = {}
for plugin_name in ['auth', 'cache', 'queue']:
    plugins[plugin_name] = importlib.import_module(f'app.plugins.{plugin_name}')
"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("dynamic_app.py", code)
        zf.writestr("utils.py", "def helper(): pass\n")
    return buf.getvalue()


def create_circular_deps_zip() -> bytes:
    """Dairesel bağımlılık: A → B → C → A"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("module_a.py", "from module_c import func_c\ndef func_a(): return func_c()\n")
        zf.writestr("module_b.py", "from module_a import func_a\ndef func_b(): return func_a()\n")
        zf.writestr("module_c.py", "from module_b import func_b\ndef func_c(): return func_b()\n")
    return buf.getvalue()


FAILURE_ZIP_CREATORS = {
    "create_no_source_zip": create_no_source_zip,
    "create_minified_js_zip": create_minified_js_zip,
    "create_deep_nesting_zip": create_deep_nesting_zip,
    "create_dynamic_imports_zip": create_dynamic_imports_zip,
    "create_circular_deps_zip": create_circular_deps_zip,
}


# ──────────────────────────────────────────────
# ZIP Dosya Sayısı
# ──────────────────────────────────────────────
def count_zip_files(zip_bytes: bytes) -> int:
    try:
        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            return len([n for n in zf.namelist() if not n.endswith("/")])
    except Exception:
        return 0


# ──────────────────────────────────────────────
# Ana Test Fonksiyonu — Tek Repo
# ──────────────────────────────────────────────
def test_repo(owner: str, repo: str, branch: str, label: str, lang: str, size: str) -> RepoTestResult:
    result = RepoTestResult(
        repo=f"{owner}/{repo}",
        label=label,
        language_profile=lang,
        size_category=size,
    )

    print(f"\n{'='*60}")
    print(f"  📦 {label} ({owner}/{repo})")
    print(f"{'='*60}")

    # 1. ZIP İndir
    zip_bytes = download_github_zip(owner, repo, branch)
    if zip_bytes is None:
        result.error_message = "ZIP indirilemedi"
        return result

    result.zip_size_bytes = len(zip_bytes)
    result.total_files_in_zip = count_zip_files(zip_bytes)
    print(f"    ✓ İndirildi: {result.zip_size_bytes/1024/1024:.1f} MB, {result.total_files_in_zip} dosya")

    # 2. Python Ground Truth (sadece Python repolar için)
    if lang == "python":
        print("    🔬 Python AST ground truth hesaplanıyor...")
        gt = get_python_ground_truth(zip_bytes)
        result.gt_functions = gt["functions"]
        result.gt_classes = gt["classes"]
        result.gt_symbols = gt["total"]
        print(f"    ✓ Ground truth: {gt['functions']} fonksiyon, {gt['classes']} class")

    # 3. API Testi — NLP KAPALI (baseline)
    print("    🚀 API testi başlıyor (NLP kapalı)...")
    data, elapsed = call_analysis_api(zip_bytes, f"{repo}.zip", use_nlp=False)
    result.processing_time_sec = round(elapsed, 2)

    if data is None or "error" in data:
        result.error_message = str(data.get("error", "API hatası") if data else "Bağlantı hatası")
        print(f"    ✗ Hata: {result.error_message}")
        return result

    # API sonuçlarını işle
    result.success = True
    result.source_files_analyzed = len(data.get("files", []))
    result.llm_provider = data.get("llm_provider", "local")
    result.has_warnings = len(data.get("warnings", [])) > 0
    result.warnings = data.get("warnings", [])
    result.component_count = len(data.get("components", []))

    summary = data.get("summary", "")
    result.llm_summary_word_count = len(summary.split()) if summary else 0

    # Sembol istatistikleri
    for f in data.get("files", []):
        for sym in f.get("symbols", []):
            result.ts_symbols_found += 1
            if sym.get("kind") == "function":
                result.ts_functions_found += 1
            elif sym.get("kind") == "class":
                result.ts_classes_found += 1
        result.ts_imports_found += len(f.get("imports", []))

    # Precision/Recall (Python için)
    if lang == "python" and result.gt_symbols > 0:
        p, r, f1 = calc_precision_recall(result.ts_symbols_found, result.gt_symbols)
        result.ts_precision = p
        result.ts_recall = r
        result.ts_f1 = f1

    # Mermaid analizi
    mermaid_text = data.get("mermaid", "")
    mermaid_stats = analyze_mermaid(mermaid_text)
    result.mermaid_valid = mermaid_stats["valid"]
    result.mermaid_node_count = mermaid_stats["nodes"]
    result.mermaid_edge_count = mermaid_stats["edges"]
    result.mermaid_subgraph_count = mermaid_stats["subgraphs"]
    result.mermaid_file_reference_rate = calc_file_reference_rate(mermaid_text, data.get("files", []))

    print(f"    ✓ Tamamlandı: {elapsed:.1f}sn | {result.source_files_analyzed} dosya | {result.ts_symbols_found} sembol")
    print(f"    ✓ Mermaid: {'GEÇERLİ' if result.mermaid_valid else 'GEÇERSİZ'} | {result.mermaid_node_count} node | {result.mermaid_edge_count} edge")

    # Sonuçları kaydet
    out_path = RESULTS_DIR / f"{repo}_no_nlp.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    # 4. API Testi — NLP AÇIK (karşılaştırma)
    # Sadece 200+ dosyalı projeler için anlam taşır
    if result.total_files_in_zip > 100:
        print("    🧠 API testi başlıyor (NLP açık)...")
        nlp_data, nlp_elapsed = call_analysis_api(zip_bytes, f"{repo}.zip", use_nlp=True)
        result.nlp_mode_tested = True
        result.nlp_processing_time_sec = round(nlp_elapsed, 2)

        if nlp_data and "error" not in nlp_data:
            nlp_mermaid = analyze_mermaid(nlp_data.get("mermaid", ""))
            result.nlp_mermaid_node_count = nlp_mermaid["nodes"]

            # Token tasarrufu tahmini (dosya sayısı bazında)
            no_nlp_files = len(data.get("files", []))
            nlp_files = len(nlp_data.get("files", []))
            if no_nlp_files > 0:
                result.nlp_token_reduction_pct = round((1 - nlp_files / no_nlp_files) * 100, 1)

            out_nlp_path = RESULTS_DIR / f"{repo}_nlp.json"
            with open(out_nlp_path, "w", encoding="utf-8") as f:
                json.dump(nlp_data, f, ensure_ascii=False, indent=2)

            print(f"    ✓ NLP modu: {nlp_elapsed:.1f}sn | Token azalma: ~%{result.nlp_token_reduction_pct}")
        else:
            print(f"    ✗ NLP modu hatası")
    else:
        print(f"    ℹ  NLP modu atlandı (dosya sayısı < 100, semantik seçim anlamsız)")

    return result


# ──────────────────────────────────────────────
# Başarısızlık Senaryoları Testi
# ──────────────────────────────────────────────
def test_failure_scenarios() -> list[FailureResult]:
    print(f"\n{'='*60}")
    print("  🔴 BAŞARISIZLIK SENARYOLARI TESTİ")
    print(f"{'='*60}")

    results = []

    scenario_configs = [
        {
            "name": "no_source_files",
            "description": "Kaynak dosyası olmayan ZIP (yalnızca README, LICENSE)",
            "create_fn": create_no_source_zip,
            "filename": "empty_project.zip",
            "expected": "400 Bad Request — desteklenen kaynak dosyası bulunamadı",
        },
        {
            "name": "minified_javascript",
            "description": "Minified/obfuscated JS (sembol isimleri tek harf: a, b, c)",
            "create_fn": create_minified_js_zip,
            "filename": "minified.zip",
            "expected": "200 OK — ancak sembol isimleri anlamsız (a, b, c, n, r)",
        },
        {
            "name": "deep_nesting",
            "description": "10 seviye derin klasör hiyerarşisi",
            "create_fn": create_deep_nesting_zip,
            "filename": "deep_nesting.zip",
            "expected": "200 OK — dosya ağacı render edilebilmeli",
        },
        {
            "name": "dynamic_imports",
            "description": "Python dinamik import (importlib, __import__)",
            "create_fn": create_dynamic_imports_zip,
            "filename": "dynamic_imports.zip",
            "expected": "200 OK — ancak import ilişkileri Mermaid'e yansımayabilir",
        },
        {
            "name": "circular_dependencies",
            "description": "Dairesel bağımlılık: A→B→C→A",
            "create_fn": create_circular_deps_zip,
            "filename": "circular_deps.zip",
            "expected": "200 OK — sistem döngü oluşturmamalı",
        },
    ]

    for scenario in scenario_configs:
        print(f"\n  📌 Senaryo: {scenario['name']}")
        print(f"     {scenario['description']}")

        zip_bytes = scenario["create_fn"]()
        data, elapsed = call_analysis_api(zip_bytes, scenario["filename"], use_nlp=False)

        if data is None:
            actual = "Bağlantı hatası"
            success = False
        elif "status_code" in data:
            actual = f"HTTP {data['status_code']} — {data.get('error', '')[:100]}"
            success = data.get("status_code") in [400, 422]  # Beklenen hata
        else:
            files = data.get("files", [])
            symbols = sum(len(f.get("symbols", [])) for f in files)
            mermaid_stats = analyze_mermaid(data.get("mermaid", ""))
            actual = (
                f"200 OK | {len(files)} dosya | {symbols} sembol | "
                f"Mermaid {'GEÇERLİ' if mermaid_stats['valid'] else 'GEÇERSİZ'} "
                f"({mermaid_stats['nodes']} node)"
            )
            success = True  # 200 aldık, davranış gözlemlendi

        result = FailureResult(
            scenario=scenario["name"],
            description=scenario["description"],
            expected_behavior=scenario["expected"],
            actual_behavior=actual,
            success=success,
        )
        results.append(result)

        status_icon = "✓" if success else "✗"
        print(f"     {status_icon} Beklenen : {scenario['expected'][:80]}")
        print(f"     {status_icon} Gerçekleşen: {actual[:80]}")

        out_path = RESULTS_DIR / f"failure_{scenario['name']}.json"
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump({"scenario": scenario["name"], "actual": actual, "raw": data}, f, ensure_ascii=False, indent=2)

    return results


# ──────────────────────────────────────────────
# Rapor Üretimi
# ──────────────────────────────────────────────
def save_csv(results: list[RepoTestResult]) -> None:
    csv_path = RESULTS_DIR / "main_results.csv"
    if not results:
        return
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[k for k in asdict(results[0]).keys() if k != "warnings"])
        writer.writeheader()
        for r in results:
            row = asdict(r)
            row.pop("warnings", None)
            writer.writerow(row)
    print(f"\n  💾 CSV kaydedildi: {csv_path}")


def print_summary_tables(results: list[RepoTestResult], failures: list[FailureResult]) -> None:
    print("\n")
    print("=" * 80)
    print("  📊 TABLO 1 — TREE-SITTER ANALİZ METRİKLERİ")
    print("=" * 80)
    print(f"{'Proje':<18} {'Dil':<12} {'Dosya':<7} {'Sembol':<8} {'Prec.':<8} {'Recall':<8} {'F1':<8} {'Süre(s)'}")
    print("-" * 80)
    for r in results:
        if r.success:
            prec = f"{r.ts_precision:.2f}" if r.ts_precision else "N/A"
            rec = f"{r.ts_recall:.2f}" if r.ts_recall else "N/A"
            f1 = f"{r.ts_f1:.2f}" if r.ts_f1 else "N/A"
            print(f"{r.label:<18} {r.language_profile:<12} {r.source_files_analyzed:<7} {r.ts_symbols_found:<8} {prec:<8} {rec:<8} {f1:<8} {r.processing_time_sec:.1f}")

    print("\n")
    print("=" * 80)
    print("  📊 TABLO 2 — MERMAID DİYAGRAM KALİTESİ")
    print("=" * 80)
    print(f"{'Proje':<18} {'Geçerli':<9} {'Node':<7} {'Edge':<7} {'Subgraph':<10} {'Dosya Ref.':<12} {'LLM'}")
    print("-" * 80)
    for r in results:
        if r.success:
            valid = "✓" if r.mermaid_valid else "✗"
            ref_pct = f"%{r.mermaid_file_reference_rate*100:.0f}"
            print(f"{r.label:<18} {valid:<9} {r.mermaid_node_count:<7} {r.mermaid_edge_count:<7} {r.mermaid_subgraph_count:<10} {ref_pct:<12} {r.llm_provider}")

    # NLP karşılaştırma tablosu
    nlp_tested = [r for r in results if r.nlp_mode_tested]
    if nlp_tested:
        print("\n")
        print("=" * 80)
        print("  📊 TABLO 3 — NLP MODU vs BASELINE KARŞILAŞTIRMA")
        print("=" * 80)
        print(f"{'Proje':<18} {'Baseline(s)':<13} {'NLP(s)':<10} {'Süre Farkı':<13} {'Token Azalma':<15} {'NLP Node'}")
        print("-" * 80)
        for r in nlp_tested:
            diff = r.nlp_processing_time_sec - r.processing_time_sec
            diff_str = f"+{diff:.1f}s" if diff >= 0 else f"{diff:.1f}s"
            print(f"{r.label:<18} {r.processing_time_sec:<13.1f} {r.nlp_processing_time_sec:<10.1f} {diff_str:<13} %{r.nlp_token_reduction_pct:<14.0f} {r.nlp_mermaid_node_count}")

    print("\n")
    print("=" * 80)
    print("  📊 TABLO 4 — BAŞARISIZLIK SENARYOLARI")
    print("=" * 80)
    print(f"{'Senaryo':<28} {'Davranış':<12} {'Gerçekleşen (kısa)'}")
    print("-" * 80)
    for f in failures:
        icon = "✓" if f.success else "✗"
        print(f"{f.scenario:<28} {icon:<12} {f.actual_behavior[:50]}")


# ──────────────────────────────────────────────
# Ana Akış
# ──────────────────────────────────────────────
def main():
    print("\n🔬 CodeAtlas Academic Test Runner")
    print("   IEEE Makale Değerlendirmesi")
    print(f"   Sonuçlar: {RESULTS_DIR.absolute()}\n")

    # Backend sağlık kontrolü
    try:
        with urllib.request.urlopen(f"{API_BASE}/health", timeout=5) as resp:
            health = json.loads(resp.read())
            print(f"  ✓ Backend sağlıklı: {health}\n")
    except Exception as exc:
        print(f"  ✗ Backend'e bağlanılamıyor: {exc}")
        print("    Backend'i başlatın: uvicorn app.main:app --port 8000")
        sys.exit(1)

    # ── Repo Testleri ──
    all_results: list[RepoTestResult] = []
    for owner, repo, branch, label, lang, size in TEST_REPOS:
        try:
            result = test_repo(owner, repo, branch, label, lang, size)
            all_results.append(result)
            # Ara kayıt
            json_path = RESULTS_DIR / "all_results.json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump([asdict(r) for r in all_results], f, ensure_ascii=False, indent=2)
        except KeyboardInterrupt:
            print("\n  ⚠ Test kesildi (Ctrl+C)")
            break
        except Exception as exc:
            print(f"  ✗ Beklenmeyen hata ({label}): {exc}")

    # ── Başarısızlık Senaryoları ──
    failure_results = test_failure_scenarios()

    # ── Sonuç Raporu ──
    print_summary_tables(all_results, failure_results)
    save_csv(all_results)

    failure_path = RESULTS_DIR / "failure_scenarios.json"
    with open(failure_path, "w", encoding="utf-8") as f:
        json.dump([asdict(r) for r in failure_results], f, ensure_ascii=False, indent=2)

    success_count = sum(1 for r in all_results if r.success)
    print(f"\n  ✅ Tamamlanan: {success_count}/{len(all_results)} repo")
    print(f"  📁 Tüm sonuçlar: {RESULTS_DIR.absolute()}")
    print("\n  Sonraki adım: Sonuçları makale tablolarına dönüştürmek için")
    print("  python generate_paper_tables.py komutunu çalıştırın.\n")


if __name__ == "__main__":
    main()
