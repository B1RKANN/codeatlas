from app.services.analysis.models import ProjectAnalysis


def build_fallback_mermaid(analysis: ProjectAnalysis) -> str:
    lines = ["graph TD", f"  project[\"{_escape(analysis.project_name)}\"]"]

    for file_index, analyzed_file in enumerate(analysis.files):
        file_id = f"file_{file_index}"
        lines.append(f"  project --> {file_id}[\"{_escape(analyzed_file.path)}\"]")
        for symbol_index, symbol in enumerate(analyzed_file.symbols[:8]):
            symbol_id = f"{file_id}_symbol_{symbol_index}"
            label = f"{symbol.kind}: {symbol.name}"
            lines.append(f"  {file_id} --> {symbol_id}[\"{_escape(label)}\"]")

    return "\n".join(lines)


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
