"""PDF evidence → Observations.

Text is extracted with pdfplumber. A document observes every resource it names (resource-id pattern) and
every resource whose external reference it carries according to a data-catalog link (e.g. statement
NST-2026-0718-1842 ↔ export_1842). The record is PRESENT; its identifiers are the document's identifiers.
Documents that name no resource (e.g. the legal retention register, which lists only order references)
produce no observation.
"""

import re
from dataclasses import dataclass
from pathlib import Path

import pdfplumber

from evidence.common import files_under
from evidence.model import RESOURCE_RE, Category, Observation, State, text_identifying_fields, link_keys_from, resource_prefix, system_for

CATEGORY_BY_PREFIX = {
    "account": Category.USER_PROFILE,
    "search": Category.SEARCH_INDEX_ENTRY,
    "export": Category.USER_EXPORT,
    "audit_record": Category.SECURITY_AUDIT_LOG,
    "legal_hold": Category.LEGAL_HOLD_RECORD,
    "analytics": Category.ANALYTICS_PROFILE,
    "marketing": Category.MARKETING_PROFILE,
}


def pdf_text(path):
    with pdfplumber.open(path) as pdf:
        return "\n".join(page.extract_text() or "" for page in pdf.pages)


def _category(prefix, text):
    if prefix == "support":
        return Category.SUPPORT_ATTACHMENT if re.search(r"attachment", text, re.I) else Category.SUPPORT_MESSAGE
    return CATEGORY_BY_PREFIX.get(prefix)


@dataclass(frozen=True)
class VisualText:
    text: str
    complete: bool


def page_texts(ef, visual_reader=None, render_dir=None, issues=None):
    """Render weak/blank extraction for inspection; never assume a blank PDF."""
    from evidence.ledger import ReferenceIssue
    with pdfplumber.open(ef.path) as pdf:
        for number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if len(re.sub(r"\s", "", text)) < 20 or text.count("\ufffd") > 3:
                destination = Path(render_dir) if render_dir else ef.path.parents[3] / "diagnostics/visual_review"
                if destination.resolve().is_relative_to(ef.path.parents[2].resolve()):
                    raise ValueError("Rendered evidence must remain outside the dataset")
                destination.mkdir(parents=True, exist_ok=True)
                path = destination / f"{ef.file_id}-page-{number}.png"
                page.to_image(resolution=120).save(path, format="PNG")
                answer = visual_reader(ef, number, path) if visual_reader is not None else None
                if not isinstance(answer, VisualText) or not answer.complete or not answer.text.strip():
                    if issues is not None:
                        issues.append(ReferenceIssue(ef.file_id, f"page:{number}", "visual_review_required", captured_at=ef.captured_at))
                    continue
                text = answer.text
            yield number, text


def load(manifest, links=(), issues=None, visual_reader=None, render_dir=None):
    observations = []
    for ef in files_under(manifest, "documents", {".pdf"}):
        pages = tuple(page_texts(ef, visual_reader, render_dir, issues))
        document_context = "\n".join(text for _, text in pages)
        for number, text in pages:
            named = set(RESOURCE_RE.findall(text))
            named |= {link.resource_id for link in links if link.label != link.resource_id and link.label and link.label in text}
            keys = link_keys_from(text)
            classified = {rid for rid in named if _category(resource_prefix(rid), document_context) is not None}
            if not classified and issues is not None:
                from evidence.ledger import ReferenceIssue
                refs_seen = False
                for line_number, line in enumerate(text.splitlines(), 1):
                    refs = sorted(set(re.findall(r"\b[A-Z]{2,12}-[A-Z0-9]+(?:-[A-Z0-9]+)*\b", line)))
                    for ref in refs:
                        refs_seen = True
                        issues.append(ReferenceIssue(ef.file_id, f"page:{number}/line:{line_number}", "external_document_reference",
                            ref, link_keys_from(line), ef.captured_at, text_identifying_fields(line)))
                if not refs_seen and keys:
                    issues.append(ReferenceIssue(ef.file_id, f"page:{number}", "external_document_reference", "", keys,
                        ef.captured_at, text_identifying_fields(text)))
            if issues is not None:
                from evidence.ledger import ReferenceIssue
                issues.extend(ReferenceIssue(ef.file_id, f"page:{number}", "unclassified_document_reference", rid,
                    keys, ef.captured_at) for rid in sorted(named - classified))
            for rid in sorted(named):
                category = _category(resource_prefix(rid), document_context)
                if category is None:
                    continue
                state = State.IDENTIFIABLE if category in (Category.ANALYTICS_PROFILE, Category.SUPPORT_MESSAGE) else State.PRESENT
                observations.append(Observation(ef.file_id, ef.captured_at, ef.captured_at, system_for(rid), rid,
                                                category, state, keys, frozenset(named - {rid}),
                                                source=f"{ef.path.name}:pdf", identifying_fields=text_identifying_fields(text),
                                                source_location=f"page:{number}", observation_time_basis="capture_time"))
    return observations
