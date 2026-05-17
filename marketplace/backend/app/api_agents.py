"""Agent API endpoints - core marketplace functionality."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Optional
import uuid

from app.database import get_db
from app.models import Agent, Rating, Subscription, User
from app.schemas import (
    AgentResponse, AgentDetailResponse, AgentListResponse, AgentCreate,
    AgentUpdate, RatingCreate, RatingResponse, AgentSearchQuery
)

router = APIRouter(prefix="/api/v1/agents", tags=["agents"])


@router.get("", response_model=AgentListResponse)
async def list_agents(
    search: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    min_rating: float = Query(0, ge=0, le=5),
    max_price: Optional[int] = Query(None),
    sort_by: str = Query("rating"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List agents with filters and search.

    - **search**: Search agent name, description, keywords
    - **category**: Filter by category
    - **min_rating**: Minimum rating (0-5)
    - **max_price**: Maximum price in cents
    - **sort_by**: Sort by rating, newest, popular, price
    - **page**: Page number (1-based)
    - **page_size**: Results per page
    """

    # Build query
    query = select(Agent).where(
        and_(
            Agent.status == "published",
            Agent.is_public == True,
            Agent.rating >= min_rating,
        )
    )

    # Apply filters
    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                Agent.name.ilike(search_term),
                Agent.description.ilike(search_term),
                Agent.keywords.contains([search_term]),
            )
        )

    if category:
        query = query.where(Agent.category == category)

    if max_price:
        query = query.where(Agent.price_usd <= max_price)

    # Apply sorting
    if sort_by == "newest":
        query = query.order_by(Agent.published_at.desc())
    elif sort_by == "popular":
        query = query.order_by(Agent.install_count.desc())
    elif sort_by == "price":
        query = query.order_by(Agent.price_usd.asc())
    else:  # rating
        query = query.order_by(Agent.rating.desc())

    # Count total
    total = await db.scalar(
        select(func.count(Agent.id)).select_from(Agent).where(
            and_(
                Agent.status == "published",
                Agent.is_public == True,
                Agent.rating >= min_rating,
            )
        )
    )

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    agents = (await db.execute(query)).scalars().all()

    return AgentListResponse(
        items=[AgentResponse.from_orm(a) for a in agents],
        total=total or 0,
        page=page,
        page_size=page_size,
        total_pages=(total or 0 + page_size - 1) // page_size,
    )


@router.get("/{agent_id}", response_model=AgentDetailResponse)
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    """Get agent details with creator info and markdown."""

    result = await db.execute(
        select(Agent).where(Agent.id == agent_id)
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Load creator
    await db.refresh(agent, ["creator"])

    return AgentDetailResponse.from_orm(agent)


@router.post("", response_model=AgentResponse, status_code=201)
async def create_agent(
    request: AgentCreate,
    db: AsyncSession = Depends(get_db),
    # current_user: User = Depends(get_current_user),  # TODO: auth
):
    """Create new agent (for creators)."""

    # TODO: Verify user is authenticated
    # if not current_user.is_creator:
    #     raise HTTPException(status_code=403, detail="Must be a creator")

    # Generate slug
    slug = f"temp-creator/{request.name.lower().replace(' ', '-')}"  # TODO: use real creator ID

    agent = Agent(
        id=str(uuid.uuid4()),
        creator_id="temp-creator-id",  # TODO: use current_user.id
        name=request.name,
        slug=slug,
        description=request.description,
        markdown_content=request.markdown_content,
        category=request.category,
        keywords=request.keywords,
        price_usd=request.price_usd,
        status="draft",
    )

    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    return AgentResponse.from_orm(agent)


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: AgentUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update agent metadata and content."""

    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # TODO: Verify ownership (current_user.id == agent.creator_id)

    # Update fields
    if request.description:
        agent.description = request.description
    if request.markdown_content:
        agent.markdown_content = request.markdown_content
    if request.category:
        agent.category = request.category
    if request.keywords is not None:
        agent.keywords = request.keywords
    if request.price_usd is not None:
        agent.price_usd = request.price_usd

    await db.commit()
    await db.refresh(agent)

    return AgentResponse.from_orm(agent)


@router.post("/{agent_id}/ratings", response_model=RatingResponse, status_code=201)
async def rate_agent(
    agent_id: str,
    request: RatingCreate,
    db: AsyncSession = Depends(get_db),
):
    """Submit rating/review for agent."""

    # TODO: Get current user from auth
    user_id = "temp-user-id"

    # Check agent exists
    result = await db.execute(select(Agent).where(Agent.id == agent_id))
    agent = result.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Check if user already rated
    existing = await db.execute(
        select(Rating).where(
            and_(Rating.agent_id == agent_id, Rating.user_id == user_id)
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Already rated this agent")

    # Create rating
    rating = Rating(
        id=str(uuid.uuid4()),
        agent_id=agent_id,
        user_id=user_id,
        rating=request.rating,
        review=request.review,
    )

    db.add(rating)

    # Update agent rating stats
    ratings_result = await db.execute(
        select(func.avg(Rating.rating), func.count(Rating.id)).select_from(Rating).where(
            Rating.agent_id == agent_id
        )
    )
    avg_rating, count = ratings_result.one()
    agent.rating = float(avg_rating or 0)
    agent.rating_count = count or 0

    await db.commit()
    await db.refresh(rating)

    return RatingResponse.from_orm(rating)


@router.get("/{agent_id}/ratings", response_model=list[RatingResponse])
async def get_ratings(
    agent_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get ratings/reviews for agent."""

    result = await db.execute(
        select(Rating)
        .where(Rating.agent_id == agent_id)
        .order_by(Rating.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    ratings = result.scalars().all()

    return [RatingResponse.from_orm(r) for r in ratings]


from sqlalchemy import or_
