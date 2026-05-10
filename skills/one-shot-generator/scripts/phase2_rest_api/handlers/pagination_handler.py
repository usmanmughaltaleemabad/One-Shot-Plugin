"""
Pagination Handler - Generate pagination logic

Supports multiple pagination styles:
- Offset/limit (most common)
- Cursor-based (for large datasets)
- Keyset pagination (for performance)
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class PaginationConfig:
    """Pagination configuration"""
    style: str = "offset"  # offset, cursor, keyset
    default_limit: int = 20
    max_limit: int = 100
    min_limit: int = 1


class PaginationGenerator:
    """Generate pagination code"""

    def __init__(self, framework: str, config: PaginationConfig):
        self.framework = framework
        self.config = config

    def generate_django(self) -> str:
        """Generate Django pagination"""
        return """
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = {default_limit}
    page_size_query_param = 'limit'
    page_size_query_description = 'Number of results to return per page'
    max_page_size = {max_limit}
    page_query_param = 'page'
    page_query_description = 'Page number'

    def get_paginated_response(self, data):
        return Response({{
            'count': self.page.paginator.count,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        }})

# Usage in ViewSet:
# pagination_class = StandardPagination
""".format(
            default_limit=self.config.default_limit,
            max_limit=self.config.max_limit
        )

    def generate_fastapi(self) -> str:
        """Generate FastAPI pagination"""
        return """
from fastapi import Query
from sqlalchemy.orm import Session
from typing import List, Generic, TypeVar

T = TypeVar('T')

class Page(Generic[T]):
    def __init__(self, items: List[T], total: int, skip: int, limit: int):
        self.items = items
        self.total = total
        self.skip = skip
        self.limit = limit
        self.pages = (total + limit - 1) // limit

async def paginate(
    db: Session,
    query,
    skip: int = Query(0, ge=0),
    limit: int = Query({default_limit}, ge={min_limit}, le={max_limit})
):
    total = query.count()
    items = query.offset(skip).limit(limit).all()
    return Page(items, total, skip, limit)

# Usage:
# @router.get("/", response_model=Page)
# async def list_items(page: Page = Depends(paginate)):
#     return page
""".format(
            default_limit=self.config.default_limit,
            min_limit=self.config.min_limit,
            max_limit=self.config.max_limit
        )

    def generate_spring(self) -> str:
        """Generate Spring Boot pagination"""
        return """
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;

@GetMapping
public Page<ItemDTO> listItems(
    @RequestParam(defaultValue = "0") int page,
    @RequestParam(defaultValue = "{default_limit}") int size,
    @RequestParam(required = false) String sort
) {{
    if (size > {max_limit}) size = {max_limit};
    if (size < {min_limit}) size = {min_limit};

    Pageable pageable = PageRequest.of(page, size, Sort.by("id").descending());
    return itemRepository.findAll(pageable).map(this::toDTO);
}}
""".format(
            default_limit=self.config.default_limit,
            min_limit=self.config.min_limit,
            max_limit=self.config.max_limit
        )


class FilteringGenerator:
    """Generate filtering logic"""

    def generate_django(self) -> str:
        """Generate Django filtering"""
        return """
from django_filters import rest_framework as filters
from rest_framework import viewsets

class ItemFilter(filters.FilterSet):
    name = filters.CharFilter(lookup_expr='icontains')
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = Item
        fields = ['name', 'status', 'created_after', 'created_before']

# Usage in ViewSet:
# filter_backends = [filters.DjangoFilterBackend, SearchFilter]
# filterset_class = ItemFilter
# search_fields = ['name', 'description']
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI filtering"""
        return """
from typing import Optional
from fastapi import Query
from sqlalchemy.orm import Session

async def get_items(
    db: Session,
    name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, le=100)
):
    query = db.query(Item)

    if name:
        query = query.filter(Item.name.ilike(f"%{name}%"))
    if status:
        query = query.filter(Item.status == status)

    total = query.count()
    items = query.offset(skip).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "skip": skip,
        "limit": limit
    }
"""


class SortingGenerator:
    """Generate sorting logic"""

    def generate_django(self) -> str:
        """Generate Django sorting"""
        return """
from rest_framework.filters import OrderingFilter

# Usage in ViewSet:
# filter_backends = [OrderingFilter]
# ordering_fields = ['created_at', 'updated_at', 'name']
# ordering = ['-created_at']  # Default sort

# Example query:
# GET /api/items/?ordering=-created_at
# GET /api/items/?ordering=name
"""

    def generate_fastapi(self) -> str:
        """Generate FastAPI sorting"""
        return """
from typing import Optional
from fastapi import Query
from sqlalchemy import desc, asc

async def get_items(
    db: Session,
    sort_by: Optional[str] = Query("created_at"),
    sort_order: Optional[str] = Query("desc", regex="^(asc|desc)$")
):
    query = db.query(Item)

    # Prevent SQL injection
    allowed_fields = ["created_at", "updated_at", "name", "id"]
    if sort_by not in allowed_fields:
        sort_by = "created_at"

    if sort_order.lower() == "desc":
        query = query.order_by(desc(getattr(Item, sort_by)))
    else:
        query = query.order_by(asc(getattr(Item, sort_by)))

    return query.all()

# Example query:
# GET /api/items/?sort_by=created_at&sort_order=desc
"""


def generate_pagination_code(
    framework: str,
    pagination_style: str = "offset",
    default_limit: int = 20,
    max_limit: int = 100
) -> str:
    """Generate pagination code"""
    config = PaginationConfig(
        style=pagination_style,
        default_limit=default_limit,
        max_limit=max_limit
    )
    generator = PaginationGenerator(framework, config)

    if framework == "django":
        return generator.generate_django()
    elif framework == "fastapi":
        return generator.generate_fastapi()
    elif framework == "spring":
        return generator.generate_spring()
    else:
        raise ValueError(f"Unsupported framework: {framework}")


def generate_filtering_code(framework: str) -> str:
    """Generate filtering code"""
    generator = FilteringGenerator()
    if framework == "django":
        return generator.generate_django()
    elif framework == "fastapi":
        return generator.generate_fastapi()
    else:
        raise ValueError(f"Unsupported framework: {framework}")


def generate_sorting_code(framework: str) -> str:
    """Generate sorting code"""
    generator = SortingGenerator()
    if framework == "django":
        return generator.generate_django()
    elif framework == "fastapi":
        return generator.generate_fastapi()
    else:
        raise ValueError(f"Unsupported framework: {framework}")
