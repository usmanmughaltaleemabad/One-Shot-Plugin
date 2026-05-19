---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Go Code Style

## Handler pattern

```go
func (h *ProductHandler) CreateProduct(w http.ResponseWriter, r *http.Request) {
    var req CreateProductRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "invalid request body", http.StatusBadRequest)
        return
    }
    product, err := h.svc.Create(r.Context(), req)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(product)
}
```

## Service layer

`internal/service/` holds business logic. Handlers only parse + delegate.

## Errors

Return errors up the stack. Use `fmt.Errorf("context: %w", err)` for wrapping.

## No globals

Inject dependencies via struct fields. No package-level vars for DB connections.
