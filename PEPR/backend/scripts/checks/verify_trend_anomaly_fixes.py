import asyncio
from sqlalchemy import select, text, inspect
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.models.analysis import DetectedTrend, DetectedAnomaly

async def verify_fixes():
    async with AsyncSessionLocal() as db:
        print("=" * 90)
        print("VERIFYING TREND & ANOMALY MODULE FIXES")
        print("=" * 90)
        
        # 1. Check database schema - verify no unique constraint
        print("\n[1] DATABASE SCHEMA CHECK:")
        try:
            inspector = inspect(db.get_bind())
            constraints = inspector.get_unique_constraints('detected_anomalies')
            print(f"    Unique constraints on detected_anomalies: {constraints}")
            if constraints:
                print("    ⚠️  WARNING: Unique constraint still exists! Migration may not have applied.")
            else:
                print("    ✓ No unique constraint found (as expected)")
        except Exception as e:
            print(f"    Error checking schema: {e}")
        
        # 2. Count total indicators
        all_indicators = (await db.execute(select(EconomicIndicator))).scalars().all()
        print(f"\n[2] TOTAL INDICATORS IN DB: {len(all_indicators)}")
        
        # 3. Count trends
        all_trends = (await db.execute(select(DetectedTrend))).scalars().all()
        print(f"\n[3] TOTAL DETECTED TRENDS: {len(all_trends)}")
        if len(all_trends) > 0:
            print(f"    Sample trends:")
            for t in all_trends[:3]:
                ind = (await db.execute(select(EconomicIndicator).where(EconomicIndicator.id == t.indicator_id))).scalars().first()
                print(f"    • {ind.name if ind else 'Unknown'}: {t.trend_direction} ({t.pct_change:+.1f}%)")
        
        # 4. Count anomalies by algorithm
        all_anomalies = (await db.execute(select(DetectedAnomaly))).scalars().all()
        print(f"\n[4] TOTAL DETECTED ANOMALIES: {len(all_anomalies)}")
        
        # Group by algorithm
        algo_count = {}
        for anom in all_anomalies:
            algo = anom.algorithm_used
            algo_count[algo] = algo_count.get(algo, 0) + 1
        
        print(f"    Anomalies by algorithm:")
        for algo, count in sorted(algo_count.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {algo}: {count} anomalies")
        
        # 5. Check observations with multiple anomalies
        print(f"\n[5] OBSERVATIONS WITH MULTIPLE ANOMALIES:")
        obs_anom_count = {}
        for anom in all_anomalies:
            obs_id = anom.observation_id
            obs_anom_count[obs_id] = obs_anom_count.get(obs_id, 0) + 1
        
        multi_anom_obs = {k: v for k, v in obs_anom_count.items() if v > 1}
        print(f"    Observations flagged by multiple algorithms: {len(multi_anom_obs)}")
        for obs_id, count in list(multi_anom_obs.items())[:5]:
            obs = (await db.execute(select(IndicatorObservation).where(IndicatorObservation.id == obs_id))).scalars().first()
            anoms = [a for a in all_anomalies if a.observation_id == obs_id]
            print(f"    • Obs {obs.timestamp if obs else 'Unknown'}: {count} algorithms flagged it")
            for anom in anoms:
                print(f"      - {anom.algorithm_used} (score: {anom.anomaly_score:.2f})")
        
        # 6. Verify trends across categories
        print(f"\n[6] TRENDS BY CATEGORY:")
        category_trends = {}
        for trend in all_trends:
            ind = (await db.execute(select(EconomicIndicator).where(EconomicIndicator.id == trend.indicator_id))).scalars().first()
            cat = getattr(ind, 'category', 'Macroeconomic') if ind else 'Unknown'
            category_trends[cat] = category_trends.get(cat, 0) + 1
        
        for cat, count in sorted(category_trends.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {cat}: {count} trends")
        
        # 7. Verify anomalies across categories
        print(f"\n[7] ANOMALIES BY CATEGORY:")
        category_anomalies = {}
        for anom in all_anomalies:
            obs = (await db.execute(select(IndicatorObservation).where(IndicatorObservation.id == anom.observation_id))).scalars().first()
            if obs:
                ind = (await db.execute(select(EconomicIndicator).where(EconomicIndicator.id == obs.indicator_id))).scalars().first()
                cat = getattr(ind, 'category', 'Macroeconomic') if ind else 'Unknown'
            else:
                cat = 'Unknown'
            category_anomalies[cat] = category_anomalies.get(cat, 0) + 1
        
        for cat, count in sorted(category_anomalies.items(), key=lambda x: x[1], reverse=True):
            print(f"    • {cat}: {count} anomalies")
        
        print("\n" + "=" * 90)
        print("VERIFICATION COMPLETE")
        print("=" * 90)
        print("\nKEY METRICS:")
        print(f"  Total Indicators: {len(all_indicators)}")
        print(f"  Total Trends: {len(all_trends)} (should be close to # of indicators with 2+ observations)")
        print(f"  Total Anomalies: {len(all_anomalies)} (should be >> {len(all_trends)})")
        print(f"  Multi-algorithm observations: {len(multi_anom_obs)}")
        print(f"  Algorithm diversity: {len(algo_count)} different algorithms")
        print("\n✓ Fix verification complete. Frontend should now show all results grouped by category.")

if __name__ == "__main__":
    asyncio.run(verify_fixes())
