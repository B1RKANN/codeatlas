from tree_sitter import Language, Parser
import tree_sitter_javascript
import tree_sitter_python
import tree_sitter_typescript

from app.services.analysis.models import AnalyzedFile, ProjectAnalysis, ProjectSnapshot, Symbol


IMPORT_NODE_TYPES = {
    "import_statement",
    "import_from_statement",
    "future_import_statement",
    "import_declaration",
}

FUNCTION_NODE_TYPES = {
    "function_definition",
    "function_declaration",
    "method_definition",
    "function_signature",
}

CLASS_NODE_TYPES = {
    "class_definition",
    "class_declaration",
}


def analyze_project(snapshot: ProjectSnapshot) -> ProjectAnalysis:
    files = [_analyze_source_file(source_file) for source_file in snapshot.source_files]
    return ProjectAnalysis(
        project_name=snapshot.project_name,
        file_tree=_build_file_tree(snapshot.paths),
        files=files,
    )


def _analyze_source_file(source_file) -> AnalyzedFile:
    parser = _get_parser(source_file.language)
    tree = parser.parse(source_file.content)
    imports: list[str] = []
    symbols: list[Symbol] = []

    def walk(node):
        if node.type in IMPORT_NODE_TYPES:
            imports.append(_node_text(source_file.content, node).strip())

        if node.type in FUNCTION_NODE_TYPES:
            name = _node_name(source_file.content, node)
            if name:
                symbols.append(Symbol(name=name, kind="function", line=node.start_point[0] + 1))

        if node.type in CLASS_NODE_TYPES:
            name = _node_name(source_file.content, node)
            if name:
                symbols.append(Symbol(name=name, kind="class", line=node.start_point[0] + 1))

        if node.type == "variable_declarator" and _contains_function_value(node):
            name = _node_name(source_file.content, node)
            if name:
                symbols.append(Symbol(name=name, kind="function", line=node.start_point[0] + 1))

        for child in node.children:
            walk(child)

    walk(tree.root_node)
    return AnalyzedFile(
        path=source_file.path,
        language=source_file.language,
        imports=_dedupe(imports),
        symbols=_dedupe_symbols(symbols),
    )


def _get_parser(language: str) -> Parser:
    parser = Parser()
    parser.language = _get_language(language)
    return parser


def _get_language(language: str) -> Language:
    if language == "python":
        return Language(tree_sitter_python.language())
    if language == "javascript":
        return Language(tree_sitter_javascript.language())
    if language == "typescript":
        return Language(tree_sitter_typescript.language_typescript())
    if language == "tsx":
        return Language(tree_sitter_typescript.language_tsx())
    raise ValueError(f"Unsupported language: {language}")


def _node_name(content: bytes, node) -> str | None:
    name_node = node.child_by_field_name("name")
    if name_node is not None:
        return _node_text(content, name_node).strip()

    for child in node.children:
        if child.type in {"identifier", "property_identifier", "type_identifier"}:
            return _node_text(content, child).strip()
    return None


def _contains_function_value(node) -> bool:
    value_node = node.child_by_field_name("value")
    if value_node is None:
        return False
    return value_node.type in {"arrow_function", "function", "function_expression"}


def _node_text(content: bytes, node) -> str:
    return content[node.start_byte : node.end_byte].decode("utf-8", errors="replace")


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


def _dedupe_symbols(symbols: list[Symbol]) -> list[Symbol]:
    seen: set[tuple[str, str, int]] = set()
    deduped: list[Symbol] = []
    for symbol in symbols:
        key = (symbol.name, symbol.kind, symbol.line)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(symbol)
    return deduped


def _build_file_tree(paths: list[str]) -> str:
    tree: dict[str, dict] = {}
    for path in paths:
        cursor = tree
        for part in path.split("/"):
            cursor = cursor.setdefault(part, {})

    lines: list[str] = []

    def render(branch: dict[str, dict], depth: int = 0) -> None:
        for name in sorted(branch):
            lines.append(f"{'  ' * depth}{name}")
            render(branch[name], depth + 1)

    render(tree)
    return "\n".join(lines)
