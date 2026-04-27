from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceFile:
    path: str
    content: bytes
    language: str


@dataclass(frozen=True)
class Symbol:
    name: str
    kind: str
    line: int


@dataclass(frozen=True)
class AnalyzedFile:
    path: str
    language: str
    imports: list[str] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)


@dataclass(frozen=True)
class ProjectSnapshot:
    project_name: str
    paths: list[str]
    source_files: list[SourceFile]


@dataclass(frozen=True)
class ProjectAnalysis:
    project_name: str
    file_tree: str
    files: list[AnalyzedFile]
