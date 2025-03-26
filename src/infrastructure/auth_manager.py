"""
Authentication and authorization system
"""
from typing import Dict, List, Optional
import jwt
import bcrypt
from datetime import datetime, timedelta
import logging
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from .database_manager import Base, DatabaseManager

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)

class Role(Base):
    __tablename__ = 'roles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    permissions = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class UserRole(Base):
    __tablename__ = 'user_roles'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role_id = Column(Integer, ForeignKey('roles.id'))
    created_at = Column(DateTime, default=datetime.utcnow)

class AuthManager:
    def __init__(self, config: Dict, db_manager: DatabaseManager):
        self.config = config
        self.db = db_manager
        self.logger = logging.getLogger(__name__)
        self.secret_key = config['jwt_secret']
        self.token_expiry = config.get('token_expiry', 3600)  # 1 hour default
        
    async def create_user(self, username: str, email: str, password: str, is_admin: bool = False) -> int:
        """Create new user"""
        try:
            # Hash password
            password_hash = bcrypt.hashpw(
                password.encode('utf-8'),
                bcrypt.gensalt()
            ).decode('utf-8')
            
            # Create user
            async with self.db.get_session() as session:
                user = User(
                    username=username,
                    email=email,
                    password_hash=password_hash,
                    is_admin=is_admin
                )
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user.id
                
        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            raise
            
    async def authenticate(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return JWT token"""
        try:
            async with self.db.get_session() as session:
                # Get user
                query = select(User).where(User.username == username)
                result = await session.execute(query)
                user = result.scalar_one_or_none()
                
                if not user or not user.is_active:
                    return None
                    
                # Verify password
                if not bcrypt.checkpw(
                    password.encode('utf-8'),
                    user.password_hash.encode('utf-8')
                ):
                    return None
                    
                # Update last login
                user.last_login = datetime.utcnow()
                await session.commit()
                
                # Generate token
                return self.generate_token(user)
                
        except Exception as e:
            self.logger.error(f"Error authenticating user: {str(e)}")
            raise
            
    def generate_token(self, user: User) -> str:
        """Generate JWT token"""
        try:
            payload = {
                'user_id': user.id,
                'username': user.username,
                'is_admin': user.is_admin,
                'exp': datetime.utcnow() + timedelta(seconds=self.token_expiry)
            }
            return jwt.encode(payload, self.secret_key, algorithm='HS256')
        except Exception as e:
            self.logger.error(f"Error generating token: {str(e)}")
            raise
            
    def verify_token(self, token: str) -> Optional[Dict]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=['HS256'])
            if payload['exp'] < datetime.utcnow().timestamp():
                return None
            return payload
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            self.logger.error(f"Error verifying token: {str(e)}")
            raise
            
    async def create_role(self, name: str, permissions: List[str]) -> int:
        """Create new role"""
        try:
            async with self.db.get_session() as session:
                role = Role(name=name, permissions=permissions)
                session.add(role)
                await session.commit()
                await session.refresh(role)
                return role.id
        except Exception as e:
            self.logger.error(f"Error creating role: {str(e)}")
            raise
            
    async def assign_role(self, user_id: int, role_id: int) -> bool:
        """Assign role to user"""
        try:
            async with self.db.get_session() as session:
                user_role = UserRole(user_id=user_id, role_id=role_id)
                session.add(user_role)
                await session.commit()
                return True
        except Exception as e:
            self.logger.error(f"Error assigning role: {str(e)}")
            raise
            
    async def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions"""
        try:
            async with self.db.get_session() as session:
                query = select(Role.permissions).join(UserRole).where(
                    UserRole.user_id == user_id
                )
                result = await session.execute(query)
                permissions_lists = result.scalars().all()
                
                # Flatten permissions lists
                permissions = set()
                for perm_list in permissions_lists:
                    permissions.update(perm_list)
                    
                return list(permissions)
                
        except Exception as e:
            self.logger.error(f"Error getting permissions: {str(e)}")
            raise
            
    async def check_permission(self, user_id: int, permission: str) -> bool:
        """Check if user has specific permission"""
        try:
            permissions = await self.get_user_permissions(user_id)
            return permission in permissions
        except Exception as e:
            self.logger.error(f"Error checking permission: {str(e)}")
            raise
