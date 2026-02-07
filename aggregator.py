class Aggregator:
    #Main
    def aggregate_document(self, sections):
        """
        Input: list of outputs from section_summarizer
        [
          {
            chapter_id: "3",
            section_id: "3.1",
            title: "...",
            page_start: 10,
            page_end: 12,
            summary: {
              rules: [...],
              exceptions: [...],
              ...
            }
          },
          ...
        ]
        Output:
        {
          chapters: [
            {
              chapter_id: "3",
              sections_included: ["3.1", "3.2"],
              page_range: [10, 15],
              aggregated: {
                rules: [...],
                exceptions: [...],
                ...
              }
            }
          ],
          document_summary: {
            rules: [...],
            exceptions: [...],
            ...
          }
        }
        """
        chapters = self._group_by_chapter(sections)
        chapter_summaries=[]
        for chapter_id, chapter_sections in chapters.items():
            chapter_summary=self._aggregate_chapter(
                chapter_id,
                chapter_sections
            )
            chapter_summaries.append(chapter_summary)
        document_summary=self._aggregate_document_level(
            chapter_summaries
        )
        return {
            "chapters": chapter_summaries,
            "document_summary": document_summary
        }
    
    #Chapter Grouping
    def _group_by_chapter(self, sections):
        chapters={}
        for sec in sections:
            cid=sec.get("chapter_id", "unknown")
            if cid not in chapters:
                chapters[cid]=[]
            chapters[cid].append(sec)
        return chapters

    #Chapter Aggregation
    def _aggregate_chapter(self, chapter_id, sections):
        combined={
            "rules": [],
            "exceptions": [],
            "constraints": [],
            "risks": [],
            "contradictions": [],
            "facts": []
        }
        #Track page range
        page_starts=[]
        page_ends=[]
        #Collect from all sections
        for sec in sections:
            summary = sec["summary"]
            for k in combined.keys():
                combined[k].extend(summary.get(k, []))
            #Track page numbers
            if sec.get("page_start") is not None:
                page_starts.append(sec["page_start"])
            if sec.get("page_end") is not None:
                page_ends.append(sec["page_end"])
        #Calculate page range
        page_range=None
        if page_starts and page_ends:
            page_range=[min(page_starts), max(page_ends)]
        return {
            "chapter_id": chapter_id,
            "sections_included": [
                s.get("section_id") for s in sections
            ],
            "page_range": page_range,
            "aggregated": combined
        }

    #Document Level
    def _aggregate_document_level(self, chapters):
        doc={
            "rules": [],
            "exceptions": [],
            "constraints": [],
            "risks": [],
            "contradictions": [],
            "facts": []
        }
        for ch in chapters:
            agg=ch["aggregated"]
            for k in doc.keys():
                doc[k].extend(agg.get(k, []))
        return doc
