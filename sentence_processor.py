import re
import spacy
from dateutil.parser import parse as parse_date

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

class SentenceProcessor:
    def __init__(self):
        self.nlp = nlp

    def process_section(self, section):
        """
        Input Format:
        section = {
            "chapter_id": "...",  # Added by pipeline
            "section_id": "...",
            "Title": "...",
            "page_range": [start, end],  # e.g., [10, 12]
            "raw_text": "..."
        }
        Output Format:
        {
            "chapter_id": "...",
            "section_id": "...",
            "title": "...",
            "page_start": ...,
            "page_end": ...,
            "sentences": [
                {
                    "sentence_id": 0,
                    "text": "...",
                    "entities": {...},
                    "source": {
                        "chapter_id": "...",
                        "section_id": "...",
                        "page_start": ...,
                        "page_end": ...,
                        "char_offset": ...
                    }
                }
            ]
        }
        """
        text=self._clean_text(section.get("raw_text", ""))
        sentences=self._split_sentences(text)
        #Extract page range
        page_range=section.get("page_range", [None, None])
        page_start=page_range[0] if isinstance(page_range, list) and len(page_range)>0 else None
        page_end=page_range[1] if isinstance(page_range, list) and len(page_range)>1 else None
        processed=[]
        char_offset=0
        for idx, sent in enumerate(sentences):
            entities=self._extract_entities(sent)
            processed.append({
                "sentence_id": idx,
                "text": sent,
                "entities": entities,
                "source": {
                    "chapter_id": section.get("chapter_id"),
                    "section_id": section.get("section_id"),
                    "page_start": page_start,
                    "page_end": page_end,
                    "char_offset": char_offset
                }
            })
            char_offset+=len(sent) + 1  # +1 for space/period
        return {
            "chapter_id": section.get("chapter_id"),
            "section_id": section.get("section_id"),
            "title": section.get("Title", section.get("title", "")),
            "page_start": page_start,
            "page_end": page_end,
            "sentences": processed
        }
    #Text Cleaning
    def _clean_text(self, text: str):
        if not text:
            return ""
        text = text.replace("\r", " ")
        text = text.replace("\t", " ")
        text = text.replace("\n", " ")
        #Remove multiple spaces
        text = re.sub(r"\s+", " ", text)
        #Normalize bullets
        text = re.sub(r"[•\-]\s+", "", text)
        return text.strip()

    #Sentence Spiltting
    def _split_sentences(self, text):
        if not text:
            return []
        doc = self.nlp(text)
        sentences = [sent.text.strip() for sent in doc.sents]
        #Fallback if spaCy fails
        if len(sentences) == 0:
            sentences = re.split(r"[.!?]+", text)
        #Remove empty or very short sentences
        sentences = [s for s in sentences if len(s) > 2]
        return sentences

    #Entity Extraction
    def _extract_entities(self, sentence: str):
        doc = self.nlp(sentence)
        entities={
            "dates": [],
            "numbers": [],
            "quantities": [],
            "percentages": [],
            "money": [],
            "organizations": [],
            "persons": []
        }
        # spaCy NER
        for ent in doc.ents:
            if ent.label_ in ["DATE", "TIME"]:
                entities["dates"].append(ent.text)
            elif ent.label_=="CARDINAL":
                entities["numbers"].append(ent.text)
            elif ent.label_=="QUANTITY":
                entities["quantities"].append(ent.text)
            elif ent.label_=="PERCENT":
                entities["percentages"].append(ent.text)
            elif ent.label_=="MONEY":
                entities["money"].append(ent.text)
            elif ent.label_=="ORG":
                entities["organizations"].append(ent.text)
            elif ent.label_=="PERSON":
                entities["persons"].append(ent.text)
        # Regex backup for durations
        duration_pattern=r"\d+\s*(day|days|week|weeks|month|months|year|years|hour|hours)"
        durations=re.findall(duration_pattern, sentence.lower())
        if durations:
            entities["quantities"].extend([" ".join(d) for d in durations])
        #Extract numeric thresholds
        threshold_pattern=r"(?:maximum|minimum|at least|at most|no more than|no less than)\s+(\d+(?:\.\d+)?)"
        thresholds=re.findall(threshold_pattern, sentence.lower())
        if thresholds:
            entities["numbers"].extend(thresholds)
        #Deduplicate
        for k in entities:
            entities[k] = list(set(entities[k]))
        return entities
