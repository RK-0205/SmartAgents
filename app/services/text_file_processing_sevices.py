import os
from app import db
from app.utils.text_processor import TextProcessor
from app.models.data_chunk import DataChunk
from app.models.content_item import ContentItem
from app.services.ollama_service import OllamaService
from app.services.pinecone_service import PineconeService


class TextFileProcessingService:
    def __init__(self, file_path, file_name, agent):
        self.file_path = file_path
        self.file_name = file_name
        self.agent = agent
        self.client = OllamaService()

    def process(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        
        if text == '' or text is None:
            return None
        
        processor = TextProcessor(text)

        #chunks = processor.chunks_with_overlap(5, 2)
        # TODO: Increase to 500 for better results - DONE
        chunks = processor.chunks_with_recursion(500, 0)

        content_item = ContentItem()
        content_item.name = self.file_name
        content_item.type = 'txt'
        content_item.agent_id = self.agent.id

        db.session.add(content_item)
        db.session.commit()

        data_chunks = []
        for chunk in chunks:
            data_chunk = DataChunk()
            data_chunk.text = chunk
            data_chunk.agent_id = self.agent.id
            data_chunk.content_item_id = content_item.id
            #TODO: remove this line - DONE
            #data_chunk.embedding = self.client.get_embedding(chunk)
            data_chunks.append(data_chunk)
        db.session.add_all(data_chunks)
        db.session.commit()

        pinecone_service = PineconeService()
        #Додаэмо наші data_chunks до БД Pinecone
        pinecone_service.insert_items(data_chunks, self.agent.id)

        return content_item
    