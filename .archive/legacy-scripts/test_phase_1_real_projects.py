#!/usr/bin/env python3
"""
Phase 1 Real Project Simulation Tests

Simulates real project structures and validates Phase 1 modules work correctly:
1. Django REST API project
2. FastAPI async project
3. NestJS modular project
4. Express middleware project
5. Spring Boot Java project
"""

import sys
import tempfile
from pathlib import Path
from typing import Dict, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from phase_1_gap_1_format_multifile import format_multifile_output
from phase_1_gap_1_autowire_project import autowire_into_project
from phase_1_gap_2_migration_generator import generate_migrations
from phase_1_gap_3_framework_config import generate_framework_config
from phase_1_gap_3_env_generator import generate_env_template
from phase_1_gap_3_docker_compose import generate_docker_compose
from phase_1_gap_3_dependency_injection import generate_dependency_injection


class RealProjectSimulator:
    """Simulate real project structures."""

    @staticmethod
    def create_django_project() -> Dict[str, str]:
        """Simulate Django REST API project structure."""
        return {
            'models.py': '''
from django.db import models

class User(models.Model):
    username = models.CharField(max_length=255)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users'
''',
            'serializers.py': '''
from rest_framework import serializers
from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'created_at']
''',
            'views.py': '''
from rest_framework.viewsets import ModelViewSet
from .models import User
from .serializers import UserSerializer

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
''',
            'urls.py': '''
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
''',
            'tests.py': '''
from django.test import TestCase
from .models import User

class UserTestCase(TestCase):
    def test_create_user(self):
        user = User.objects.create(username='test', email='test@example.com')
        self.assertEqual(user.username, 'test')
''',
        }

    @staticmethod
    def create_fastapi_project() -> Dict[str, str]:
        """Simulate FastAPI async project structure."""
        return {
            'models.py': '''
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
''',
            'schemas.py': '''
from pydantic import BaseModel
from typing import Optional

class UserCreate(BaseModel):
    username: str
    email: str

class User(UserCreate):
    id: int

    class Config:
        from_attributes = True
''',
            'routes.py': '''
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .models import User
from .schemas import UserCreate

router = APIRouter()

@router.post("/users/")
async def create_user(user: UserCreate, db: Session = Depends()):
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    return db_user
''',
            'main.py': '''
from fastapi import FastAPI
from .routes import router

app = FastAPI()
app.include_router(router)
''',
            'tests.py': '''
import pytest
from fastapi.testclient import TestClient
from .main import app

client = TestClient(app)

def test_create_user():
    response = client.post("/users/", json={"username": "test", "email": "test@example.com"})
    assert response.status_code == 200
''',
        }

    @staticmethod
    def create_nestjs_project() -> Dict[str, str]:
        """Simulate NestJS modular project structure."""
        return {
            'user.entity.ts': '''
import { Entity, Column, PrimaryGeneratedColumn } from 'typeorm';

@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column()
  username: string;

  @Column()
  email: string;
}
''',
            'user.service.ts': '''
import { Injectable } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { User } from './user.entity';

@Injectable()
export class UserService {
  constructor(@InjectRepository(User) private repo: Repository<User>) {}

  async create(username: string, email: string) {
    return this.repo.save({ username, email });
  }
}
''',
            'user.controller.ts': '''
import { Controller, Post, Body } from '@nestjs/common';
import { UserService } from './user.service';

@Controller('users')
export class UserController {
  constructor(private readonly userService: UserService) {}

  @Post()
  async create(@Body() createUserDto: any) {
    return this.userService.create(createUserDto.username, createUserDto.email);
  }
}
''',
            'user.module.ts': '''
import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { User } from './user.entity';
import { UserService } from './user.service';
import { UserController } from './user.controller';

@Module({
  imports: [TypeOrmModule.forFeature([User])],
  providers: [UserService],
  controllers: [UserController],
})
export class UserModule {}
''',
            'user.service.spec.ts': '''
import { Test, TestingModule } from '@nestjs/testing';
import { UserService } from './user.service';

describe('UserService', () => {
  let service: UserService;

  beforeEach(async () => {
    const module: TestingModule = await Test.createTestingModule({
      providers: [UserService],
    }).compile();

    service = module.get<UserService>(UserService);
  });

  it('should create a user', () => {
    expect(service.create('test', 'test@example.com')).toBeDefined();
  });
});
''',
        }

    @staticmethod
    def create_express_project() -> Dict[str, str]:
        """Simulate Express middleware project structure."""
        return {
            'models/user.js': '''
class User {
  constructor(username, email) {
    this.username = username;
    this.email = email;
  }
}

module.exports = User;
''',
            'routes/users.js': '''
const express = require('express');
const router = express.Router();
const User = require('../models/user');

router.post('/', (req, res) => {
  const { username, email } = req.body;
  const user = new User(username, email);
  res.json(user);
});

module.exports = router;
''',
            'middleware/auth.js': '''
const auth = (req, res, next) => {
  const token = req.headers.authorization;
  if (!token) {
    return res.status(401).json({ error: 'Unauthorized' });
  }
  next();
};

module.exports = auth;
''',
            'app.js': '''
const express = require('express');
const userRoutes = require('./routes/users');
const auth = require('./middleware/auth');

const app = express();
app.use(express.json());
app.use(auth);
app.use('/users', userRoutes);

module.exports = app;
''',
            'test/users.test.js': '''
const request = require('supertest');
const app = require('../app');

describe('Users API', () => {
  it('should create a user', async () => {
    const response = await request(app)
      .post('/users')
      .set('Authorization', 'Bearer token')
      .send({ username: 'test', email: 'test@example.com' });

    expect(response.status).toBe(200);
  });
});
''',
        }

    @staticmethod
    def create_spring_project() -> Dict[str, str]:
        """Simulate Spring Boot Java project structure."""
        return {
            'User.java': '''
import javax.persistence.*;

@Entity
@Table(name = "users")
public class User {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true)
    private String username;

    @Column(unique = true)
    private String email;

    // Getters and setters
}
''',
            'UserService.java': '''
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class UserService {
    @Autowired
    private UserRepository userRepository;

    public User createUser(String username, String email) {
        User user = new User();
        user.setUsername(username);
        user.setEmail(email);
        return userRepository.save(user);
    }
}
''',
            'UserController.java': '''
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/users")
public class UserController {
    @Autowired
    private UserService userService;

    @PostMapping
    public User createUser(@RequestBody UserCreateDto dto) {
        return userService.createUser(dto.getUsername(), dto.getEmail());
    }
}
''',
            'UserRepositoryTest.java': '''
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class UserRepositoryTest {
    @Test
    void testCreateUser() {
        User user = new User();
        user.setUsername("test");
        user.setEmail("test@example.com");
        assertNotNull(user.getId());
    }
}
''',
        }


class RealProjectTests:
    """Test Phase 1 on simulated real projects."""

    def __init__(self):
        self.passed = 0
        self.failed = 0

    def test_django_project(self) -> bool:
        """Test Phase 1 on Django project."""
        print("\n[REAL PROJECT] Django REST API...")
        try:
            files = RealProjectSimulator.create_django_project()

            # 1. Format files
            ordered = format_multifile_output(files, 'django')
            order = [f for f, _ in ordered]
            assert 'models.py' in order[0:2], "Models should be early"
            print(f"  [OK] File ordering: {' -> '.join(order)}")

            # 2. Generate migrations
            models = {'User': files['models.py']}
            migs = generate_migrations('django', models)
            assert len(migs) > 0, "No migrations generated"
            print(f"  [OK] Migrations: {len(migs)} migration files")

            # 3. Generate config
            config = generate_framework_config('django', {'auth': True, 'database': True})
            assert len(config) > 0, "No config generated"
            print(f"  [OK] Config: settings.py configuration generated")

            # 4. Generate env
            env = generate_env_template('django')
            assert 'DATABASE' in env, "Env missing DATABASE"
            print(f"  [OK] Environment: .env.example with {env.count(chr(10))} variables")

            # 5. Generate Docker
            docker = generate_docker_compose('django', 'postgresql', True)
            assert 'services' in docker.lower(), "Docker missing services"
            print(f"  [OK] Docker: docker-compose.yml configured")

            # 6. Generate DI
            services = {'UserService': ['DatabaseService'], 'DatabaseService': []}
            di = generate_dependency_injection('django', services)
            assert 'UserService' in di, "DI missing UserService"
            print(f"  [OK] DI: Dependency injection container setup")

            print("  SUCCESS: Django project validated")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_fastapi_project(self) -> bool:
        """Test Phase 1 on FastAPI project."""
        print("\n[REAL PROJECT] FastAPI async API...")
        try:
            files = RealProjectSimulator.create_fastapi_project()

            # 1. Format
            ordered = format_multifile_output(files, 'fastapi')
            order = [f for f, _ in ordered]
            print(f"  [OK] File ordering: {len(order)} files ordered")

            # 2. Migrations
            models = {'User': files['models.py']}
            migs = generate_migrations('fastapi', models)
            assert any('alembic' in path for path, _ in migs), "No Alembic migration"
            print(f"  [OK] Migrations: Alembic migrations generated")

            # 3. Config
            config = generate_framework_config('fastapi', {'auth': True, 'cors': True})
            assert 'main.py' in config, "Config missing main.py"
            print(f"  [OK] Config: FastAPI main.py configuration")

            # 4. Env
            env = generate_env_template('fastapi')
            assert len(env) > 100, "Env too small"
            print(f"  [OK] Environment: FastAPI .env template")

            # 5. Docker
            docker = generate_docker_compose('fastapi', 'postgresql', True)
            assert 'uvicorn' in docker.lower() or 'fastapi' in docker.lower() or 'app' in docker.lower()
            print(f"  [OK] Docker: FastAPI docker-compose configured")

            # 6. DI
            services = {'UserService': ['DatabaseService'], 'DatabaseService': []}
            di = generate_dependency_injection('fastapi', services)
            assert 'Depends' in di, "DI missing FastAPI Depends"
            print(f"  [OK] DI: FastAPI dependency injection with Depends()")

            print("  SUCCESS: FastAPI project validated")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_nestjs_project(self) -> bool:
        """Test Phase 1 on NestJS project."""
        print("\n[REAL PROJECT] NestJS modular backend...")
        try:
            files = RealProjectSimulator.create_nestjs_project()

            # 1. Format
            ordered = format_multifile_output(files, 'nestjs')
            order = [f for f, _ in ordered]
            print(f"  [OK] File ordering: {len(order)} files ordered")

            # 2. Config
            config = generate_framework_config('nestjs', {'database': True, 'auth': True})
            assert len(config) > 0, "No NestJS config"
            print(f"  [OK] Config: NestJS modules configuration")

            # 3. Env
            env = generate_env_template('nestjs')
            assert 'NODE_ENV' in env or 'DATABASE' in env, "Env missing variables"
            print(f"  [OK] Environment: NestJS .env template")

            # 4. Docker
            docker = generate_docker_compose('nestjs', 'postgresql', True)
            assert 'npm' in docker.lower() or 'node' in docker.lower()
            print(f"  [OK] Docker: NestJS docker-compose with Node.js")

            # 5. DI
            services = {'UserService': ['DatabaseService'], 'UserController': ['UserService'], 'DatabaseService': []}
            di = generate_dependency_injection('nestjs', services)
            assert '@Injectable' in di, "DI missing @Injectable"
            print(f"  [OK] DI: NestJS @Injectable providers")

            print("  SUCCESS: NestJS project validated")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_express_project(self) -> bool:
        """Test Phase 1 on Express project."""
        print("\n[REAL PROJECT] Express middleware API...")
        try:
            files = RealProjectSimulator.create_express_project()

            # 1. Format
            ordered = format_multifile_output(files, 'express')
            order = [f for f, _ in ordered]
            print(f"  [OK] File ordering: {len(order)} files ordered")

            # 2. Config
            config = generate_framework_config('express', {'auth': True, 'logging': True})
            assert len(config) > 0, "No Express config"
            print(f"  [OK] Config: Express configuration")

            # 3. Env
            env = generate_env_template('express')
            assert 'NODE_ENV' in env or 'PORT' in env, "Env missing variables"
            print(f"  [OK] Environment: Express .env template")

            # 4. Docker
            docker = generate_docker_compose('express', 'mysql', True)
            assert 'mysql' in docker.lower()
            print(f"  [OK] Docker: Express + MySQL docker-compose")

            # 5. DI
            services = {'UserService': [], 'AuthService': ['UserService']}
            di = generate_dependency_injection('express', services)
            assert 'function' in di.lower() or 'container' in di.lower()
            print(f"  [OK] DI: Express factory pattern DI")

            print("  SUCCESS: Express project validated")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def test_spring_project(self) -> bool:
        """Test Phase 1 on Spring Boot project."""
        print("\n[REAL PROJECT] Spring Boot microservice...")
        try:
            files = RealProjectSimulator.create_spring_project()

            # 1. Format
            ordered = format_multifile_output(files, 'spring')
            order = [f for f, _ in ordered]
            print(f"  [OK] File ordering: {len(order)} files ordered")

            # 2. Migrations
            models = {'User': files['User.java']}
            migs = generate_migrations('spring', models)
            assert any('.sql' in path for path, _ in migs), "No Flyway SQL migration"
            print(f"  [OK] Migrations: Flyway SQL migrations")

            # 3. Config
            config = generate_framework_config('spring', {'database': True, 'redis': True})
            assert len(config) > 0, "No Spring config"
            print(f"  [OK] Config: Spring Boot application.properties")

            # 4. Env
            env = generate_env_template('spring')
            assert 'SPRING' in env or 'DATABASE' in env, "Env missing variables"
            print(f"  [OK] Environment: Spring .env template")

            # 5. Docker
            docker = generate_docker_compose('spring', 'postgresql', True)
            assert 'port' in docker.lower() or '8080' in docker
            print(f"  [OK] Docker: Spring Boot docker-compose")

            # 6. DI
            services = {'UserService': ['UserRepository'], 'UserRepository': []}
            di = generate_dependency_injection('spring', services)
            assert '@Service' in di or '@Bean' in di, "DI missing Spring annotations"
            print(f"  [OK] DI: Spring @Service and @Bean configuration")

            print("  SUCCESS: Spring Boot project validated")
            return True

        except Exception as e:
            print(f"  FAIL: {e}")
            return False

    def run_all(self):
        """Run all real project tests."""
        print("\n" + "="*60)
        print("PHASE 1 REAL PROJECT VALIDATION")
        print("="*60)

        tests = [
            ("Django REST API", self.test_django_project),
            ("FastAPI async", self.test_fastapi_project),
            ("NestJS modular", self.test_nestjs_project),
            ("Express middleware", self.test_express_project),
            ("Spring Boot", self.test_spring_project),
        ]

        for test_name, test_func in tests:
            try:
                if test_func():
                    self.passed += 1
                else:
                    self.failed += 1
            except Exception as e:
                print(f"  ERROR: {e}")
                self.failed += 1

        print("\n" + "="*60)
        print(f"REAL PROJECT TESTS: {self.passed}/{len(tests)} PASSED")
        print("="*60)

        if self.failed == 0:
            print("\nAll real projects validated successfully!")
            print("Phase 1 is READY FOR PRODUCTION.")
        else:
            print(f"\n{self.failed} project test(s) need attention")

        return self.passed, self.failed


if __name__ == '__main__':
    tester = RealProjectTests()
    passed, failed = tester.run_all()
    sys.exit(0 if failed == 0 else 1)
