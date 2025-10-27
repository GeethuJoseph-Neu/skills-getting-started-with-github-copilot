import copy
import urllib.parse

import pytest
from fastapi.testclient import TestClient

import src.app as app_module

client = TestClient(app_module.app)

# Keep an immutable copy of the original in-memory data so tests can reset state
ORIG_ACTIVITIES = copy.deepcopy(app_module.activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities mapping before each test so tests are independent."""
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(ORIG_ACTIVITIES))
    yield


def test_get_activities_returns_data():
    resp = client.get("/activities")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "participants" in data["Chess Club"]


def test_signup_and_prevent_duplicate():
    activity = "Chess Club"
    email = "newstudent@mergington.edu"

    # Sign up should succeed first time
    resp = client.post(f"/activities/{urllib.parse.quote(activity)}/signup", params={"email": email})
    assert resp.status_code == 200
    body = resp.json()
    assert "Signed up" in body.get("message", "")

    # Signing up again should be rejected (400)
    resp2 = client.post(f"/activities/{urllib.parse.quote(activity)}/signup", params={"email": email})
    assert resp2.status_code == 400


def test_unregister_existing_participant():
    activity = "Chess Club"
    # michael@mergington.edu exists in the initial data
    email = "michael@mergington.edu"

    # Ensure participant exists initially
    resp0 = client.get("/activities")
    assert email in resp0.json()[activity]["participants"]

    # Delete the participant
    resp = client.delete(f"/activities/{urllib.parse.quote(activity)}/participants", params={"email": email})
    assert resp.status_code == 200
    body = resp.json()
    assert f"Removed {email}" in body.get("message", "")

    # Confirm participant is removed
    resp2 = client.get("/activities")
    assert email not in resp2.json()[activity]["participants"]


def test_unregister_nonexistent_participant_returns_404():
    activity = "Chess Club"
    email = "doesnotexist@mergington.edu"

    resp = client.delete(f"/activities/{urllib.parse.quote(activity)}/participants", params={"email": email})
    assert resp.status_code == 404