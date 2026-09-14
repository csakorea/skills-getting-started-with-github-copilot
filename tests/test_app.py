from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original_activities)


def test_get_activities_returns_activity_catalog(client):
    # Arrange
    expected_participant = "michael@mergington.edu"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert "Chess Club" in response_data
    assert expected_participant in response_data["Chess Club"]["participants"]


def test_root_redirects_to_static_index(client):
    # Arrange
    client = TestClient(app, follow_redirects=False)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_signup_adds_participant_to_activity(client):
    # Arrange
    activity_name = "Basketball Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity_without_mutation(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_name not in activities


def test_signup_rejects_duplicate_participant_without_mutation(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }
    assert activities[activity_name]["participants"] == original_participants


def test_unregister_removes_participant_from_activity(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {activity_name}"
    }
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity_without_mutation(client):
    # Arrange
    activity_name = "Unknown Club"
    email = "student@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
    assert activity_name not in activities


def test_unregister_rejects_non_participant_without_mutation(client):
    # Arrange
    activity_name = "Chess Club"
    email = "absent.student@mergington.edu"
    original_participants = activities[activity_name]["participants"].copy()

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }
    assert activities[activity_name]["participants"] == original_participants
