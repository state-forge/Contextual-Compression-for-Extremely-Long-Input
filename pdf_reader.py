import pdfplumber as pp
import re
import json
from pathlib import Path


file_path = input("Enter the File Path : ")

if Path(file_path).is_file():

    pdf = pp.open(file_path)

    doc_struct = {
        "doc_id" : Path(file_path).stem,
        "metadata" : pdf.metadata,
        "chapters" : []
    }

    def is_chapter_name(line):
        return re.match(r"^CHAPTER\s*(\d+)((?:\s+.*))?$", line, re.IGNORECASE)
    
    def create_chapter(m, pg):
        doc_struct["chapters"].append({
            "chapter_id" : m.group(1),
            "chapter_title" : m.group(2).strip(),
            "page_start" : pg,
            "page_end" : None,
            "chapter_text" : "",
            "sections" : []
        })
        return doc_struct["chapters"][-1]
    
    current_chapter = None
    current_section = None

    def close_curr_chap(pg, curr_chap):
        curr_chap["page_end"] = pg
        return
    
    def is_section_name(line):
        return re.match(r"^(\d+(?:\.\d)+)\s+(.*)$", line)
    
    def create_section(m, pg, curr_chap):
        curr_chap["sections"].append({
            "section_id" : m.group(1),
            "section_title" : m.group(2).strip(),
            "page_start" : pg,
            "page_end" : None,
            "raw_text" : ""
        })
        return curr_chap["sections"][-1]
    
    def close_curr_section(pg, curr_sec):
        curr_sec["page_end"] = pg
        return
    
    for page in pdf.pages:
        text = page.extract_text()
        if text is None:
            continue
        lines = text.splitlines()
        for idx, line in enumerate(lines):
                line = line.strip()
                m = is_chapter_name(line)
                if m:
                    if current_chapter is not None:
                        if idx == 0:
                            if current_section is not None:
                                close_curr_section(page.page_number - 1, current_section)
                                current_section = None
                            close_curr_chap(page.page_number - 1, current_chapter)
                            
                        else:
                            if current_section is not None:
                                close_curr_section(page.page_number, current_section)
                                current_section = None
                            close_curr_chap(page.page_number, current_chapter)
                            
                    current_chapter = create_chapter(m, page.page_number)
                    continue
                m = is_section_name(line)
                if m:
                    if current_section is not None:
                        if idx == 0:
                            close_curr_section(page.page_number - 1, current_section)
                        else:
                            close_curr_section(page.page_number, current_section)
                    current_section = create_section(m, page.page_number, current_chapter)
                    continue
                if current_chapter is not None and current_section is None:
                    current_chapter["chapter_text"] += line + "\n"
                if current_section is not None:
                    current_section["raw_text"] += line + "\n"
    if current_chapter is not None:
        if current_section is not None:
            close_curr_section(pdf.pages[-1].page_number, current_section)   
        close_curr_chap(pdf.pages[-1].page_number, current_chapter)             

else :
    print("Incorrect File Path.\nEnter a valid File Path.")