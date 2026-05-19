---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Go Testing Rules

## Table-driven tests

```go
func TestCreateProduct(t *testing.T) {
    tests := []struct {
        name    string
        input   CreateProductRequest
        wantErr bool
    }{
        {"valid product", CreateProductRequest{Name: "Widget", Price: 9.99}, false},
        {"empty name",   CreateProductRequest{Name: "", Price: 9.99},         true},
    }
    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {
            _, err := svc.Create(context.Background(), tc.input)
            if (err != nil) != tc.wantErr {
                t.Errorf("got err=%v, wantErr=%v", err, tc.wantErr)
            }
        })
    }
}
```

## Coverage: `go test ./... -cover` — target 80%

## Integration tests use real DB (testcontainers-go or local Postgres)
