# ServiceDesk на ALT Linux: запуск, права, службы и устранение неполадок

Этот документ — про то, как «железно» поднять приложение и что делать с
ошибками **503** и **404**. Здесь: кто под каким пользователем работает, какие
права у файлов, готовые конфиги служб (TCP и unix-сокет) и пошаговая диагностика.
Всё с учётом Kerberos.

---

## 1. Кто кого запускает (общая картина)

```
Браузер ──https──► Apache (служба httpd2, пользователь apache2)
                     │  обратный прокси
                     ▼
                 gunicorn (служба servicedesk, пользователь servicedesk)
                     │
                     ▼
                 Flask-приложение  ──►  PostgreSQL (служба postgresql)
```

Три отдельные службы и три пользователя:
| Служба | Что делает | Под каким пользователем |
|--------|-----------|--------------------------|
| `httpd2` | Apache: TLS, Kerberos, проксирует запросы | `apache2` |
| `servicedesk` | gunicorn + наше приложение | `servicedesk` |
| `postgresql` | база данных | `postgres` |

> Проверить, под кем реально работает Apache на вашем сервере:
> `ps -o user= -C httpd2 | sort -u` (обычно `apache2`). Дальше по тексту
> «группа веб-сервера» = эта группа.

**Важно:** в нашей схеме Apache **проксирует ВСЁ** (включая `/static`) на gunicorn,
поэтому Apache **не нужен доступ к файлам приложения** в `/opt/servicedesk`. Ему
нужны только свои файлы: сертификаты и keytab. Это сильно упрощает права.

---

## 2. Права и владельцы файлов (таблица)

| Путь | Владелец:группа | Права | Зачем |
|------|------------------|-------|-------|
| `/opt/servicedesk` и всё внутри | `servicedesk:servicedesk` | папки 755, файлы 644 | приложение работает под `servicedesk` |
| `/opt/servicedesk/.env` | `servicedesk:servicedesk` | `640` | секреты (пароли) — только владельцу |
| `/opt/servicedesk/.venv` | `servicedesk:servicedesk` | как есть | **не трогать массовым chmod!** (см. ниже) |
| `/opt/servicedesk/app/static/uploads` (и `tickets/`, `kb/`) | `servicedesk:servicedesk` | 755 | приложение **записывает** сюда вложения |
| `/etc/systemd/system/servicedesk.service` | `root:root` | 644 | юнит systemd |
| `/etc/httpd2/conf/sites-available/servicedesk.conf` | `root:root` | 644 | конфиг Apache |
| `/etc/httpd2/servicedesk.keytab` | `root:apache2` | `640` | Apache читает для Kerberos |
| `/etc/ssl/servicedesk/servicedesk.key` | `root:root` | `600` | закрытый ключ TLS (читает мастер-процесс Apache, он root) |
| `/etc/ssl/servicedesk/*.crt` | `root:root` | 644 | открытые сертификаты |

### Выставить права на приложение одной командой
```bash
chown -R servicedesk:servicedesk /opt/servicedesk
chmod 640 /opt/servicedesk/.env
```
> ⚠️ **Не делайте** `find /opt/servicedesk -type f -exec chmod 644 {} \;` — это
> снимет «исполняемость» с файлов внутри `.venv` (python, gunicorn) и приложение
> перестанет запускаться. Достаточно `chown -R` (владельца), режимы из коробки
> корректны. Если уже сломали `.venv` — восстановите:
> `chmod +x /opt/servicedesk/.venv/bin/*` (или пересоздайте окружение).
   
### Права на keytab и сертификаты
```bash
chown root:apache2 /etc/httpd2/servicedesk.  keytab && chmod 640 /etc/httpd2/servicedesk.keytab
chown root:root /etc/ssl/servicedesk/* && chmod 600 /etc/ssl/servicedesk/servicedesk.key && chmod 644 /etc/ssl/servicedesk/*.crt
```

---

## 3. Служба приложения — `servicedesk.service` (вариант TCP, рекомендуется)

Файл `/etc/systemd/system/servicedesk.service` (готовый — в `deploy/servicedesk.service`):
```ini
[Unit]
Description=ServiceDesk (gunicorn)
After=network-online.target postgresql.service
Wants=network-online.target

[Service]
User=servicedesk
Group=servicedesk
WorkingDirectory=/opt/servicedesk
Environment=PYTHONUNBUFFERED=1
ExecStart=/opt/servicedesk/.venv/bin/gunicorn -k gthread -w 1 --threads 8 --timeout 120 -b 127.0.0.1:8000 run:app
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```
Применить:
```bash
cp /opt/servicedesk/deploy/servicedesk.service /etc/systemd/system/servicedesk.service
systemctl daemon-reload
systemctl enable --now servicedesk
systemctl status servicedesk         # ждём active (running)
```

> ❗ `-w 1` НЕ увеличивать: чат (Socket.IO) хранит состояние в памяти процесса.
> Несколько воркеров → сообщения «разъезжаются». Для нагрузки увеличивайте
> `--threads`, не воркеры.

---

## 4. Конфиг Apache

Готовый файл — `deploy/apacheservicedesk.conf` (HTTPS + Kerberos + ручной
доменный вход + аварийный локальный вход через `/login`). Кладётся в
`/etc/httpd2/conf/sites-available/servicedesk.conf`.

Включить модули и сайт:
```bash
a2enmod ssl proxy proxy_http headers auth_gssapi
a2ensite servicedesk
a2dissite 000-default          # отключить дефолтный сайт, чтобы он не перехватывал запросы
httpd2 -t                       # проверка синтаксиса конфига (должно быть "Syntax OK")
systemctl restart httpd2
```

В TCP-варианте в конфиге должно быть:
```apache
ProxyPreserveHost On
ProxyPass        / http://127.0.0.1:8000/
ProxyPassReverse / http://127.0.0.1:8000/
```

---

Если возникает ошибка с AuthType, добавляем в конец файла etc/httpd2/httpd2.conf: 
----------------------------------------------------------------
LoadModule authn_core_module modules/mod_authn_core.so
LoadModule authn_file_module modules/mod_authn_file.so
LoadModule authz_core_module modules/mod_authz_core.so
LoadModule authz_user_module modules/mod_authz_user.so
LoadModule auth_basic_module modules/mod_auth_basic.so
# LoadModule auth_digest_module modules/mod_auth_digest.so
----------------------------------------------------------------
## 5. Запуск по слоям + проверка (диагностируем снизу вверх)

Проверяйте по очереди — так сразу видно, на каком слое поломка.

**Слой 1. База:**
```bash
systemctl status postgresql        # active (running)?
```

**Слой 2. Приложение (gunicorn):**
```bash
systemctl status servicedesk
journalctl -u servicedesk -e        # если не запускается — тут будет причина
```

**Слой 3. Приложение отвечает напрямую (минуя Apache):**
```bash
curl -i http://127.0.0.1:8000/login
```
- Пришёл ответ HTTP (200/302/...) → приложение работает, проблема в Apache (слой 4).
- `Connection refused` / нет ответа → приложение НЕ слушает порт: смотрите
  `journalctl -u servicedesk -e` (частые причины — в разделах 7 и 11).

**Слой 4. Apache:**
```bash
httpd2 -t                           # синтаксис
httpd2 -S                           # какие VirtualHost и какой матчится
systemctl status httpd2
tail -n 50 /var/log/httpd2/servicedesk_error.log   # путь из конфига (ErrorLog)
```

**Слой 5. Браузер:** открываем `https://srv01061.polyot.ru`.

---

## 6. Вариант с unix-сокетом (и почему была ошибка прав)

Сокет быстрее TCP, но требует, чтобы пользователь Apache (`apache2`) имел доступ
к файлу-сокету, который создаёт gunicorn (под `servicedesk`). Именно здесь у вас
и возникала ошибка — у `apache2` не было прав на сокет, отсюда **503**.

**Правильная настройка:**

1. В `servicedesk.service` замените строку `ExecStart` и добавьте `RuntimeDirectory`:
   ```ini
   # systemd сам создаст /run/servicedesk (владелец servicedesk) и удалит при остановке
   RuntimeDirectory=servicedesk
   RuntimeDirectoryMode=0750
   ExecStart=/opt/servicedesk/.venv/bin/gunicorn -k gthread -w 1 --threads 8 --timeout 120 --umask 007 -b unix:/run/servicedesk/gunicorn.sock run:app
   ```
   `--umask 007` → сокет создаётся с правами `0770` (доступ владельцу и **группе**).

2. Добавьте пользователя Apache в группу `servicedesk` (чтобы он попадал в группу
   сокета) и перезапустите Apache:
   ```bash
   usermod -aG servicedesk apache2
   systemctl daemon-reload
   systemctl restart servicedesk
   systemctl restart httpd2
   ```

3. В Apache замените проксирование на сокет:
   ```apache
   ProxyPreserveHost On
   ProxyPass        / unix:/run/servicedesk/gunicorn.sock|http://127.0.0.1/
   ProxyPassReverse / unix:/run/servicedesk/gunicorn.sock|http://127.0.0.1/
   ```

**Если сокет всё равно даёт ошибку** (`Permission denied`, `AH02454`, 503):
- проверьте, что `apache2` реально в группе: `id apache2` (должна быть `servicedesk`);
- проверьте сам сокет: `ls -l /run/servicedesk/` (должно быть `srwxrwx--- servicedesk servicedesk`);
- путь к сокету в Apache и в gunicorn совпадает буква-в-букву;
- после `usermod` Apache обязательно **перезапустить** (группа подхватывается только при старте).

> 💡 Если возиться не хочется — вернитесь на TCP (раздел 3). Он работает без
> этих плясок с правами и для внутреннего сервиса быстрее чем достаточно.

---

## 7. Ошибка 503 (Service Unavailable)

503 от Apache = **Apache работает, но не смог достучаться до приложения**.
Проверяйте по порядку:

| Причина | Как проверить / решить |
|---------|------------------------|
| Приложение не запущено | `systemctl status servicedesk`; причина — в `journalctl -u servicedesk -e` |
| Приложение упало при старте | см. раздел 11 (типичные ошибки в логе) |
| `ProxyPass` указывает не туда (порт/сокет) | сверьте порт `8000` / путь сокета в конфиге Apache и в `ExecStart` |
| Нет прав на unix-сокет | раздел 6 (добавить `apache2` в группу `servicedesk`, `--umask 007`) |
| Не включены модули прокси | `a2enmod proxy proxy_http` → `systemctl restart httpd2` |
| Приложение слушает не тот адрес | `ss -ltnp | grep 8000` — должен слушать gunicorn на 127.0.0.1:8000 |

Быстрый тест, чтобы локализовать: `curl -i http://127.0.0.1:8000/login`.
Работает напрямую, но через Apache 503 → проблема в связке Apache↔приложение
(прокси/права/сокет). Не работает напрямую → проблема в самом приложении.

---

## 8. Ошибка 404 (Not Found)

404 обычно значит, что **запрос попал не на наш сайт/не на прокси**, а на
файловую систему Apache (где ничего нет). Причины:

| Причина | Решение |
|---------|---------|
| Сайт не включён / дефолтный перехватывает | `a2ensite servicedesk`, `a2dissite 000-default`, `systemctl restart httpd2` |
| `ServerName`/`ServerAlias` не совпадает с адресом в браузере | впишите реальные имена; проверьте `httpd2 -S` (какой vhost матчится) |
| В нужном VirtualHost нет `ProxyPass` | добавьте `ProxyPass / ...` (раздел 4/6) — иначе Apache ищет файлы на диске |
| Лишний `DocumentRoot` перехватывает | в нашем vhost его быть не должно; всё идёт через `ProxyPass /` |
| 404 отдаёт само приложение | значит до приложения дошли — проверьте URL/маршрут (`curl -i http://127.0.0.1:8000/НУЖНЫЙ_путь`) |

`httpd2 -S` показывает все VirtualHost и какой отвечает на каждое имя/порт —
это главный инструмент при 404.

---

## 9. Kerberos: на что влияет и типичные проблемы

Kerberos живёт в Apache (модуль `auth_gssapi`) и на запуск приложения почти не
влияет, но ломает вход, если что-то не так:

| Симптом | Причина / решение |
|---------|-------------------|
| Apache не стартует, `httpd2 -t` ругается на GSSAPI | не включён модуль (`a2enmod auth_gssapi`) или ошибка в блоке `<Location>` |
| 500 Internal Server Error на входе | Apache не может прочитать keytab → права `root:apache2`, `chmod 640` (раздел 2) |
| Снова и снова просит пароль / не пускает | время рассинхронено (`timedatectl`), DNS не на контроллер домена, в keytab нет нужного `HTTP/<имя>` (`klist -kt /etc/httpd2/servicedesk.keytab`) |
| Вошёл в Apache, но приложение не логинит | не передаётся имя: проверьте `RequestHeader set X-Remote-User "%{REMOTE_USER}s"` и что включён модуль `headers` |
| Нужен вход без домена (домен недоступен) | открыть `https://<сервер>/login` — там вход локальной учёткой (в конфиге `/login` выведен из-под Kerberos) |

> Напоминание: приложение читает имя из заголовка `X-Remote-User` (за прокси
> переменная `REMOTE_USER` до него не доходит). Это уже учтено в коде `auth/routes.py`
> и в конфиге Apache.

---

## 10. Чеклист «чистый запуск с нуля»

```bash
# 1. Права на приложение
chown -R servicedesk:servicedesk /opt/servicedesk
chmod 640 /opt/servicedesk/.env

# 2. Проверить структуру (пакет должен быть в app/)
ls /opt/servicedesk            # ожидаем: run.py config.py app/ .venv/ .env
ls /opt/servicedesk/app        # ожидаем: __init__.py extensions.py blueprints/ ...

# 3. Приложение
cp /opt/servicedesk/deploy/servicedesk.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now servicedesk
curl -i http://127.0.0.1:8000/login        # ответ HTTP = ок

# 4. Сертификаты и keytab (права)
chown root:apache2 /etc/httpd2/servicedesk.keytab && chmod 640 /etc/httpd2/servicedesk.keytab
chmod 600 /etc/ssl/servicedesk/servicedesk.key

# 5. Apache
a2enmod ssl proxy proxy_http headers auth_gssapi
cp /opt/servicedesk/deploy/apacheservicedesk.conf /etc/httpd2/conf/sites-available/servicedesk.conf
# (отредактировать ServerName/пути)
a2ensite servicedesk && a2dissite 000-default
httpd2 -t && systemctl restart httpd2

# 6. Проверка
httpd2 -S                                   # какой vhost отвечает
# открыть https://<сервер> в браузере
```

---

## 11. Частые ошибки в логах `journalctl -u servicedesk -e` и что они значат

| В логе | Что это и что делать |
|--------|----------------------|
| `ModuleNotFoundError: No module named 'app'` | неверная раскладка — пакет должен лежать в `/opt/servicedesk/app/`, а `run.py`/`config.py` — в `/opt/servicedesk/` |
| `ModuleNotFoundError: No module named 'flask'` (или др.) | не установлены зависимости в venv: `.venv/bin/pip install -r requirements.txt gunicorn` |
| `Permission denied: '/opt/servicedesk/...'` | владелец не `servicedesk` → `chown -R servicedesk:servicedesk /opt/servicedesk` |
| `exec: .../gunicorn: Permission denied` | сняли +x с venv (массовый chmod) → `chmod +x /opt/servicedesk/.venv/bin/*` или пересоздать venv |
| `could not connect to server` / `password authentication failed` (PostgreSQL) | неверный `DATABASE_URL` в `.env` или БД не запущена (`systemctl status postgresql`) |
| `Address already in use` (порт 8000) | порт занят другим процессом: `ss -ltnp | grep 8000`, остановите дубликат |
| `SECRET_KEY` / падает на старте сессий | в `.env` не задан `SECRET_KEY`/`SERCET_KEY` |
| Сокет: `Permission denied` при старте Apache | права на unix-сокет — раздел 6 |

> Полезное: `journalctl -u servicedesk -f` — смотреть логи приложения в реальном
> времени; `tail -f /var/log/httpd2/servicedesk_error.log` — логи Apache.
> (Если на ALT логи Apache в другом месте — посмотрите `ErrorLog` в конфиге или
> `ls /var/log/httpd2/`.)
