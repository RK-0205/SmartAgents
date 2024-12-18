from langchain_community.document_loaders import AsyncChromiumLoader
from langchain_community.document_transformers import Html2TextTransformer
from app import db
from app.utils.text_processor import TextProcessor
from app.models.data_chunk import DataChunk
from app.models.content_item import ContentItem
from app.services.ollama_service import OllamaService
from app.utils.robots_txt_parse import RobotsTXTParser
from app.services.pinecone_service import PineconeService


class WebPageProcesService:
    def __init__(self, url, agent):
        self.url = url
        self.agent = agent

    def process(self):
        robots_checker = RobotsTXTParser()

        if not robots_checker.is_allowed(self.url):
            print("Webpage is forbidden for crawding.")
            return None


        loader = AsyncChromiumLoader([self.url], user_agent='TestAgent')
        data =loader.load()

        if data == [] or data is None:
            return None

        transformer = Html2TextTransformer()
        web_page_content = transformer.transform_documents(data)[0].page_content

        if web_page_content == '' or web_page_content is None:
            return None

        processor = TextProcessor(web_page_content)

        chunks = processor.chunks_with_recursion(500, 0)

        client = OllamaService()

        # Added document summary
        document_summary = client.generate_document_summary(web_page_content)
        chunks.append(document_summary)
        print(f"Document summary: \n {document_summary}")

        content_item = ContentItem()
        content_item.name = self.url
        content_item.type = 'webpage'
        content_item.agent_id = self.agent.id
        
        db.session.add(content_item)
        db.session.commit()

        data_chunks = []

        for chunk in chunks:
            #Added chunk context
            chunk_context = client.generate_chunk_context(chunk, web_page_content)
            chunk = chunk_context + '\n' + chunk
            print(f"Chunk context: \n {chunk_context}")

            data_chunk = DataChunk()
            data_chunk.text = chunk
            data_chunk.agent_id = self.agent.id
            data_chunk.content_item_id = content_item.id

            #data_chunk.embedding = client.get_embedding(chunk)

            data_chunks.append(data_chunk)
        db.session.add_all(data_chunks)
        db.session.commit()

        pinecone_service = PineconeService()
        #Додаэмо наші data_chunks до БД Pinecone
        pinecone_service.insert_items(data_chunks, self.agent.id)

        return content_item

