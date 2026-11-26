from api.memory_store import (
    add_memory, authenticate, create_workspace, delete_memory, list_memories, retrieve,
)


def test_workspace_is_private_and_memory_crud_works(tmp_path):
    db = tmp_path / "app.sqlite3"
    workspace = create_workspace(db)
    assert authenticate(workspace["workspace_id"], workspace["workspace_key"], db)
    assert not authenticate(workspace["workspace_id"], "wrong-key", db)

    saved = add_memory(workspace["workspace_id"], "MemWeave studies conversational memory.", "notes", db)
    items = list_memories(workspace["workspace_id"], db_path=db)
    assert len(items) == 1
    assert items[0]["id"] == saved["id"]

    matches = retrieve(workspace["workspace_id"], "conversational memory", db_path=db)
    assert len(matches) == 1
    assert matches[0]["matched_terms"] == ["conversational", "memory"]

    assert delete_memory(workspace["workspace_id"], saved["id"], db)
    assert list_memories(workspace["workspace_id"], db_path=db) == []


def test_workspaces_do_not_share_memories(tmp_path):
    db = tmp_path / "app.sqlite3"
    first = create_workspace(db)
    second = create_workspace(db)
    add_memory(first["workspace_id"], "private first workspace note", db_path=db)
    assert list_memories(second["workspace_id"], db_path=db) == []
