# Example: nestjs-realtime-api

NestJS 10 service exposing GraphQL subscriptions backed by Redis pub/sub.
Consumes `order.created`, `order.shipped`, `order.delivered` and pushes to
WebSocket subscribers in real time.

## Original prompt

```
/one-shot-prompting:one-shot-generator
Add NestJS GraphQL subscription for order status updates. Backend uses
Redis pub/sub. Include DI, WebSocket transport, RxJS pipes, Jest e2e tests.
@./
```

## Generated assumptions block (excerpt)

```
- Framework: NestJS 10 (detected @nestjs/core in package.json)
- GraphQL: @nestjs/graphql code-first
- Transport: graphql-ws over WebSocket
- Pub/Sub: graphql-subscriptions backed by Redis (ioredis)
- Tests: Jest 29 + supertest + ws-client
- Convention: 2-space indent, prefer const, full DI
```

## Files generated (8)

| File | Purpose | LOC |
|------|---------|-----|
| `src/orders/orders.module.ts` | module definition | 30 |
| `src/orders/orders.resolver.ts` | GraphQL resolver + subscription | 70 |
| `src/orders/orders.service.ts` | publishing logic | 50 |
| `src/pubsub/pubsub.module.ts` | Redis-backed pub/sub provider | 40 |
| `src/orders/orders.spec.ts` | unit tests | 90 |
| `test/orders.e2e-spec.ts` | end-to-end WebSocket test | 110 |
| `Dockerfile` | Node 20 multi-stage | 25 |
| `package.json` | scripts + deps | 50 |

## Run

```bash
npm install
npm run start:dev
npm run test
```
