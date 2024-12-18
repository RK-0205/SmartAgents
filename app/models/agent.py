from app import db

class Agent(db.Model):
    __tablename__ = 'agents'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable = False)
    description = db.Column(db.String(300), nullable = False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    data_chunks = db.relationship('DataChunk', backref='agent', lazy=True, cascade='all, delete-orphan')

    content_items = db.relationship('ContentItem', backref='agent', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Agent {self.name}>'