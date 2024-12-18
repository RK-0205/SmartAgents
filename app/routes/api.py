from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename
from app import db
from app.models.agent import Agent
from app.models.data_chunk import DataChunk
import os
from app.services.text_file_processing_sevices import TextFileProcessingService
# TODO: Import the PDFFileProcessingService - DONE
from app.services.pdf_file_processing_service import PDFFileProcessingService
import app.services.text_file_processing_sevices
from app.services.ollama_service import OllamaService
from app.services.web_page_processing_service import WebPageProcesService
from app.services.pinecone_service import PineconeService
from app.models.content_item import ContentItem


api_bp = Blueprint('api', __name__)


@api_bp.route('/', methods=['GET'])
def index():
    agents = Agent.query.all()
    agents = [{'id': agent.id, 'name': agent.name, 'description': agent.description} for agent in agents]
    return jsonify({
        'status': 'success',
        'agents': agents})


@api_bp.route('/<int:id>', methods=['GET'])
def show(id):
    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            'status': "failed",
            'message': 'Agent not found'}), 404
    return jsonify({
        'status': 'success',
        'agent': {
            'id': agent.id, 
            'name': agent.name, 
            'description': agent.description,
            }
        })  


@api_bp.route('/', methods=['POST'])
def create():
    data = request.get_json()

    agent = Agent(name=data['name'], description=data['description'])
    db.session.add(agent)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'agent': {
            'id': agent.id, 
            'name': agent.name, 
            'description': agent.description}})


@api_bp.route('/<int:id>', methods=['PUT'])
def update(id):
    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            'status': 'failed',
            'message': 'Agent not found'}), 404
    data = request.get_json()
    agent.name = data['name']
    agent.description = data['description']
    db.session.commit()

    return jsonify({
        "status": "success",
        "agent": {
            'id': agent.id, 
            'name': agent.name, 
            'description': agent.description}})


@api_bp.route('/<int:id>', methods=['DELETE'])
def delete(id):
    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            'status': "failed",
            'message': 'Agent not found'}), 404
    
    #Створюємо екземпляр PineconeSirvice
    pinecone_service = PineconeService()

    #Видаляємо namespace пов'язаний з цим агентом.
    #Якщо виникне помилка, то ігноруємо
    try:
        pinecone_service.delete_namespace(agent.id)
    except Exception as e:
        pass

    db.session.delete(agent)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'agent': {
            'id': agent.id, 
            'name': agent.name, 
            'description': agent.description}
    })


@api_bp.route('/<int:id>/content/<int:content_item_id>', methods=['DELETE'])
def delete_content(id, content_item_id):
    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            'status': "failed",
            'message': 'Agent not found'}), 404

    content_item = ContentItem.query.get(content_item_id)
    if content_item is None:
        return jsonify({
            "status": "failed",
            "message": 'Content item not found'
        }), 404

    #Створюємо екземпляр PineconeService
    pinecone_service = PineconeService()

    #Формуємо масив id з data_chunks
    ids = [f"{data_chunk.id}" for data_chunk in content_item.data_chunks]

    #Намагаємось видалити data_chunks з Pinecone
    #для відповідного namespace
    try:
        pinecone_service.delete_content_item(ids, agent.id)
    except Exception as e:
        pass

    #Видаляємо сам контент-елемент з бази даних
    db.session.delete(content_item)
    db.session.commit()

    return jsonify({
        "status": "success",
        "content": content_item.to_dict()
    })


@api_bp.route('/<int:id>/file', methods=["POST"])
def upload_file(id):

    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            'status': "failed",
            'message': 'Agent not found'}), 404

    if 'file' not in request.files:
        return jsonify({
            'status': "failed",
            'message': "No file provided"}), 400
    
    file = request.files['file']

    if file.filename == '':
        return jsonify({
            'status': "failed",
            'message': "No file provided"}), 400
    
    # TODO: Add pdf support - DONE
    if not file.filename.endswith(('.txt', '.pdf')):
        return jsonify({
            'status': "failed",
            "message": "Invalid file format, expect .txt or .pdf"}), 400
    
    filename = secure_filename(file.filename)

    if not os.path.exists('./uploads'):
        os.makedirs('./uploads')

    file.save(f'./uploads/{filename}')

    file.close()
    
    #TODO: Use PDFFileProcessingService for pdf files - DONE
       
    if filename.endswith('.pdf'):
        service = PDFFileProcessingService(f'./uploads/{filename}', filename, agent)
    
    if filename.endswith('.txt'):
        service = TextFileProcessingService(f'./uploads/{filename}', filename, agent)
   
    content_item = service.process()

    os.remove(f'./uploads/{filename}')

    if content_item is None:
        return jsonify({
            "status": "failed",
            'message': 'Can not process the txt file'}), 400

    return jsonify({
        "status": "success",
        "content": content_item.to_dict()})


@api_bp.route('/<int:id>/ask', methods=['POST'])
def ask(id):
    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            'status': "failed",
            'message': 'Agent not found'}), 404
    data = request.get_json()
    question = data['body']

    ollama_service = OllamaService()
    #question_embedding = ollama_service.get_embedding(question)
    #threshold = 0.5
    limit = 5

    #Створюємо екземпляр PineconeService
    pinecone_service = PineconeService()

    #Виконуємо пошук
    results = pinecone_service.query(question, agent.id, limit)

    #results = DataChunk.query \
            # .filter(DataChunk.agent_id == id) \
            # .filter(DataChunk.embedding.cosine_distance(question_embedding) < threshold) \
            # .order_by(DataChunk.embedding.cosine_distance(question_embedding)) \
            # .limit(limit) \
            # .all()

    if len(results) == 0:
        return jsonify({
            "status": "success",
            "message": {
                'body': 'I don\'t know',
                "agent_id": agent.id
                }
            })

    print (f'Check len of results: {len(results)}')

    # for result in results:
    #     print(f'\nResult: {result}')

    # resut_text = '\n'.join([result.text for result in results])
    # print(f"result text:\n{resut_text}")



    response = ollama_service.get_answer(question, results) 


    return jsonify({
        "status": "success",
        "message": {
            'body': response,
            'agent_id': agent.id
            }
        })


@api_bp.route('/<int:id>/webpage', methods=['POST'])
def upload_page(id):
    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            "status": "failed",
            'message': 'Agent not found'}), 404

    if 'webpage_url' not in request.json:
        return jsonify({
            "status": "failed",
            "message": "No page provided"}), 400

    webpage_url = request.json['webpage_url']

    service = WebPageProcesService(webpage_url, agent)
    content_item = service.process()
    if content_item is None:
        return jsonify({
            "status": "failed",
            'message': 'Can not process the webpage'}), 400

    return jsonify({
        "status": "success",
        "content": content_item.to_dict()})


@api_bp.route('/<int:id>/content', methods=['GET'])
def list_content(id):
    agent = Agent.query.get(id)
    if agent is None:
        return jsonify({
            'status': "failed",
            'message': 'Agent not found'}), 404
    
    if not agent.content_items:
        return jsonify({
            'status': "success",
            'content': []
        })
    
    return jsonify({
        "status": "success",
        "content": [content_item.to_dict() for content_item in agent.content_items]
    })