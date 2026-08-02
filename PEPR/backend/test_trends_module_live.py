import asyncio
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.models.analysis import DetectedTrend, DetectedAnomaly

async def audit_trends_module():
    async with AsyncSessionLocal() as db:
        print("==========================================================================================")
        print("                  LIVE TREND MODULE & ANOMALY ENGINE AUDIT (POSTGRESQL)                   ")
        print("==========================================================================================")
        
        # 1. Fetch Trends
        trends_stmt = select(DetectedTrend, EconomicIndicator).join(EconomicIndicator, DetectedTrend.indicator_id == EconomicIndicator.id)
        trends_res = await db.execute(trends_stmt)
        trends_rows = trends_res.all()

        print(f"\n[1] TOTAL EVALUATED TRENDLINES IN DB: {len(trends_rows)}")
        for t, ind in trends_rows[:5]:
            print(f"  • [{ind.code:<20}] {ind.name:<35} | Direction: {t.trend_direction:<7} | Shift: {t.pct_change:+.1f}% | Severity: {t.severity}")

        # 2. Fetch ML Anomalies
        anom_stmt = select(DetectedAnomaly, IndicatorObservation, EconomicIndicator).join(IndicatorObservation, DetectedAnomaly.observation_id == IndicatorObservation.id).join(EconomicIndicator, IndicatorObservation.indicator_id == EconomicIndicator.id)
        anom_res = await db.execute(anom_stmt)
        anom_rows = anom_res.all()

        print(f"\n[2] TOTAL ML ANOMALIES FLAGGED IN DB: {len(anom_rows)}")
        for a, obs, ind in anom_rows[:5]:
            print(f"  • [{ind.code:<20}] {ind.name:<35} | Score: {a.anomaly_score:.2f} | Method: {a.algorithm_used}")

        # 3. Time Series History for Line Chart
        ind_cpi_stmt = select(EconomicIndicator).where(EconomicIndicator.code == "PAK_CPI_YOY")
        cpi_ind = (await db.execute(ind_cpi_stmt)).scalars().first()

        if cpi_ind:
            history_stmt = select(IndicatorObservation).where(IndicatorObservation.indicator_id == cpi_ind.id).order_by(IndicatorObservation.timestamp.asc())
            history_rows = (await db.execute(history_stmt)).scalars().all()
            print(f"\n[3] LIVE TIME-SERIES HISTORY FOR LINE CHART ('{cpi_ind.name}'):")
            print(f"  • Total Historical Observations: {len(history_rows)}")
            for obs in history_rows[:5]:
                print(f"      - Date: {obs.timestamp.strftime('%Y-%m-%d')} | Value: {obs.value:.2f}% YoY")

        print("==========================================================================================")

if __name__ == "__main__":
    asyncio.run(audit_trends_module())
