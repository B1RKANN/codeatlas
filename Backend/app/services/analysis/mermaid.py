import re

from app.services.analysis.models import AnalyzedFile, ProjectAnalysis


MAX_DIAGRAM_FILES = 28
MAX_SYMBOLS_PER_FILE = 3
MAX_IMPORT_EDGES_PER_FILE = 4
MAX_IMPORT_EDGES_TOTAL = 24
MAX_FILES_PER_GROUP = 8


def build_fallback_mermaid(analysis: ProjectAnalysis) -> str:
    visible_files = analysis.files[:MAX_DIAGRAM_FILES]
    lines = [
        "flowchart LR",
        f"  project[\"{_escape(analysis.project_name)}\"]",
        "  source[\"High-Level Architecture\"]",
        "  project --> source",
    ]

    file_ids: dict[str, str] = {}
    symbol_ids: list[str] = []
    grouped_files = _group_files_by_directory(visible_files)

    file_index = 0
    for group_index, (directory, files) in enumerate(grouped_files.items()):
        group_id = f"group_{group_index}"
        group_hub_id = f"{group_id}_hub"
        group_label = _group_label(directory)
        lines.append(f"  source --> {group_hub_id}")
        lines.append(f"  subgraph {group_id}[\"{_escape(group_label)}\"]")
        lines.append(f"    {group_hub_id}[\"{_escape(group_label)}\"]")

        shown_files = files[:MAX_FILES_PER_GROUP]
        for analyzed_file in shown_files:
            file_id = f"file_{file_index}"
            file_index += 1
            file_ids[analyzed_file.path] = file_id
            lines.append(f"    {group_hub_id} --> {file_id}[\"{_escape(_basename(analyzed_file.path))}\"]")

            for symbol_index, symbol in enumerate(analyzed_file.symbols[:MAX_SYMBOLS_PER_FILE]):
                symbol_id = f"{file_id}_symbol_{symbol_index}"
                symbol_ids.append(symbol_id)
                label = _symbol_label(symbol.kind, symbol.name)
                lines.append(f"    {file_id} --> {symbol_id}([\"{_escape(label)}\"])")

        if len(files) > len(shown_files):
            hidden_count = len(files) - len(shown_files)
            lines.append(f"    {group_hub_id} --> {group_id}_more[\"+{hidden_count} more files\"]")

        lines.append("  end")

    dependency_edges = _build_dependency_edges(visible_files, file_ids)
    if dependency_edges:
        lines.extend(dependency_edges)

    if len(analysis.files) > len(visible_files):
        remaining = len(analysis.files) - len(visible_files)
        lines.append(f"  source --> more_files[\"+{remaining} more files\"]")

    lines.extend(
        [
            "  classDef project fill:#ff4d8d,stroke:#ffd6e7,stroke-width:2px,color:#ffffff;",
            "  classDef layer fill:#6d2f5f,stroke:#c77db0,stroke-width:2px,color:#ffffff;",
            "  classDef file fill:#2f1a3a,stroke:#9f6b91,color:#ffffff;",
            "  classDef symbol fill:#172033,stroke:#7aa2ff,color:#ffffff,font-size:12px;",
            "  class project,source project;",
        ]
    )
    for group_index in range(len(grouped_files)):
        lines.append(f"  class group_{group_index}_hub layer;")
    for file_id in file_ids.values():
        lines.append(f"  class {file_id} file;")
    for symbol_id in symbol_ids:
        lines.append(f"  class {symbol_id} symbol;")

    return "\n".join(lines)


def select_mermaid(analysis: ProjectAnalysis, generated_mermaid: str | None) -> tuple[str, str | None]:
    fallback = build_fallback_mermaid(analysis)
    if not generated_mermaid or _is_too_simple(generated_mermaid, analysis):
        return fallback, "Üretilen Mermaid diyagramı çok basit kaldı; detaylı yerel mimari diyagramı döndürüldü."
    if not _has_enough_file_references(generated_mermaid, analysis):
        return fallback, "Üretilen Mermaid diyagramı gerçek dosya adlarını yeterince göstermedi; dosya yollarını içeren yerel diyagram döndürüldü."
    return generated_mermaid, None


def build_fallback_summary(analysis: ProjectAnalysis) -> str:
    file_count = len(analysis.files)
    symbol_count = sum(len(file.symbols) for file in analysis.files)
    languages = sorted({file.language for file in analysis.files})
    return (
        f"{analysis.project_name} projesinde {file_count} desteklenen kaynak dosya, "
        f"{symbol_count} fonksiyon/class sembolü bulundu. "
        f"Analiz edilen diller: {', '.join(languages)}."
    )


def _escape(value: str) -> str:
    return value.replace('"', "'").replace("\n", " ")


def _group_files_by_directory(files: list[AnalyzedFile]) -> dict[str, list[AnalyzedFile]]:
    grouped: dict[str, list[AnalyzedFile]] = {}
    for file in files:
        grouped.setdefault(_directory_name(file.path), []).append(file)
    return grouped


def _directory_name(path: str) -> str:
    parts = [part for part in path.split("/") if part]
    if len(parts) <= 1:
        return "root"
    return "/".join(parts[:-1])


def _group_label(directory: str) -> str:
    if directory == "root":
        return "Root"
    parts = directory.split("/")
    if len(parts) <= 2:
        return directory
    return "/".join(parts[-2:])


def _basename(path: str) -> str:
    return path.rsplit("/", 1)[-1]


def _symbol_label(kind: str, name: str) -> str:
    if kind == "function":
        return f"{name}()"
    if kind == "class":
        return name
    return f"{kind}: {name}"


def _build_dependency_edges(files: list[AnalyzedFile], file_ids: dict[str, str]) -> list[str]:
    edges: list[str] = []
    seen: set[tuple[str, str]] = set()
    for file in files:
        if file.path not in file_ids:
            continue
        source_id = file_ids[file.path]
        for target_path in _resolve_import_targets(file, file_ids)[:MAX_IMPORT_EDGES_PER_FILE]:
            target_id = file_ids[target_path]
            edge = (source_id, target_id)
            if source_id == target_id or edge in seen:
                continue
            seen.add(edge)
            edges.append(f"  {source_id} -.-> {target_id}")
            if len(edges) >= MAX_IMPORT_EDGES_TOTAL:
                return edges
    return edges


def _resolve_import_targets(file: AnalyzedFile, file_ids: dict[str, str]) -> list[str]:
    targets: list[str] = []
    for import_line in file.imports:
        import_tokens = _import_tokens(import_line)
        for target_path in file_ids:
            if target_path == file.path:
                continue
            target_stem = _path_stem(target_path)
            target_name = _basename(target_stem)
            if any(token == target_stem or token == target_name for token in import_tokens):
                targets.append(target_path)
                break
    return list(dict.fromkeys(targets))


def _import_tokens(import_line: str) -> set[str]:
    quoted = re.findall(r"[\"']([^\"']+)[\"']", import_line)
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_./-]*", import_line)
    tokens = {token.strip("./") for token in quoted + words if token not in {"import", "from", "require"}}
    expanded = set(tokens)
    for token in tokens:
        expanded.add(token.replace(".", "/"))
        expanded.add(_basename(token))
    return expanded


def _path_stem(path: str) -> str:
    return re.sub(r"\.(py|js|jsx|ts|tsx)$", "", path)


def _is_too_simple(mermaid: str, analysis: ProjectAnalysis) -> bool:
    meaningful_nodes = 1 + len(analysis.files) + sum(min(len(file.symbols), MAX_SYMBOLS_PER_FILE) for file in analysis.files)
    if meaningful_nodes <= 5:
        return False

    node_count = len(re.findall(r"\[[\"']?[^\]]+", mermaid))
    edge_count = len(re.findall(r"-->|---|-.->|==>", mermaid))
    expected_nodes = min(10, meaningful_nodes)
    expected_edges = min(8, max(0, meaningful_nodes - 1))
    return node_count < expected_nodes or edge_count < expected_edges


def _has_enough_file_references(mermaid: str, analysis: ProjectAnalysis) -> bool:
    if not analysis.files:
        return True

    normalized_mermaid = mermaid.replace("\\", "/")
    matched_files = 0
    for file in analysis.files[:MAX_DIAGRAM_FILES]:
        path = file.path.replace("\\", "/")
        if path in normalized_mermaid or _basename(path) in normalized_mermaid:
            matched_files += 1

    return matched_files >= min(3, len(analysis.files))
