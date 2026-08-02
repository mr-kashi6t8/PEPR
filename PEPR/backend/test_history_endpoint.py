import asyncio
import httpx

async def test_history():
    async with httpx.AsyncClient(base_url="http://localhost:8000/api/v1", follow_redirects=True, timeout=30.0) as client:
        r_sum = await client.get("/indicators/summary")
        indicators = r_sum.json()
        print(f"Loaded {len(indicators)} indicators from summary endpoint.")
        
        for ind in indicators[:3]:
            ind_id = ind["id"]
            ind_name = ind["name"]
            r_hist = await client.get(f"/indicators/{ind_id}/history")
            print(f"Indicator '{ind_name}' ({ind['code']}): Status={r_hist.status_code}")
            if r_hist.status_code == 200:
                hist_data = r_hist.json().get("history", [])
                print(f"  -> Successfully returned {len(hist_data)} time-series points!")

if __name__ == "__main__":
    asyncio.run(test_history())
