"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, EmailStr, field_validator


class UserBase(BaseModel):
    """Base user schema."""
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=255)
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    """User creation schema."""
    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """User response schema."""
    id: str
    is_creator: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentBase(BaseModel):
    """Base agent schema."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10, max_length=5000)
    category: str = Field(..., min_length=1, max_length=100)
    keywords: List[str] = Field(default_factory=list, max_length=20)
    price_usd: int = Field(default=0, ge=0)  # In cents


class AgentCreate(AgentBase):
    """Agent creation schema."""
    markdown_content: str = Field(..., min_length=100)


class AgentUpdate(BaseModel):
    """Agent update schema."""
    description: Optional[str] = None
    markdown_content: Optional[str] = None
    category: Optional[str] = None
    keywords: Optional[List[str]] = None
    price_usd: Optional[int] = None


class AgentResponse(AgentBase):
    """Agent response schema."""
    id: str
    creator_id: str
    slug: str
    version: str
    status: str
    is_public: bool
    rating: float
    rating_count: int
    install_count: int
    created_at: datetime
    published_at: Optional[datetime]

    class Config:
        from_attributes = True


class AgentDetailResponse(AgentResponse):
    """Detailed agent response with markdown."""
    markdown_content: str
    creator: UserResponse


class SubscriptionCreate(BaseModel):
    """Subscription creation schema."""
    agent_id: str


class SubscriptionResponse(BaseModel):
    """Subscription response schema."""
    id: str
    user_id: str
    agent_id: str
    status: str
    started_at: datetime
    current_period_end: datetime
    canceled_at: Optional[datetime]

    class Config:
        from_attributes = True


class RatingCreate(BaseModel):
    """Rating creation schema."""
    rating: int = Field(..., ge=1, le=5)
    review: Optional[str] = Field(None, max_length=5000)


class RatingResponse(BaseModel):
    """Rating response schema."""
    id: str
    agent_id: str
    user_id: str
    rating: int
    review: Optional[str]
    helpful_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Agent list response with pagination."""
    items: List[AgentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TransactionResponse(BaseModel):
    """Transaction response schema."""
    id: str
    type: str
    amount_usd: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    """Error response schema."""
    detail: str
    status_code: int


# Search and filter schemas
class AgentSearchQuery(BaseModel):
    """Agent search query schema."""
    search: Optional[str] = None
    category: Optional[str] = None
    min_rating: float = Field(default=0, ge=0, le=5)
    max_price: Optional[int] = None  # In cents
    sort_by: str = Field(default="rating")  # rating, newest, popular, price
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @field_validator("sort_by")
    def validate_sort_by(cls, v):
        valid_sorts = ["rating", "newest", "popular", "price"]
        if v not in valid_sorts:
            raise ValueError(f"sort_by must be one of {valid_sorts}")
        return v
