import pdfplumber as pp
import re
import json
from pathlib import Path

def structurize(file_path):
    try:
        # Check if file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Check if it's a PDF file
        if not file_path.lower().endswith('.pdf'):
            raise ValueError("Input file must be a PDF document")
        
        pdf = pp.open(file_path)

        doc_struct = {
            "doc_id" : Path(file_path).stem,
            "metadata" : pdf.metadata,
            "chapters" : []
        }

        def is_chapter_name(line):
            try:
                return re.match(r"^(CHAPTER|ARTICLE|PART|SUBPART)\s*(\d+)((?:\s+.*))?$", line, re.IGNORECASE)
            except re.error:
                return None
        
        def create_chapter(m, pg):
            try:
                doc_struct["chapters"].append({
                    "chapter_id" : m.group(1),
                    "chapter_title" : m.group(2).strip(),
                    "page_start" : pg,
                    "page_end" : None,
                    "chapter_text" : "",
                    "sections" : []
                })
                return doc_struct["chapters"][-1]
            except (IndexError, AttributeError) as e:
                print(f"Warning: Error creating chapter: {str(e)}")
                return None
        
        current_chapter = None
        current_section = None

        def close_curr_chap(pg, curr_chap):
            try:
                curr_chap["page_end"] = pg
            except (KeyError, TypeError):
                pass
            return
        
        def is_section_name(line):
            try:
                return re.match(r"^(\d+(?:\.\d)+)\s+(.*)$", line)
            except re.error:
                return None
        
        def create_section(m, pg, curr_chap):
            try:
                if curr_chap is None:
                    print("Warning: Cannot create section without a chapter")
                    return None
                curr_chap["sections"].append({
                    "section_id" : m.group(1),
                    "section_title" : m.group(2).strip(),
                    "page_start" : pg,
                    "page_end" : None,
                    "raw_text" : ""
                })
                return curr_chap["sections"][-1]
            except (IndexError, AttributeError) as e:
                print(f"Warning: Error creating section: {str(e)}")
                return None
        
        def close_curr_section(pg, curr_sec):
            try:
                curr_sec["page_end"] = pg
            except (KeyError, TypeError):
                pass
            return
        
        for page in pdf.pages:
            try:
                text = page.extract_text()
                if text is None:
                    continue
                lines = text.splitlines()
                for idx, line in enumerate(lines):
                    try:
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
                    except Exception as line_error:
                        print(f"Warning: Error processing line: {str(line_error)}")
                        continue
            except Exception as page_error:
                print(f"Warning: Error processing page: {str(page_error)}")
                continue
                
        if current_chapter is not None:
            if current_section is not None:
                close_curr_section(pdf.pages[-1].page_number, current_section)   
            close_curr_chap(pdf.pages[-1].page_number, current_chapter)

        output_path = Path(file_path).with_suffix(".json")

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(doc_struct, f, indent=2, ensure_ascii=False)
            print(f"Successfully saved to: {output_path}")
            return
        except (IOError, PermissionError, json.JSONEncodeError) as write_error:
            print(f"Error writing output file: {str(write_error)}")
            return
            
    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        return
    except ValueError as e:
        print(f"Error: {str(e)}")
        return
    except pp.PDFSyntaxError as e:
        print(f"Error: Invalid or corrupted PDF file: {str(e)}")
        return
    except Exception as e:
        print(f"Unexpected error during PDF processing: {str(e)}")
        return