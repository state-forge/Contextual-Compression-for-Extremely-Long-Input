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
            "chapter_title" : m.group(2),
            "page_start" : pg,
            "page_end" : None,
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
            "section_title" : m.group(2),
            "page_start" : pg,
            "page_end" : None,
            "raw_text" : ""
        })
        return curr_chap[-1]
    
    def close_curr_section(pg, curr_sec):
        curr_sec["page_end"] = pg
        return
    
    for page in pdf.pages:
        for line in page.extract_text().splitlines():
            m = is_chapter_name(line)
            if m:
                if current_chapter is not None:
                    if line == page.extract_text().splitlines()[0]:
                        close_curr_chap(page.page_number - 1, current_chapter)
                    else:
                        close_curr_chap(page.page_number, current_chapter)
                current_chapter = create_chapter(m, page.page_number)
                continue
            m = is_section_name(line)
            if m:
                if current_section is not None:
                    if line == page.extract_text().splitlines()[0]:
                        close_curr_section(page.page_number - 1, current_section)
                    else:
                        close_curr_section(page.page_number, current_section)
                current_section = create_section(m, page.page_number, current_chapter)
                continue
            current_section["raw_text"] += line
    close_curr_section(pdf.pages[-1].page_number, current_section)   
    close_curr_chap(pdf.pages[-1].page_number, current_chapter)             

else :
    print("Incorrect File Path.\nEnter a valid File Path.")
