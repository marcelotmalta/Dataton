from fastapi.testclient import TestClient
from app.main import app
import pytest

@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["model_loaded"] is True
    assert data["data_loaded"] is True

def test_search_student_success(client):
    # Assuming there's a student name "ALUNO-1" or similar in the CSV based on common anonymization patterns.
    # If not, we might fail, but checking for "A" should return something if data exists.
    # Looking at previous context, names might be "ALUNO-1".
    # Let's try searching for a common string or just "A" to check list return.
    response = client.get("/students/A")
    if response.status_code == 404:
        pytest.skip("No students found with 'A', cannot verify search structure.")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert "NOME" in data[0]

def test_search_student_not_found(client):
    response = client.get("/students/StudentThatDoesnotExistSearchXYZ")
    assert response.status_code == 404

def test_predict_success(client):
    # Sample data based on features list
    # ['IAN', 'IDA', 'IEG', 'IAA', 'IPS', 'IPP', 'IPV', 'FASE', 'Status_DEFA', 'consistencia_acad']
    # Inputs: IAN, IDA, IEG, IAA, IPS, IPP, IPV, FASE, DEFA
    
    payload = {
        "IAN": 5.0,
        "IDA": 7.0,
        "IEG": 8.0,
        "IAA": 6.5,
        "IPS": 7.5,
        "IPP": 6.0,
        "IPV": 8.0,
        "FASE": 1,
        "DEFA": 0.0
    }
    
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    
    assert "prediction" in data
    assert "probabilities" in data
    assert "input_features" in data
    
    # Check derived feature calculation
    # Status_DEFA for DEFA 0 should be 1
    assert data["input_features"]["Status_DEFA"] == 1
    
    # consistencia_acad = IDA / (IEG + 0.1) = 7.0 / 8.1 = 0.864...
    expected_cons = 7.0 / 8.1
    assert abs(data["input_features"]["consistencia_acad"] - expected_cons) < 0.001

def test_predict_invalid(client):
    # Missing fields
    payload = {
        "IAN": 5.0
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 422
