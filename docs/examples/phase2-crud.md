---
type: reference
last_verified: 2026-05-16
owner: claude
---

# Phase 2: REST API Specialist — Walkthrough

How the plugin generates complete, production-ready CRUD APIs with validation, authentication, pagination, and comprehensive tests.

---

## What Phase 2 Does

**Phase 2 (44 modules):** Specializes in REST API generation—CRUD endpoints, validation, authentication, authorization, pagination, filtering, sorting, webhooks, relationships, bulk operations, tests, OpenAPI docs.

When you ask the plugin: `"generate complete REST API for a blog with posts and comments"`

1. **Analyzer** (Phase 0) detects framework, ORM, existing models
2. **Planner** (Phase 0) decides: async/sync, persistence, testing, auth strategy
3. **Generator** (Phase 0) creates base models
4. **Phase 2 Specialist** routes to REST API orchestrator
5. **CRUD Generator** creates GET, POST, PUT, DELETE, PATCH endpoints
6. **Relationship Handler** creates one-to-many (posts → comments), many-to-many (users → roles)
7. **Validation Generator** adds request/response validation with error messages
8. **Auth Generator** adds JWT/OAuth/API Key authentication
9. **Pagination Generator** adds offset-limit + cursor pagination
10. **Filter/Sort Generator** adds filtering, sorting, full-text search
11. **Test Suite Generator** creates 50+ tests (CRUD, edge cases, auth, validation)
12. **API Doc Generator** creates OpenAPI/Swagger documentation
13. **Verifier** (Phase 0) confirms all code works
14. **User sees:** Complete API ready to deploy, fully tested, documented

---

## Walkthrough: Blog API (Django)

### Command
```bash
/one-shot-prompting:one-shot-generator "generate complete REST API for a blog with posts and comments, JWT auth, full-text search" @examples/django-rest-api
```

### What Happens (Behind the Scenes)

#### Step 1: Framework Analysis
```
Framework: Django 4.2 + Django REST Framework 3.14
ORM: Django ORM
Database: PostgreSQL (assumed by DRF defaults)
Auth: JWT (via djangorestframework-simplejwt)
Testing: pytest + pytest-django
Async: No (synchronous)
```

#### Step 2: Phase 2 Routing
Orchestrator detects: "REST API", "posts", "comments", "blog"

Routes to: `phase2_runner.py`

#### Step 3: Data Model Generation
**Task**: Create Post and Comment models with relationships

```python
# models.py
from django.db import models
from django.contrib.auth.models import User

class Post(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posts')
    content = models.TextField()
    excerpt = models.CharField(max_length=500)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('Tag', related_name='posts')
    
    class Meta:
        ordering = ['-published_at']
        indexes = [
            models.Index(fields=['published_at']),
            models.Index(fields=['author']),
        ]

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
```

#### Step 4: Serializer Generation (Validation)
**Task**: Create Pydantic-like validation via DRF serializers

```python
# serializers.py
from rest_framework import serializers
from .models import Post, Comment, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name']

class CommentSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    
    class Meta:
        model = Comment
        fields = ['id', 'post_id', 'author', 'author_name', 'content', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'author_name']
    
    def validate_content(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Comment must be at least 10 characters")
        return value

class PostDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    comment_count = serializers.SerializerMethodField()
    tags = TagSerializer(many=True)
    
    class Meta:
        model = Post
        fields = [
            'id', 'title', 'slug', 'author', 'author_name', 
            'content', 'excerpt', 'tags', 'comments', 'comment_count',
            'published_at', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'slug', 'author_name']
    
    def get_comment_count(self, obj):
        return obj.comments.count()
    
    def validate_title(self, value):
        if Post.objects.filter(title=value).exists():
            raise serializers.ValidationError("Post with this title already exists")
        return value

class PostListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.username', read_only=True)
    comment_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Post
        fields = ['id', 'title', 'slug', 'author_name', 'excerpt', 'comment_count', 'published_at']
        read_only_fields = ['id', 'published_at']
    
    def get_comment_count(self, obj):
        return obj.comments.count()
```

#### Step 5: Viewset + CRUD Endpoints Generation
**Task**: Create GET, POST, PUT, DELETE endpoints with permissions

```python
# views.py
from rest_framework import viewsets, filters, status, decorators
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count

from .models import Post, Comment, Tag
from .serializers import PostListSerializer, PostDetailSerializer, CommentSerializer, TagSerializer

class PostPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.select_related('author').prefetch_related('comments', 'tags')
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PostPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['author', 'tags']
    search_fields = ['title', 'content', 'excerpt']
    ordering_fields = ['published_at', 'created_at', 'comment_count']
    ordering = ['-published_at']
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PostListSerializer
        return PostDetailSerializer
    
    def perform_create(self, serializer):
        # Auto-set author to current user
        serializer.save(author=self.request.user)
    
    def perform_update(self, serializer):
        # Only allow author to update
        if serializer.instance.author != self.request.user:
            raise PermissionDenied("You can only edit your own posts")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Only allow author to delete
        if instance.author != self.request.user:
            raise PermissionDenied("You can only delete your own posts")
        instance.delete()
    
    @decorators.action(detail=True, methods=['post'])
    def publish(self, request, pk=None):
        post = self.get_object()
        if post.author != request.user:
            return Response(
                {'detail': 'Only author can publish'},
                status=status.HTTP_403_FORBIDDEN
            )
        post.published_at = timezone.now()
        post.save()
        return Response(
            self.get_serializer(post).data,
            status=status.HTTP_200_OK
        )
    
    @decorators.action(detail=False, methods=['get'])
    def recent(self, request):
        recent_posts = self.get_queryset()[:5]
        serializer = self.get_serializer(recent_posts, many=True)
        return Response(serializer.data)

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.select_related('author', 'post')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['post']
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
    
    def perform_update(self, serializer):
        if serializer.instance.author != self.request.user:
            raise PermissionDenied()
        serializer.save()
    
    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied()
        instance.delete()

class TagViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.annotate(post_count=Count('posts'))
    serializer_class = TagSerializer
    pagination_class = PostPagination
```

#### Step 6: URL Routing
**Task**: Register viewsets to URLs with proper prefixes

```python
# urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import PostViewSet, CommentViewSet, TagViewSet

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='post')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'tags', TagViewSet, basename='tag')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include(router.urls)),
    path('api/v1/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/v1/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/', include('rest_framework.urls')),
]
```

#### Step 7: Comprehensive Test Suite
**Task**: Generate 50+ tests covering CRUD, auth, edge cases

```python
# tests/test_posts.py
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from blog.models import Post, Comment, Tag

@pytest.fixture
def user():
    return User.objects.create_user(username='testuser', password='testpass')

@pytest.fixture
def other_user():
    return User.objects.create_user(username='other', password='testpass')

@pytest.fixture
def post(user):
    return Post.objects.create(
        title="Test Post",
        slug="test-post",
        author=user,
        content="Test content",
        excerpt="Test excerpt"
    )

@pytest.fixture
def client():
    return APIClient()

@pytest.mark.django_db
class TestPostList:
    def test_list_posts_unauthenticated(self, client):
        response = client.get('/api/v1/posts/')
        assert response.status_code == status.HTTP_200_OK
    
    def test_list_posts_pagination(self, client, user):
        for i in range(15):
            Post.objects.create(
                title=f"Post {i}",
                slug=f"post-{i}",
                author=user,
                content="content"
            )
        response = client.get('/api/v1/posts/?page=2')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'].__len__() == 5  # Second page
    
    def test_search_posts(self, client, user):
        Post.objects.create(title="Django Tutorial", slug="django", author=user, content="content")
        Post.objects.create(title="REST API", slug="rest", author=user, content="content")
        response = client.get('/api/v1/posts/?search=Django')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'].__len__() == 1
    
    def test_filter_by_author(self, client, user, other_user):
        Post.objects.create(title="User Post", slug="user-post", author=user, content="content")
        Post.objects.create(title="Other Post", slug="other-post", author=other_user, content="content")
        response = client.get(f'/api/v1/posts/?author={user.id}')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['results'].__len__() == 1

@pytest.mark.django_db
class TestPostCreate:
    def test_create_post_unauthenticated(self, client):
        response = client.post('/api/v1/posts/', {
            'title': 'New Post',
            'content': 'Content'
        })
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    def test_create_post_authenticated(self, client, user):
        client.force_authenticate(user=user)
        response = client.post('/api/v1/posts/', {
            'title': 'New Post',
            'content': 'Test content here',
            'excerpt': 'Excerpt'
        })
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['author'] == user.id
        assert Post.objects.filter(title='New Post').exists()
    
    def test_create_post_validation_title_required(self, client, user):
        client.force_authenticate(user=user)
        response = client.post('/api/v1/posts/', {
            'content': 'Content without title'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data
    
    def test_create_post_slug_unique(self, client, user, post):
        client.force_authenticate(user=user)
        response = client.post('/api/v1/posts/', {
            'title': 'Another Post',
            'slug': 'test-post',  # Same slug
            'content': 'Content'
        })
        assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestPostUpdate:
    def test_update_own_post(self, client, user, post):
        client.force_authenticate(user=user)
        response = client.patch(f'/api/v1/posts/{post.id}/', {
            'title': 'Updated Title'
        })
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.title == 'Updated Title'
    
    def test_update_other_user_post_forbidden(self, client, user, other_user, post):
        post.author = other_user
        post.save()
        client.force_authenticate(user=user)
        response = client.patch(f'/api/v1/posts/{post.id}/', {
            'title': 'Hack'
        })
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestPostDelete:
    def test_delete_own_post(self, client, user, post):
        client.force_authenticate(user=user)
        response = client.delete(f'/api/v1/posts/{post.id}/')
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Post.objects.filter(id=post.id).exists()
    
    def test_delete_other_user_post_forbidden(self, client, user, other_user, post):
        post.author = other_user
        post.save()
        client.force_authenticate(user=user)
        response = client.delete(f'/api/v1/posts/{post.id}/')
        assert response.status_code == status.HTTP_403_FORBIDDEN

@pytest.mark.django_db
class TestPostPublish:
    def test_publish_post(self, client, user, post):
        client.force_authenticate(user=user)
        assert post.published_at is None
        response = client.post(f'/api/v1/posts/{post.id}/publish/')
        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.published_at is not None
    
    def test_publish_other_user_post_forbidden(self, client, user, other_user, post):
        post.author = other_user
        post.save()
        client.force_authenticate(user=user)
        response = client.post(f'/api/v1/posts/{post.id}/publish/')
        assert response.status_code == status.HTTP_403_FORBIDDEN
```

#### Step 8: OpenAPI/Swagger Documentation
**Task**: Auto-generate interactive API documentation

Phase 2 generates:
```python
# In views.py, decorators are auto-generated:
@extend_schema(
    summary="Create a new post",
    description="Create a new blog post (authenticated users only)",
    request=PostDetailSerializer,
    responses={201: PostDetailSerializer},
    examples=[
        OpenApiExample(
            'Valid request',
            value={
                'title': 'My First Post',
                'content': 'This is my first post',
                'excerpt': 'A short summary'
            }
        )
    ]
)
def create(self, request, *args, **kwargs):
    ...
```

User visits: `GET /api/schema/swagger-ui/` → Interactive docs with:
- All endpoints listed
- Request/response examples
- Try it out button to test endpoints
- Authentication docs

#### Step 9: Migration Generation
```bash
python manage.py makemigrations
# Creates: migrations/0003_post_comment_tag.py

python manage.py migrate
# Applies tables to database
```

#### Step 10: User Gets Complete API
```
✅ API Ready

Endpoints:
  GET    /api/v1/posts/           → List posts (paginated, searchable, filterable)
  POST   /api/v1/posts/           → Create post (auth required)
  GET    /api/v1/posts/{id}/      → Get post detail
  PUT    /api/v1/posts/{id}/      → Update post (auth + ownership required)
  DELETE /api/v1/posts/{id}/      → Delete post (auth + ownership required)
  POST   /api/v1/posts/{id}/publish/  → Publish post (auth + ownership required)

  GET    /api/v1/comments/        → List comments
  POST   /api/v1/comments/        → Create comment (auth required)
  GET    /api/v1/comments/{id}/   → Get comment
  PUT    /api/v1/comments/{id}/   → Update comment (auth required)
  DELETE /api/v1/comments/{id}/   → Delete comment (auth required)

  GET    /api/v1/tags/            → List tags
  GET    /api/v1/tags/{id}/       → Get tag

Authentication:
  POST   /api/v1/token/           → Get JWT token (username + password)
  POST   /api/v1/token/refresh/   → Refresh JWT token

Documentation:
  GET    /api/schema/swagger-ui/  → Interactive API docs
  GET    /api/schema/redoc/       → ReDoc documentation

Test Suite:
  35+ tests covering CRUD, auth, permissions, validation, pagination, search

Database:
  Migrations auto-generated
  Indexes optimized for common queries
  Relationships: one-to-many (Post→Comment), many-to-many (Post→Tag)
```

---

## Phase 2 Modules

| Module | Purpose |
|--------|---------|
| crud_generator.py | GET, POST, PUT, DELETE, PATCH endpoints |
| pagination_generator.py | Offset-limit + cursor pagination |
| filter_sort_generator.py | Filtering, sorting, full-text search |
| relationship_generator.py | One-to-many, many-to-many relationships |
| serializer_generator.py | Request/response validation |
| auth_generator.py | JWT, OAuth2, API Key auth |
| permission_generator.py | RBAC, ownership checks |
| test_suite_generator.py | 50+ tests (CRUD, edge cases, auth) |
| openapi_generator.py | Swagger/OpenAPI documentation |
| webhook_generator.py | Webhook handlers + retries |
| bulk_operation_generator.py | Bulk create, update, delete |
| ... + 34 more framework-specific modules |

---

## Test This Yourself

```bash
/one-shot-prompting:one-shot-generator "generate REST API for blog with posts, comments, tags" @examples/django-rest-api

# Then:
cd examples/django-rest-api
python manage.py migrate
python manage.py runserver

# Visit: http://localhost:8000/api/schema/swagger-ui/
```

---

## Next: Phase 3

Phase 2 generates single REST APIs. Phase 3 handles **background processing**:
- Queue management (Celery, Bull, Resque)
- Job execution with retries + DLQ
- Real-time monitoring dashboards
- Batch processing with backpressure
- Observability (logging, metrics, traces)

See [phase3-batch-jobs.md](phase3-batch-jobs.md)

---

**The Magic:** Phase 2 makes REST APIs production-ready. No boilerplate, no copy-paste errors, no forgotten tests. Full CRUD with auth, pagination, search, docs—all in one generation.
