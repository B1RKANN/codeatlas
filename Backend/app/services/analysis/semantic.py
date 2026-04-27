from app.core.config import settings
from app.services.analysis.models import AnalyzedFile, ProjectAnalysis


_model = None
_model_name: str | None = None


def select_prompt_files(analysis: ProjectAnalysis) -> tuple[list[AnalyzedFile], list[str]]:
    max_files = max(1, settings.semantic_max_prompt_files)
    if not settings.semantic_analysis_enabled or len(analysis.files) <= max_files:
        return analysis.files[:max_files], []

    try:
        model = _get_model()
        file_docs = [_file_to_embedding_text(file) for file in analysis.files]
        query = _query_text(analysis)
        query_embedding = model.encode(query, normalize_embeddings=True)
        file_embeddings = model.encode(file_docs, normalize_embeddings=True)
    except Exception as exc:
        return (
            analysis.files[:max_files],
            [
                "Semantic file ranking with "
                f"{settings.semantic_embedding_model} failed; used file order instead. Reason: {exc}"
            ],
        )

    ranked_indices = sorted(
        range(len(analysis.files)),
        key=lambda index: _dot_product(query_embedding, file_embeddings[index]),
        reverse=True,
    )[:max_files]

    return [analysis.files[index] for index in ranked_indices], []


def _get_model():
    global _model, _model_name

    if _model is not None and _model_name == settings.semantic_embedding_model:
        return _model

    from sentence_transformers import SentenceTransformer

    _model = SentenceTransformer(settings.semantic_embedding_model)
    _model_name = settings.semantic_embedding_model
    return _model


def _query_text(analysis: ProjectAnalysis) -> str:
    return " ".join(
        [
            analysis.project_name,
            "Turkish architecture summary",
            "important source files services API database authentication analysis components",
            "Mermaid high level relationships",
        ]
    )


def _file_to_embedding_text(file: AnalyzedFile) -> str:
    symbols = " ".join(f"{symbol.kind} {symbol.name}" for symbol in file.symbols[:80])
    imports = " ".join(file.imports[:40])
    return " ".join([file.path, file.language, imports, symbols]).strip()


def _dot_product(left, right) -> float:
    return float(sum(float(a) * float(b) for a, b in zip(left, right, strict=False)))
