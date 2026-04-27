from app.schemas.analysis import ComponentSummary, FileAnalysis, ProjectAnalysisResponse, SymbolInfo
from app.services.analysis.extractor import read_project_zip
from app.services.analysis.gemini_client import summarize_with_gemini
from app.services.analysis.tree_sitter_analyzer import analyze_project


def analyze_zip_project(filename: str, content: bytes) -> ProjectAnalysisResponse:
    snapshot = read_project_zip(filename, content)
    analysis = analyze_project(snapshot)
    summary, components, mermaid, warnings, provider = summarize_with_gemini(analysis)

    return ProjectAnalysisResponse(
        project_name=analysis.project_name,
        file_tree=analysis.file_tree,
        summary=summary,
        components=[ComponentSummary(**component) for component in components],
        files=[
            FileAnalysis(
                path=file.path,
                language=file.language,
                imports=file.imports,
                symbols=[
                    SymbolInfo(name=symbol.name, kind=symbol.kind, line=symbol.line)
                    for symbol in file.symbols
                ],
            )
            for file in analysis.files
        ],
        mermaid=mermaid,
        llm_provider=provider,
        warnings=warnings,
    )
