import re
from pypdf import PdfReader

CHAPTER_TOC_REGEX = re.compile(r"(Chapter-\s*[IVXLC]+)\s+(.+?)\.+\s*(\d+)")
SECTION_TOC_REGEX = re.compile(r"^\s*([A-Z]\.)\s+(.*?)\s+(\d+)\s*$", re.MULTILINE)
SECTION_HEADER_RE = re.compile(r"^\s*([A-Z])\.\s+(.+)$", re.MULTILINE)


def extract_pdf_pages(file_path: str):
    reader = PdfReader(file_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages.append({"page_no": i + 1, "text": text.strip()})

    return pages


def get_toc_text(pages, max_pages=2):
    toc_text = ""
    for page in pages[:max_pages]:
        toc_text += page["text"] + "\n"
    return toc_text


def parse_chapters_from_toc(toc_text):
    chapters = []
    for match in CHAPTER_TOC_REGEX.finditer(toc_text):
        chapters.append(
            {
                "chapter_id": match.group(1).strip(),
                "chapter_title": match.group(2).strip(),
                "start_page": int(match.group(3)),
            }
        )
    return chapters


def is_valid_section(section_id: str, title: str) -> bool:
    if len(title.strip()) < 5:
        return False

    if title.lower().strip() in {"no", "page", "sl"}:
        return False

    return True


def clean_section_title(title: str) -> str:
    title = re.sub(r"\.{3,}", "", title)
    return title.strip()


def parse_sections_from_toc(toc_text):
    sections = []

    for match in SECTION_TOC_REGEX.finditer(toc_text):
        section_id = match.group(1)
        section_title = match.group(2).strip()
        start_page = int(match.group(3))

        if not is_valid_section(section_id, section_title):
            continue

        sections.append(
            {
                "section_id": section_id,
                "section_title": section_title,
                "start_page": start_page,
            }
        )

    for sec in sections:
        sec["section_title"] = clean_section_title(sec["section_title"])

    return sections


def build_page_map(pages):
    return {p["page_no"]: p["text"] for p in pages}


def add_chapter_ranges(chapters, total_pages):
    for i, ch in enumerate(chapters):
        if i + 1 < len(chapters):
            end = chapters[i + 1]["start_page"] - 1
        else:
            end = total_pages
        ch["end_page"] = end
    return chapters


def attach_sections_to_chapters(chapters, sections):
    for ch in chapters:
        ch["sections"] = []

    for sec in sections:
        for ch in chapters:
            if ch["start_page"] <= sec["start_page"] <= ch["end_page"]:
                ch["sections"].append(sec)
                break
    return chapters


def add_section_ranges(chapter, total_pages):
    sections = sorted(
        chapter["sections"], key=lambda s: (s["start_page"], s["section_id"])
    )

    for i, sec in enumerate(sections):
        start = sec["start_page"]
        end = chapter.get("end_page", total_pages)

        for j in range(i + 1, len(sections)):
            next_start = sections[j]["start_page"]
            if next_start > start:
                end = next_start - 1
                break

        sec["end_page"] = end

    chapter["sections"] = sections
    return chapter


def split_sections_within_chapter(chapter, page_map, max_content_page):
    sections = chapter["sections"]
    if not sections:
        chapter_text = ""
        end_page = min(chapter["end_page"], max_content_page)
        for p in range(chapter["start_page"], end_page + 1):
            chapter_text += page_map.get(p, "") + "\n"
        chapter["sections"] = [
            {
                "section_id": "CHAPTER",
                "section_title": chapter["chapter_title"],
                "start_page": chapter["start_page"],
                "end_page": end_page,
                "text": chapter_text.strip(),
            }
        ]
        return chapter

    chapter_text = ""
    end_page = min(chapter["end_page"], max_content_page)
    for p in range(chapter["start_page"], end_page + 1):
        chapter_text += page_map.get(p, "") + "\n"

    headers = list(SECTION_HEADER_RE.finditer(chapter_text))
    if not headers:
        return chapter

    header_blocks = []
    for i, m in enumerate(headers):
        start = m.start()
        end = headers[i + 1].start() if i + 1 < len(headers) else len(chapter_text)
        section_id = f"{m.group(1)}."
        header_blocks.append(
            {
                "section_id": section_id,
                "section_title": m.group(2).strip(),
                "text": chapter_text[start:end].strip(),
            }
        )

    existing_by_id = {s["section_id"]: s for s in sections}
    rebuilt_sections = []
    for hb in header_blocks:
        sec = existing_by_id.get(hb["section_id"])
        if sec is None:
            sec = {
                "section_id": hb["section_id"],
                "section_title": hb["section_title"],
                "start_page": chapter["start_page"],
                "end_page": chapter["end_page"],
            }
        sec["text"] = hb["text"]
        rebuilt_sections.append(sec)

    chapter["sections"] = rebuilt_sections
    return chapter
