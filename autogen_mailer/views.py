from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, JSONParser
from django.shortcuts import get_object_or_404
from .models import EmailCampaign, Recipient, GeneratedEmail, EmailReply
from .serializers import EmailCampaignSerializer, RecipientSerializer, GeneratedEmailSerializer
from .autogen_service import AutoGenEmailGenerator
from .gmail_service import GmailService
from rest_framework.decorators import api_view
from rest_framework.decorators import api_view, permission_classes
import csv
from io import TextIOWrapper
from rest_framework.permissions import AllowAny
from django.utils import timezone
import logging
from .reply_handler import ReplyHandler
from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from .weaviate_client import WeaviateEmailManager
import PyPDF2
import docx
import os

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from rest_framework import status

@api_view(['POST'])
@parser_classes([MultiPartParser])
def upload_knowledge_document(request):
    try:
        file = request.FILES['file']
        title = request.POST.get('title', 'Untitled Document')
        tags = [tag.strip() for tag in request.POST.get('tags', '').split(',') if tag.strip()]
        campaign_id = request.POST.get('campaign_id')
        
        # Extract text based on file type
        text = ''
        if file.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file)
            text = '\n'.join([page.extract_text() for page in reader.pages])
        elif file.name.endswith(('.docx', '.doc')):
            doc = docx.Document(file)
            text = '\n'.join([para.text for para in doc.paragraphs])
        else:  # txt, md, etc.
            text = file.read().decode('utf-8')
        
        # Store in Weaviate
        weaviate = WeaviateEmailManager()
        success = weaviate.add_knowledge_item(
            title=title,
            content=text,
            tags=tags
        )
        
        if success:
            return JsonResponse({'status': 'success'})
        return JsonResponse({'status': 'error', 'message': 'Weaviate storage failed'}, status=500)
    
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        try:
            user = User.objects.get(username=username)
            if user.check_password(password):
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": {
                        "username": user.username,
                        "email": user.email
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def user_logout(request):
    logout(request)
    return Response({'message': 'Logged out successfully'})

class EmailCampaignViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    queryset = EmailCampaign.objects.all()
    serializer_class = EmailCampaignSerializer
    parser_classes = [MultiPartParser, JSONParser]  # Handle both file uploads and JSON

    # Hardcoded user details
    HARDCODED_USER = {
        'username': 'sowjanya',
        'email': 'simplysowj@gmail.com'
    }
    
    def get_hardcoded_user_email(self):
        return self.HARDCODED_USER['email']

    


    @action(detail=True, methods=['get'])
    def reply_stats(self, request, pk=None):
        """Get statistics about replies for a campaign"""
        campaign = self.get_object()
        stats = {
            'total_replies': EmailReply.objects.filter(campaign=campaign).count(),
            'pending_replies': EmailReply.objects.filter(
                campaign=campaign, 
                processed=False
            ).count(),
            'sent_replies': EmailReply.objects.filter(
                campaign=campaign, 
                reply_sent=True
            ).count(),
        }
        return Response(stats)

    @action(detail=True, methods=['post'])
    def process_replies(self, request, pk=None):
        """Process replies for a specific campaign with detailed response"""
        try:
            print("entered for replies")
            campaign = self.get_object()
            gmail = GmailService()
            print(gmail)
            reply_handler = ReplyHandler()
            print(reply_handler)
            
            # Step 1: Find new replies
            found_count = gmail.process_replies_for_campaign(campaign)
            print(found_count)
            
            # Step 2: Process replies
            sent_count = reply_handler.process_pending_replies_for_campaign(campaign)
            print(sent_count)
            
            # Get updated stats
            stats = self.reply_stats(request, pk).data
            print(stats)
            print(campaign.name)
            print(campaign.id)
            
            return Response({
                'status': 'success',
                'message': f'Processed {found_count} replies and sent {sent_count} responses',
                'stats': stats,
                'details': {
                    'new_replies_found': found_count,
                    'responses_sent': sent_count,
                    'campaign_id': campaign.id,
                    'campaign_name': campaign.name
                }
            })
            
        except Exception as e:
            logger.error(f"Error processing replies: {str(e)}", exc_info=True)
            return Response(
                {
                    'status': 'error',
                    'message': str(e),
                    'details': {
                        'campaign_id': pk,
                        'error_type': type(e).__name__
                    }
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
     # Add this new action just before the RecipientViewSet class definition
    @action(detail=True, methods=['get'])
    def verify_replies(self, request, pk=None):
        """Verify reply processing status"""
        campaign = self.get_object()
        
        # Check for unprocessed replies
        pending_replies = EmailReply.objects.filter(
            campaign=campaign,
            processed=False
        ).count()
        
        # Get last processing attempt
        last_processed = EmailReply.objects.filter(
            campaign=campaign,
            processed=True
        ).order_by('-received_at').first()
        
        return Response({
            'status': 'success',
            'campaign_id': campaign.id,
            'pending_replies': pending_replies,
            'last_processed': last_processed.received_at if last_processed else None,
            'last_recipient': last_processed.recipient.email if last_processed else None,
            'message': 'Verification complete'
        })

        
    @action(detail=True, methods=['post'])
    def import_recipients(self, request, pk=None):
        campaign = get_object_or_404(EmailCampaign, pk=pk)  # Fixed typo
        file = request.FILES.get('file')
        
        if not file:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            csv_file = TextIOWrapper(file.file, encoding='utf-8')
            reader = csv.DictReader(csv_file)
            
            recipients = []
            for row in reader:
                email = row.get('email', '').strip() if row.get('email') else ''
                name = row.get('name', '').strip() if row.get('name') else ''
                
                if not email:  # Skip rows with empty email
                    continue
                    
                recipients.append(Recipient(
                    campaign=campaign,
                    email=email,
                    name=name
                ))
            
            if not recipients:
                return Response({'error': 'No valid recipients found in file'}, status=status.HTTP_400_BAD_REQUEST)
            
            Recipient.objects.bulk_create(recipients)
            return Response({'message': f'{len(recipients)} recipients imported successfully'})
        
        except Exception as e:
            print("error")
            return Response(
                {'error': f'Error processing file: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    @action(detail=True, methods=['post'])
    def generate_content(self, request, pk=None):
        campaign = get_object_or_404(EmailCampaign, pk=pk)
        details = campaign.details or ""
        key_points = [point.strip() for point in details.split('\n') if point.strip()]
        
        context = {
            "purpose": str(campaign.topic),
            "key_points": key_points,
            "tone": str(campaign.tone)
        }
        
        generator = AutoGenEmailGenerator()
        try:
            email_content = generator.generate_email(context)
            
            GeneratedEmail.objects.update_or_create(
                campaign=campaign,
                defaults={
                    'subject': email_content['subject'],
                    'body_text': email_content['body_text'],
                    'body_html': email_content['body_html']
                }
            )
            
            return Response(GeneratedEmailSerializer(instance=campaign.generated_email).data)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def preview(self, request, pk=None):
        campaign = get_object_or_404(EmailCampaign, pk=pk)
        if not hasattr(campaign, 'generated_email'):
            return Response({'error': 'No generated content'}, status=status.HTTP_404_NOT_FOUND)
        return Response(GeneratedEmailSerializer(instance=campaign.generated_email).data)
    
    @action(detail=True, methods=['post'])
    def send_emails(self, request, pk=None):
        campaign = get_object_or_404(EmailCampaign, pk=pk)
        if not hasattr(campaign, 'generated_email'):
            return Response({'error': 'Generate content first'}, status=status.HTTP_400_BAD_REQUEST)
        
        recipients = campaign.recipients.filter(is_sent=False)
        if not recipients.exists():
            return Response({'message': 'No recipients to send'})
        
        updated = recipients.update(is_sent=True, sent_at=timezone.now())
        return Response({'message': f'Marked {updated} emails as sent'})

    @action(detail=True, methods=['post'])
    def generate_and_send(self, request, pk=None):
        campaign = get_object_or_404(EmailCampaign, pk=pk)
        details = campaign.details or ""
        key_points = [point.strip() for point in details.split('\n') if point.strip()]
        
        # Get files if they exist (optional)
        files = request.FILES.getlist('attachments', [])
        
        # Validate files if any were provided
        if files:
            print("entered for files in views")
            for file in files:
                if file.size > 25 * 1024 * 1024:  # Gmail's 25MB limit
                    return Response(
                        {'error': f'File {file.name} is too large (max 25MB)'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
                valid_extensions = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', 
                                '.jpg', '.jpeg', '.png', '.txt', '.csv')
                if not file.name.lower().endswith(valid_extensions):
                    return Response(
                        {'error': f'Unsupported file type: {file.name}'}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )

        try:
            # Generate email content
            generator = AutoGenEmailGenerator()
            context = {
                "purpose": str(campaign.topic),
                "key_points": key_points,
                "tone": str(campaign.tone)
            }
            email_content = generator.generate_email(context)
            
            # Save generated content
            generated_email, created = GeneratedEmail.objects.update_or_create(
                campaign=campaign,
                defaults={
                    'subject': email_content['subject'],
                    'body_text': email_content['body_text'],
                    'body_html': email_content['body_html']
                }
            )
            
            # Send emails (with or without attachments)
            gmail = GmailService()
            sender_email = self.get_hardcoded_user_email()
            recipients = campaign.recipients.filter(is_sent=False)
            
            results = {'success': 0, 'failures': []}
            
            for recipient in recipients:
                try:
                    # Need to rewind file pointers if they exist
                    attachment_files = []
                    if files:
                        print("entered gmail")
                        for file in files:
                            from django.core.files.uploadedfile import InMemoryUploadedFile
                            from io import BytesIO
                            
                            file_content = file.read()
                            new_file = InMemoryUploadedFile(
                                BytesIO(file_content),
                                None,
                                file.name,
                                file.content_type,
                                len(file_content),
                                None
                            )
                            attachment_files.append(new_file)
                            file.seek(0)  # Rewind original file
                    
                    gmail.send_email(
                        sender=sender_email,
                        to=recipient.email,
                        subject=email_content['subject'],
                        body_text=email_content['body_text'],
                        body_html=email_content['body_html'],
                        attachments=attachment_files if attachment_files else None
                    )
                    recipient.is_sent = True
                    recipient.sent_at = timezone.now()
                    recipient.save()
                    results['success'] += 1
                    logger.info(f"Email {'with attachments ' if files else ''}sent to {recipient.email}")
                except Exception as e:
                    logger.error(f"Failed to send to {recipient.email}: {str(e)}")
                    results['failures'].append({
                        'email': recipient.email,
                        'error': str(e)
                    })
            
            return Response({
                'message': f'Successfully sent {results["success"]} emails',
                'failures': results['failures'],
                'generated_email': GeneratedEmailSerializer(instance=generated_email).data
            })
            
        except Exception as e:
            logger.error(f"Error in generate_and_send: {str(e)}", exc_info=True)
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
class RecipientViewSet(viewsets.ModelViewSet):
    serializer_class = RecipientSerializer
    
    def get_queryset(self):
        campaign_id = self.request.query_params.get('campaign_id')
        if campaign_id:
            return Recipient.objects.filter(campaign_id=campaign_id)
        return Recipient.objects.none()