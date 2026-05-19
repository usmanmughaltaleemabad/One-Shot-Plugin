---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Spring Boot Code Style

## Controller pattern

```java
@RestController
@RequestMapping("/api/users")
@RequiredArgsConstructor
public class UserController {
    private final UserService userService;

    @PostMapping
    @ResponseStatus(HttpStatus.CREATED)
    public UserResponse createUser(@Valid @RequestBody UserRequest request) {
        return userService.createUser(request);
    }
}
```

## Service layer

Business logic in `@Service` classes. Controllers only delegate.

## Repository

Use `JpaRepository` interfaces. No native SQL unless justified in a comment.

## Validation

Use Bean Validation (`@Valid`, `@NotBlank`, `@Email`) on all request DTOs.
