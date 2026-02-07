import re

class Classifier:
    def __init__(self):
        #Keyword dictionaries
        self.rule_keywords=[
            "must", "shall", "required", "mandatory",
            "is to", "are to", "obligated", "responsible for",
            "will", "should", "need to", "have to"
        ]
        self.exception_keywords=[
            "unless", "except", "provided that",
            "excluding", "other than", "not applicable when",
            "does not apply", "exempted", "waived"
        ]
        self.constraint_keywords=[
            "only", "maximum", "minimum", "limited to",
            "not exceed", "at most", "at least", "no more than",
            "no less than", "restricted to", "capped at"
        ]
        self.risk_keywords=[
            "risk", "conflict", "issue", "may cause",
            "could lead", "danger", "violation", "penalty",
            "failure to", "non-compliance", "breach"
        ]
        self.contradiction_keywords=[
            "however", "but", "on the other hand",
            "nevertheless", "although", "despite",
            "conversely", "in contrast", "whereas"
        ]

    #Main
    def classify_sentences(self, processed_section):
        results=[]
        for s in processed_section["sentences"]:
            text=s["text"]
            label=self.classify_text(text)
            results.append({
                "sentence_id": s["sentence_id"],
                "text": text,
                "type": label,
                "entities": s["entities"],
                "source": s["source"]
            })
        return {
            "chapter_id": processed_section.get("chapter_id"),
            "section_id": processed_section.get("section_id"),
            "title": processed_section.get("title"),
            "page_start": processed_section.get("page_start"),
            "page_end": processed_section.get("page_end"),
            "classified": results
        }

    #Classification Logic
    def classify_text(self, text):
        t=text.lower()
        #Priority order is critical
        #Exceptions
        if self._contains(t, self.exception_keywords):
            return "exception"
        #Contradictions
        if self._contains(t, self.contradiction_keywords):
            return "contradiction"
        # Risks
        if self._contains(t, self.risk_keywords):
            return "risk"
        #Constraints
        if self._contains(t, self.constraint_keywords):
            return "constraint"
        #Rules
        if self._contains(t, self.rule_keywords):
            return "rule"
        #Default-factual information
        return "fact"
    
    #Helper function
    def _contains(self, text, keywords):
        for k in keywords:
            #Word boundary check to avoid partial matches
            pattern = r"\b" + re.escape(k) + r"\b"
            if re.search(pattern, text):
                return True
        return False
