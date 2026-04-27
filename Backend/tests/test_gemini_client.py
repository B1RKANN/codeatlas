import io
import json
import unittest
from contextlib import ExitStack
from unittest import mock
from urllib import error

from app.services.analysis import gemini_client
from app.services.analysis.models import AnalyzedFile, ProjectAnalysis, Symbol


class FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False

    def read(self) -> bytes:
        return self._body


def make_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        project_name="sample",
        file_tree="sample/app.py",
        files=[
            AnalyzedFile(
                path="app.py",
                language="python",
                imports=[],
                symbols=[Symbol(name="main", kind="function", line=1)],
            )
        ],
    )


def make_http_error(status: int, message: str, headers: dict[str, str] | None = None) -> error.HTTPError:
    return error.HTTPError(
        url="https://generativelanguage.googleapis.com/test",
        code=status,
        msg=message,
        hdrs=headers or {},
        fp=io.BytesIO(message.encode("utf-8")),
    )


class GeminiClientTests(unittest.TestCase):
    def run_with_settings(self, urlopen_side_effect):
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_api_key", "test-key"))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_model", "gemini-test"))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_timeout_seconds", 5))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_max_retries", 2))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_retry_backoff_seconds", 0))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_rate_limit_cooldown_seconds", 60))
            stack.enter_context(mock.patch.object(gemini_client, "_rate_limited_until", 0.0))
            sleep_mock = stack.enter_context(mock.patch.object(gemini_client.time, "sleep"))
            urlopen_mock = stack.enter_context(
                mock.patch.object(gemini_client.request, "urlopen", side_effect=urlopen_side_effect)
            )

            result = gemini_client.summarize_with_gemini(make_analysis())

        return result, urlopen_mock, sleep_mock

    def test_retries_503_then_returns_gemini_result(self):
        gemini_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "summary": "Gemini summary",
                                        "components": [
                                            {"file": "app.py", "description": "Entry point"}
                                        ],
                                        "mermaid": "graph TD\n  A[\"App\"]",
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }

        result, urlopen_mock, sleep_mock = self.run_with_settings(
            [make_http_error(503, "Service Unavailable"), FakeResponse(gemini_payload)]
        )

        summary, components, mermaid, warnings, provider = result
        self.assertEqual(summary, "Gemini summary")
        self.assertEqual(components, [{"file": "app.py", "description": "Entry point"}])
        self.assertEqual(mermaid, "graph TD\n  A[\"App\"]")
        self.assertEqual(warnings, [])
        self.assertEqual(provider, "gemini")
        self.assertEqual(urlopen_mock.call_count, 2)
        sleep_mock.assert_not_called()

    def test_returns_fallback_after_retryable_errors_are_exhausted(self):
        result, urlopen_mock, _ = self.run_with_settings(
            [
                make_http_error(503, "Service Unavailable"),
                make_http_error(503, "Service Unavailable"),
                make_http_error(503, "Service Unavailable"),
            ]
        )

        summary, components, mermaid, warnings, provider = result
        self.assertIn("sample projesinde 1 desteklenen kaynak dosya", summary)
        self.assertEqual(components[0]["file"], "app.py")
        self.assertTrue(mermaid.startswith("graph TD"))
        self.assertEqual(provider, None)
        self.assertEqual(urlopen_mock.call_count, 3)
        self.assertEqual(len(warnings), 1)
        self.assertIn("Gemini request failed after 3 attempt(s)", warnings[0])
        self.assertIn("HTTP Error 503", warnings[0])

    def test_uses_retry_after_header_before_retry(self):
        gemini_payload = {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": json.dumps(
                                    {
                                        "summary": "Gemini summary",
                                        "components": [],
                                        "mermaid": "graph TD\n  A[\"App\"]",
                                    }
                                )
                            }
                        ]
                    }
                }
            ]
        }

        result, urlopen_mock, sleep_mock = self.run_with_settings(
            [make_http_error(429, "Too Many Requests", {"Retry-After": "7"}), FakeResponse(gemini_payload)]
        )

        _, _, _, warnings, provider = result
        self.assertEqual(warnings, [])
        self.assertEqual(provider, "gemini")
        self.assertEqual(urlopen_mock.call_count, 2)
        sleep_mock.assert_called_once_with(7.0)

    def test_skips_gemini_during_rate_limit_cooldown(self):
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_api_key", "test-key"))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_model", "gemini-test"))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_timeout_seconds", 5))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_max_retries", 2))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_retry_backoff_seconds", 0))
            stack.enter_context(mock.patch.object(gemini_client.settings, "gemini_rate_limit_cooldown_seconds", 60))
            stack.enter_context(mock.patch.object(gemini_client, "_rate_limited_until", 0.0))
            stack.enter_context(mock.patch.object(gemini_client.time, "sleep"))
            urlopen_mock = stack.enter_context(
                mock.patch.object(
                    gemini_client.request,
                    "urlopen",
                    side_effect=[
                        make_http_error(429, "Too Many Requests"),
                        make_http_error(429, "Too Many Requests"),
                        make_http_error(429, "Too Many Requests"),
                    ],
                )
            )

            first_result = gemini_client.summarize_with_gemini(make_analysis())
            second_result = gemini_client.summarize_with_gemini(make_analysis())

        self.assertEqual(urlopen_mock.call_count, 3)
        self.assertIn("Gemini request failed after 3 attempt(s)", first_result[3][0])
        self.assertIn("Gemini rate limit is cooling down", second_result[3][0])
        self.assertEqual(second_result[4], None)


if __name__ == "__main__":
    unittest.main()
