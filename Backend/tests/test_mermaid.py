import unittest

from app.services.analysis.mermaid import build_fallback_mermaid, select_mermaid
from app.services.analysis.models import AnalyzedFile, ProjectAnalysis, Symbol


def make_analysis() -> ProjectAnalysis:
    return ProjectAnalysis(
        project_name="sample",
        file_tree="sample\n  app.py\n  services\n    auth.py\n    users.py",
        files=[
            AnalyzedFile(
                path="app.py",
                language="python",
                imports=["from services.auth import login"],
                symbols=[Symbol("main", "function", 1), Symbol("create_app", "function", 4)],
            ),
            AnalyzedFile(
                path="services/auth.py",
                language="python",
                imports=["from services.users import UserService"],
                symbols=[Symbol("AuthService", "class", 3), Symbol("login", "function", 12)],
            ),
            AnalyzedFile(
                path="services/users.py",
                language="python",
                imports=[],
                symbols=[Symbol("UserService", "class", 2), Symbol("get_user", "function", 8)],
            ),
        ],
    )


class MermaidTests(unittest.TestCase):
    def test_fallback_mermaid_includes_modules_symbols_and_imports(self):
        diagram = build_fallback_mermaid(make_analysis())

        self.assertTrue(diagram.startswith("flowchart LR"))
        self.assertIn("source[\"High-Level Architecture\"]", diagram)
        self.assertIn("subgraph group_1[\"services\"]", diagram)
        self.assertIn("file_1[\"auth.py\"]", diagram)
        self.assertIn("main()", diagram)
        self.assertIn("AuthService", diagram)
        self.assertIn("-.->", diagram)
        self.assertNotIn("-->|tanımlar|", diagram)
        self.assertNotIn("-->|dosya|", diagram)

    def test_select_mermaid_replaces_oversimplified_generated_diagram(self):
        diagram, warning = select_mermaid(make_analysis(), "graph TD\n  A[\"App\"]")

        self.assertIsNotNone(warning)
        self.assertIn("High-Level Architecture", diagram)
        self.assertIn("-.->", diagram)

    def test_select_mermaid_replaces_diagram_without_file_references(self):
        generated = """graph TD
  A[\"Backend\"]
  B[\"App\"]
  C[\"Components\"]
  D[\"Notification\"]
  E[\"Tenant Context\"]
  F[\"Anasayfa\"]
  G[\"Yukilanlari\"]
  H[\"Auth\"]
  I[\"Users\"]
  J[\"Database\"]
  A -->|bileşenleri birleştirir| B
  B -->|bileşenleri birleştirir| C
  C -->|bildirimleri yönetir| D
  C -->|tenant bilgilerini yönetir| E
  C -->|ana sayfayı gösterir| F
  C -->|yük ilanlarını listeler| G
  B -->|kimlik doğrular| H
  H -->|kullanıcıları yönetir| I
  I -->|veri saklar| J
"""

        diagram, warning = select_mermaid(make_analysis(), generated)

        self.assertIsNotNone(warning)
        self.assertIn("gerçek dosya adlarını", warning)
        self.assertIn("auth.py", diagram)


if __name__ == "__main__":
    unittest.main()
