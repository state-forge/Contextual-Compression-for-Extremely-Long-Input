class Explainability:

    def generate_report(self, aggregated_output):
        """
        Input: output of aggregator.py
        {
          chapters: [...],
          document_summary: {
            rules: [...],
            exceptions: [...],
            ...
          }
        }
        Output:
        {
          compression_policy: {...},
          information_loss: {...},
          traceability: {...},
          statistics: {...}
        }
        """
        policy=self._compression_policy()
        loss=self._estimate_loss(aggregated_output)
        trace=self._verify_traceability(aggregated_output)
        stats=self._generate_statistics(aggregated_output)
        return {
            "compression_policy": policy,
            "information_loss": loss,
            "traceability": trace,
            "statistics": stats
        }
    #Policy
    def _compression_policy(self):
        return {
            "kept_content": [
                "rules",
                "exceptions",
                "constraints",
                "risks",
                "contradictions",
                "critical facts with numbers/dates",
                "decision-critical entities (dates, numbers, money, percentages)"
            ],
            "removed_content": [
                "narrative explanations",
                "examples and illustrations",
                "historical background",
                "repetitions",
                "non-critical descriptive text"
            ],
            "reasoning": (
                "Only decision-critical information is retained "
                "to support question answering and auditability. "
                "All retained items include source traceability "
                "for drill-down to original text."
            )
        }

    #Loss Estimation
    def _estimate_loss(self, aggregated):
        total=0
        high_importance=0
        medium_importance=0
        low_importance=0
        for k in aggregated["document_summary"].keys():
            items=aggregated["document_summary"][k]
            for item in items:
                total+=1
                imp=item.get("importance", "low")
                if imp=="high":
                    high_importance+=1
                elif imp=="medium":
                    medium_importance+=1
                else:
                    low_importance+=1
        #Calculate loss level
        if total==0:
            level="unknown"
            high_ratio=0
        else:
            high_ratio=high_importance/total
            if high_ratio > 0.6:
                level="low"
            elif high_ratio > 0.3:
                level="medium"
            else:
                level="high"
        return {
            "level": level,
            "high_importance_count": high_importance,
            "medium_importance_count": medium_importance,
            "low_importance_count": low_importance,
            "total_items": total,
            "high_importance_ratio": round(high_ratio, 3) if total > 0 else 0,
            "explanation": self._get_loss_explanation(level, high_ratio, total)
        }
 
    def _get_loss_explanation(self, level, ratio, total):
        if total==0:
            return "No items processed, unable to estimate loss."
        if level=="low":
            return (
                f"{int(ratio * 100)}% of retained content is high importance. "
                "Most decision-critical information has been preserved."
            )
        elif level=="medium":
            return (
                f"{int(ratio * 100)}% of retained content is high importance. "
                "Key information preserved, but some context lost."
            )
        else:
            return (
                f"Only {int(ratio * 100)}% of retained content is high importance. "
                "Significant context filtered; recommend reviewing source for details."
            )
    #Traceability
    def _verify_traceability(self, aggregated):
        missing=[]
        incomplete=[]
        total_checked=0
        for k in aggregated["document_summary"].keys():
            for note in aggregated["document_summary"][k]:
                total_checked+=1
                src=note.get("source")
                if not src:
                    missing.append({
                        "statement": note.get("statement"),
                        "type": note.get("type"),
                        "issue": "No source provided"
                    })
                elif not src.get("section_id"):
                    incomplete.append({
                        "statement": note.get("statement"),
                        "type": note.get("type"),
                        "issue": "Missing section_id in source"
                    })
                elif not src.get("page_start") and not src.get("page_end"):
                    incomplete.append({
                        "statement": note.get("statement"),
                        "type": note.get("type"),
                        "issue": "Missing page information in source"
                    })
        all_traceable=len(missing)==0 and len(incomplete)==0
        return {
            "all_traceable": all_traceable,
            "total_items_checked": total_checked,
            "missing_sources": missing,
            "incomplete_sources": incomplete,
            "traceability_score": self._calculate_traceability_score(
                total_checked, missing, incomplete
            )
        }

    def _calculate_traceability_score(self, total, missing, incomplete):
        if total==0:
            return 0
        #Missing sources are worse than incomplete
        missing_penalty=len(missing) * 1.0
        incomplete_penalty=len(incomplete) * 0.5
        total_penalty=missing_penalty+incomplete_penalty
        score=max(0, 100-(total_penalty/total * 100))
        return round(score, 1)

    #Stats
    def _generate_statistics(self, aggregated):

        doc_summary=aggregated["document_summary"]
        stats={
            "total_chapters": len(aggregated.get("chapters", [])),
            "total_items": 0,
            "items_by_type": {},
            "items_by_importance": {
                "high": 0,
                "medium": 0,
                "low": 0
            }
        }
        for k in doc_summary.keys():
            count=len(doc_summary[k])
            stats["items_by_type"][k] = count
            stats["total_items"] += count
            for item in doc_summary[k]:
                imp=item.get("importance", "low")
                if imp in stats["items_by_importance"]:
                    stats["items_by_importance"][imp] += 1
        return stats
