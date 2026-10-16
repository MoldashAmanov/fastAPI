# Скрипт создания администратора

import getpass
from app.database import SessionLocal, engine, Base
from app import models
from app.models import User
from app.auth import get_password_hash

Base.metadata.create_all(bind=engine)


def main():
    print("### Создание администратора ###\n")

    username = input("Имя администратора: ").strip()
    if len(username) < 3:
        print("Имя должно быть минимум 3 символа")
        return

    email = input("Email: ").strip()
    if "@" not in email:
        print("Некорректный email")
        return

    password = getpass.getpass("Повторите пароль: ")
    if len(password) < 6:
        print("Пароль минимум 6 символов")
        return

    confirm = getpass.getpass("Повторите пароль: ")
    if password != confirm:
        print("Пароли не совпадают")
        return

    db = SessionLocal()
    try:
        # Проверка уникальности
        if db.query(User).filter(User.username == username).first():
            print(f"Пользователь '{username}' уже существует")
            return

        if db.query(User).filter(User.email == email).first():
            print(f"Email '{email}' уже занят")
            return

        # Создаем админа
        admin = User(
            username=username,
            email=email,
            hashed_password=get_password_hash(password),
            is_admin=True,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        print(f"\nАдминистратор '{admin.username}' создан (ID: {admin.id})")
    finally:
        db.close()



if __name__ == "__main__":
    main()
    
