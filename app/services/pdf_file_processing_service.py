import os
from app import db
from app.utils.text_processor import TextProcessor
from app.models.data_chunk import DataChunk
from app.models.content_item import ContentItem
from app.services.ollama_service import OllamaService
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.document_loaders import PyMuPDFLoader
from app.services.pinecone_service import PineconeService


class PDFFileProcessingService:
     def __init__(self, path, name, agent):
        self.path = path
        self.name = name
        self.agent = agent

     def process(self):
        # TODO: Replace with PyMuPDF for better results - DONE
        loader = PyMuPDFLoader(self.path)
        documents = loader.load()

        if documents == [] or documents is None:
            return None

        text = ""
        text = "\n".join(page.page_content for page in documents)
        if text == "":
            return None
        # TODO: Pass the text to the TextProcessor not documents - DONE
        processor = TextProcessor(text)

        chunks = processor.chunks_with_recursion(500, 0)

        client = OllamaService()

        content_item = ContentItem()
        content_item.name = self.name
        content_item.type = 'pdf'
        content_item.agent_id = self.agent.id

        db.session.add(content_item)
        db.session.commit()

        data_chunks = []

        for chunk in chunks:
            data_chunk = DataChunk()
            data_chunk.text = chunk
            data_chunk.agent_id = self.agent.id
            data_chunk.content_item_id = content_item.id
            
            # TODO: remove this line - DONE
            #data_chunk.embedding = client.get_embedding(chunk)

            data_chunks.append(data_chunk)
        db.session.add_all(data_chunks)
        db.session.commit()

        pinecone_service = PineconeService()
        #Додаэмо наші data_chunks до БД Pinecone
        pinecone_service.insert_items(data_chunks, self.agent.id)

        return content_item
     