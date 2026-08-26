# PBOT

* * *

### это прям на сервере
`gunicorn -w 1 -b 127.0.0.1:8080 bot:app`

* * *

### ну это локальный запуск
`flask --app bot run --debug --host=0.0.0.0 --port=5000`

* * *

### установим библиотеки
`pip install Flask pyTelegramBotAPI gunicorn`

* * *
