---
type: standards
last_verified: 2026-05-19
owner: claude
---

# Django Code Style

## ViewSets

```python
from rest_framework import viewsets, status
from rest_framework.response import Response

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("customer").all()
    serializer_class = OrderSerializer

    def perform_create(self, serializer):
        order_service.create_order(serializer.validated_data)
```

## Serializers

```python
class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["id", "customer", "status", "total", "created_at"]
        read_only_fields = ["id", "created_at"]
```

## Service layer pattern

```python
# orders/services.py — business logic only, no HTTP
def create_order(validated_data: dict) -> Order:
    order = Order.objects.create(**validated_data)
    order_created.send(sender=Order, order=order)
    return order
```

## Queries
Always use `select_related` for FK, `prefetch_related` for M2M. No raw SQL.
