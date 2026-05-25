from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo
from flask_wtf.file import FileAllowed, MultipleFileField

class RegistrationForm(FlaskForm):
    full_name = StringField('Полное имя', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Повторите пароль', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Войти')

class EditProfileForm(FlaskForm):
    full_name = StringField('Полное имя', validators=[DataRequired(), Length(min=2, max=100)])
    faculty = StringField('Факультет')
    course = StringField('Курс')
    bio = TextAreaField('О себе')
    avatar = FileField('Фото профиля', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Только изображения!')
    ])
    submit = SubmitField('Сохранить изменения')

class MaterialForm(FlaskForm):
    title = StringField('Название', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Описание')
    type = SelectField('Тип материала', choices=[
        ('конспект', 'Конспект'),
        ('решение', 'Решение задач'),
        ('видео', 'Видеообъяснение'),
        ('презентация', 'Презентация')
    ], validators=[DataRequired()])
    subject_name = StringField('Предмет', validators=[DataRequired()])
    course = StringField('Курс/группа')
    files = MultipleFileField('Файлы (PDF, изображения, можно несколько)')
    tags = StringField('Теги (через запятую)')
    submit = SubmitField('Загрузить')
    


