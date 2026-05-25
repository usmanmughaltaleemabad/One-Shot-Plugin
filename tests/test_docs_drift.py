import pytest
from pathlib import Path
from scripts.codebase_diff import extract_classes_and_functions, detect_changes, scan_codebase


def test_extract_classes():
    """Test extraction of classes and their methods."""
    code = '''
class User:
    def __init__(self, name):
        self.name = name
    def get_name(self):
        return self.name
'''
    entities = extract_classes_and_functions(code)
    assert len(entities["classes"]) == 1
    assert entities["classes"][0]["name"] == "User"
    assert "get_name" in entities["classes"][0]["methods"]
    assert "__init__" in entities["classes"][0]["methods"]


def test_extract_functions():
    """Test extraction of module-level functions."""
    code = '''
def helper(x, y):
    return x + y

def process():
    pass
'''
    entities = extract_classes_and_functions(code)
    assert len(entities["functions"]) == 2
    function_names = {f["name"] for f in entities["functions"]}
    assert "helper" in function_names
    assert "process" in function_names


def test_extract_imports():
    """Test extraction of imports."""
    code = '''
import os
from pathlib import Path
from typing import Dict, List
'''
    entities = extract_classes_and_functions(code)
    assert len(entities["imports"]) == 3


def test_detect_added_class():
    """Test detection of newly added classes."""
    old = {"file.py": {"classes": [], "functions": [], "imports": []}}
    new = {"file.py": {"classes": [{"name": "NewClass", "methods": [], "bases": []}], "functions": [], "imports": []}}
    changes = detect_changes(old, new)
    assert "NewClass" in changes["added_classes"]
    assert len(changes["removed_classes"]) == 0


def test_detect_removed_class():
    """Test detection of removed classes."""
    old = {"file.py": {"classes": [{"name": "OldClass", "methods": [], "bases": []}], "functions": [], "imports": []}}
    new = {"file.py": {"classes": [], "functions": [], "imports": []}}
    changes = detect_changes(old, new)
    assert "OldClass" in changes["removed_classes"]
    assert len(changes["added_classes"]) == 0


def test_detect_added_function():
    """Test detection of newly added functions."""
    old = {"file.py": {"classes": [], "functions": [], "imports": []}}
    new = {"file.py": {"classes": [], "functions": [{"name": "helper", "params": ["x"]}], "imports": []}}
    changes = detect_changes(old, new)
    assert "helper" in changes["added_functions"]
    assert len(changes["removed_functions"]) == 0


def test_detect_removed_function():
    """Test detection of removed functions."""
    old = {"file.py": {"classes": [], "functions": [{"name": "old_helper", "params": []}], "imports": []}}
    new = {"file.py": {"classes": [], "functions": [], "imports": []}}
    changes = detect_changes(old, new)
    assert "old_helper" in changes["removed_functions"]
    assert len(changes["added_functions"]) == 0


def test_detect_multiple_changes():
    """Test detection of multiple changes across classes and functions."""
    old = {
        "file.py": {
            "classes": [{"name": "Old", "methods": [], "bases": []}],
            "functions": [{"name": "old_func", "params": []}],
            "imports": []
        }
    }
    new = {
        "file.py": {
            "classes": [{"name": "New", "methods": [], "bases": []}],
            "functions": [{"name": "new_func", "params": ["x"]}],
            "imports": []
        }
    }
    changes = detect_changes(old, new)
    assert "New" in changes["added_classes"]
    assert "Old" in changes["removed_classes"]
    assert "new_func" in changes["added_functions"]
    assert "old_func" in changes["removed_functions"]


def test_class_with_inheritance():
    """Test extraction of classes with base classes."""
    code = '''
class Parent:
    pass

class Child(Parent):
    def method(self):
        pass
'''
    entities = extract_classes_and_functions(code)
    assert len(entities["classes"]) == 2
    child = next((c for c in entities["classes"] if c["name"] == "Child"), None)
    assert child is not None
    assert "Parent" in child["bases"]


def test_syntax_error_handling():
    """Test that syntax errors are handled gracefully."""
    code = '''
def broken(:
    pass
'''
    entities = extract_classes_and_functions(code)
    assert entities == {"classes": [], "functions": [], "imports": []}


def test_nested_functions_not_extracted():
    """Nested functions should not be extracted as module-level functions."""
    code = '''
def outer():
    def inner():
        pass
    return inner
'''
    entities = extract_classes_and_functions(code)
    # Should only have 'outer', not 'inner'
    assert len(entities["functions"]) == 1
    assert entities["functions"][0]["name"] == "outer"
