from models import SignalExtractionResult, ScoredAccount

class ScoringService:
    def __init__(self):
        pass

    def score_account(self, company: str, website: str, industry: str, extraction: SignalExtractionResult) -> ScoredAccount:
        score = 0
        reasons = []

        for signal in extraction.signals:
            stype = signal.signal_type.lower()
            if "funding" in stype:
                score += 20
                reasons.append("Funding detected")
            elif "hiring" in stype:
                score += 20
                reasons.append("Hiring detected")
            elif "expansion" in stype:
                score += 15
                reasons.append("Expansion detected")
            elif "shipping complaint" in stype or "shipping" in stype:
                score += 30
                reasons.append("Shipping complaints detected")
            elif "returns complaint" in stype or "return" in stype:
                score += 30
                reasons.append("Returns complaints detected")
            elif "competitor" in stype or "loop" in stype or "redo" in stype or "aftership" in stype:
                score += 25
                reasons.append("Competitor detected")
            else:
                score += 10
                reasons.append(f"{signal.signal_type} detected")

        score = min(score, 100)
        
        if score >= 80:
            priority = "High"
            recommendation = "Immediate outreach recommended. Strong buying intent."
        elif score >= 50:
            priority = "Medium"
            recommendation = "Nurture account. Moderate buying intent."
        else:
            priority = "Low"
            recommendation = "Monitor for future signals."

        return ScoredAccount(
            company=company,
            website=website,
            industry=industry,
            score=score,
            priority=priority,
            confidence=extraction.confidence,
            reason=", ".join(reasons) if reasons else extraction.reasoning,
            recommendation=recommendation,
            signals=extraction.signals
        )
