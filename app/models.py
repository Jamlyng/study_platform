from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

material_tags = db.Table('material_tags',
    db.Column('material_id', db.Integer, db.ForeignKey('material.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Tag {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    full_name = db.Column(db.String(100), nullable=False)
    avatar = db.Column(db.String(200), default='defaults_avatars/default.png')
    role = db.Column(db.String(20), default='student')  # student, teacher, admin
    faculty = db.Column(db.String(100), default='')
    course = db.Column(db.String(10), default='')
    bio = db.Column(db.Text, default='')
    rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Отношения
    materials = db.relationship('Material', backref='author', lazy='dynamic')
    ratings = db.relationship('Rating', backref='user', lazy='dynamic')
    comments = db.relationship('Comment', backref='user', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='user', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def __repr__(self):
        return f'<User {self.full_name}>'

class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True)
    faculty = db.Column(db.String(100))
    description = db.Column(db.Text)

    materials = db.relationship('Material', backref='subject', lazy='dynamic')

    def __repr__(self):
        return f'<Subject {self.name}>'

class MaterialFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    original_name = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    material = db.relationship('Material', backref=db.backref('files', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<MaterialFile {self.original_name}>'

class Material(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(20))  # 'конспект', 'решение', 'видео', 'презентация'
    file_url = db.Column(db.String(300))  # ссылка или путь к файлу
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    course_id = db.Column(db.Integer)  # или связь с курсом, пока просто число
    views = db.Column(db.Integer, default=0)
    downloads = db.Column(db.Integer, default=0)
    average_rating = db.Column(db.Float, default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tags = db.relationship('Tag', secondary=material_tags, backref=db.backref('materials', lazy='dynamic'), lazy='dynamic')
    
    # Отношения
    comments = db.relationship('Comment', backref='material', lazy='dynamic')
    ratings = db.relationship('Rating', backref='material', lazy='dynamic')
    favorites = db.relationship('Favorite', backref='material', lazy='dynamic')

    def recalc_rating(self):
        avg = db.session.query(db.func.avg(Rating.value)).filter(Rating.material_id==self.id).scalar()
        self.average_rating = avg or 0.0
        db.session.commit()

    def __repr__(self):
        return f'<Material {self.title}>'

class Rating(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    value = db.Column(db.Integer, nullable=False)  # 1-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'material_id', name='unique_user_material_rating'),)

    def __repr__(self):
        return f'<Rating {self.value}>'

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Для ответов на комментарии
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

    def __repr__(self):
        return f'<Comment {self.id}>'

class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    material_id = db.Column(db.Integer, db.ForeignKey('material.id'), nullable=False)
    saved_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'material_id', name='unique_favorite'),)

    def __repr__(self):
        return f'<Favorite {self.id}>'
    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.String(300), nullable=False)
    link = db.Column(db.String(300))  # куда перейти при клике
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('notifications', lazy='dynamic'))

    def __repr__(self):
        return f'<Notification {self.id}: {self.text[:30]}>'