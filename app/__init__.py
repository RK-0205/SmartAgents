from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from pinecone import Pinecone

pc = Pinecone(api_key="PINECONE_API_KEY")

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)

    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:postgres@localhost:5432/flaskdb'
    db.init_app(app)
    migrate.init_app(app, db)

    from app.models import agent
    from app.models import content_item
    
    #Register Blueprints
    from app.routes.api import api_bp
    app.register_blueprint(api_bp, url_prefix='/api/agents')
    from app.routes.web import web_bp
    app.register_blueprint(web_bp, url_prefix='/')
 
    #TODO: Remove this route - DONE
    # @app.route('/')
    # def home():
    #     return 'Hello, World!'
    return app


