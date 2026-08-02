import logging
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.news import NewsArticle, NewsTopic, SentimentAnalysisResult
from app.models.economy import EconomicIndicator, IndicatorObservation
from app.models.policy import PolicyTarget, PolicyActual, PolicyGap
from app.services.analysis.policy_engine import PolicyEngine
from app.services.nlp.text_processor import TextProcessor

logger = logging.getLogger("pepr.analysis")

TOPIC_KEYWORDS = {
    "Inflation & Prices": ["inflation", "cpi", "price", "hike", "cost", "expensive", "food"],
    "Fiscal Policy & Tax": ["tax", "fbr", "revenue", "budget", "fiscal", "duty", "tariff"],
    "Monetary Policy & Rates": ["sbp", "interest rate", "policy rate", "rupee", "pkr", "dollar", "forex", "reserves"],
    "Energy & Power": ["power", "electricity", "circular debt", "fuel", "petrol", "gas", "tariff", "disco"],
    "IMF & Foreign Debt": ["imf", "bailout", "debt", "loan", "program", "tranche", "external"],
    "Trade & Exports": ["export", "import", "trade", "psx", "stock", "market", "deficit"],
}

async def run_post_ingestion_analysis(db: AsyncSession, source_type: str) -> None:
    """
    Automatically runs NLP sentiment analysis & topic modeling on unprocessed news/transcripts
    immediately after ingestion completes.
    """
    try:
        if source_type in {"youtube", "rss"}:
            # Find articles that don't have sentiment results yet
            stmt = (
                select(NewsArticle)
                .outerjoin(SentimentAnalysisResult, NewsArticle.id == SentimentAnalysisResult.article_id)
                .where(SentimentAnalysisResult.id == None)
                .limit(50)
            )
            res = await db.execute(stmt)
            unprocessed_articles = res.scalars().all()

            if not unprocessed_articles:
                logger.info("No unprocessed news/transcripts found for NLP analysis.")
                return

            analyzed_count = 0
            for article in unprocessed_articles:
                text = f"{article.title}. {article.content or ''}"
                lang = TextProcessor.detect_language(text)
                sentiment_score = TextProcessor.analyze_sentiment(text, lang if lang in {'en', 'ur'} else 'en')

                label = "positive" if sentiment_score > 0.15 else ("negative" if sentiment_score < -0.15 else "neutral")

                # Insert SentimentAnalysisResult
                sentiment_obj = SentimentAnalysisResult(
                    id=uuid.uuid4(),
                    article_id=article.id,
                    score=sentiment_score,
                    label=label,
                    ai_model_version="pepr-nlp-v1",
                )
                db.add(sentiment_obj)

                # Match topics based on keyword presence
                text_lower = text.lower()
                matched_topics = []
                for topic_name, keywords in TOPIC_KEYWORDS.items():
                    if any(kw in text_lower for kw in keywords):
                        matched_topics.append(topic_name)

                if not matched_topics:
                    matched_topics.append("General Macroeconomics")

                for topic_name in matched_topics:
                    topic_obj = NewsTopic(
                        id=uuid.uuid4(),
                        article_id=article.id,
                        topic_label=topic_name,
                        confidence_score=0.85,
                        ai_model_version="pepr-topic-v1",
                    )
                    db.add(topic_obj)

                analyzed_count += 1

            await db.commit()
            logger.info(f"Post-ingestion NLP Analysis completed: {analyzed_count} articles/transcripts processed with sentiment and topic labels.")

        # M1 Economic Indicator Ingestion Trigger for M2 Statistical & ML Engine
        # Always run after any ingestion so trends and anomalies are updated every run
        if True:
            from app.services.analysis.trend_detector import TrendDetector
            from app.services.analysis.anomaly_detector import AnomalyDetector
            from app.models.analysis import DetectedTrend, DetectedAnomaly
            from sqlalchemy import delete

            ind_stmt = select(EconomicIndicator)
            ind_res = await db.execute(ind_stmt)
            indicators = ind_res.scalars().all()

            for ind in indicators:
                obs_stmt = (
                    select(IndicatorObservation)
                    .where(IndicatorObservation.indicator_id == ind.id)
                    .order_by(IndicatorObservation.timestamp.asc())
                )
                obs_res = await db.execute(obs_stmt)
                observations = obs_res.scalars().all()

                if not observations:
                    continue

                obs_dicts = [
                    {"timestamp": o.timestamp, "value": o.value, "id": o.id}
                    for o in observations
                ]

                # 1. Run Trend Detector
                td = TrendDetector(indicator_id=str(ind.id))
                trend_res = td.analyze(obs_dicts)
                if trend_res:
                    trend_obj = DetectedTrend(
                        id=uuid.uuid4(),
                        indicator_id=ind.id,
                        trend_direction=trend_res["direction"],
                        current_value=trend_res["current_value"],
                        previous_value=trend_res["previous_value"],
                        pct_change=trend_res["percentage_change"],
                        period=trend_res["period"],
                        severity=trend_res["severity"],
                        detection_method=trend_res["detection_method"],
                        confidence_score=trend_res["confidence"],
                    )
                    db.add(trend_obj)

                # 2. Run ML Anomaly Detector
                anom_detector = AnomalyDetector(indicator_id=str(ind.id))
                anom_list = anom_detector.analyze(obs_dicts)
                for a in anom_list:
                    target_obs_id = obs_dicts[-1]["id"]
                    anom_stmt = select(DetectedAnomaly).where(DetectedAnomaly.observation_id == target_obs_id)
                    existing_anom = (await db.execute(anom_stmt)).scalars().first()
                    if not existing_anom:
                        anom_obj = DetectedAnomaly(
                            id=uuid.uuid4(),
                            observation_id=target_obs_id,
                            anomaly_score=float(a["anomaly_score"]),
                            algorithm_used=a["detection_method"],
                        )
                        db.add(anom_obj)

            await db.commit()
            logger.info("Post-ingestion M2 Statistical Trends & ML Anomalies successfully evaluated from M1 time-series data.")

        # M4 Policy Gap Engine — runs after every ingestion to keep gaps current
        try:
            from app.api.v1.endpoints.indicators import resolve_policy_benchmark

            # 1. Auto-create PolicyTarget for any EconomicIndicator missing one
            all_inds_res = await db.execute(select(EconomicIndicator))
            all_indicators = all_inds_res.scalars().all()

            existing_pt_res = await db.execute(select(PolicyTarget))
            existing_pts = existing_pt_res.scalars().all()
            existing_ind_ids = {pt.indicator_id for pt in existing_pts if pt.indicator_id}

            for ind in all_indicators:
                if ind.id not in existing_ind_ids:
                    bm = resolve_policy_benchmark(ind.code, ind.name)
                    new_pt = PolicyTarget(
                        id=uuid.uuid4(),
                        indicator_id=ind.id,
                        target_name=bm["target_name"],
                        target_value=bm["target_value"],
                        target_unit=bm["target_unit"],
                        target_period="FY25",
                        target_source=bm["citation"],
                        responsible_institution=bm["institution"],
                        source_citation=bm["citation"],
                        higher_is_better=bm["higher_is_better"],
                        importance_weight=1.0,
                    )
                    db.add(new_pt)
                    existing_ind_ids.add(ind.id)
            await db.flush()

            # 2. Re-fetch all policy targets
            pt_res = await db.execute(select(PolicyTarget))
            policy_targets = pt_res.scalars().all()

            gap_count = 0
            seen_target_keys = set()
            for pt in policy_targets:
                key = (pt.target_name or str(pt.id)).strip().lower()
                if key in seen_target_keys:
                    continue
                seen_target_keys.add(key)
                # Get latest observation for this target's indicator
                latest_obs_stmt = (
                    select(IndicatorObservation)
                    .where(IndicatorObservation.indicator_id == pt.indicator_id)
                    .order_by(IndicatorObservation.timestamp.desc())
                    .limit(1)
                )
                latest_obs = (await db.execute(latest_obs_stmt)).scalars().first()
                if not latest_obs:
                    continue

                # Normalize actual value scale if actual is in raw units (> 1e8) and target is scaled (< 1000)
                raw_actual_val = latest_obs.value
                target_val = pt.target_value or 1.0

                if abs(raw_actual_val) > 1e8 and abs(target_val) < 1000:
                    if abs(raw_actual_val) > 1e11:
                        norm_actual_val = raw_actual_val / 1e12
                    elif abs(raw_actual_val) > 1e8:
                        norm_actual_val = raw_actual_val / 1e9
                    elif abs(raw_actual_val) > 1e5:
                        norm_actual_val = raw_actual_val / 1e6
                    else:
                        norm_actual_val = raw_actual_val
                else:
                    norm_actual_val = raw_actual_val

                # Create a transient PolicyActual (not persisted separately — embed in gap)
                pa = PolicyActual(
                    id=uuid.uuid4(),
                    target_id=pt.id,
                    actual_value=norm_actual_val,
                    actual_period="Latest Ingestion Run",
                    actual_source="PEPR Auto-Evaluation",
                    data_quality_status=1.0,
                )
                db.add(pa)
                await db.flush()  # get pa.id without full commit

                # Fetch historical gaps for persistence scoring
                hist_gaps_res = await db.execute(
                    select(PolicyGap)
                    .where(PolicyGap.target_id == pt.id)
                    .order_by(PolicyGap.created_at.asc())
                )
                historical_gaps = hist_gaps_res.scalars().all()

                # Calculate and persist the gap
                gap = PolicyEngine.calculate_gap(target=pt, actual=pa, historical_gaps=historical_gaps)
                db.add(gap)
                gap_count += 1

            await db.commit()
            logger.info(f"Post-ingestion M4 Policy Engine evaluated {gap_count} policy gaps from live indicator data.")

        except Exception as policy_err:
            logger.warning(f"Post-ingestion M4 Policy Engine failed (non-fatal): {policy_err}", exc_info=True)
            await db.rollback()

        # M5 Emerging Problem Synthesizer — synthesizes Top 10 Emerging Economic Problems from 7-day database window
        try:
            from app.services.analysis.problem_synthesizer import run_emerging_problem_synthesis
            synthesized = await run_emerging_problem_synthesis(db)
            logger.info(f"Post-ingestion M5 Problem Synthesizer generated {len(synthesized)} emerging economic problems from 7-day database window.")
        except Exception as prob_err:
            logger.warning(f"Post-ingestion M5 Problem Synthesizer failed (non-fatal): {prob_err}", exc_info=True)
            await db.rollback()

    except Exception as e:
        logger.error(f"Post-ingestion analysis encountered error: {e}", exc_info=True)
