"""Data models for the patent downloader."""

from dataclasses import dataclass


@dataclass
class PatentInfo:
    """Information about a patent."""

    patent_number: str
    title: str
    inventors: list[str]
    assignee: str
    publication_date: str
    abstract: str
    url: str | None = None
    pdf_url: str | None = None


@dataclass
class DownloadResult:
    """Result of a patent download operation."""

    patent_number: str
    success: bool
    file_path: str | None = None
    error_message: str | None = None


@dataclass
class SearchResult:
    """Result of a patent search."""

    patents: list[PatentInfo]
    total_count: int
    query: str
