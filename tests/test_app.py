from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


INITIAL_ACTIVITIES = deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client():
    return TestClient(app)


def test_get_activities_returns_seeded_data(client):
    # Arrange
    expected_activities = deepcopy(INITIAL_ACTIVITIES)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json() == expected_activities


def test_signup_adds_valid_email(client):
    # Arrange
    activity_name = "Tennis Club"
    email = "student@example.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_rejects_malformed_email_without_mutating_state(client):
    # Arrange
    activity_name = "Tennis Club"
    participants_before = deepcopy(activities[activity_name]["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "not-an-email"},
    )

    # Assert
    assert response.status_code == 422
    assert activities[activity_name]["participants"] == participants_before


def test_signup_returns_404_for_unknown_activity(client):
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_returns_400_for_duplicate_email(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_400_when_activity_is_full(client):
    # Arrange
    activity_name = "Tennis Club"
    activity = activities[activity_name]
    activity["participants"] = [
        f"student{index}@example.edu"
        for index in range(activity["max_participants"])
    ]
    participants_before = deepcopy(activity["participants"])

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@example.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"
    assert activity["participants"] == participants_before


def test_unregister_removes_valid_email(client):
    # Arrange
    activity_name = "Volleyball Team"
    email = "student@example.edu"
    activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_unregister_rejects_malformed_email_without_mutating_state(client):
    # Arrange
    activity_name = "Volleyball Team"
    participants_before = deepcopy(activities[activity_name]["participants"])

    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/not-an-email"
    )

    # Assert
    assert response.status_code == 422
    assert activities[activity_name]["participants"] == participants_before


def test_unregister_returns_404_for_unknown_activity(client):
    # Arrange
    email = "student@example.edu"

    # Act
    response = client.delete(f"/activities/Unknown Club/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_404_when_email_is_not_registered(client):
    # Arrange
    activity_name = "Volleyball Team"
    email = "student@example.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/participants/{email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_root_redirects_to_static_index(client):
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location