import asyncio
from app.infrastructure.database import AsyncSessionLocal
from app.services.analysis.problem_synthesizer import run_emerging_problem_synthesis

async def main():
    async with AsyncSessionLocal() as db:
        print("=== SYNTHESIZING TOP 10 EMERGING ECONOMIC PROBLEMS FROM 7-DAY DATABASE ===")
        problems = await run_emerging_problem_synthesis(db)
        print(f"Synthesized {len(problems)} Top Emerging Problems:")
        for idx, p in enumerate(problems, 1):
            print(f"{idx}. [{p.severity}] {p.title}")

if __name__ == "__main__":
    asyncio.run(main())
