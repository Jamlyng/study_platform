from flask import Blueprint, render_template, request, redirect, url_for, current_app
from app.models import Material, User, Subject, Tag
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    search = request.args.get('q', '')
    
    # Если есть поисковый запрос — редиректим в каталог
    if search:
        return redirect(url_for('materials.browse', q=search))
    
    # Последние материалы
    latest = Material.query.order_by(Material.created_at.desc()).limit(6).all()
    
    # Популярные по рейтингу
    top_rated = Material.query.filter(Material.ratings.any())\
        .order_by(Material.average_rating.desc()).limit(3).all()
    
    # Статистика
    stats = {
        'materials': Material.query.count(),
        'users': User.query.count(),
        'subjects': Subject.query.count(),
    }
    
    return render_template('index.html', 
                           latest=latest, 
                           top_rated=top_rated, 
                           stats=stats,
                           search='')