# API: внутренний обмен между нодами

Все эндпоинты — под префиксом `/clinic/`. Защищены заголовком `X-Internal-Token`, значение — `INTERNAL_SYNC_TOKEN` из `.env`. Без заголовка или с неверным значением — `403 {"error": "forbidden"}`.

## 1. `GET /clinic/network/height`

Состояние блокчейна ноды.

**Запрос:**

```http
GET /clinic/network/height
X-Internal-Token: <token>
```

**Ответ 200:**

```json
{
  "node_id": "node0",
  "height": 1,
  "last_hash": "47a005a242e3d0ccebc61c62f389389f376ab9391e602f1d2b46c54ba555d2e8"
}
```

- `height: -1` — цепочка пуста (genesis ещё не создан).
- `height: 0` — только genesis.

## 2. `GET /clinic/network/blocks?from=N`

Блоки с индексом ≥ `N`.

**Запрос:**

```http
GET /clinic/network/blocks?from=0
X-Internal-Token: <token>
```

**Ответ 200:**

```json
{
  "blocks": [
    {
      "index": 0,
      "prev_hash": "0000...0000",
      "type": "genesis",
      "timestamp": "2026-11-12T00:23:21.016898+00:00",
      "content_hash": "4289ed2a...",
      "payload": {"msg": "genesis"},
      "hash": "ef9ddc8a..."
    },
    {
      "index": 1,
      "prev_hash": "ef9ddc8a...",
      "type": "medical_record",
      "timestamp": "2026-11-12T00:23:21.065203+00:00",
      "content_hash": "4fecb96a...",
      "payload": {"diagnosis": "headache", "patient_name": "test123"},
      "hash": "47a005a2..."
    }
  ]
}
```

**Ошибки:**

- `400 {"error": "from must be integer"}` — параметр `from` не число.

## 3. `POST /clinic/network/blocks`

Приём одного блока от пира. Перед добавлением блок проходит валидацию.

**Запрос:**

```http
POST /clinic/network/blocks
X-Internal-Token: <token>
Content-Type: application/json

{
  "index": 1,
  "prev_hash": "ef9ddc8a...",
  "type": "medical_record",
  "timestamp": "2026-11-12T00:23:21.065203+00:00",
  "content_hash": "4fecb96a...",
  "payload": {"diagnosis": "headache", "patient_name": "test123"},
  "hash": "47a005a2..."
}
```

**Ответ 200 (блок принят):**

```json
{"ok": true, "index": 1}
```

**Ответ 400 (блок отклонён):**

```json
{"ok": false, "error": "hash mismatch: sent=000000000000…, computed=47a005a242e3…"}
```

## 4. Проверки при приёме блока

`services.validate_incoming_block` выполняет по порядку:

| Проверка | Условие | Ошибка |
|---|---|---|
| Обязательные поля | все из `index`, `prev_hash`, `type`, `timestamp`, `content_hash`, `payload`, `hash` | `missing field: <name>` |
| Индекс — целое | `int(index)` без исключения | `index is not an integer` |
| Пересборка блока | `Block` собирается из полей | `cannot rebuild block: <e>` |
| Хеш блока | `computed_hash == data["hash"]` | `hash mismatch: sent=…, computed=…` |
| `content_hash` (для `medical_record`) | `sha256(canonical_json(payload)) == content_hash` | `content_hash mismatch: payload подменён` |
| Непрерывность индекса | `index == local_height + 1` | `index gap: expected …, got …` |
| Связь с предыдущим | `prev_hash == local_last_hash` | `prev_hash mismatch: expected …, got …` |

## 5. Синхронизация

`python manage.py sync_chain` на узле:

1. Для каждого пира из `settings.PEERS` — `GET /network/height`.
2. Если у пира высота больше локальной — `GET /network/blocks?from=local_height+1`.
3. Для каждого блока — `validate_incoming_block`. При ошибке — лог и остановка для этого пира.
4. При успехе — `add_block_from_dict`, высота растёт.

Вызов вручную:

```powershell
docker compose exec node1 python manage.py sync_chain
```

Ожидаемо:

```
local height: -1
http://node0:8000: accepted block 0
http://node0:8000: accepted block 1
http://node2:8000: up to date (remote=-1)
```

## 6. Коды ошибок (сводка)

| Код | `error` | Причина |
|---|---|---|
| 403 | `forbidden` | нет/неверный `X-Internal-Token` |
| 400 | `bad json` | тело не парсится как JSON |
| 400 | `missing field: <name>` | нет обязательного поля |
| 400 | `index is not an integer` | `index` не число |
| 400 | `cannot rebuild block: <e>` | блок не собирается из полей |
| 400 | `hash mismatch: sent=…, computed=…` | хеш не совпадает |
| 400 | `content_hash mismatch: payload подменён` | payload не соответствует `content_hash` |
| 400 | `index gap: expected …, got …` | разрыв в индексах |
| 400 | `prev_hash mismatch: expected …, got …` | неверная ссылка на предыдущий блок |
| 400 | `from must be integer` | параметр `from` не число (GET) |