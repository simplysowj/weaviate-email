import logging
from openai import OpenAI
from django.conf import settings
from .models import EmailReply, Recipient
from .gmail_service import GmailService

logger = logging.getLogger(__name__)

class ReplyHandler:
    def __init__(self):
        self.client = OpenAI(api_key="")
        self.gmail = GmailService()
        self.weaviate = WeaviateEmailManager()
        print("self.gmail")
        print(self.gmail)
        
    
    def generate_reply(self, email_reply):
        print(f"Recipient ID: {email_reply.recipient.id}")
        """Generate a personalized reply using AI"""
        try:
            print("replyhandler")
            # Verify recipient still exists
            if not Recipient.objects.filter(pk=email_reply.recipient.id).exists():
                return None
            similar_replies = self.weaviate.get_similar_replies(
                original_content=email_reply.reply_content,
                limit=3
            )
            
            # Get relevant knowledge
            knowledge = self.weaviate.query_knowledge(
                query=email_reply.campaign.topic,
                tags=[email_reply.campaign.tone]
            )
                
            prompt = f"""
            Campaign: {email_reply.campaign.name}
            Original Email: {email_reply.campaign.generated_email.body_text}
            Received Reply: {email_reply.reply_content}
            SIMILAR PAST REPLIES:
            {self._format_similar_replies(similar_replies)}
            
            RELEVANT KNOWLEDGE:
            {self._format_knowledge(knowledge)}
            
            Please compose a professional response that:
            1. Acknowledges their reply
            2. Addresses any questions/points they raised

            3. Maintains a {email_reply.campaign.tone} tone
            4. Is concise (under 150 words)
            5.remember that you are replying on behalf of Sowjanya for the company Realcoderz Pvt Limited
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300
            )
            
            reply_content = response.choices[0].message.content.strip()
            
            # Store the reply in Weaviate
            self.weaviate.store_email_reply(
                original_content=email_reply.reply_content,
                reply_content=reply_content,
                recipient_email=email_reply.recipient.email
            )
            
            return reply_content
        
        except Exception as e:
            logger.error(f"Error generating reply: {str(e)}")
            raise
    def _format_similar_replies(self, replies: list[dict]) -> str:
        """Format similar replies for prompt"""
        if not replies:
            return "No similar replies found"
        return "\n".join(
            f"• {item['replyContent'][:200]}..."
            for item in replies
        )

    def _format_knowledge(self, knowledge_items: list[dict]) -> str:
        """Format knowledge base items for prompt"""
        if not knowledge_items:
            return "No relevant knowledge found"
        return "\n".join(
            f"• {item['title']}: {item['content'][:200]}..."
            for item in knowledge_items
        )
    def process_pending_replies_for_campaign(self, campaign):
        """Process and reply to pending messages for a campaign"""
        pending_replies = EmailReply.objects.filter(
            campaign=campaign,
            processed=False
        )
        print(pending_replies.count())
        print("pending_replies.count()")
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
                reply.processed = True  # Mark as processed to avoid retrying
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