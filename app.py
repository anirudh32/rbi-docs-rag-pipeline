import json
from pathlib import Path

from src.ingest import (
    extract_pdf_pages,
    get_toc_text,
    parse_chapters_from_toc,
    parse_sections_from_toc,
    build_page_map,
    add_chapter_ranges,
    attach_sections_to_chapters,
    add_section_ranges,
    split_sections_within_chapter,
)
from src.chunk import build_chunks
from src.qa import build_qa_report


CONFIG_PATH = Path("config.json")


def process_document(doc_cfg):
    pdf_path = Path(doc_cfg["pdf_path"])
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    annex_start_page = int(doc_cfg.get("annex_start_page", 10**9))
    max_content_page = annex_start_page - 1

    pages = extract_pdf_pages(str(pdf_path))
    toc_text = get_toc_text(pages)
    chapters = parse_chapters_from_toc(toc_text)
    sections = parse_sections_from_toc(toc_text)
    page_map = build_page_map(pages)

    add_chapter_ranges(chapters, min(len(pages), max_content_page))
    attach_sections_to_chapters(chapters, sections)

    for ch in chapters:
        add_section_ranges(ch, min(len(pages), max_content_page))
        split_sections_within_chapter(ch, page_map, max_content_page)

    doc_meta = {
        "id": doc_cfg["id"],
        "title": doc_cfg["title"],
        "regulator": doc_cfg["regulator"],
        "jurisdiction": doc_cfg["jurisdiction"],
        "pdf_name": pdf_path.name,
    }

    chunks = build_chunks(chapters, page_map, doc_meta, max_content_page)
    qa_report = build_qa_report(chunks)

    out_dir = Path("data") / "processed" / doc_cfg["id"]
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "chunks.json", "w", encoding="utf-8") as f:
        json.dump(chunks, f, ensure_ascii=False, indent=2)

    with open(out_dir / "qa_report.json", "w", encoding="utf-8") as f:
        json.dump(qa_report, f, ensure_ascii=False, indent=2)

    print(f"{doc_cfg['id']}: wrote {len(chunks)} chunks to {out_dir / 'chunks.json'}")


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    for doc in cfg.get("documents", []):
        process_document(doc)


if __name__ == "__main__":
    main()
