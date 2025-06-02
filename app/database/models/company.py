from typing import Dict, Any, List, Optional
from ..base import BaseDocument
from bson import ObjectId

class Company(BaseDocument):
    """Company document model"""
    collection_name = 'companies'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name: str = kwargs.get('name', '')
        self.domain: str = kwargs.get('domain', '')
        self.size: str = kwargs.get('size', '')
        self.headquarters: str = kwargs.get('headquarters', '')
        self.locations: List[str] = kwargs.get('locations', [])
        self.industry: str = kwargs.get('industry', '')
        self.description: str = kwargs.get('description', '')
        self.linkedin_url: str = kwargs.get('linkedin_url', '')
        self.website_data: Dict[str, Any] = kwargs.get('website_data', {})
        self.opencorporates_data: Dict[str, Any] = kwargs.get('opencorporates_data', {})
        self.company_number: str = kwargs.get('company_number', '')
        self.jurisdiction: str = kwargs.get('jurisdiction', '')
        self.status: str = kwargs.get('status', 'active')
        
    def validate(self) -> bool:
        """Validate required fields"""
        if not self.name.strip():
            raise ValueError("Company name is required")
        if not self.domain.strip():
            raise ValueError("Company domain is required")
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert company to dictionary"""
        base_dict = super().to_dict()
        company_dict = {
            'name': self.name,
            'domain': self.domain,
            'size': self.size,
            'headquarters': self.headquarters,
            'locations': self.locations,
            'industry': self.industry,
            'description': self.description,
            'linkedin_url': self.linkedin_url,
            'website_data': self.website_data,
            'opencorporates_data': self.opencorporates_data,
            'company_number': self.company_number,
            'jurisdiction': self.jurisdiction,
            'status': self.status
        }
        return {**base_dict, **company_dict}
    
    @classmethod
    def find_by_name(cls, name: str, db_manager) -> Optional['Company']:
        """Find a company by name"""
        collection = db_manager.get_collection(cls.collection_name)
        result = collection.find_one({'name': name})
        if result:
            return cls.from_dict(result)
        return None
    
    @classmethod
    def search(cls, query: str, db_manager, limit: int = 20) -> List['Company']:
        """Search for companies by name or domain"""
        collection = db_manager.get_collection(cls.collection_name)
        results = collection.find({
            '$or': [
                {'name': {'$regex': query, '$options': 'i'}},
                {'domain': {'$regex': query, '$options': 'i'}}
            ]
        }).limit(limit)
        return [cls.from_dict(doc) for doc in results] 