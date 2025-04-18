from rest_framework import serializers
from .models import EmailCampaign, Recipient, GeneratedEmail,EmailReply
from django.core.files.base import ContentFile
import base64

class RecipientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Recipient
        fields = ['id', 'email', 'name', 'is_sent', 'sent_at']
class EmailReplySerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailReply
        fields = '__all__'
class GeneratedEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedEmail
        fields = ['subject', 'body_text', 'body_html', 'generated_at']

class EmailCampaignSerializer(serializers.ModelSerializer):
    recipients = RecipientSerializer(many=True, read_only=True)
    generated_email = GeneratedEmailSerializer(read_only=True)
    replies = EmailReplySerializer(many=True, read_only=True)
    attachments = serializers.ListField(
        child=serializers.FileField(
            max_length=100000,
            allow_empty_file=False,
            use_url=False,
            required=False
        ),
        write_only=True,
        required=False
    )

    class Meta:
        model = EmailCampaign
        fields = [
            'id', 'name', 'topic', 'details', 'tone', 'created_at',
            'recipients', 'generated_email', 'attachments','replies'
        ]
        extra_kwargs = {
            'attachments': {'write_only': True}
        }

    def validate_attachments(self, value):
        if not value:  # No files provided is valid (optional)
            return value
            
        for file in value:
            # Validate file size (10MB max)
            if file.size > 10 * 1024 * 1024:
                raise serializers.ValidationError(
                    f"File {file.name} is too large (max 10MB)"
                )
            
            # Validate file types
            valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png']
            if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
                raise serializers.ValidationError(
                    f"Unsupported file type: {file.name}. "
                    f"Allowed types: {', '.join(valid_extensions)}"
                )
        return value

    def create(self, validated_data):
        # Remove attachments if present (they're handled separately)
        attachments = validated_data.pop('attachments', None)
        
        # Create the campaign
        campaign = super().create(validated_data)
        
        # If you want to store attachments, you would process them here
        # For now, they'll just be passed through to the email sending
        
        return campaign