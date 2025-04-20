import logging
from openai import OpenAI
from django.conf import settings
from .models import EmailReply, Recipient
from .gmail_service import GmailService
import weaviate

logger = logging.getLogger(__name__)

# Initialize Weaviate client
weaviate_client = weaviate.Client(
    url="https://your-instance.weaviate.network",  # Use "http://localhost:8080" if testing locally
    auth_client_secret=weaviate.AuthApiKey(api_key="your-weaviate-api-key"),
    additional_headers={"X-OpenAI-Api-Key": settings.OPENAI_API_KEY}
)

# Define schema for EmailInteraction if not already present
def create_schema():
    if not weaviate_client.schema.contains({"class": "EmailInteraction"}):
        schema = {
            "class": "EmailInteraction",
            "description": "Storing AI replies",
            "vectorizer": "text2vec-openai",
            "moduleConfig": {
                "text2vec-openai": {
                    "vectorizeClassName": True
                }
            },
            "properties": [
                {"name": "reply_text", "dataType": ["text"]},
                {"name": "ai_reply", "dataType": ["text"]},
                {"name": "campaign_name", "dataType": ["text"]},
                {"name": "tone", "dataType": ["text"]}
            ]
        }
        weaviate_client.schema.create_class(schema)

create_schema()

class ReplyHandler:
    def __init__(self):
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.gmail = GmailService()
        self.weaviate = weaviate_client

    def store_reply(self, email_reply, ai_reply):
        self.weaviate.data_object.create({
            "reply_text": email_reply.reply_content,
            "ai_reply": ai_reply,
            "campaign_name": email_reply.campaign.name,
            "tone": email_reply.campaign.tone
        }, "EmailInteraction")

    def find_similar_reply(self, reply_text):
        result = self.weaviate.query.get("EmailInteraction", ["reply_text", "ai_reply"])\
            .with_near_text({"concepts": [reply_text]})\
            .with_limit(1).do()

        matches = result['data']['Get']['EmailInteraction']
        return matches[0]['ai_reply'] if matches else None

    def generate_reply(self, email_reply):
        try:
            if not Recipient.objects.filter(pk=email_reply.recipient.id).exists():
                return None

            similar_reply = self.find_similar_reply(email_reply.reply_content)

            prompt = f"""
            Campaign: {email_reply.campaign.name}
            Original Email: {email_reply.campaign.generated_email.body_text}
            Received Reply: {email_reply.reply_content}
            {f"Example past similar reply: {similar_reply}" if similar_reply else ""}

            Please compose a professional response that:
            1. Acknowledges their reply
            2. Addresses any questions/points they raised
            3. Maintains a {email_reply.campaign.tone} tone
            4. Is concise (under 150 words)
            """

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )

            ai_reply = response.choices[0].message.content.strip()
            self.store_reply(email_reply, ai_reply)
            return ai_reply

        except Exception as e:
            logger.error(f"Error generating reply: {str(e)}")
            raise

    def process_pending_replies_for_campaign(self, campaign):
        pending_replies = EmailReply.objects.filter(
            campaign=campaign,
            processed=False
        )
        results = {
            'total': pending_replies.count(),
            'success': 0,
            'failed': 0,
            'details': []
        }
        for reply in pending_replies:
            try:
                ai_reply = self.generate_reply(reply)
                if not ai_reply:
                    logger.warning(f"No reply generated for {reply.id}")
                    results['details'].append({
                        'reply_id': reply.id,
                        'status': 'skipped',
                        'reason': 'no_reply_generated'
                    })
                    continue
                reply_text_with_breaks = ai_reply.replace('\n', '<br>')
                html_content = f"<p>{reply_text_with_breaks}</p>"

                self.gmail.send_email(
                    sender=self.gmail.get_hardcoded_user_email(),
                    to=reply.recipient.email,
                    subject=f"Re: {reply.campaign.generated_email.subject}",
                    body_text=ai_reply,
                    body_html=html_content
                )

                reply.processed = True
                reply.reply_sent = True
                reply.save()
                results['success'] += 1
                results['details'].append({
                    'reply_id': reply.id,
                    'status': 'sent',
                    'recipient': reply.recipient.email,
                    'message': 'Reply sent successfully'
                })
            except Exception as e:
                logger.error(f"Failed to process reply: {str(e)}")
                reply.processed = True
                reply.save()
                results['failed'] += 1
                results['details'].append({
                    'reply_id': reply.id,
                    'status': 'failed',
                    'error': str(e),
                    'error_type': type(e).__name__
                })

        logger.info(f"Reply processing completed: {results['success']} sent, {results['failed']} failed")
        return results
