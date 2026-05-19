# Example: spring-payment-service

> [!NOTE]
> **This is an example *prompt*, not a runnable project.** The directory
> contains only this README. Run the prompt below against your own
> Spring Boot codebase to produce the files listed.

Spring Boot 3 service implementing a saga step in a payments pipeline.
Consumes `order.placed`, charges via Stripe, emits `payment.captured` or
`payment.failed`, and rolls back via a compensating handler.

## Original prompt

```
/one-shot-prompting:one-shot-generator
Add a Spring Boot saga step that consumes order.placed via Kafka, charges
through Stripe, emits payment.captured on success or payment.failed on
error. Include compensating handler for inventory.release, JPA entity for
audit, Flyway migration, JUnit 5 tests. @./
```

## Generated assumptions block (excerpt)

```
- Framework: Spring Boot 3.1 (detected pom.xml + spring-boot-starter-web)
- Persistence: JPA + Hibernate (detected spring-boot-starter-data-jpa)
- Migrations: Flyway (detected spring-boot-starter-flyway)
- Bus: spring-kafka (detected on classpath)
- Tests: JUnit 5 + Mockito + Testcontainers
- Validation: Bean Validation 3 (jakarta.validation)
- Convention: 4-space indent, Lombok for boilerplate
```

## Files generated (10)

| File | Purpose | LOC |
|------|---------|-----|
| `PaymentController.java` | REST endpoint for manual replay | 40 |
| `PaymentService.java` | Stripe integration | 80 |
| `PaymentSagaListener.java` | Kafka @KafkaListener | 65 |
| `CompensatingHandler.java` | inventory.release listener | 50 |
| `Payment.java` | JPA entity | 40 |
| `PaymentRepository.java` | Spring Data repository | 15 |
| `db/migration/V1__init.sql` | Flyway baseline | 25 |
| `PaymentSagaListenerTest.java` | unit + slice tests | 110 |
| `PaymentServiceIT.java` | integration test w/ testcontainers | 80 |
| `application.yml` | profile-specific config | 35 |

## Run

```bash
mvn spring-boot:run
mvn verify
```
