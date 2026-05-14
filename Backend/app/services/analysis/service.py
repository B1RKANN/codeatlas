from app.schemas.analysis import ComponentSummary, FileAnalysis, ProjectAnalysisResponse, SymbolInfo
from app.services.analysis.extractor import read_project_zip
from app.services.analysis.gemini_client import summarize_with_gemini
from app.services.analysis.openai_client import summarize_with_gpt
from app.services.analysis.tree_sitter_analyzer import analyze_project


def analyze_zip_project(
    filename: str,
    content: bytes,
    provider: str = "gemini",
    use_nlp: bool = False,
) -> ProjectAnalysisResponse:
    snapshot = read_project_zip(filename, content)
    analysis = analyze_project(snapshot)
    if provider == "gpt":
        summary, components, mermaid, warnings, llm_provider = summarize_with_gpt(analysis, use_nlp=use_nlp)
    elif provider == "gemini":
        summary, components, mermaid, warnings, llm_provider = summarize_with_gemini(analysis, use_nlp=use_nlp)
    else:
        raise ValueError("Unsupported analysis provider. Use 'gemini' or 'gpt'.")

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
        llm_provider=llm_provider,
        warnings=warnings,
    )
