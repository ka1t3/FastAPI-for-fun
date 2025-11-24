import pytest

API_KEY = "admin-secret"

def test_delete_note_no_auth(client):
    # Create a note first
    create_response = client.post("/notes", json={"topic": "To Delete", "content": "..."})
    note_id = create_response.json()["id"]
    
    # Try to delete without auth header
    response = client.delete(f"/notes/{note_id}")
    assert response.status_code == 403
    assert response.json() == {"detail": "Not authenticated"}

def test_delete_note_invalid_auth(client):
    # Create a note first
    create_response = client.post("/notes", json={"topic": "To Delete", "content": "..."})
    note_id = create_response.json()["id"]
    
    # Try to delete with wrong key
    response = client.delete(
        f"/notes/{note_id}",
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 403
    assert response.json() == {"detail": "Could not validate credentials"}

def test_delete_note_valid_auth(client):
    # Create a note first
    create_response = client.post("/notes", json={"topic": "To Delete", "content": "..."})
    note_id = create_response.json()["id"]
    
    # Delete with correct key
    response = client.delete(
        f"/notes/{note_id}",
        headers={"X-API-Key": API_KEY}
    )
    assert response.status_code == 200
    assert response.json() == {"message": "Note deleted successfully"}
    
    # Verify it's gone
    get_response = client.get(f"/notes/{note_id}")
    assert get_response.status_code == 404