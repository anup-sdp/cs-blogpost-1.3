# tests/test_demo.py:
# sync approach to testing a FastAPI app using TestClient (extra file)
from fastapi import FastAPI
from fastapi.testclient import TestClient

demo_app = FastAPI()

@demo_app.get("/")
def demo_home():
    return {"message": "Hello!"}

client  = TestClient(demo_app)

def test_homepage():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello!"}


# uv run pytest tests/test_demo.py -v

"""
psycopg = Sync PostgreSQL driver (this file uses TestClient, which is synchronous)
asyncpg = Async PostgreSQL driver
httpx = Async HTTP client for testing FastAPI endpoints
"""