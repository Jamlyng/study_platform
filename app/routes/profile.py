import os
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models import User, Material, Favorite
from app.forms import EditProfileForm

profile_bp = Blueprint('profile', __name__)



@profile_bp.route('/profile/<int:id>')
def user_profile(id):
    user = User.query.get_or_404(id)
    materials = Material.query.filter_by(user_id=user.id).order_by(Material.created_at.desc()).all()
    return render_template('profile/profile.html', user=user, materials=materials)




@profile_bp.route('/favorites')
@login_required
def favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).order_by(Favorite.saved_at.desc()).all()
    return render_template('profile/favorites.html', favorites=favs)




@profile_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    
    # Список стандартных аватаров
    avatars_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'defaults_avatars')
    default_avatars = []
    if os.path.exists(avatars_dir):
        default_avatars = sorted(os.listdir(avatars_dir))
    
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.faculty = form.faculty.data
        current_user.course = form.course.data
        current_user.bio = form.bio.data
        
        # Выбор стандартного аватара
        selected_default = request.form.get('default_avatar')
        if selected_default:
            current_user.avatar = 'defaults_avatars/' + selected_default
        # Или загрузка своего
        elif form.avatar.data:
            filename = secure_filename(form.avatar.data.filename)
            unique_name = f"avatar_{current_user.id}_{filename}"
            avatar_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'avatars', unique_name)
            os.makedirs(os.path.dirname(avatar_path), exist_ok=True)
            form.avatar.data.save(avatar_path)
            current_user.avatar = 'avatars/' + unique_name
        
        db.session.commit()
        flash('Профиль обновлён!')
        return redirect(url_for('profile.user_profile', id=current_user.id))
    
    # Предзаполнение
    form.full_name.data = current_user.full_name
    form.faculty.data = current_user.faculty
    form.course.data = current_user.course
    form.bio.data = current_user.bio
    
    return render_template('profile/edit_profile.html', form=form, default_avatars=default_avatars)