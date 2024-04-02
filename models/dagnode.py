from .base import db

class DAGNodeModel(db.Model):
    __tablename__ = 'dagnodes'

    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(120), db.ForeignKey('transactions.transaction_id'), unique=True, nullable=False)
    dependencies = db.relationship('DAGNodeModel', secondary='dagnode_dependencies',
                                   primaryjoin='DAGNodeModel.id==dagnode_dependencies.c.dagnode_id',
                                   secondaryjoin='DAGNodeModel.id==dagnode_dependencies.c.dependency_id',
                                   backref='dependents')

    def __repr__(self):
        return f'<DAGNode {self.transaction_id}>'

class DAGNodeDependencies(db.Model):
    __tablename__ = 'dagnode_dependencies'
    dagnode_id = db.Column(db.Integer, db.ForeignKey('dagnodes.id'), primary_key=True)
    dependency_id = db.Column(db.Integer, db.ForeignKey('dagnodes.id'), primary_key=True)
