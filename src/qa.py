def build_qa_report(chunks):
    report = {
        "total_chunks": len(chunks),
        "duplicate_ids": [],
        "chapters": {},
        "sections": {},
    }

    seen = set()
    for c in chunks:
        cid = c["id"]
        if cid in seen:
            report["duplicate_ids"].append(cid)
        else:
            seen.add(cid)

    def add_range_stats(key, nums, container):
        if not nums:
            return
        nums = sorted(set(nums))
        missing = [n for n in range(nums[0], nums[-1] + 1) if n not in nums]
        container[key] = {
            "min": nums[0],
            "max": nums[-1],
            "count": len(nums),
            "missing": missing,
        }

    chapter_nums = {}
    section_nums = {}
    for c in chunks:
        ch = c["metadata"]["chapter_id"]
        sec = c["metadata"]["section_id"]
        num = int(c["metadata"]["clause_number"])
        chapter_nums.setdefault(ch, []).append(num)
        section_nums.setdefault((ch, sec), []).append(num)

    for ch, nums in chapter_nums.items():
        add_range_stats(ch, nums, report["chapters"])

    for (ch, sec), nums in section_nums.items():
        add_range_stats(f"{ch}:{sec}", nums, report["sections"])

    return report
