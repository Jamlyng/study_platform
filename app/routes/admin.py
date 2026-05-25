from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import User, Material, Comment, Subject, Notification
from app.decorators import admin_required

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    stats = {
        'users': User.query.count(),
        'materials': Material.query.count(),
        'comments': Comment.query.count(),
        'subjects': Subject.query.count(),
    }
    return render_template('admin/dashboard.html', stats=stats)

# Управление пользователями
@admin_bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/<int:id>/toggle-role')
@login_required
@admin_required
def toggle_role(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Нельзя изменить свою роль')
        return redirect(url_for('admin.users'))
    
    if user.role == 'admin':
        user.role = 'student'
    elif user.role == 'student':
        user.role = 'admin'
    else:
        user.role = 'student'
    
    db.session.commit()
    flash(f'Роль пользователя {user.full_name} изменена на {user.role}')
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:id>/delete')
@login_required
@admin_required
def delete_user(id):
    user = User.query.get_or_404(id)
    if user.id == current_user.id:
        flash('Нельзя удалить себя')
        return redirect(url_for('admin.users'))
    
    db.session.delete(user)
    db.session.commit()
    flash(f'Пользователь {user.full_name} удалён')
    return redirect(url_for('admin.users'))

# Управление материалами
@admin_bp.route('/materials')
@login_required
@admin_required
def materials():
    materials = Material.query.order_by(Material.created_at.desc()).all()
    return render_template('admin/materials.html', materials=materials)

@admin_bp.route('/materials/<int:id>/delete')
@login_required
@admin_required
def delete_material(id):
    material = Material.query.get_or_404(id)
    title = material.title
    db.session.delete(material)
    db.session.commit()
    flash(f'Материал «{title}» удалён')
    return redirect(url_for('admin.materials'))

# Управление комментариями
@admin_bp.route('/comments')
@login_required
@admin_required
def comments():
    comments = Comment.query.order_by(Comment.created_at.desc()).all()
    return render_template('admin/comments.html', comments=comments)

@admin_bp.route('/comments/<int:id>/delete')
@login_required
@admin_required
def delete_comment(id):
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('Комментарий удалён')
    return redirect(url_for('admin.comments'))