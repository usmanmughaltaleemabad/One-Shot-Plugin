---
type: reference
last_verified: 2026-05-21
owner: usman
---

# API Documentation Standards

## GEN-004: API Endpoints Documented in OpenAPI

**Rule:** All generated API endpoints must be documented in OpenAPI specification.

**Scope:**
- FastAPI: auto-generated via docstrings + type hints
- Django REST: explicit serializers + docstrings
- Spring: Swagger annotations

**Enforcement:** Generator produces openapi.json; reviewer validates schema matches endpoints.

**Valid Example (FastAPI):**
```python
@app.post("/carts", response_model=CartResponse)
async def create_cart(request: CartCreate) -> CartResponse:
    """Create a new shopping cart.
    
    Parameters:
      request: Cart creation details
    
    Returns:
      CartResponse: Created cart with ID
    """
    cart = Cart(**request.dict())
    db.add(cart)
    db.commit()
    return cart
```

**Invalid Example (caught by GEN-004):**
```python
@app.post("/carts")  # ❌ No docstring, missing response_model
def create_cart(request):
    return Cart()
```
