import unittest
from contextlib import ExitStack
from unittest import mock

from app.services.analysis import semantic
from app.services.analysis.models import AnalyzedFile, ProjectAnalysis, Symbol


class FakeEmbeddingModel:
    def encode(self, values, normalize_embeddings=True):
        if isinstance(values, str):
            return [1.0, 0.0]
        return [[0.1, 0.0], [0.9, 0.0], [0.2, 0.0]]


class SemanticSelectionTests(unittest.TestCase):
    def test_selects_most_relevant_files_with_embedding_model(self):
        analysis = ProjectAnalysis(
            project_name="sample",
            file_tree="sample",
            files=[
                AnalyzedFile("first.py", "python", symbols=[Symbol("first", "function", 1)]),
                AnalyzedFile("service.py", "python", symbols=[Symbol("service", "class", 1)]),
                AnalyzedFile("third.py", "python", symbols=[Symbol("third", "function", 1)]),
            ],
        )

        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(semantic.settings, "semantic_analysis_enabled", True))
            stack.enter_context(mock.patch.object(semantic.settings, "semantic_max_prompt_files", 2))
            stack.enter_context(mock.patch.object(semantic, "_get_model", return_value=FakeEmbeddingModel()))

            files, warnings = semantic.select_prompt_files(analysis)

        self.assertEqual([file.path for file in files], ["service.py", "third.py"])
        self.assertEqual(warnings, [])

    def test_does_not_load_model_when_project_fits_prompt_limit(self):
        analysis = ProjectAnalysis(
            project_name="sample",
            file_tree="sample",
            files=[AnalyzedFile("app.py", "python")],
        )

        with ExitStack() as stack:
            stack.enter_context(mock.patch.object(semantic.settings, "semantic_analysis_enabled", True))
            stack.enter_context(mock.patch.object(semantic.settings, "semantic_max_prompt_files", 120))
            get_model = stack.enter_context(mock.patch.object(semantic, "_get_model"))

            files, warnings = semantic.select_prompt_files(analysis)

        self.assertEqual([file.path for file in files], ["app.py"])
        self.assertEqual(warnings, [])
        get_model.assert_not_called()


if __name__ == "__main__":
    unittest.main()
