from app import db


class ContentItem(db.Model):
    __tablename__ = 'content_items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    #possible types: 'txt', 'pdf', 'webpage'
    type = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    data_chunks = db.relationship('DataChunk', backref='content_item', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<ContentItem id:{self.id}>, name: {self.name}, type:{self.type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
        }