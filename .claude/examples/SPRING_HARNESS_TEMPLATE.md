---
type: example
last_verified: 2026-05-17
owner: claude
---

# Spring Boot Project Harness Template

**Framework**: Spring Boot 3.2+, JPA, Maven  
**Features**: REST APIs, transaction management, security  

## .claude/CLAUDE.md

```markdown
---
type: router
last_verified: 2026-05-17
owner: claude
---

# Spring Boot Project

## Quick Links

| For... | See... |
|--------|--------|
| Code style | `.claude/standards/code-style-spring.md` |
| Testing | `.claude/standards/testing-rules.md` |
| Security | `.claude/standards/security-rules.md` |

## Critical Rules

1. All endpoints return ResponseEntity<>
2. Use @Service for business logic
3. All database operations through @Repository
4. Transactions: @Transactional on service methods
5. Exception handling via @ControllerAdvice
6. Tests: 80%+ coverage with MockMvc
```

## .claude/standards/code-style-spring.md

```markdown
# Spring Boot Code Style

## Controller Pattern

```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @Autowired
    private UserService userService;
    
    @GetMapping
    public ResponseEntity<List<UserResponse>> listUsers(
            @RequestParam(defaultValue = "0") int page) {
        return ResponseEntity.ok(userService.listUsers(page));
    }
    
    @PostMapping
    public ResponseEntity<UserResponse> createUser(@RequestBody UserCreateRequest req) {
        return ResponseEntity.status(HttpStatus.CREATED)
                .body(userService.createUser(req));
    }
}
```

## Service Pattern

```java
@Service
@Transactional
public class UserService {
    
    @Autowired
    private UserRepository userRepository;
    
    public List<UserResponse> listUsers(int page) {
        return userRepository.findAll(PageRequest.of(page, 10))
                .map(UserResponse::from)
                .toList();
    }
    
    public UserResponse createUser(UserCreateRequest req) {
        User user = new User(req.getEmail(), req.getName());
        userRepository.save(user);
        return UserResponse.from(user);
    }
}
```

## JPA Entity

```java
@Entity
@Table(name = "users")
public class User {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String email;
    
    @Column(nullable = false)
    private String name;
    
    @CreationTimestamp
    private LocalDateTime createdAt;
}
```
```

## .claude/standards/testing-rules.md

```markdown
# Spring Boot Testing (MockMvc)

## Minimum Coverage: 80%

```bash
mvn test jacoco:report
```

## Test Pattern

```java
@WebMvcTest(UserController.class)
public class UserControllerTest {
    
    @Autowired
    private MockMvc mockMvc;
    
    @MockBean
    private UserService userService;
    
    @Test
    void testListUsers() throws Exception {
        mockMvc.perform(get("/api/users"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$", hasSize(0)));
    }
    
    @Test
    void testCreateUser() throws Exception {
        UserCreateRequest req = new UserCreateRequest("test@example.com", "Test");
        mockMvc.perform(post("/api/users")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content(new ObjectMapper().writeValueAsString(req)))
                .andExpect(status().isCreated());
    }
}
```
```

## .claude/standards/security-rules.md

```markdown
# Spring Boot Security

## Authentication

```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
                .csrf().disable()
                .authorizeRequests()
                    .requestMatchers("/api/auth/**").permitAll()
                    .anyRequest().authenticated()
                .and()
                .httpBasic()
                .and().build();
    }
}
```

## SQL Injection Prevention

- ✅ Use JPA @Query with parameters: `@Query("SELECT u FROM User u WHERE u.email = ?1")`
- ✅ Use native queries with `nativeQuery=true` + parameterized
- ❌ Never concatenate SQL strings

## Secrets Management

```yaml
# application.yml
spring:
  datasource:
    url: ${DB_URL}
    username: ${DB_USER}
    password: ${DB_PASSWORD}
```
```
