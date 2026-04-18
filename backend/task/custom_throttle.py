# throttles.py
from rest_framework.throttling import UserRateThrottle

class AIChatThrottle(UserRateThrottle):
    scope = 'ai_chat'