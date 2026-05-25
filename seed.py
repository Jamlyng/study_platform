from app import create_app, db
from app.models import User, Subject, Material, Tag
import csv
import random
from datetime import datetime, timedelta

app = create_app()

def load_subjects_from_file(filename):
    """Загружает предметы из текстового файла (по одной строке на предмет)"""
    subjects = []
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            name = line.strip()
            if name:
                code = name.upper().replace(' ', '_')[:20]
                faculty = 'Факультет информатики и вычислительной техники'
                subjects.append(Subject(name=name, code=code, faculty=faculty))
    return subjects

def load_users_from_file(filename):
    """Загружает пользователей из CSV файла (формат: имя, email, пароль, роль)"""
    users = []
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        dialect = csv.Sniffer().sniff(content)
        f.seek(0)
        reader = csv.reader(f, dialect)
        
        for row in reader:
            if len(row) >= 4:
                full_name = row[0].strip()
                email = row[1].strip()
                password = row[2].strip()
                role = row[3].strip().lower()
                
                if role not in ['admin', 'teacher', 'student']:
                    print(f"Предупреждение: неизвестная роль '{role}' для {email}, установлена 'student'")
                    role = 'student'
                
                user = User(email=email, full_name=full_name, role=role)
                user.set_password(password)
                users.append(user)
    return users

def create_sample_materials(users, subjects):
    """Создаёт тестовые материалы"""
    materials_data = [
        {
            'title': 'Конспект по пределам функций',
            'description': 'Подробный конспект лекций по пределам. Включает определение предела, свойства, замечательные пределы, примеры вычисления.',
            'type': 'конспект',
            'subject': 'Математический анализ',
            'tags': ['пределы', 'функции', 'лекции', '1 курс'],
            'author_email': 'ivan@mail.ru'
        },
        {
            'title': 'Лабораторная работа: сортировка массивов',
            'description': 'Реализация и сравнение алгоритмов сортировки: пузырьком, быстрая, слиянием. Код на Python с замерами времени.',
            'type': 'решение',
            'subject': 'Алгоритмы и структуры данных',
            'tags': ['сортировка', 'python', 'лабораторная', '2 курс'],
            'author_email': 'maria@mail.ru'
        },
        {
            'title': 'Презентация: Введение в SQL',
            'description': 'Основные понятия реляционных баз данных: таблицы, ключи, нормализация. Синтаксис SELECT, JOIN, GROUP BY.',
            'type': 'презентация',
            'subject': 'Технологии баз данных',
            'tags': ['SQL', 'базы данных', 'презентация', '3 курс'],
            'author_email': 'alex@mail.ru'
        },
        {
            'title': 'Решение задач по комбинаторике',
            'description': 'Разбор 15 типовых задач: размещения, перестановки, сочетания с повторениями и без. Подробные решения.',
            'type': 'решение',
            'subject': 'Дискретная математика',
            'tags': ['комбинаторика', 'задачи', 'решения', '1 курс'],
            'author_email': 'ivan@mail.ru'
        },
        {
            'title': 'Видеоурок: Настройка Linux сервера',
            'description': 'Пошаговая инструкция по установке и базовой настройке Ubuntu Server: SSH, брандмауэр, создание пользователей.',
            'type': 'видео',
            'subject': 'Операционные системы Linux',
            'tags': ['linux', 'сервер', 'ubuntu', 'ssh', '3 курс'],
            'author_email': 'dmitry@mail.ru'
        },
        {
            'title': 'Шпаргалка по HTML и CSS',
            'description': 'Краткий справочник основных тегов HTML5 и свойств CSS3. Удобно для быстрой проверки перед экзаменом.',
            'type': 'конспект',
            'subject': 'Разработка веб-приложений на Kotlin',
            'tags': ['html', 'css', 'шпаргалка', 'веб'],
            'author_email': 'elena@mail.ru'
        },
        {
            'title': 'Лекции по теории графов',
            'description': 'Конспект семестрового курса: деревья, обходы, кратчайшие пути, потоки в сетях, паросочетания.',
            'type': 'конспект',
            'subject': 'Дискретная математика',
            'tags': ['графы', 'лекции', 'алгоритмы', '2 курс'],
            'author_email': 'ivan@mail.ru'
        },
        {
            'title': 'Проект: Чат-бот на Python',
            'description': 'Учебный проект по созданию Telegram-бота с использованием aiogram. Подключение к API погоды.',
            'type': 'решение',
            'subject': 'Алгоритмы и структуры данных',
            'tags': ['python', 'telegram', 'бот', 'проект'],
            'author_email': 'maria@mail.ru'
        },
        {
            'title': 'Методичка по PostgreSQL',
            'description': 'Администрирование PostgreSQL: создание БД, пользователи, права, бэкап и восстановление, индексы.',
            'type': 'конспект',
            'subject': 'Система управления базами данных PostgreSQL',
            'tags': ['postgresql', 'sql', 'администрирование', 'методичка'],
            'author_email': 'alex@mail.ru'
        },
        {
            'title': 'Решение экзаменационных задач по матану',
            'description': 'Сборник задач с экзаменов прошлых лет. Производные, интегралы, ряды. С подробным разбором.',
            'type': 'решение',
            'subject': 'Математический анализ',
            'tags': ['экзамен', 'задачи', 'интегралы', 'производные'],
            'author_email': 'dmitry@mail.ru'
        },
        {
            'title': 'Презентация: Основы машинного обучения',
            'description': 'Введение в ML: типы задач, алгоритмы классификации и регрессии, метрики качества.',
            'type': 'презентация',
            'subject': 'Введение в машинное обучение',
            'tags': ['ML', 'машинное обучение', 'презентация', '4 курс'],
            'author_email': 'elena@mail.ru'
        },
        {
            'title': 'Конспект по многопоточности',
            'description': 'Потоки, процессы, синхронизация, мьютексы, семафоры, deadlock. Примеры на C и Python.',
            'type': 'конспект',
            'subject': 'Многопоточное и асинхронное программирование',
            'tags': ['потоки', 'многопоточность', 'синхронизация', 'c'],
            'author_email': 'ivan@mail.ru'
        },
    ]
    
    materials = []
    for data in materials_data:
        # Находим автора
        author = User.query.filter_by(email=data['author_email']).first()
        if not author:
            continue
        
        # Находим предмет
        subject = Subject.query.filter_by(name=data['subject']).first()
        if not subject:
            continue
        
        # Случайная дата за последние 30 дней
        random_days = random.randint(0, 30)
        created = datetime.utcnow() - timedelta(days=random_days)
        
        material = Material(
            title=data['title'],
            description=data['description'],
            type=data['type'],
            user_id=author.id,
            subject_id=subject.id,
            views=random.randint(10, 300),
            downloads=random.randint(0, 50),
            average_rating=round(random.uniform(3.0, 5.0), 1),
            created_at=created,
            updated_at=created
        )
        
        # Добавляем теги
        for tag_name in data['tags']:
            tag = Tag.query.filter_by(name=tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                db.session.add(tag)
            material.tags.append(tag)
        
        materials.append(material)
    
    return materials

def seed_database():
    with app.app_context():
        print("Очистка базы данных...")
        db.drop_all()
        print("Создание таблиц...")
        db.create_all()

        # Загружаем предметы
        print("\nЗагрузка предметов из subjects.txt...")
        try:
            subjects = load_subjects_from_file('subjects.txt')
            db.session.add_all(subjects)
            print(f"Добавлено {len(subjects)} предметов")
        except FileNotFoundError:
            print("Ошибка: файл subjects.txt не найден!")
            return

        # Загружаем пользователей
        print("\nЗагрузка пользователей из users.txt...")
        try:
            users = load_users_from_file('users.txt')
            db.session.add_all(users)
            print(f"Добавлено {len(users)} пользователей")
        except FileNotFoundError:
            print("Ошибка: файл users.txt не найден!")
            return
        
        # Сохраняем, чтобы были id у пользователей и предметов
        db.session.commit()
        
        # Создаём тестовые материалы
        print("\nСоздание тестовых материалов...")
        try:
            materials = create_sample_materials(users, subjects)
            db.session.add_all(materials)
            print(f"Добавлено {len(materials)} материалов")
        except Exception as e:
            print(f"Ошибка при создании материалов: {e}")
        
        db.session.commit()
        
        print("\n" + "="*50)
        print("Готово! База данных успешно заполнена.")
        print("="*50)
        
        print("\nСозданные пользователи:")
        print("-" * 50)
        for user in users:
            print(f"{user.role:10} | {user.full_name:20} | {user.email}")
        
        print(f"\nСоздано предметов: {len(subjects)}")
        print(f"Создано материалов: {len(materials)}")
        
        print("\nМатериалы:")
        print("-" * 50)
        for m in materials:
            print(f"{m.type:10} | {m.title[:40]:40} | {m.author.full_name}")

if __name__ == '__main__':
    seed_database()