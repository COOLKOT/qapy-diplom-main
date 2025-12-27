# Тестирование веб-приложения "Покупка тура" (SUT)

---

## Технологии

- **Язык:** Python 3.9+
- **Тестирование:** `pytest`, `selenium`, `allure-pytest`
- **UI:** Веб-приложение (SUT)
- **База данных:** MySQL
- **Запуск SUT:** Docker Compose
- **Отчётность:** Allure Report

---

## Установка зависимостей

1. Убедитесь, что у вас установлены:
   - [Python 3.9+]
   - [pip]
   - [Docker и Docker Compose]

2. Установите зависимости из `requirements.txt`:
    
    bash pip install -r requirements.txt

---

## Запуск SUT через Docker Compose

SUT — веб-приложение и база данных — запускаются через `docker-compose.yml`.

### Шаги:

1. Убедитесь, что Docker запущен.
2. Перейдите в корень проекта (где находится `docker-compose.yml`).
3. Запустите SUT:
    bash docker-compose up -d
4. Дождитесь полной загрузки контейнеров:
   - `app` — веб-приложение (доступно по `http://localhost:8080`)
   - `mysql` — база данных
5. Проверьте статус:
   bash docker-compose ps
6. Остановка:
   bash docker-compose dow
   

---

## Запуск тестов

### 1. Убедитесь, что SUT запущен
   bash docker-compose ps
   Должны быть в статусе `Up`.

---

### 2. Запуск всех тестов

#### Запуск тестов UI:
    bash pytest Tests/test_UI.py
--alluredir=Reports/Allure-Results
--clean-alluredir
-v


---

## Генерация отчёта Allure

После выполнения тестов:

1. Сгенерируйте и откройте отчёт:
    bash allure serve Reports/Allure-Results
2. Автоматически откроется браузер с интерактивным отчётом.

3. Экспорт в HTML (для отправки):
    bash allure generate Reports/Allure-Results -o Reports/Allure-HTML --clean


---

## Структура проекта
```text
.
├── docker-compose.yml          # Запуск SUT и БД
├── requirements.txt             # Зависимости Python
├── Tests/                     # Папка с тестами
│   ├── test-case-api.md      # Тест-кейсы API
│   ├── test-case-ui.md       # Тест-кейсы UI
│   ├── test-case-db.md       # Тест-кейсы БД
│   ├── test_UI.py             # UI-тесты
│   ├── test_db.py             # Тесты работы с БД
│   ├── test_api.py            # API-тесты
│   └── use_functions.py        # Вспомогательные функции
├── Data/                    # Данные для тестов
└── README.md
```    

   

---

## Требования к окружению

- **Память:** минимум 4 ГБ для Docker
- **Порт 8080:** должен быть свободен (используется SUT)
- **Порт 3306:** должен быть свободен (используется MySQL)

---

## Примечания

- Если тесты падают из-за таймаутов — увеличьте `WebDriverWait` до 15–20 сек.
- Все тесты используют `allure` для детализированного отчёта.
