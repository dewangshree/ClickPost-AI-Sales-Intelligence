import logging
import pandas as pd
from config import setup_logging
from services.search_service import SearchService
from services.signal_service import SignalService
from services.scoring_service import ScoringService
from services.outreach_service import OutreachService
from services.export_service import ExportService
from models import RankedAccount

logger = logging.getLogger(__name__)

def main():
    setup_logging()
    logger.info("Starting ClickPost AI Sales Intelligence Pipeline")

    try:
        df = pd.read_csv("brands.csv")
    except Exception as e:
        logger.error(f"Failed to load brands.csv: {e}")
        return

    search_svc = SearchService()
    signal_svc = SignalService()
    score_svc = ScoringService()
    outreach_svc = OutreachService()
    export_svc = ExportService()

    scored_accounts = []
    all_extractions = []

    for index, row in df.iterrows():
        company = row['company']
        website = row['website']
        industry = row['industry']

        logger.info(f"Processing [{index+1}/{len(df)}]: {company}")

        try:
            # Step 1: Search
            search_results = search_svc.search_company(company, website)
            
            # Step 2: Extract Signals
            extraction = signal_svc.extract_signals(company, search_results)
            all_extractions.append(extraction)
            
            # Step 3: Score
            scored_account = score_svc.score_account(company, website, industry, extraction)
            scored_accounts.append(scored_account)
            
        except Exception as e:
            logger.error(f"Failed to process {company}: {e}")
            # Continue to next brand

    # Step 4: Rank
    scored_accounts.sort(key=lambda x: x.score, reverse=True)
    
    ranked_accounts = []
    for rank, acc in enumerate(scored_accounts, 1):
        ranked_acc = RankedAccount(**acc.model_dump())
        ranked_acc.rank = rank
        ranked_accounts.append(ranked_acc)

    # Step 5: Outreach for Top 5
    top_5 = ranked_accounts[:5]
    outreaches = []
    
    for acc in top_5:
        logger.info(f"Generating outreach for Top 5 account: {acc.company}")
        try:
            outreach = outreach_svc.generate_outreach(acc)
            outreaches.append(outreach)
        except Exception as e:
            logger.error(f"Failed to generate outreach for {acc.company}: {e}")

    # Step 6: Export
    export_svc.export_ranked_accounts(ranked_accounts)
    export_svc.export_signals(all_extractions)
    export_svc.export_outreach(outreaches)

    logger.info("Pipeline completed successfully.")

if __name__ == "__main__":
    main()
