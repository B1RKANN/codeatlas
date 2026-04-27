from pathlib import PurePosixPath
from zipfile import BadZipFile, ZipFile
from io import BytesIO

from app.core.config import settings
from app.services.analysis.models import ProjectSnapshot, SourceFile


LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
}

IGNORED_PARTS = {
    ".git",
    ".idea",
    ".venv",
    "build",
    "dist",
    "node_modules",
    "__pycache__",
}


def read_project_zip(filename: str, content: bytes) -> ProjectSnapshot:
    if not filename.lower().endswith(".zip"):
        raise ValueError("Only .zip project uploads are supported.")

    if len(content) > settings.analysis_max_zip_bytes:
        raise ValueError("Zip file is too large.")

    try:
        archive = ZipFile(BytesIO(content))
    except BadZipFile as exc:
        raise ValueError("Uploaded file is not a valid zip archive.") from exc

    with archive:
        entries = []
        for info in archive.infolist():
            if info.is_dir():
                continue
            safe_path = _safe_zip_path(info.filename)
            if safe_path is None or _is_ignored(safe_path):
                continue
            entries.append((info, safe_path))

        if len(entries) > settings.analysis_max_files:
            raise ValueError("Zip contains too many analyzable files.")

        total_uncompressed_size = sum(info.file_size for info, _ in entries)
        if total_uncompressed_size > settings.analysis_max_uncompressed_bytes:
            raise ValueError("Zip uncompressed size is too large.")

        paths: list[str] = []
        source_files: list[SourceFile] = []

        for info, safe_path in entries:
            if info.flag_bits & 0x1:
                raise ValueError("Encrypted zip entries are not supported.")

            paths.append(safe_path)
            extension = PurePosixPath(safe_path).suffix.lower()
            language = LANGUAGE_BY_EXTENSION.get(extension)
            if language is None:
                continue

            if info.file_size > settings.analysis_max_source_file_bytes:
                continue

            source_files.append(
                SourceFile(
                    path=safe_path,
                    content=archive.read(info),
                    language=language,
                )
            )

    if not source_files:
        raise ValueError("No supported source files were found in the zip.")

    project_name = PurePosixPath(filename).stem or "uploaded-project"
    return ProjectSnapshot(
        project_name=project_name,
        paths=sorted(paths),
        source_files=source_files,
    )


def _safe_zip_path(raw_path: str) -> str | None:
    normalized = raw_path.replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError("Zip contains unsafe paths.")
    if not path.name:
        return None
    return str(path)


def _is_ignored(path: str) -> bool:
    return any(part in IGNORED_PARTS for part in PurePosixPath(path).parts)
