from datetime import datetime
from typing import Dict, Any, Optional, Type, TypeVar
from bson import ObjectId
from .connection import DatabaseManager

T = TypeVar('T', bound='BaseDocument')

class BaseDocument:
    """Base class for all MongoDB documents"""
    collection_name: str = None
    
    def __init__(self, **kwargs):
        self._id: Optional[ObjectId] = kwargs.get('_id')
        if isinstance(self._id, str):
            self._id = ObjectId(self._id)
        self.created_at: datetime = kwargs.get('created_at', datetime.utcnow())
        self.updated_at: datetime = kwargs.get('updated_at', datetime.utcnow())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary"""
        def format_datetime(dt):
            if dt is None:
                return None
            if isinstance(dt, str):
                return dt
            try:
                return dt.isoformat()
            except AttributeError:
                return None

        return {
            '_id': str(self._id) if self._id else None,
            'created_at': format_datetime(self.created_at),
            'updated_at': format_datetime(self.updated_at)
        }
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """Create instance from dictionary"""
        if '_id' in data and isinstance(data['_id'], str):
            data['_id'] = ObjectId(data['_id'])
        
        # Handle datetime fields
        for field in ['created_at', 'updated_at', 'completed_at']:
            if field in data and isinstance(data[field], str):
                try:
                    data[field] = datetime.fromisoformat(data[field].replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    data[field] = None
        
        return cls(**data)
    
    def validate(self) -> bool:
        """Validate document before saving"""
        return True
    
    def save(self, db_manager: DatabaseManager) -> bool:
        """Save document to database"""
        if not self.validate():
            raise ValueError("Document validation failed")
            
        if not self.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        collection = db_manager.get_collection(self.collection_name)
        self.updated_at = datetime.utcnow()
        
        data = self.to_dict()
        # Convert string IDs back to ObjectId for MongoDB
        if '_id' in data and isinstance(data['_id'], str):
            data['_id'] = ObjectId(data['_id'])
            
        if self._id:
            result = collection.replace_one({'_id': self._id}, data)
            return result.modified_count > 0
        else:
            if '_id' in data:
                del data['_id']
            result = collection.insert_one(data)
            self._id = result.inserted_id
            return bool(self._id)
    
    @classmethod
    def find_by_id(cls: Type[T], doc_id: str, db_manager: DatabaseManager) -> Optional[T]:
        """Find document by ID"""
        if not cls.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        try:
            collection = db_manager.get_collection(cls.collection_name)
            data = collection.find_one({'_id': ObjectId(doc_id)})
            return cls.from_dict(data) if data else None
        except Exception as e:
            return None
    
    @classmethod
    def find_one(cls: Type[T], query: Dict[str, Any], db_manager: DatabaseManager) -> Optional[T]:
        """Find one document by query"""
        if not cls.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        collection = db_manager.get_collection(cls.collection_name)
        data = collection.find_one(query)
        return cls.from_dict(data) if data else None
    
    def delete(self, db_manager: DatabaseManager) -> bool:
        """Delete document from database"""
        if not self._id:
            return False
            
        if not self.collection_name:
            raise ValueError("collection_name must be set in derived class")
            
        collection = db_manager.get_collection(self.collection_name)
        result = collection.delete_one({'_id': self._id})
        return result.deleted_count > 0 