"""FastAPI example application."""
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime
import os

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./test.db')
engine = create_engine(DATABASE_URL, connect_args={'check_same_thread': False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class PostDB(Base):
    """Database Post model."""
    __tablename__ = 'posts'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), index=True)
    content = Column(String)
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

# Schemas
class PostCreate(BaseModel):
    """Create post request."""
    title: str
    content: str
    published: bool = False

class PostResponse(BaseModel):
    """Post response."""
    id: int
    title: str
    content: str
    published: bool
    created_at: datetime

    class Config:
        from_attributes = True

# FastAPI app
app = FastAPI(title='one-shot-prompting Example API', version='0.1.0')

def get_db():
    """Database dependency."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints
@app.get('/health')
async def health():
    """Health check endpoint."""
    return {'status': 'ok'}

@app.post('/posts', response_model=PostResponse)
async def create_post(post: PostCreate, db: Session = Depends(get_db)):
    """Create a new post."""
    db_post = PostDB(**post.dict())
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@app.get('/posts', response_model=list[PostResponse])
async def list_posts(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    """List all posts."""
    return db.query(PostDB).offset(skip).limit(limit).all()

@app.get('/posts/{post_id}', response_model=PostResponse)
async def get_post(post_id: int, db: Session = Depends(get_db)):
    """Get a specific post."""
    post = db.query(PostDB).filter(PostDB.id == post_id).first()
    if not post:
        raise HTTPException(status_code=404, detail='Post not found')
    return post

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8000)
