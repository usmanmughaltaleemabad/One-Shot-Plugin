---
type: reference
last_verified: 2026-05-21
owner: usman
---

# Foreign Key Validation Standards

Detailed rules for validating foreign key relationships (GEN-002).

## Validation Rules

1. **Type Match:** FK column type must match referenced PK type
2. **Model Exists:** Referenced model must be defined in the same generation or existing codebase
3. **No Circular References:** Unless explicitly handled with backref/back_populates
4. **Cascade Semantics:** ON DELETE behavior must match domain logic

## Validation Script

The hook runs this logic:
```python
def validate_foreign_keys(spec_json: dict, generated_files: list) -> bool:
    errors = []
    for entity in spec_json['entities']:
        for rel in entity.get('foreign_keys', []):
            # Check type match
            if not type_matches(rel['type'], rel['references_type']):
                errors.append(f"Type mismatch in {entity.name}.{rel.column}")
            
            # Check model exists
            if not model_exists(rel['references_model']):
                errors.append(f"Model {rel['references_model']} not found")
    
    return len(errors) == 0, errors
```
