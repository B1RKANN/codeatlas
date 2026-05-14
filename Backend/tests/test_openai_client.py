import io
import json
import unittest
from contextlib import ExitStack
from unittest import mock
from urllib import error

from app.services.analysis import openai_client
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
        url="https://api.openai.com/v1/chat/completions",
        code=status,
        msg=message,
        hdrs=headers or {},
        fp=io.BytesIO(message.encode("utf-8")),
    )


class OpenAIClientTests(unittest.TestCase):
    def run_with_settings(self, urlopen_side_effect):
        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(openai_client.settings, "openai_api_key", "test-key"))
            stack.enter_context(mock.patch.object(openai_client.settings, "openai_model", "gpt-4o-mini"))
            stack.enter_context(mock.patch.object(openai_client.settings, "openai_timeout_seconds", 5))
            stack.enter_context(mock.patch.object(openai_client.settings, "openai_max_retries", 2))
            stack.enter_context(mock.patch.object(openai_client.settings, "openai_retry_backoff_seconds", 0))
            sleep_mock = stack.enter_context(mock.patch.object(openai_client.time, "sleep"))
            urlopen_mock = stack.enter_context(
                mock.patch.object(openai_client.request, "urlopen", side_effect=urlopen_side_effect)
            )

            result = openai_client.summarize_with_gpt(make_analysis())

        return result, urlopen_mock, sleep_mock

    def test_returns_gpt_result(self):
        openai_payload = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps(
                            {
                                "summary": "GPT summary",
                                "components": [{"file": "app.py", "description": "Entry point"}],
                                "mermaid": "flowchart LR\n  APP[\"app.py\"]",
                            }
                        )
                    }
                }
            ]
        }

        result, urlopen_mock, sleep_mock = self.run_with_settings([FakeResponse(openai_payload)])

        summary, components, mermaid, warnings, provider = result
        self.assertEqual(summary, "GPT summary")
        self.assertEqual(components, [{"file": "app.py", "description": "Entry point"}])
        self.assertEqual(mermaid, "flowchart LR\n  APP[\"app.py\"]")
        self.assertEqual(warnings, [])
        self.assertEqual(provider, "gpt")
        self.assertEqual(urlopen_mock.call_count, 1)
        sleep_mock.assert_not_called()

        request_arg = urlopen_mock.call_args.args[0]
        payload = json.loads(request_arg.data.decode("utf-8"))
        self.assertEqual(payload["model"], "gpt-4o-mini")
        self.assertEqual(payload["response_format"], {"type": "json_object"})
        self.assertEqual(request_arg.headers["Authorization"], "Bearer test-key")

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
        self.assertTrue(mermaid.startswith("flowchart LR"))
        self.assertEqual(provider, None)
        self.assertEqual(urlopen_mock.call_count, 3)
        self.assertEqual(len(warnings), 1)
        self.assertIn("OpenAI request failed after 3 attempt(s)", warnings[0])


if __name__ == "__main__":
    unittest.main()
