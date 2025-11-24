def test_create_note(client):
    response = client.post(
        "/notes",
        json={"topic": "Test Note", "content": "This is a test note", "author": "Tester"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["topic"] == "Test Note"
    assert data["content"] == "This is a test note"
    assert data["author"] == "Tester"
    assert "id" in data
    assert "created_at" in data
    assert data["votes"] == 0

def test_create_note_default_author(client):
    response = client.post(
        "/notes",
        json={"topic": "Anonymous Note", "content": "Content"}
    )
    assert response.status_code == 201
    assert response.json()["author"] == "Anonymous"

def test_read_notes(client):
    # Create two notes
    client.post("/notes", json={"topic": "Note 1", "content": "Content 1"})
    client.post("/notes", json={"topic": "Note 2", "content": "Content 2"})
    
    response = client.get("/notes")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_read_note_by_id(client):
    create_response = client.post("/notes", json={"topic": "Target", "content": "Target Content"})
    note_id = create_response.json()["id"]
    
    response = client.get(f"/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["topic"] == "Target"

def test_read_note_not_found(client):
    response = client.get("/notes/999")
    assert response.status_code == 404

def test_update_note(client):
    create_response = client.post("/notes", json={"topic": "Old", "content": "Old Content"})
    note_id = create_response.json()["id"]
    
    response = client.put(
        f"/notes/{note_id}",
        json={"topic": "New", "content": "New Content"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["topic"] == "New"
    assert data["content"] == "New Content"

def test_delete_note(client):
    create_response = client.post("/notes", json={"topic": "To Delete", "content": "..."})
    note_id = create_response.json()["id"]
    
    response = client.delete(
        f"/notes/{note_id}",
        headers={"X-API-Key": "admin-secret"}
    )
    assert response.status_code == 200
    
    # Verify it's gone
    get_response = client.get(f"/notes/{note_id}")
    assert get_response.status_code == 404

def test_vote_note(client):
    create_response = client.post("/notes", json={"topic": "Vote Me", "content": "..."})
    note_id = create_response.json()["id"]
    
    response = client.post(f"/notes/{note_id}/vote")
    assert response.status_code == 200
    assert response.json()["votes"] == 1
    
    # Vote again
    response = client.post(f"/notes/{note_id}/vote")
    assert response.json()["votes"] == 2

def test_top_notes(client):
    # Create 3 notes
    id1 = client.post("/notes", json={"topic": "1", "content": "1"}).json()["id"]
    id2 = client.post("/notes", json={"topic": "2", "content": "2"}).json()["id"]
    id3 = client.post("/notes", json={"topic": "3", "content": "3"}).json()["id"]
    
    # Vote for note 2 twice
    client.post(f"/notes/{id2}/vote")
    client.post(f"/notes/{id2}/vote")
    
    # Vote for note 1 once
    client.post(f"/notes/{id1}/vote")
    
    response = client.get("/notes/top")
    data = response.json()
    
    assert len(data) >= 3
    assert data[0]["id"] == id2  # Most votes
    assert data[1]["id"] == id1  # Second most