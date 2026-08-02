import asyncio
from sqlalchemy import select
from app.infrastructure.database import AsyncSessionLocal
from app.models.economy import EconomicIndicator, IndicatorObservation, IndicatorMetadata
from app.models.policy import PolicyTarget, PolicyActual, PolicyGap

async def audit():
    async with AsyncSessionLocal() as db:
        print("==========================================================================================================")
        print("                           PEPR ECONOMICS ENGINE: COMPLETE MATHEMATICAL AUDIT TRACE                      ")
        print("==========================================================================================================")
        
        stmt = select(EconomicIndicator)
        res = await db.execute(stmt)
        indicators = res.scalars().all()

        for ind in indicators:
            obs_stmt = (
                select(IndicatorObservation)
                .where(IndicatorObservation.indicator_id == ind.id)
                .order_by(IndicatorObservation.timestamp.desc())
                .limit(10)
            )
            obs_res = await db.execute(obs_stmt)
            recent_obs = obs_res.scalars().all()

            if not recent_obs:
                continue

            latest_raw = recent_obs[0].value
            prev_raw = recent_obs[1].value if len(recent_obs) > 1 else latest_raw
            for o in recent_obs[1:]:
                if o.value != latest_raw:
                    prev_raw = o.value
                    break

            meta_stmt = select(IndicatorMetadata).where(IndicatorMetadata.indicator_id == ind.id)
            meta_res = await db.execute(meta_stmt)
            meta = meta_res.scalars().first()

            target_stmt = (
                select(PolicyTarget, PolicyGap, PolicyActual)
                .join(PolicyGap, PolicyTarget.id == PolicyGap.target_id)
                .join(PolicyActual, PolicyTarget.id == PolicyActual.target_id)
                .where(PolicyTarget.indicator_id == ind.id)
            )
            target_res = await db.execute(target_stmt)
            target_row = target_res.first()

            code = ind.code
            unit = meta.unit if meta else "Units"

            # Formatted values
            if "RESERVES" in code and latest_raw > 1e6:
                val = latest_raw / 1e9
                prev = prev_raw / 1e9
                unit = "Billion USD"
            elif "CURRENT_ACCOUNT" in code and abs(latest_raw) > 1e6:
                val = latest_raw / 1e6
                prev = prev_raw / 1e6
                unit = "Million USD"
            else:
                val = latest_raw
                prev = prev_raw

            # Math calculations
            abs_diff = val - prev
            rel_pct_change = ((val - prev) / abs(prev)) * 100.0 if prev != 0 else 0.0

            print(f"\nINDICATOR: {ind.name} [{code}]")
            print(f"  • Raw Observations: Latest={latest_raw}, Previous={prev_raw}")
            print(f"  • Scaled Values:    Latest={val:.2f} {unit}, Previous={prev:.2f} {unit}")
            print(f"  • Absolute Shift:   {abs_diff:+.2f} {unit}")
            print(f"  • Relative Shift %: {rel_pct_change:+.2f}%")

            if target_row:
                pt, pg, pa = target_row
                tv = pt.target_value
                abs_gap = val - tv
                rel_gap_pct = ((val - tv) / tv) * 100.0 if tv != 0 else 0.0

                print(f"  • POLICY TARGET AUDIT:")
                print(f"      - Benchmark Name:        {pt.target_name}")
                print(f"      - Target Benchmark:      {tv:.2f} {pt.target_unit}")
                print(f"      - Actual Value:          {val:.2f} {pt.target_unit}")
                print(f"      - Absolute Gap:          {abs_gap:+.2f} {pt.target_unit}")
                print(f"      - Relative Gap %:        {rel_gap_pct:+.2f}% (Formula: ((Actual - Target) / Target) * 100)")
                print(f"      - Evaluated Gap Status:  {pg.gap_status}")
                print(f"      - Magnitude Score:       {pg.magnitude_score:.2f} / 10.0")
                print(f"      - Engine Severity Score: {pg.engine_score:.2f}")

        print("\n==========================================================================================================")

if __name__ == "__main__":
    asyncio.run(audit())
