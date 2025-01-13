# serializers.py
from rest_framework import serializers
from .models import PromptHistory

class PromptHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = PromptHistory
        fields = ['id', 'session_id', 'prompt', 'response', 'created_at']  # Include any other fields you need
        
        
from .models import CurrentUsingCollection

class CurrentUsingCollectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CurrentUsingCollection
        fields = ['current_using_collection']
