##Yatube – социальная сеть для публикации дневников.
Сайт позволяет создавать, редактировать и удалять записи. В проекте реализованы пагинация постов и кэширование, поиск по сайту, регистрация с верификацией данных, сменой и восстановлением пароля. Пользователи имеют возможность подписки на авторов и комментирования их записей.
##Технологии:
Python, Django, Django ORM, Unittest, SQLite, HTML
##Запуск проекта:
Клонировать репозиторий и перейти в него в командной строке:

`git clone https://github.com/alexeytikhonchuk/yatube`

`cd yatube`

Создать и активировать виртуальное окружение:
```
python -m venv venv
source venv/bin/activate (Mac, Linux)
source venv/scripts/activate (Windows)
```

Установить зависимости из файла requirements.txt:
```
python -m pip install --upgrade pip
pip install -r requirements.txt
 ```
Перейти в рабочую папку и выполнить миграции:
```
cd yatube
python manage.py migrate
```
Запустить сервер:
```
python manage.py runserver
```
###Автор
Алексей Тихончук