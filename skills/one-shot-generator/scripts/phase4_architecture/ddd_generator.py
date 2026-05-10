#!/usr/bin/env python3
"""DDD Aggregate and Entity Generation"""
from typing import Dict

class DDDGenerator:
    def __init__(self, framework: str):
        self.framework = framework.lower()

    def generate(self) -> Dict[str, str]:
        files = {}
        files['domain/aggregates/order_aggregate.py'] = self._order_aggregate()
        files['domain/entities/order_item.py'] = self._order_item()
        files['domain/value_objects/money.py'] = self._money()
        files['domain/repositories/order_repository.py'] = self._order_repository()
        files['domain/services/order_service.py'] = self._order_service()
        files['domain/events.py'] = self._domain_events()
        return files

    def _order_aggregate(self) -> str:
        return '''class OrderAggregate:
    def __init__(self, order_id: str, customer_id: str):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = []
        self.total = 0
        self.status = "pending"

    def add_item(self, product_id, quantity, price):
        self.items.append({"product_id": product_id, "quantity": quantity, "price": price})
        self._update_total()

    def _update_total(self):
        self.total = sum(item["price"] * item["quantity"] for item in self.items)

    def confirm(self):
        if self.status == "pending":
            self.status = "confirmed"
            return {"type": "OrderConfirmed", "order_id": self.order_id}
        raise ValueError("Invalid status transition")
'''

    def _order_item(self) -> str:
        return '''class OrderItem:
    def __init__(self, product_id, quantity, price):
        self.product_id = product_id
        self.quantity = quantity
        self.price = price
'''

    def _money(self) -> str:
        return '''class Money:
    def __init__(self, amount, currency="USD"):
        self.amount = amount
        self.currency = currency
'''

    def _order_repository(self) -> str:
        return '''from abc import ABC, abstractmethod

class OrderRepository(ABC):
    @abstractmethod
    def save(self, order): pass
    
    @abstractmethod
    def find_by_id(self, order_id): pass
'''

    def _order_service(self) -> str:
        return '''class OrderDomainService:
    def __init__(self, order_repo):
        self.order_repo = order_repo
'''

    def _domain_events(self) -> str:
        return '''from dataclasses import dataclass
from datetime import datetime

@dataclass
class OrderCreated:
    order_id: str = None
    customer_id: str = None
'''
