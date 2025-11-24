def test_pin_note(client):
    # Create a note
    create_response = client.post(
        "/notes",
        json={"topic": "Important Note", "content": "This should be pinned"}
    )
    note_id = create_response.json()["id"]
    
    # Pin the note
    response = client.post(f"/notes/{note_id}/pin")
    
    # Assertions
    assert response.status_code == 200
    data = response.json()
    assert data["pinned"] is True
    
    # Verify persistence
    get_response = client.get(f"/notes/{note_id}")
    assert get_response.json()["pinned"] is True