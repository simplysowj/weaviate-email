import weaviate
from datetime import datetime

class WeaviateEmailManager:
    def __init__(self):
        # Initialize logger
        
        
        try:
            # New client initialization (v3+ syntax)
            self.client = weaviate.Client(
                url="http://localhost:8080",  # Local Weaviate
                additional_headers={
                    "X-OpenAI-Api-Key": ""  # Replace with your key
                }
            )
            self._init_schema()
            
        except Exception as e:
            print("error")
            

    def _init_schema(self):
        schema = {
            "classes": [
                {
                    "class": "EmailCampaign",
                    "properties": [
                        {"name": "campaignId", "dataType": ["text"]},
                        {"name": "name", "dataType": ["text"]},
                        {"name": "topic", "dataType": ["text"]},
                        {"name": "tone", "dataType": ["text"]}
                    ]
                },
                {
                    "class": "GeneratedEmail",
                    "properties": [
                        {"name": "campaignId", "dataType": ["text"]},
                        {"name": "subject", "dataType": ["text"]},
                        {"name": "bodyText", "dataType": ["text"]},
                        {"name": "generatedAt", "dataType": ["date"]}
                    ]
                },
                {
                    "class": "EmailReply",
                    "properties": [
                        {"name": "campaignId", "dataType": ["text"]},
                        {"name": "recipientEmail", "dataType": ["text"]},
                        {"name": "replyContent", "dataType": ["text"]},
                        {"name": "receivedAt", "dataType": ["date"]},
                        {"name": "processed", "dataType": ["boolean"]}
                    ]
                },
                {
                    "class": "KnowledgeBase",
                    "properties": [
                        {"name": "title", "dataType": ["text"]},
                        {"name": "content", "dataType": ["text"]},
                        {"name": "tags", "dataType": ["text[]"]}
                    ]
                }
            ]
        }
        if not self.client.schema.contains():
            self.client.schema.create(schema)

    def store_campaign(self, campaign):
        self.client.data_object.create(
            data_object={
                "campaignId": str(campaign.id),
                "name": campaign.name,
                "topic": campaign.topic,
                "tone": campaign.tone
            },
            class_name="EmailCampaign"
        )

    def store_generated_email(self, email):
        self.client.data_object.create(
            data_object={
                "campaignId": str(email.campaign.id),
                "subject": email.subject,
                "bodyText": email.body_text,
                "generatedAt": email.generated_at.isoformat()
            },
            class_name="GeneratedEmail"
        )

    def store_reply(self, reply):
        self.client.data_object.create(
            data_object={
                "campaignId": str(reply.campaign.id),
                "recipientEmail": reply.recipient.email,
                "replyContent": reply.reply_content,
                "receivedAt": reply.received_at.isoformat(),
                "processed": reply.processed
            },
            class_name="EmailReply"
        )

    def get_similar_replies(self, campaign_id, query, limit=3):
        result = self.client.query.get(
            "EmailReply",
            ["replyContent", "processed"]
        ).with_near_text({
            "concepts": [query],
            "certainty": 0.7
        }).with_where({
            "path": ["campaignId"],
            "operator": "Equal",
            "valueString": str(campaign_id)
        }).with_limit(limit).do()
        
        return result.get('data', {}).get('Get', {}).get('EmailReply', [])

    def get_knowledge(self, query, tags=None, limit=3):
        where_filter = {
            "path": ["tags"],
            "operator": "ContainsAny",
            "valueTextArray": tags
        } if tags else None

        query_builder = self.client.query.get(
            "KnowledgeBase",
            ["title", "content"]
        ).with_near_text({
            "concepts": [query],
            "certainty": 0.65
        }).with_limit(limit)

        if where_filter:
            query_builder = query_builder.with_where(where_filter)

        result = query_builder.do()
        return result.get('data', {}).get('Get', {}).get('KnowledgeBase', [])
    def chunk_text(self, text, chunk_size=1000, overlap=200):
        """Split large documents into manageable chunks"""
        words = text.split()
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = ' '.join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks

    def add_knowledge_item(self, title, content, tags=None):
        """Store document with chunking for better retrieval"""
        try:
            chunks = self.chunk_text(content)
            results = []
            
            for i, chunk in enumerate(chunks):
                chunk_title = f"{title} [Part {i+1}]" if len(chunks) > 1 else title
                
                result = self.client.data_object.create(
                    data_object={
                        "title": chunk_title,
                        "content": chunk,
                        "tags": tags or [],
                    },
                    class_name="KnowledgeBase"
                )
                results.append(result)
            
            return all(results)
        except Exception as e:
            self.logger.error(f"Failed to add knowledge item: {str(e)}")
            return False

    def query_knowledge_enhanced(self, query, tags=None, limit=5):
        """Enhanced retrieval with score threshold"""
        try:
            where_filter = {
                "path": ["tags"],
                "operator": "ContainsAny",
                "valueTextArray": tags
            } if tags else None

            query_builder = self.client.query.get(
                "KnowledgeBase",
                ["title", "content", "_additional {certainty}"]
            ).with_near_text({
                "concepts": [query],
                "certainty": 0.6  # Minimum relevance threshold
            }).with_limit(limit)

            if where_filter:
                query_builder = query_builder.with_where(where_filter)

            result = query_builder.do()
            items = result.get('data', {}).get('Get', {}).get('KnowledgeBase', [])
            
            # Filter by certainty score and format
            return [
                {
                    "title": item["title"],
                    "content": item["content"],
                    "score": item["_additional"]["certainty"]
                }
                for item in items
            ]
        except Exception as e:
            self.logger.error(f"Failed to query knowledge: {str(e)}")
            return []