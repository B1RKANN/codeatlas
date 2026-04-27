from pydantic import BaseModel, Field


class SymbolInfo(BaseModel):
    name: str
    kind: str
    line: int


class FileAnalysis(BaseModel):
    path: str
    language: str
    imports: list[str]
    symbols: list[SymbolInfo]


class ComponentSummary(BaseModel):
    file: str
    description: str


class ProjectAnalysisResponse(BaseModel):
    project_name: str
    file_tree: str
    summary: str
    components: list[ComponentSummary]
    files: list[FileAnalysis]
    mermaid: str
    llm_provider: str | None = None
    warnings: list[str] = Field(default_factory=list)
