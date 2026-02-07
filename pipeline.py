from sentence_processor import SentenceProcessor
from classifier import Classifier
from section_summarizer import SectionSummarizer
from aggregator import Aggregator
from explainability import Explainability

def process_document(doc_structure):
    """
    Input Format:
    {
        "doc_id": "doc_name",
        "chapters": [
            {
                "chapter_id": "...",  # Optional, will be auto-generated if missing
                "sections": [
                    {
                        "section_id": "...",
                        "Title": "...",
                        "page_range": [start, end],
                        "raw_text": "..."
                    }
                ]
            }
        ]
    }
    Output Format:
    {
        "doc_id": "...",
        "metadata": {...},
        "analysis": {
            "chapters": [...],
            "document_summary": {...}
        },
        "explainability": {...},
        "traceability_enabled": true
    }
    """
    #Initialize modules
    sp = SentenceProcessor()
    cl = Classifier()
    ss = SectionSummarizer()
    ag = Aggregator()
    ex = Explainability()
    processed_sections = []
    #Process each chapter and section
    for chapter_idx, chapter in enumerate(doc_structure.get("chapters", [])):
        #Get or generate chapter_id
        chapter_id = chapter.get("chapter_id", f"chapter_{chapter_idx + 1}")
        for section in chapter.get("sections", []):
            #Add chapter_id to section for processing
            section["chapter_id"] = chapter_id
            try:
                #Step1:Sentence processing
                processed=sp.process_section(section)
                #Step2:Classification
                classified=cl.classify_sentences(processed)
                #Step3:Section summarization
                summarized=ss.summarize_section(classified)
                processed_sections.append(summarized)
            except Exception as e:
                #Log error but continue processing
                print(f"Error processing section {section.get('section_id')}: {str(e)}")
                continue
    #Step4:Aggregation
    aggregated=ag.aggregate_document(processed_sections)
    #Step5:Explainability
    report=ex.generate_report(aggregated)
    #Return final compressed output
    return {
        "doc_id": doc_structure.get("doc_id"),
        "metadata": doc_structure.get("metadata", {}),
        "analysis": aggregated,
        "explainability": report,
        "traceability_enabled": True
    }

def get_drill_down(compressed_output, item_type, index):
    """
    Helper function to drill down into specific items.
    Args:
        compressed_output: Output from process_document
        item_type: "rules", "exceptions", "constraints", etc.
        index: Index of the item in that category
    Returns:
        Full details including source location
    """
    doc_summary=compressed_output.get("analysis", {}).get("document_summary", {})
    items=doc_summary.get(item_type, [])
    if index<0 or index>=len(items):
        return {"error": "Index out of range"}
    item = items[index]
    return {
        "statement": item.get("statement"),
        "type": item.get("type"),
        "importance": item.get("importance"),
        "entities": item.get("entities"),
        "source": item.get("source"),
        "drill_down_instructions": (
            f"See {item.get('source', {}).get('section_id')} "
            f"on pages {item.get('source', {}).get('page_start')}-"
            f"{item.get('source', {}).get('page_end')}"
        )
    }
