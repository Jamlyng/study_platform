import os, re
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_from_directory, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models import Material, Subject, Rating, Comment, Favorite, Tag, Notification, MaterialFile 
from app.forms import MaterialForm
from werkzeug.utils import secure_filename
from sqlalchemy import or_, func

materials_bp = Blueprint('materials', __name__, url_prefix='/materials')

def transliterate(text):
    """Транслитерация кириллицы в латиницу для безопасных имён файлов"""
    mapping = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya',
    }
    result = ''
    for char in text:
        result += mapping.get(char, char)
    # Заменяем всё, кроме букв, цифр, точек и дефисов
    result = re.sub(r'[^a-zA-Z0-9.\-]', '_', result)
    return result

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx', 'txt'}



@materials_bp.route('/browse')
def browse():
    search = request.args.get('q', '')
    subject_filter = request.args.get('subject')
    type_filter = request.args.get('type')
    tag_filter = request.args.get('tag')
    sort = request.args.get('sort', 'date')
    page = request.args.get('page', 1, type=int)
    per_page = 9  # по 9 карточек на странице

    query = Material.query

    if search:
        query = query.filter(
            or_(
                Material.title.ilike(f'%{search}%'),
                Material.description.ilike(f'%{search}%'),
                Material.tags.any(Tag.name.ilike(f'%{search}%'))
            )
        )
    if subject_filter:
        query = query.filter(Material.subject.has(Subject.name == subject_filter))
    if type_filter:
        query = query.filter(Material.type == type_filter)
    if tag_filter:
        query = query.filter(Material.tags.any(Tag.name == tag_filter))

    # Сортировка
    if sort == 'rating':
        query = query.order_by(Material.average_rating.desc())
    elif sort == 'popular':
        query = query.order_by(Material.views.desc())
    elif sort == 'downloads':
        query = query.order_by(Material.downloads.desc())
    else:
        query = query.order_by(Material.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    materials = pagination.items
    subjects = Subject.query.order_by(Subject.name).all()
    all_tags = Tag.query.order_by(Tag.name).all()

    return render_template('materials/browse.html', 
                           materials=materials, 
                           subjects=subjects,
                           all_tags=all_tags,
                           pagination=pagination,
                           current_subject=subject_filter, 
                           current_type=type_filter,
                           tag_filter=tag_filter,
                           search=search, 
                           sort=sort)



@materials_bp.route('/<int:id>')
def material_detail(id):
    material = Material.query.get_or_404(id)
    material.views += 1
    db.session.commit()
    user_rating = None
    if current_user.is_authenticated:
        rating_obj = Rating.query.filter_by(user_id=current_user.id, material_id=id).first()
        if rating_obj:
            user_rating = rating_obj.value
    return render_template('materials/material_detail.html', material=material, user_rating=user_rating)



@materials_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = MaterialForm()

    if form.validate_on_submit():
        # Находим или создаём предмет
        subject_name = form.subject_name.data.strip()
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name, code=subject_name[:20].upper().replace(' ', '_'))
            db.session.add(subject)
            db.session.flush()  # чтобы получить subject.id
        material = Material(
            title=form.title.data,
            description=form.description.data,
            type=form.type.data,
            user_id=current_user.id,
            subject_id=subject.id,
            course_id=form.course.data if form.course.data else None
        )

        # Обработка тегов
        if form.tags.data:
            tag_names = [name.strip().lower() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                material.tags.append(tag)

        # Обработка файлов
        files_added = False
        if form.files.data:
            for file in form.files.data:
                if file.filename and allowed_file(file.filename):
                    # Транслитерация имени файла
                    safe_name = transliterate(file.filename.rsplit('.', 1)[0])
                    extension = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else ''
                    filename = f"{safe_name}.{extension}" if extension else safe_name
                    
                    unique_name = f"{current_user.id}_{filename}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
                    file.save(file_path)
                    
                    material_file = MaterialFile(
                        filename=unique_name,
                        original_name=file.filename  # оригинальное имя с кириллицей
                    )
                    material.files.append(material_file)
                    files_added = True

        if not files_added:
            flash('Добавьте хотя бы один файл')
            return render_template('materials/upload.html', form=form)

        db.session.add(material)
        db.session.commit()
        flash(f'Материал успешно загружен! Прикреплено файлов: {material.files.count()}')
        return redirect(url_for('materials.material_detail', id=material.id))

    return render_template('materials/upload.html', form=form)



@materials_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_material(id):
    material = Material.query.get_or_404(id)
    
    # Проверка прав: только автор или админ
    if material.author.id != current_user.id and not current_user.is_admin():
        abort(403)
    
    form = MaterialForm()
    
    if form.validate_on_submit():
        material.title = form.title.data
        material.description = form.description.data
        material.type = form.type.data
        material.course_id = form.course.data if form.course.data else None
        
        # Обновление предмета
        subject_name = form.subject_name.data.strip()
        subject = Subject.query.filter_by(name=subject_name).first()
        if not subject:
            subject = Subject(name=subject_name, code=subject_name[:20].upper().replace(' ', '_'))
            db.session.add(subject)
            db.session.flush()
        material.subject_id = subject.id
        
        # Обновление тегов
        material.tags = []
        if form.tags.data:
            tag_names = [name.strip().lower() for name in form.tags.data.split(',') if name.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                material.tags.append(tag)
        
        # Добавление новых файлов (старые не трогаем)
        if form.files.data:
            for file in form.files.data:
                if file.filename and allowed_file(file.filename):
                    safe_name = transliterate(file.filename.rsplit('.', 1)[0])
                    extension = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else ''
                    filename = f"{safe_name}.{extension}" if extension else safe_name
                    unique_name = f"{current_user.id}_{filename}"
                    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_name)
                    file.save(file_path)
                    
                    material_file = MaterialFile(
                        filename=unique_name,
                        original_name=file.filename
                    )
                    material.files.append(material_file)
        
        material.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Материал обновлён!')
        return redirect(url_for('materials.material_detail', id=material.id))
    
    # Предзаполнение формы
    form.title.data = material.title
    form.description.data = material.description
    form.type.data = material.type
    form.subject_name.data = material.subject.name if material.subject else ''
    form.course.data = material.course_id
    form.tags.data = ', '.join([tag.name for tag in material.tags])
    
    return render_template('materials/edit_material.html', form=form, material=material)



@materials_bp.route('/<int:material_id>/file/<int:file_id>/delete')
@login_required
def delete_file(material_id, file_id):
    material = Material.query.get_or_404(material_id)
    
    if material.author.id != current_user.id and not current_user.is_admin():
        abort(403)
    
    file = MaterialFile.query.get_or_404(file_id)
    
    # Удаляем физический файл
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(file)
    material.updated_at = datetime.utcnow()
    db.session.commit()
    flash('Файл удалён')
    return redirect(url_for('materials.edit_material', id=material_id))



@materials_bp.route('/rate/<int:material_id>', methods=['POST'])
@login_required
def rate(material_id):
    material = Material.query.get_or_404(material_id)
    value = request.form.get('rating', type=int)

    if current_user.id == material.author.id:
        flash('Нельзя оценить свой материал')
        return redirect(url_for('materials.material_detail', id=material_id))

    if value < 1 or value > 5:
        flash('Оценка должна быть от 1 до 5')
        return redirect(url_for('materials.material_detail', id=material_id))

    existing = Rating.query.filter_by(user_id=current_user.id, material_id=material_id).first()
    if existing:
        existing.value = value
    else:
        rating = Rating(user_id=current_user.id, material_id=material_id, value=value)
        db.session.add(rating)

    db.session.commit()
    material.recalc_rating()
    flash('Ваш голос учтён!')
    return redirect(url_for('materials.material_detail', id=material_id))

@materials_bp.route('/comment/<int:material_id>', methods=['POST'])
@login_required
def add_comment(material_id):
    material = Material.query.get_or_404(material_id)
    text = request.form.get('text')
    parent_id = request.form.get('parent_id', type=int)
    if not text or len(text.strip()) == 0:
        flash('Комментарий не может быть пустым')
        return redirect(url_for('materials.material_detail', id=material_id))
    comment = Comment(user_id=current_user.id, material_id=material_id, text=text.strip())
    if parent_id:
        parent = Comment.query.get(parent_id)
        if parent and parent.material_id == material_id:
            comment.parent_id = parent_id
    db.session.add(comment)
    db.session.commit()

    # Уведомление автору материала о новом комментарии
    if material.author.id != current_user.id:
        notification = Notification(
            user_id=material.author.id,
            text=f"{current_user.full_name} оставил комментарий к вашему материалу «{material.title}»",
            link=url_for('materials.material_detail', id=material.id)
        )
        db.session.add(notification)

    # Уведомление родителю комментария, если это ответ
    if parent_id:
        parent = Comment.query.get(parent_id)
        if parent and parent.user_id != current_user.id:
            reply_notification = Notification(
                user_id=parent.user_id,
                text=f"{current_user.full_name} ответил на ваш комментарий к «{material.title}»",
                link=url_for('materials.material_detail', id=material.id)
            )
            db.session.add(reply_notification)

    db.session.commit()
    
    flash('Комментарий добавлен!')
    return redirect(url_for('materials.material_detail', id=material_id))



@materials_bp.route('/favorite/<int:material_id>', methods=['POST'])
@login_required
def toggle_favorite(material_id):
    material = Material.query.get_or_404(material_id)
    fav = Favorite.query.filter_by(user_id=current_user.id, material_id=material_id).first()
    if fav:
        db.session.delete(fav)
        db.session.commit()
        flash('Удалено из избранного')
    else:
        fav = Favorite(user_id=current_user.id, material_id=material_id)
        db.session.add(fav)
        db.session.commit()
        flash('Добавлено в избранное')
    return redirect(url_for('materials.material_detail', id=material_id))



@materials_bp.route('/download/<int:file_id>')
def download(file_id):
    material_file = MaterialFile.query.get_or_404(file_id)
    material_file.material.downloads += 1
    db.session.commit()
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], material_file.filename, 
                               as_attachment=True, download_name=material_file.original_name)



@materials_bp.route('/api/subjects')
def api_subjects():
    q = request.args.get('q', '')
    if q:
        q_lower = q.lower()
        subjects = Subject.query.order_by(Subject.name).limit(100).all()
        # Фильтруем в Python, где lower() работает с кириллицей
        result = [s for s in subjects if q_lower in s.name.lower()]
        subjects = result[:10]
    else:
        subjects = Subject.query.order_by(Subject.name).limit(20).all()
    
    return jsonify([{'id': s.id, 'name': s.name} for s in subjects])