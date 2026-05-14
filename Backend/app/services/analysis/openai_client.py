import json
import random
import time
from email.utils import parsedate_to_datetime
from urllib import error, request

from app.core.config import settings
from app.services.analysis.gemini_client import (
    _build_prompt,
    _fallback_components,
    _normalize_components,
)
from app.services.analysis.mermaid import build_fallback_mermaid, build_fallback_summary, select_mermaid
from app.services.analysis.models import ProjectAnalysis
from app.services.analysis.semantic import select_prompt_files


_RETRYABLE_HTTP_STATUSES = {429, 500, 502, 503, 504}


def summarize_with_gpt(
    analysis: ProjectAnalysis,
    use_nlp: bool = False,
) -> tuple[str, list[dict[str, str]], str, list[str], str | None]:
    fallback_summary = build_fallback_summary(analysis)
    fallback_components = _fallback_components(analysis)
    fallback_mermaid = build_fallback_mermaid(analysis)

    if not settings.openai_api_key:
        return (
            fallback_summary,
            fallback_components,
            fallback_mermaid,
            ["OPENAI_API_KEY is not configured; returned local Tree-sitter analysis."],
            None,
        )

    prompt_files, semantic_warnings = select_prompt_files(analysis) if use_nlp else (None, [])
    payload = {
        "model": settings.openai_model,
        "messages": [
            {
                "role": "user",
                "content": _build_prompt(analysis, prompt_files),
            }
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
    }
    req = request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    attempts = max(1, settings.openai_max_retries + 1)
    for attempt in range(1, attempts + 1):
        try:
            with request.urlopen(req, timeout=settings.openai_timeout_seconds) as response:
                data = json.loads(response.read().decode("utf-8"))
            break
        except (error.HTTPError, error.URLError, TimeoutError) as exc:
            if attempt >= attempts or not _is_retryable_error(exc):
                return (
                    fallback_summary,
                    fallback_components,
                    fallback_mermaid,
                    [
                        "OpenAI request failed after "
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
                [f"OpenAI returned invalid JSON; returned local analysis. Reason: {exc}"],
                None,
            )

    text = _extract_text(data)
    try:
        generated = json.loads(text)
    except json.JSONDecodeError:
        generated = None

    if generated is None:
        return (
            fallback_summary,
            fallback_components,
            fallback_mermaid,
            ["OpenAI returned non-JSON content; returned local analysis."],
            None,
        )

    mermaid, mermaid_warning = select_mermaid(analysis, str(generated.get("mermaid") or ""))
    warnings = semantic_warnings + ([mermaid_warning] if mermaid_warning else [])
    return (
        str(generated.get("summary") or fallback_summary),
        _normalize_components(generated.get("components"), fallback_components),
        mermaid,
        warnings,
        "gpt",
    )


def _extract_text(data: dict) -> str:
    choices = data.get("choices") or []
    if not choices:
        return ""
    message = choices[0].get("message") or {}
    return str(message.get("content") or "")


def _is_retryable_error(exc: Exception) -> bool:
    if isinstance(exc, error.HTTPError):
        return exc.code in _RETRYABLE_HTTP_STATUSES
    return isinstance(exc, (error.URLError, TimeoutError))


def _sleep_before_retry(attempt: int, exc: Exception) -> None:
    retry_after = _retry_after_seconds(exc)
    if retry_after is not None:
        delay = retry_after
    else:
        backoff_seconds = max(0.0, settings.openai_retry_backoff_seconds)
        delay = backoff_seconds * (2 ** (attempt - 1))
        if delay > 0:
            delay += random.uniform(0, delay * 0.25)

    if delay > 0:
        time.sleep(delay)


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
