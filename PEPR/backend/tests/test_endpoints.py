import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.api.v1.endpoints.indicators import get_indicators_summary
from app.api.v1.endpoints.trends import list_trends
from app.api.v1.endpoints.policy import list_policy_gaps
from app.api.v1.endpoints.reports import list_reports

async def test_all_endpoints():
    print("Testing backend endpoint database responses...")
    async with AsyncSessionLocal() as db:
        ind_summary = await get_indicators_summary(db)
        print(f" -> Indicators Summary ({len(ind_summary)} items):", ind_summary[:2] if ind_summary else [])
        
        trends = await list_trends(db=db)
        print(f" -> Trends ({len(trends)} items):", trends[:2] if trends else [])
        
        gaps = await list_policy_gaps(db=db)
        print(f" -> Policy Gaps ({len(gaps)} items):", gaps[:2] if gaps else [])
        
        reports = await list_reports(db=db)
        print(f" -> Reports ({len(reports)} items):", reports[:2] if reports else [])

if __name__ == "__main__":
    asyncio.run(test_all_endpoints())
