"""
Rate limiting utility to manage request rates per domain.
"""
import time
from collections import defaultdict
from threading import Lock
from typing import List, DefaultDict

class RateLimiter:
    """Rate limiter to prevent overwhelming target servers."""
    
    def __init__(self, window_size: int = 60):
        """
        Initialize the rate limiter.
        
        Args:
            window_size (int): Time window in seconds for rate limiting
        """
        self.window_size = window_size
        self.requests: DefaultDict[str, List[float]] = defaultdict(list)
        self.lock = Lock()
    
    def can_make_request(self, domain: str, requests_per_minute: int = 30) -> bool:
        """
        Check if we can make a request to this domain.
        
        Args:
            domain (str): The domain to check
            requests_per_minute (int): Maximum allowed requests per minute
            
        Returns:
            bool: True if request is allowed, False otherwise
        """
        with self.lock:
            current_time = time.time()
            # Remove old requests outside the window
            self.requests[domain] = [
                req_time for req_time in self.requests[domain]
                if current_time - req_time <= self.window_size
            ]
            
            # Check if we're under the rate limit
            return len(self.requests[domain]) < requests_per_minute
    
    def record_request(self, domain: str):
        """
        Record that we made a request to this domain.
        
        Args:
            domain (str): The domain to record the request for
        """
        with self.lock:
            current_time = time.time()
            self.requests[domain].append(current_time)
    
    def get_remaining_delay(self, domain: str, requests_per_minute: int = 30) -> float:
        """
        Get the remaining delay needed before the next request.
        
        Args:
            domain (str): The domain to check
            requests_per_minute (int): Maximum allowed requests per minute
            
        Returns:
            float: Time in seconds to wait before next request (0 if no delay needed)
        """
        with self.lock:
            if not self.requests[domain]:
                return 0
                
            current_time = time.time()
            # Clean up old requests
            self.requests[domain] = [
                req_time for req_time in self.requests[domain]
                if current_time - req_time <= self.window_size
            ]
            
            if len(self.requests[domain]) < requests_per_minute:
                return 0
                
            # Calculate when the oldest request will expire
            oldest_request = min(self.requests[domain])
            return max(0, self.window_size - (current_time - oldest_request))
    
    def clear(self, domain: str = None):
        """
        Clear rate limiting history.
        
        Args:
            domain (str, optional): Specific domain to clear, or all if None
        """
        with self.lock:
            if domain:
                self.requests[domain].clear()
            else:
                self.requests.clear() 