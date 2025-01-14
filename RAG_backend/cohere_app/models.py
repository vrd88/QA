# models.py
from django.db import models
import uuid
from django.contrib.auth.models import User


class PromptHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_id = models.UUIDField(default=uuid.uuid4, editable=False)  # Unique identifier for each chat session
    prompt = models.TextField()
    response = models.TextField()
    comments = models.TextField(null=True, blank=True)
    thumbs_feedback = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def str(self):
        return f"User: {self.user.username}, Prompt: {self.prompt}"
    
    


class CurrentUsingCollection(models.Model):
    current_using_collection = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.current_using_collection
