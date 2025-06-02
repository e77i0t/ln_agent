from typing import Dict, Any, Optional
from bson import ObjectId
from ..base import BaseDocument

class Contact(BaseDocument):
    """Contact document model"""
    collection_name = 'contacts'
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name: str = kwargs.get('name', '')
        self.title: str = kwargs.get('title', '')
        self.company_id: Optional[ObjectId] = kwargs.get('company_id')
        if isinstance(self.company_id, str):
            self.company_id = ObjectId(self.company_id)
        self.email: str = kwargs.get('email', '')
        self.linkedin_profile: str = kwargs.get('linkedin_profile', '')
        self.phone: str = kwargs.get('phone', '')
        self.notes: str = kwargs.get('notes', '')
        self.source: str = kwargs.get('source', '')  # e.g., 'linkedin', 'website', 'manual'
        
    def validate(self) -> bool:
        """Validate required fields"""
        if not self.name.strip():
            raise ValueError("Contact name is required")
        if not self.company_id:
            raise ValueError("Company ID is required")
        return True
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary"""
        base_dict = super().to_dict()
        contact_dict = {
            'name': self.name,
            'title': self.title,
            'company_id': self.company_id,
            'email': self.email,
            'linkedin_profile': self.linkedin_profile,
            'phone': self.phone,
            'notes': self.notes,
            'source': self.source
        }
        return {**base_dict, **contact_dict} 