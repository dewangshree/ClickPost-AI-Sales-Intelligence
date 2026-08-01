import csv
import json
import logging
from typing import List
from models import RankedAccount, SignalExtractionResult, Outreach

logger = logging.getLogger(__name__)

class ExportService:
    def __init__(self):
        self.output_dir = "output"

    def export_ranked_accounts(self, accounts: List[RankedAccount], filename: str = "ranked_accounts.csv"):
        filepath = f"{self.output_dir}/{filename}"
        try:
            with open(filepath, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([
                    "Rank", "Company", "Website", "Industry", "Score", 
                    "Priority", "Confidence", "Reason", "Recommendation"
                ])
                for acc in accounts:
                    writer.writerow([
                        acc.rank, acc.company, acc.website, acc.industry, acc.score,
                        acc.priority, acc.confidence, acc.reason, acc.recommendation
                    ])
            logger.info(f"Exported ranked accounts to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export ranked accounts: {e}")

    def export_signals(self, extractions: List[SignalExtractionResult], filename: str = "signals.json"):
        filepath = f"{self.output_dir}/{filename}"
        try:
            data = [ext.model_dump() for ext in extractions]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info(f"Exported signals to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export signals: {e}")

    def export_outreach(self, outreaches: List[Outreach], filename: str = "top5_outreach.json"):
        filepath = f"{self.output_dir}/{filename}"
        try:
            data = [out.model_dump() for out in outreaches]
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            logger.info(f"Exported outreach to {filepath}")
        except Exception as e:
            logger.error(f"Failed to export outreach: {e}")
