# Диаграмма компонентов Django

![Диаграмма компонентов Django](
https://img.plantuml.biz/plantuml/png/TP51QiCm44NtSuh1wwQB7g04cIPquJR4uFrKcRZ2iYGa9I6KthrA9Hj3qutuF0t_QT0wHFBnD6e8WpAEF8teI0xKSnklcj6pZ6HwpG25OoMjEQg-GWfOlxzjNhVu1OX7bSQhm34gquS7F7cTJWgzofERBNmlIiYvy2YjvzApVrcqd1LVGhxe5jN-h2GNtivyj0VMXJP_7H_Qoa5-aZA_8wA-wn7_UCHTZsXcAltLHLkg_OpTayjiTtjHMXvNg-VRDbDCGgYxJ5kesvoQAIKlY6wAei1cJaarnHt0ciqXVU8F)

## config

Корневой пакет Django-проекта. Содержит настройки и точку входа.

    settings.py — конфигурация (БД, приложения, крипто, P2P).

    urls.py — корневая маршрутизация.

    asgi.py — точка входа ASGI (для P2P и async).

Зависит от: apps.core, apps.blockchain.
## apps.core

Доменный слой: всё, что связано с медициной и консорциумом.

Внутри — три слоя:

    views — HTTP-интерфейс: аутентификация, портал заявок, API для врачей и пациентов.

    services — бизнес-логика: создание записей, выдача и отзыв креденшлов, реестр клиник.

    models — сущности: Clinic, Doctor, Patient, Credential, MedicalRecord.

Зависит от: apps.blockchain (для записи блоков и криптографии).
## apps.blockchain

Инфраструктурный слой: блокчейн, консенсус, сеть, криптография.

Внутри — пять слоёв:

    views — P2P-API: приём предложений блоков и голосов от других узлов.

    services — консенсус, валидация блоков, синхронизация цепочки.

    models — Block, Chain.

    crypto — AES, RSA, подписи, канонизация (JCS/CBOR).

    p2p — сервер и клиент для обмена блоками между узлами.

Не зависит от apps.core — это ключевое правило: блокчейн не знает про медицину.
