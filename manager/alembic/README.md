# Памятка по основным командам alembic

## Набор основных команд:

Инициализировать приложение alembic в проекте:
```
alembic init --template async alembic
```

Создать файл миграции:
```
alembic revision --autogenerate -m "Comment" --rev-id <Number of migration>
```

Применить миграции:
```
alembic upgrade head
```

Последняя применённая миграция:
```
alembic current
```

Откатить все миграции в проекте:
```
alembic downgrade base
```

Отмена последней миграции:
```
alembic downgrade -1
```

Все миграции в хронологическом порядке:
```
alembic history 
```

Все миграции в хронологическом порядке в развёрнутом виде:
```
alembic history -v
```

Просмотр истории с пометкой актуальной миграции:
```
alembic history -i 
```
