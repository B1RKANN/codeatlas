import json
import random
import time
from email.utils import parsedate_to_datetime
from urllib import error, request

from app.core.config import settings
from app.services.analysis.mermaid import build_fallback_mermaid, build_fallback_summary
from app.services.analysis.models import ProjectAnalysis
from app.services.analysis.semantic import select_prompt_files


_RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}
_rate_limited_until = 0.0


def summarize_with_gemini(analysis: ProjectAnalysis) -> tuple[str, list[dict[str, str]], str, list[str], str | None]:
    global _rate_limited_until

    fallback_summary = build_fallback_summary(analysis)
    fallback_components = _fallback_components(analysis)
    fallback_mermaid = build_fallback_mermaid(analysis)

    if not settings.gemini_api_key:
        return (
            fallback_summary,
            fallback_components,
            fallback_mermaid,
            ["GEMINI_API_KEY is not configured; returned local Tree-sitter analysis."],
            None,
        )

    now = time.monotonic()
    if now < _rate_limited_until:
        retry_after = max(1, int(_rate_limited_until - now))
        return (
            fallback_summary,
            fallback_components,
            fallback_mermaid,
            [
                "Gemini rate limit is cooling down; returned local analysis. "
                f"Try again in about {retry_after} second(s)."
            ],
            None,
        )

    prompt_files, semantic_warnings = select_prompt_files(analysis)
    prompt = _build_prompt(analysis, prompt_files)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "responseMimeType": "application/json",
        },
    }

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{settings.gemini_model}:generateContent?key={settings.gemini_api_key}"
    )
    req = request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    attempts = max(1, settings.gemini_max_retries + 1)
    for attempt in range(1, attempts + 1):
        try:
            with request.urlopen(req, timeout=settings.gemini_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            if attempt >= attempts or not _is_retryable_error(exc):
                if _is_rate_limit_error(exc):
                    _rate_limited_until = time.monotonic() + _cooldown_seconds(exc)
                return (
                    fallback_summary,
                    fallback_components,
                    fallback_mermaid,
                    [
                        "Gemini request failed after "
                        f"{attempt} attempt(s); returned local analysis. Reason: {exc}"
                    ],
                    None,
                )
            _sleep_before_retry(attempt, exc)
        except json.JSONDecodeError as exc:
            return (
                fallback_summary,
                fallback_components,
                fallback_mermaid,
                [f"Gemini returned invalid JSON; returned local analysis. Reason: {exc}"],
                None,
            )

    text = _extract_text(data)
    try:
        generated = json.loads(text)
    except json.JSONDecodeError:
        generated = _extract_json_object(text)

    if generated is None:
        return (
            fallback_summary,
            fallback_components,
            fallback_mermaid,
            ["Gemini returned non-JSON content; returned local analysis."],
            None,
        )

    return (
        str(generated.get("summary") or fallback_summary),
        _normalize_components(generated.get("components"), fallback_components),
        str(generated.get("mermaid") or fallback_mermaid),
        semantic_warnings,
        "gemini",
    )


def _build_prompt(analysis: ProjectAnalysis, prompt_files=None) -> str:
    files = analysis.files if prompt_files is None else prompt_files
    compact_files = [
        {
            "path": file.path,
            "language": file.language,
            "imports": file.imports[:20],
            "symbols": [
                {"name": symbol.name, "kind": symbol.kind, "line": symbol.line}
                for symbol in file.symbols[:50]
            ],
        }
        for file in files
    ]
    return f"""
You are CodeAtlas. Analyze this project structure and Tree-sitter symbol map.
Return only valid JSON with these keys:
- summary: Turkish architecture summary, concise but useful.
- components: array of objects with file and description fields. Explain what important files/functions/classes do in Turkish.
- mermaid: a valid Mermaid graph TD diagram that shows high-level architecture and relationships.

Do not wrap the JSON in markdown. Do not invent files that are not present.
Mermaid requirements:
- Start with exactly: graph TD
- Use only ASCII node ids like A, B, API, DB, SERVICE_1.
- Put node labels in double quoted square brackets, for example API["API Layer"].
- Use edge labels only with pipe syntax, for example API -->|uses| DB.
- Do not use quoted subgraph titles like subgraph "Backend"; use subgraph BACKEND["Backend"] instead.
- Do not include markdown fences around the Mermaid text.

Project name: {analysis.project_name}

File tree:
{analysis.file_tree}

Tree-sitter analysis JSON:
{json.dumps(compact_files, ensure_ascii=False)}
""".strip()


def _extract_text(data: dict) -> str:
    candidates = data.get("candidates") or []
    if not candidates:
        return ""
    parts = candidates[0].get("content", {}).get("parts", [])
    return "".join(part.get("text", "") for part in parts)


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, error.HTTPError):
        return exc.code in _RETRYABLE_HTTP_STATUSES
    return isinstance(exc, (error.URLError, TimeoutError))


def _is_rate_limit_error(exc: Exception) -> bool:
    return isinstance(exc, error.HTTPError) and exc.code == 429


def _sleep_before_retry(attempt: int, exc: Exception) -> None:
    retry_after = _retry_after_seconds(exc)
    if retry_after is not None:
        delay = retry_after
    else:
        backoff_seconds = max(0.0, settings.gemini_retry_backoff_seconds)
        delay = backoff_seconds * (2 ** (attempt - 1))
        if delay > 0:
            delay += random.uniform(0, delay * 0.25)

    if delay > 0:
        time.sleep(delay)


def _cooldown_seconds(exc: Exception) -> float:
    retry_after = _retry_after_seconds(exc)
    configured = max(0.0, settings.gemini_rate_limit_cooldown_seconds)
    if retry_after is None:
        return configured
    return max(configured, retry_after)


def _retry_after_seconds(exc: Exception) -> float | None:
    if not isinstance(exc, error.HTTPError):
        return None

    retry_after = exc.headers.get("Retry-After")
    if retry_after is None:
        return None

    try:
        return max(0.0, float(retry_after))
    except ValueError:
        pass

    try:
        retry_at = parsedate_to_datetime(retry_after)
    except (TypeError, ValueError, IndexError, OverflowError):
        return None

    delay = retry_at.timestamp() - time.time()
    return max(0.0, delay)


def _extract_json_object(text: str) -> dict | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def _fallback_components(analysis: ProjectAnalysis) -> list[dict[str, str]]:
    components: list[dict[str, str]] = []
    for file in analysis.files:
        symbols = ", ".join(symbol.name for symbol in file.symbols[:8]) or "sembol bulunamadı"
        components.append(
            {
                "file": file.path,
                "description": f"{file.language} dosyası. Öne çıkan semboller: {symbols}.",
            }
        )
    return components


def _normalize_components(value, fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return fallback
    components: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        file = item.get("file")
        description = item.get("description")
        if file and description:
            components.append({"file": str(file), "description": str(description)})
    return components or fallback
