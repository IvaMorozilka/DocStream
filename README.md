# DocStream

## Сервис, состоящий из Телеграм бота и бэкэнда для реализации задачи автозагрузки документов (Excel, csv)

### Стэк Телеграм бота

* **ЯП**: Python
* **Библиотеки**
  * Aiogram 3.0
  * Openpyxl, Pandas
  * Aiohttp
  * Asyncpg-lite

### Стэк сервиса Processor

* **ЯП**: Python
* **Библиотеки**
  * FastAPI
  * DLT[s3, postgre]
  * boto3
  * Pandas, Openpyxl

