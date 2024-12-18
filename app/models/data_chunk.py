from app import db
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector


V_DIM = 2048
class DataChunk(db.Model):
    __tablename__ = 'data_chunks'

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)

    tsvector = db.Column(TSVECTOR, nullable=True)
    embedding = db.Column(Vector(V_DIM), nullable=True)

    content_item_id = db.Column(db.Integer, db.ForeignKey('content_items.id'), nullable=True)

    def __repr__(self):
        return f'<DataChunk id: {self.id}. text: {self.text}>'

    def to_dict(self):
        return {
            'id': self.id,
            'text': self.text,
            'created_at': self.created_at,
            'agent_id': self.agent_id,
            'tsvector': self.tsvector
        }
