# TelegramBot
Hakaton work
Я скинул тестовую базу данных но для полной проверки лучше запустить код у вас и через /start создасться новая БД
Через /debug есть тестовые данные

### Технологии:
1. **Python** – основной язык разработки бота.
2. **pyTelegramBotApi** – библиотека для создания бота в Telegram.
3. **SQLite** – используется для хранения данных (информация о пользователях, командах и голосах).
4. **Schedule** и **Threading** – для планирования напоминаний и работы с многозадачностью (например, отправка напоминаний ежедневно).

### Основной функционал:
 **Команды для пользователей:**
   `/start` – запускает бота и объясняет функционал.
   `/reg` – регистрация пользователя в команде.
   `/changeteam` – смена команды.
   `/vote` – голосование по уровню энергии (оценка от 1 до 10).
   `/mystats` – просмотр личной статистики.
  
 **Команды для менеджеров:**
   `/manteams` – управление командами (просмотр списка, добавление/удаление команд).
   `/statsteams` – статистика по всем командам.
   `/regman` – регистрация менеджера с использованием секретного пароля.
   `/addteam` - создание новой команды.
   `/removeteam` - удаление команды.

 **Логика работы:**
   Бот хранит данные о пользователях, командах и голосах в базе данных SQLite.
   Пользователь может голосовать о своем уровне энергии (сохранение данных).
   Менеджеры могут управлять командами и просматривать статистику по ним.
   Для поддержания вовлеченности пользователям ежедневно отправляется напоминание через напоминалку, реализованную с помощью **schedule**.
   Статистика по голосам доступна в разных разрезах: "всё время", "последнюю неделю", "сегодня".
  
 **Особенности работы с базой данных:**
   Используются таблицы для голосов и команд.
   Каждому пользователю присваивается команда, он может голосовать только после регистрации.
   Статистика рассчитывается на основе данных голосов.

 **Напоминания:**
   Напоминания о необходимости проголосовать отправляются пользователям ежедневно в 10:00.

Бот обеспечивает удобный интерфейс для голосования и управления командами, а также анализирует энергию в командах и предлагает рекомендации.
