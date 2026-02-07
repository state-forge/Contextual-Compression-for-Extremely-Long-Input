class SectionSummarizer:
    def __init__(self):
        pass
    #Main
    def summarize_section(self, classified_section):
        """
        Input format: output of classifier
        {
          chapter_id: "...",
          section_id: "...",
          title: "...",
          page_start: ...,
          page_end: ...,
          classified: [
            {
              sentence_id: 0,
              text: "...",
              type: "rule"|"exception"|...,
              entities: {...},
              source: {...}
            }
          ]
        }
        Output format:
        {
          chapter_id: "...",
          section_id: "...",
          title: "...",
          page_start: ...,
          page_end: ...,
          summary: {
            rules: [...],
            exceptions: [...],
            constraints: [...],
            risks: [...],
            contradictions: [...],
            facts: [...]
          }
        }
        """
        notes=[]
        for sent in classified_section["classified"]:
            note=self._create_note(sent)
            notes.append(note)
        #Group by type
        grouped=self._group_notes(notes)
        return {
            "chapter_id": classified_section.get("chapter_id"),
            "section_id": classified_section.get("section_id"),
            "title": classified_section.get("title"),
            "page_start": classified_section.get("page_start"),
            "page_end": classified_section.get("page_end"),
            "summary": grouped
        }
    
    #Note creation
    def _create_note(self, sentence_obj):
        note_type=sentence_obj["type"]
        importance=self._estimate_importance(
            note_type,
            sentence_obj["entities"]
        )
        return {
            "statement": sentence_obj["text"],
            "type": note_type,
            "importance": importance,
            "entities": sentence_obj["entities"],
            "source": sentence_obj["source"]
        }

    #Imporatant Heuristics
    def _estimate_importance(self, note_type, entities):
        #High priority cases
        if note_type in ["exception", "risk", "contradiction"]:
            return "high"
        #Numbers, dates, money usually important
        has_critical_entities = (
            entities.get("numbers") or
            entities.get("dates") or
            entities.get("money") or
            entities.get("percentages")
        )
        if has_critical_entities:
            return "high"
        #Constraints moderately important
        if note_type=="constraint":
            return "medium"
        #Rules with quantities are medium importance
        if note_type=="rule" and entities.get("quantities"):
            return "medium"
        #Default
        return "low"
    
    #Grouping
    def _group_notes(self, notes):
        grouped={
            "rules": [],
            "exceptions": [],
            "constraints": [],
            "risks": [],
            "contradictions": [],
            "facts": []
        }
        for n in notes:
            t=n["type"]
            if t=="rule":
                grouped["rules"].append(n)
            elif t=="exception":
                grouped["exceptions"].append(n)
            elif t=="constraint":
                grouped["constraints"].append(n)
            elif t=="risk":
                grouped["risks"].append(n)
            elif t=="contradiction":
                grouped["contradictions"].append(n)
            else:
                grouped["facts"].append(n)
        return grouped