"""Immutable rapportmodel voor Word/PDF-export (slice 57)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReportParagraph:
    text: str


@dataclass(frozen=True)
class ReportTable:
    headers: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]


@dataclass(frozen=True)
class ReportFigure:
    png_bytes: bytes
    caption: str


@dataclass(frozen=True)
class ReportSection:
    title: str
    paragraphs: tuple[ReportParagraph, ...] = ()
    tables: tuple[ReportTable, ...] = ()
    figures: tuple[ReportFigure, ...] = ()
    children: tuple[ReportSection, ...] = ()


@dataclass(frozen=True)
class ReportDocument:
    sections: tuple[ReportSection, ...]

    def section_titles(self) -> tuple[str, ...]:
        out: list[str] = []

        def walk(section: ReportSection) -> None:
            out.append(section.title)
            for child in section.children:
                walk(child)

        for section in self.sections:
            walk(section)
        return tuple(out)
