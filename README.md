# ira-utils
Разные утилиты для команды по борьбе с кремлеботами

## Скрипт для сбора статистики YouTube

Скрипт main.py проходит по списку каналов из файла channels.txt, а также по списку видео из videos.txt, смотрит 
комментарии под всеми видео (вышедшие начиная с указанной в интерфейсе даты) и составляет таблицу (в файле 
stat_<дата>.csv): идентификатор пользователя, идентификатор канала, количество комментариев от пользователя под видео 
с канала  

### Установка и запуск

На github в разделе actions https://github.com/civsocit/ira-utils/actions должны лежать автоматически собранные 
бинарные файлы. Проще всего взять запустить их, предварительно положив рядом файл channels.txt со списком каналов и 
(или) videos.txt со списком видео   

Можно запустить и из python (версия 3.7 или старше). Делать это как-то так:
```
python -m pip install poetry
poetry install --no-dev
poetry run python main.py
```

Для статистики по каналам файл channels.txt со списком каналов должен лежать рядом со скриптом. Пример файла есть в 
репозитории. Для статистики по видео файл videos.txt со списком видео должен лежать рядом со скриптом, и пример тоже 
есть в репозитории. 

Для работы скрипта нужен Google API Key для YouTube https://developers.google.com/youtube/v3/getting-started  
Регистрировать OAuth2.0 не надо, скрипт использует простой API Key

API Key можно ввести в программе в поле для ввода. Либо, чтобы не вводить его каждый раз заново, рядом с файлом 
программы создать файл с именем "environment.env" или ".env" и записать ключ там:
```
YOUTUBE_API_KEY=<ваш ключ>
``` 

Google API имеет ограничения на использование https://developers.google.com/youtube/v3/getting-started#quota. На момент 
написания скрипта квоты хватает примерно на 2 запуска в день со списком из 40 не слишком популярных каналов, с датой 
отсечки 3 дня от сегодняшнего. Если квоты не будет хватать, список каналов нужно будет разбить и запускать по частям в 
разные дни.  

Ход работы скрипта пишется в консоль. Поэтому консоль нужно держать открытой и следить за происходящим. 

Иногда комментариев бывает настолько много, что скрипт не справляется с выгрузкой (ограничения API). На этот случай 
есть параметр COMMENTS_LIMIT=ЧИСЛО. Укажите его в .env файле под ключём, чтобы ограничить число выгружаемых комментариев
```
COMMENTS_LIMIT=10000
```

