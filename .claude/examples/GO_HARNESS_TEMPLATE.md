---
type: example
last_verified: 2026-05-17
owner: claude
---

# Go Project Harness Template

**Framework**: Go 1.21+, Chi router, stdlib  
**Features**: Goroutines, interfaces, error handling

## .claude/CLAUDE.md

```markdown
---
type: router
last_verified: 2026-05-17
owner: claude
---

# Go Project

## Quick Links

| For... | See... |
|--------|--------|
| Code style | `.claude/standards/code-style-go.md` |
| Testing | `.claude/standards/testing-rules.md` |
| Security | `.claude/standards/security-rules.md` |

## Critical Rules

1. Use Chi router for HTTP endpoints
2. All errors must be handled (never ignore)
3. Interfaces over concretions
4. Use context.Context for cancellation
5. No global state (dependency injection)
```

## .claude/standards/code-style-go.md

```markdown
# Go Code Style

## Handler Pattern

```go
type UserHandler struct {
    service UserService
}

func (h *UserHandler) ListUsers(w http.ResponseWriter, r *http.Request) {
    users, err := h.service.ListUsers(r.Context())
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    json.NewEncoder(w).Encode(users)
}

func (h *UserHandler) CreateUser(w http.ResponseWriter, r *http.Request) {
    var req struct {
        Email string `json:"email"`
        Name  string `json:"name"`
    }
    
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request", http.StatusBadRequest)
        return
    }
    
    user, err := h.service.CreateUser(r.Context(), req.Email, req.Name)
    if err != nil {
        http.Error(w, err.Error(), http.StatusInternalServerError)
        return
    }
    
    w.Header().Set("Content-Type", "application/json")
    w.WriteHeader(http.StatusCreated)
    json.NewEncoder(w).Encode(user)
}
```

## Router Setup

```go
func NewRouter(userService UserService) *chi.Mux {
    r := chi.NewRouter()
    h := &UserHandler{service: userService}
    
    r.Get("/api/users", h.ListUsers)
    r.Post("/api/users", h.CreateUser)
    
    return r
}
```

## Error Handling

```go
// ❌ WRONG
users := getAllUsers()  // Ignores error

// ✅ CORRECT
users, err := getAllUsers()
if err != nil {
    return fmt.Errorf("failed to get users: %w", err)
}
```
```

## .claude/standards/testing-rules.md

```markdown
# Go Testing

## Minimum Coverage: 80%

```bash
go test ./... -cover
go test ./... -coverprofile=coverage.out
go tool cover -html=coverage.out
```

## Test Pattern

```go
func TestListUsers(t *testing.T) {
    service := &mockUserService{
        users: []User{{ID: 1, Email: "test@example.com"}},
    }
    
    handler := &UserHandler{service: service}
    req := httptest.NewRequest("GET", "/api/users", nil)
    w := httptest.NewRecorder()
    
    handler.ListUsers(w, req)
    
    if w.Code != http.StatusOK {
        t.Errorf("Expected 200, got %d", w.Code)
    }
}
```
```

## .claude/standards/security-rules.md

```markdown
# Go Security

## SQL Injection Prevention

```go
// ❌ WRONG
query := fmt.Sprintf("SELECT * FROM users WHERE id = %d", userID)
rows, err := db.Query(query)

// ✅ CORRECT
query := "SELECT * FROM users WHERE id = $1"
rows, err := db.Query(query, userID)
```

## Input Validation

```go
if len(email) == 0 || len(name) == 0 {
    return fmt.Errorf("email and name are required")
}
```
```
