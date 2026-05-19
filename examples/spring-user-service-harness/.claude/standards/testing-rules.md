---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Spring Boot Testing Rules

## Use @SpringBootTest for integration, @WebMvcTest for controller slice

```java
@SpringBootTest
@AutoConfigureMockMvc
class UserControllerTest {
    @Autowired MockMvc mockMvc;

    @Test
    void createUser_returns201() throws Exception {
        mockMvc.perform(post("/api/users")
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"name\":\"Alice\",\"email\":\"alice@example.com\"}"))
            .andExpect(status().isCreated());
    }
}
```

## Coverage: 80% minimum via JaCoCo
