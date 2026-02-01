try:
    from fastapi import APIRouter, Request
except ImportError:
    APIRouter = Request = None
import random
import asyncio

router = APIRouter()

@router.post("/mock/clearbit/v2/companies/find")
async def mock_clearbit(request: Request):
    await asyncio.sleep(random.uniform(0.15, 0.25))
    if random.random() > 0.95:
        return {"error": "API failure"}
    data = await request.json()
    domain = data.get("domain", "test.com")
    return {
        "company": domain.split(".")[0].capitalize(),
        "domain": domain,
        "employee_count": random.randint(100, 10000),
        "tech_stack": random.sample(["salesforce", "aws", "react", "postgres", "kafka"], 3),
        "funding": {"stage": "series_b", "amount": 25000000},
        "confidence_score": round(random.uniform(0.7, 1.0), 2),
        "data_completeness": random.randint(60, 100)
    }
