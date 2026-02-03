# RBI Docs RAG (Clause-Level)

This project builds a low-hallucination RAG pipeline for RBI regulatory PDFs.
The current focus is RBI Commercial Banks Governance Directions, 2025, with clause-level chunking and rich metadata for traceable retrieval.

## Goals

- Build a clause-level RAG index for RBI documents
- Minimize hallucinations by grounding answers in exact clause text
- Preserve document structure (Chapter -> Section -> Clause)
- Scale to multiple RBI PDFs with consistent processing

## What’s Done So Far

- Extracted text from RBI PDF
- Parsed TOC to get chapters/sections
- Split sections by in-text headers (A., B., C., etc.)
- Split into clause-level chunks using `1.` numbering
- Added metadata for:
  - document, regulator, jurisdiction
  - chapter/section info
  - clause number
  - page range
- Exported outputs:
  - `chunks.json`
  - `qa_report.json` (coverage + duplicates)

## Current Folder Structure

```
data/
  raw/
    rbi_governance.pdf
  processed/
    rbi_governance_2025/
      chunks.json
      qa_report.json
src/
  ingest.py
  chunk.py
  qa.py
app.py
config.json
```

## How to Run

```bash
python app.py
```

Outputs go to:

```
data/processed/rbi_governance_2025/
```

## Next Steps

- Add per-clause page range detection (not just section range)
- Add semantic validation (clause integrity checks)
- Build a retrieval pipeline (vector DB + RAG)
- Add more RBI PDFs via `config.json`

## Notes

- Clause extraction is based on `1.` numbering only
- Section headers are rebuilt from in-text headings to avoid TOC gaps

## Future Scope
- Clause-level embedding with citations
- Answering system with strict context-only responses
