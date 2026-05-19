"""
Phase 2 Runner - Integration with SKILL.md

Called when user runs:
/one-shot-prompting:generate "Add user CRUD API" @/project --phase2

or automatically detected when request is for REST API generation.

Coordinates:
1. Codebase analysis
2. Framework detection
3. REST API generation
4. Validation
5. Test generation
6. Documentation
"""

import sys
import json
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
from typing import Dict, Any, List, Optional


def parse_arguments(args_string: str) -> Dict[str, Any]:
    """Parse command arguments into config"""
    # Parse format: "Add user CRUD API @/project --options"
    parts = args_string.split()

    config = {
        "description": "",
        "project_path": None,
        "framework": None,
        "language": None,
        "resources": [],
        "options": {}
    }

    # Extract project path
    for part in parts:
        if part.startswith("@"):
            config["project_path"] = part[1:]
        elif part.startswith("--"):
            key = part[2:]
            config["options"][key] = True

    # Use first few words as description
    config["description"] = " ".join(p for p in parts if not p.startswith("@") and not p.startswith("--"))

    return config


def detect_resource_from_description(description: str) -> Optional[Dict[str, Any]]:
    """
    Detect resource name and type from description.

    Examples:
    - "Add user CRUD API" -> {"name": "user", "plural": "users", "type": "crud"}
    - "Create product REST endpoints" -> {"name": "product", "plural": "products"}
    """
    words = description.lower().split()

    # Find potential resource name (usually first noun-like word)
    resource_name = None
    for word in words:
        if word not in ["add", "create", "generate", "build", "api", "crud", "rest", "endpoints"]:
            resource_name = word
            break

    if not resource_name:
        return None

    return {
        "name": resource_name,
        "plural": f"{resource_name}s",  # Simple pluralization
        "schema": {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "name": {"type": "string"},
                "description": {"type": "string"},
                "created_at": {"type": "string", "format": "date-time"},
                "updated_at": {"type": "string", "format": "date-time"}
            }
        }
    }


def infer_config_from_codebase(project_path: str) -> Dict[str, str]:
    """
    Infer framework and language from codebase.

    Returns: {framework: str, language: str}
    """
    # Check for framework indicators
    indicators = {
        "django": ["manage.py", "django.conf", "settings.py"],
        "fastapi": ["fastapi", "main.py", "app.py"],
        "spring": ["pom.xml", "build.gradle", "Spring"],
        "nestjs": ["package.json", "@nestjs"],
        "go": ["go.mod", "go.sum", "main.go"]
    }

    framework = "fastapi"  # Default
    language = "python"  # Default

    try:
        project = Path(project_path)
        for file in project.rglob("*"):
            content_str = str(file)

            for fw, signs in indicators.items():
                if any(sign in content_str for sign in signs):
                    framework = fw
                    if fw == "spring":
                        language = "java"
                    elif fw == "go":
                        language = "go"
                    elif fw == "nestjs":
                        language = "typescript"
                    break
    except:
        pass  # Use defaults

    return {"framework": framework, "language": language}


def run_phase2_generation(args_string: str) -> Dict[str, Any]:
    """
    Main Phase 2 runner.

    Args:
        args_string: Full argument string from user

    Returns: Generation result with code, tests, docs
    """
    print("🚀 Phase 2: REST API Specialist Generation Starting...")

    # Parse arguments
    config = parse_arguments(args_string)
    print(f"  Input: {config['description']}")
    print(f"  Project: {config['project_path']}")

    # Detect resource from description
    resource = detect_resource_from_description(config['description'])
    if not resource:
        return {"error": "Could not detect resource from description", "status": "failed"}

    print(f"  Detected resource: {resource['name']}")
    config['resources'] = [resource]

    # Infer framework from project
    if config['project_path']:
        inferred = infer_config_from_codebase(config['project_path'])
        config['framework'] = inferred['framework']
        config['language'] = inferred['language']
    else:
        config['framework'] = "fastapi"  # Default
        config['language'] = "python"

    print(f"  Framework detected: {config['framework']} ({config['language']})")

    # Generate API
    try:
        from phase2_rest_api import orchestrate_phase2

        phase2_config = {
            "framework": config['framework'],
            "language": config['language'],
            "api_name": f"{resource['name'].capitalize()} Service",
            "api_version": "v1",
            "base_path": "/api/v1",
            "resources": config['resources'],
            "include_tests": True,
            "include_docs": True,
            "include_pagination": True,
            "include_filtering": True,
            "include_auth": True
        }

        result = orchestrate_phase2(phase2_config)

        print(f"✅ Phase 2 generation complete!")
        print(f"  Generated {result['files_generated']} files")

        return {
            "status": "success",
            "phase": "phase2",
            "framework": config['framework'],
            "language": config['language'],
            "resource": resource['name'],
            **result
        }

    except Exception as e:
        print(f"❌ Generation failed: {str(e)}")
        return {
            "status": "failed",
            "error": str(e),
            "phase": "phase2"
        }


# Entry point
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python phase2_runner.py <arguments>")
        sys.exit(1)

    args_string = " ".join(sys.argv[1:])
    result = run_phase2_generation(args_string)

    print("\n" + "="*60)
    print("GENERATION RESULT")
    print("="*60)
    print(json.dumps(result, indent=2, default=str))
