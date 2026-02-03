import re

CLAUSE_RE = re.compile(r"^\s*(\d+)\.\s+", re.MULTILINE)


def roman_to_int(roman: str) -> int:
    roman = roman.upper()
    values = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100, "D": 500, "M": 1000}
    total = 0
    prev = 0
    for ch in reversed(roman):
        val = values.get(ch, 0)
        if val < prev:
            total -= val
        else:
            total += val
            prev = val
    return total


def clean_text(text):
    text = re.sub(r"^\s*\d+\s*$", "", text, flags=re.MULTILINE)
    return text


def is_valid_clause_number(num: str) -> bool:
    if len(num) >= 4 and num.startswith(("19", "20")):
        return False
    n = int(num)
    if n <= 0 or n > 500:
        return False
    return True


def split_into_clauses(text):
    text = clean_text(text)
    matches = list(CLAUSE_RE.finditer(text))
    if not matches:
        return []

    clauses = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        clause_number = m.group(1)
        if not is_valid_clause_number(clause_number):
            continue
        clause_text = text[start:end].strip()
        clauses.append({"number": clause_number, "text": clause_text})
    return clauses


def has_subclauses(text):
    return bool(re.search(r"\(\s*[ivx]+\s*\)|\(\s*[a-z]\s*\)", text, re.IGNORECASE))


def extract_section_text(section, page_map, max_content_page):
    if "text" in section:
        return section["text"].strip()

    text = ""
    end_page = min(section["end_page"], max_content_page)
    for p in range(section["start_page"], end_page + 1):
        text += page_map.get(p, "") + "\n"
    return text.strip()


def build_chunks(chapters, page_map, doc_meta, max_content_page):
    chunks = []

    doc_title = doc_meta["title"]
    regulator = doc_meta["regulator"]
    jurisdiction = doc_meta["jurisdiction"]
    pdf_name = doc_meta["pdf_name"]

    for ch in chapters:
        chapter_id = ch["chapter_id"]
        chapter_title = ch["chapter_title"]

        roman = chapter_id.split("-")[-1]
        chapter_num = roman_to_int(roman)
        chapter_key = f"ch{chapter_num}" if chapter_num > 0 else chapter_id.lower()

        for sec in ch["sections"]:
            section_id = sec["section_id"].replace(".", "")
            section_title = sec["section_title"]

            section_text = extract_section_text(sec, page_map, max_content_page)
            clauses = split_into_clauses(section_text)

            for clause in clauses:
                clause_number = clause["number"]
                clause_text = clause["text"]
                chunk_id = f"rbi_cb_gov_{chapter_key}_sec{section_id}_clause{clause_number}"

                chunks.append(
                    {
                        "id": chunk_id,
                        "text": clause_text,
                        "metadata": {
                            "doc_title": doc_title,
                            "regulator": regulator,
                            "jurisdiction": jurisdiction,
                            "chapter_id": chapter_id,
                            "chapter_title": chapter_title,
                            "section_id": section_id,
                            "section_title": section_title,
                            "clause_number": clause_number,
                            "has_subclauses": has_subclauses(clause_text),
                            "page_start": sec["start_page"],
                            "page_end": sec["end_page"],
                            "source": {
                                "pdf": pdf_name,
                                "page_range": [sec["start_page"], sec["end_page"]],
                            },
                        },
                    }
                )

    return chunks
