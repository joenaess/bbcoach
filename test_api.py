"""
Test the new FastAPI backend
"""
import sys
import os

sys.path.append(os.path.abspath("src"))

import requests
import json


def test_api():
    """Test the FastAPI endpoints"""
    base_url = "http://localhost:8000"

    print("Testing BBCoach API...")
    print("=" * 50)

    # Test health
    print("\n1. Health Check")
    response = requests.get(f"{base_url}/health")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.json()}")

    # Test data status
    print("\n2. Data Status")
    response = requests.get(f"{base_url}/api/data/status")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.json()}")

    # Test seasons
    print("\n3. Get Seasons")
    response = requests.get(f"{base_url}/api/stats/seasons")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.json()}")

    # Test teams
    if response.json().get("seasons"):
        season = response.json()["seasons"][0]
        print(f"\n4. Get Teams for season {season}")
        response = requests.get(f"{base_url}/api/stats/teams?season={season}")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Teams: {len(data.get('teams', []))}")

        # Test top players
        print(f"\n5. Get Top Players for season {season}")
        response = requests.get(f"{base_url}/api/stats/top-players?season={season}")
        print(f"   Status: {response.status_code}")
        data = response.json()
        print(f"   Top Players: {len(data.get('players', []))}")

    # Test coach model info
    print("\n6. Coach Model Info")
    response = requests.get(f"{base_url}/api/coach/model-info")
    print(f"   Status: {response.status_code}")
    print(f"   Data: {response.json()}")

    print("\n" + "=" * 50)
    print("API tests complete!")


if __name__ == "__main__":
    try:
        test_api()
    except requests.exceptions.ConnectionError:
        print("ERROR: Could not connect to API server.")
        print("Make sure the server is running: uv run python -m api.main")
    except Exception as e:
        print(f"ERROR: {e}")
