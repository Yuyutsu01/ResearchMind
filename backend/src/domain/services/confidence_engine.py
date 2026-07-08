from src.domain.blackboard.blackboard import ResearchBlackboard

class ConfidenceEngine:
    @staticmethod
    def adjust_claim_confidence(blackboard: ResearchBlackboard, claim_text: str, evidence_type: str, weight: float = 0.15):
        """
        Dynamically adjusts claim confidence based on evidence weighting:
        - evidence_type 'SUPPORT': increases score
        - evidence_type 'CONTRADICT': decreases score
        """
        claim_entry = None
        for c in blackboard.claims:
            if c["claim_text"] == claim_text:
                claim_entry = c
                break
                
        if not claim_entry:
            claim_entry = {
                "claim_text": claim_text,
                "confidence_score": 0.5,
                "evidence": [],
                "status": "PROVISIONAL"
            }
            blackboard.claims.append(claim_entry)
            
        old_score = claim_entry["confidence_score"]
        
        if evidence_type == "SUPPORT":
            claim_entry["confidence_score"] = min(1.0, old_score + weight)
            if claim_entry["confidence_score"] > 0.7:
                claim_entry["status"] = "SUPPORTED"
        elif evidence_type == "CONTRADICT":
            claim_entry["confidence_score"] = max(0.0, old_score - (weight * 1.5))
            if claim_entry["confidence_score"] < 0.4:
                claim_entry["status"] = "CONTRADICTED"
                
        print(f"[Confidence Engine] Adjusted claim confidence: {old_score:.2f} ──> {claim_entry['confidence_score']:.2f} (Status: {claim_entry['status']})")
