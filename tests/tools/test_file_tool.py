import pytest
import os
from pathlib import Path
from familiar_agent.tools.file_tool import FileTool

@pytest.fixture
def temp_workspace(tmp_path):
    """Fixture to provide a clean temporary workspace for testing."""
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    return workspace

@pytest.fixture
def file_tool(temp_workspace):
    """Fixture to provide a FileTool instance pointed at the temp workspace."""
    return FileTool(base_dir=temp_workspace)

def test_write_and_read_file(file_tool, temp_workspace):
    """Test basic write and read operations."""
    filename = "test.txt"
    content = "Hello, familiar-ai!"
    
    # Write
    result = file_tool.write_file(filename, content)
    assert "Successfully" in result
    assert (temp_workspace / filename).read_text(encoding="utf-8") == content
    
    # Read
    read_result = file_tool.read_file(filename)
    assert read_result == content

def test_read_non_existent_file(file_tool):
    """Test reading a file that doesn't exist."""
    result = file_tool.read_file("ghost.txt")
    assert "Error" in result

def test_list_files(file_tool, temp_workspace):
    """Test listing files in the workspace."""
    (temp_workspace / "file1.txt").write_text("1")
    (temp_workspace / "file2.txt").write_text("2")
    
    result = file_tool.list_files()
    assert "file1.txt" in result
    assert "file2.txt" in result

def test_read_truncation(file_tool, temp_workspace):
    """Test that reading is truncated to max_lines."""
    large_file = temp_workspace / "large.txt"
    large_file.write_text("\n".join([str(i) for i in range(200)]))
    
    result = file_tool.read_file("large.txt", max_lines=50)
    assert "--- [Truncated" in result
    # Check that it roughly matches the expected line count
    assert len(result.splitlines()) >= 50

def test_safety_denylist(file_tool):
    """Test that restricted files are blocked."""
    denied_files = [".env", "ME.md", "pyproject.toml"]
    for f in denied_files:
        # Try to write
        write_res = file_tool.write_file(f, "bad")
        assert "Error: Access denied" in write_res
        
        # Try to read
        read_res = file_tool.read_file(f)
        assert "Error" in read_res and "access denied" in read_res

def test_safety_directory_traversal(file_tool):
    """Test that directory traversal (..) is blocked."""
    # Attempt to access something outside the workspace
    result = file_tool.read_file("../some_secret.txt")
    assert "Error" in result or "access denied" in result

@pytest.mark.asyncio
async def test_see_file(file_tool, temp_workspace):
    """Test reading an image file as base64."""
    img_path = temp_workspace / "test.jpg"
    img_path.write_bytes(b"fake-jpeg-data")
    
    msg, b64 = await file_tool.call("see_file", {"filename": "test.jpg"})
    assert b64 is not None
    assert "You are looking at" in msg

def test_write_subdir(file_tool, temp_workspace):
    """Test writing to a nested subdirectory."""
    filename = "notes/daily/2026-02-26.txt"
    content = "Self-reflection entry."
    
    result = file_tool.write_file(filename, content)
    assert "Successfully" in result
    assert (temp_workspace / filename).exists()
    assert (temp_workspace / filename).read_text() == content
