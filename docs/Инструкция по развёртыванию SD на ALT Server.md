# Развёртывание ServiceDesk на выделенном сервере ALT Linux

Инструкция для начинающего пользователя Linux: каждая команда снабжена
пояснением «что она делает». Рассчитана на **отдельный (выделенный) сервер**
ALT Linux в рабочей сети с доменом Active Directory.

Что в итоге получится:
```
Браузер пользователя
      │  https (порт 443) / http (порт 80)
      ▼
Apache (служба httpd2)  ←─ здесь проверка Kerberos и TLS-сертификаты
      │  обратный прокси на 127.0.0.1:8000
      ▼
gunicorn (служба servicedesk)  ──►  Flask-приложение (наш код)
      │
      ├── PostgreSQL (база заявок)
      ├── Active Directory по LDAP (выгрузка пользователей) — sync_ad_users.py
      └── Kerberos (билет от браузера → имя пользователя, вход без пароля)
```

> ⚠️ Заглушки, которые надо заменить: `polyot.ru`, `POLYOT`, `srv01061.polyot.ru`,
> `MyPass123`, адреса контроллеров домена. Доменные значения — у сисадмина.

> 💡 Имена пакетов в ALT могут отличаться по версии. Если `apt-get` пишет
> «Невозможно найти пакет» — найдите точное имя: `apt-cache search <слово>`.

---

## 0. Где лежат файлы и как они должны быть разложены

В этой инструкции:
- **`/home/user/servicedesk_usr`** — папка, куда **загружены исходники** проекта
  (то, что прислали/скопировали). Это «склад», из него мы раскладываем код.
- **`/opt/servicedesk`** — **рабочая папка**, из которой приложение запускается.

> Если у вас две папки используются наоборот — просто поменяйте пути местами по
> тексту. Главное — соблюсти структуру ниже.

**Важно про структуру.** Код использует импорты вида `from app.extensions import ...`,
поэтому сам пакет приложения должен лежать в папке с именем **`app`**, а
запускающие скрипты (`run.py`, `config.py`) — на уровень выше:
```
/opt/servicedesk/
├── run.py              ← точка входа (gunicorn берёт отсюда объект app)
├── config.py           ← настройки (читает .env)
├── init_db.py          ← создание таблиц
├── sync_ad_users.py    ← выгрузка пользователей из AD
├── requirements.txt
├── .env                ← реальные значения/пароли (создаём вручную)
├── .venv/              ← изолированные Python-библиотеки
└── app/                ← САМ ПАКЕТ приложения
    ├── __init__.py
    ├── extensions.py
    ├── blueprints/ models/ services/ utils/ forms/
    ├── static/
    └── templates/
```

> ❗ Если свалить все файлы «в кучу» в `/opt/servicedesk`, приложение НЕ запустится
> с ошибкой `No module named 'app'`. Пакет обязан лежать в подпапке `app/`.

---

## 1. Подготовка сервера

Войдите под root (или станьте им):
```bash
su -
```
- `su -` — стать администратором root (выйти обратно — `exit`).

Проверьте время и DNS (критично для домена и Kerberos):
```bash
apt-get update
apt-get install -y chrony
systemctl enable --now chronyd
timedatectl
```
- `apt-get update` — обновить список пакетов из репозитория;
- `chrony` — синхронизация времени (Kerberos не работает при расхождении времени);
- `timedatectl` — показать текущее время/часовой пояс.

> DNS сервера должен указывать на **контроллер домена** (иначе домен/Kerberos не
> заработают). Это настраивает сисадмин в сетевых параметрах сервера.

Создайте служебного пользователя, под которым будет работать приложение:
```bash
useradd --system --shell /sbin/nologin servicedesk
```
- `--system` — системная учётка (без личной папки и входа);
- `--shell /sbin/nologin` — под ней нельзя залогиниться (только запуск службы).

> Если пользователь уже есть — команда сообщит об этом, ничего страшного.

---

## 2. Системные пакеты (из локального репозитория repo.polyot.ru)

```bash
apt-get install -y apache2 apache2-mod_ssl apache2-mod_auth_gssapi \
  postgresql18-server postgresql18 \
  python3 python3-module-pip python3-module-system-seed-wheels \
  krb5-kinit libkrb5
```
Что это:
- `apache2` — веб-сервер (служба называется **`httpd2`**). Модуль обратного прокси
  (`mod_proxy`) уже входит в `apache2` — отдельно ставить не нужно;
- `apache2-mod_ssl` — поддержка HTTPS;
- `apache2-mod_auth_gssapi` — модуль проверки Kerberos-билетов (вход по домену);
- `postgresql16-server`, `postgresql16` — сервер и клиент базы (нет такой версии —
  посмотрите доступную: `apt-cache search '^postgresql1[0-9]-server'`);
- `python3`, `python3-module-pip` — Python и установщик библиотек;
- `python3-module-system-seed-wheels` — нужен, чтобы заработала команда создания
  виртуального окружения `python3 -m venv` (отдельного пакета `python3-venv` в ALT нет);
- `krb5-kinit`, `libkrb5` — клиент и библиотеки Kerberos. Заодно дают утилиты
  `klist` и `ktutil` (понадобятся для keytab, раздел 10).

---

## 3. PostgreSQL — создать базу

Сначала **инициализируем кластер** (создаёт служебные файлы базы). Вы уже root,
`sudo` не нужен:
```bash
# 1) узнать путь к initdb и куда служба кладёт данные
find / -name initdb -type f 2>/dev/null                 # обычно /usr/bin/initdb
systemctl cat postgresql.service | grep -iE 'PGDATA|ExecStart'   # ищем "-D /путь"

# 2) инициализировать кластер от пользователя postgres (с русскими буквами).
#    runuser работает, даже если у postgres «запрещённая» оболочка (nologin).
runuser -u postgres -- /usr/bin/initdb -D /var/lib/pgsql/data --encoding=UTF8 --locale=C.UTF-8

# 3) включить автозапуск, запустить, проверить
systemctl enable --now postgresql
systemctl status postgresql
```
> ❗ На ALT `service postgresql initdb` НЕ работает (ответит `Unknown command verb`).
> Если `su -l postgres` пишет `su: exec failed` — это нормально (у postgres
> оболочка nologin), поэтому и используем `runuser`. Если служба не стартует
> (`control process exited`) — кластер не инициализирован; смотрите
> `journalctl -xeu postgresql.service | tail -n 30`.

Создаём пользователя БД и саму базу:
```bash
runuser -u postgres -- psql
```
В консоли (`postgres=#`) введите построчно (пароль — латиница и цифры, без `@ : /`):
```sql
CREATE USER servicedesk WITH PASSWORD 'MyPass123';
CREATE DATABASE servicedesk OWNER servicedesk;
GRANT ALL PRIVILEGES ON DATABASE servicedesk TO servicedesk;
\q
```
Строка подключения для `.env` будет такой:
```
postgresql+psycopg2://servicedesk:MyPass123@localhost:5432/servicedesk
```

---

## 4. Разложить код в /opt/servicedesk

Раскладываем файлы из «склада» (`/home/user/servicedesk_usr`) в рабочую папку,
соблюдая структуру из раздела 0:
```bash
mkdir -p /opt/servicedesk/app
cd /home/user/servicedesk_usr

# 1) сам пакет приложения — в подпапку app/ 
cp -r __init__.py extensions.py blueprints models services utils forms static templates \
      /opt/servicedesk/app/

# 2) запускающие скрипты и настройки — на уровень выше
cp run.py config.py init_db.py seed_data.py sync_ad_users.py requirements.txt \
      /opt/servicedesk/

# 3) шаблон настроек (если есть) — тоже наверх
cp .env.example /opt/servicedesk/ 2>/dev/null || true

# 4) отдать всю папку служебному пользователю
chown -R servicedesk:servicedesk /opt/servicedesk
```
- `cp -r ОТКУДА КУДА` — копировать (`-r` — вместе с вложенными папками);
- `chown -R владелец:группа путь` — назначить владельца рекурсивно.

> Если в `/opt/servicedesk` уже что-то лежит — убедитесь, что структура совпадает
> с разделом 0 (пакет в `app/`, скрипты наверху), иначе будет `No module named 'app'`.

---

## 5. Виртуальное окружение и библиотеки

```bash
cd /opt/servicedesk
sudo -u servicedesk python3 -m venv .venv
sudo -u servicedesk .venv/bin/pip install --upgrade pip
```
- `python3 -m venv .venv` — создать «изолированный ящик» для библиотек проекта;
- `sudo -u servicedesk` — выполнять от имени служебного пользователя, чтобы файлы
  принадлежали ему.

Дальше — **установка зависимостей**. Два варианта:

**A. Если у сервера есть доступ к зеркалу пакетов Python (интернет/прокси):**
```bash
sudo -u servicedesk .venv/bin/pip install -r requirements.txt gunicorn
```

**B. Если интернета нет — из заранее подготовленной папки `wheels`** (её собирают
там, где интернет есть, командой `pip download -r requirements.txt gunicorn -d wheels`
на такой же версии ALT/Python):
```bash
sudo -u servicedesk .venv/bin/pip install --no-index --find-links=/home/user/servicedesk_usr/wheels -r requirements.txt gunicorn
```
- `--no-index` — не выходить в интернет; `--find-links=...` — брать из папки `wheels`.

> `gunicorn` ставим отдельно — его нет в `requirements.txt`, но именно он запускает
> приложение на боевом сервере.

---

## 6. Файл настроек `.env`

```bash
nano /opt/servicedesk/.env
```
(`nano` — редактор: сохранить `Ctrl+O`, `Enter`; выйти `Ctrl+X`.) Заполните:
```ini
# Длинная случайная строка (подпись сессий/CSRF). Поддерживаются оба имени —
# SECRET_KEY (правильное) и SERCET_KEY (старое).
SECRET_KEY=ЗАМЕНИТЕ_НА_ДЛИННУЮ_СЛУЧАЙНУЮ_СТРОКУ

DATABASE_URL=postgresql+psycopg2://servicedesk:MyPass123@localhost:5432/servicedesk

# Вход по Kerberos (на сервере в домене — true):
KERBEROS_SSO_ENABLED=true

# Запасной локальный администратор (вход до настройки домена):
BOOTSTRAP_ADMIN_EMAIL=admin@local
BOOTSTRAP_ADMIN_PASSWORD=ЗАМЕНИТЕ_ПАРОЛЬ

# --- Active Directory (выгрузка пользователей по LDAP) ---
# МОЖНО указать НЕСКОЛЬКО контроллеров через запятую (отказоустойчивый пул).
# Работает только с обновлённым services/ad_service.py (с поддержкой пула)!
AD_LDAP_SERVER=ldaps://dc01.polyot.ru,ldaps://dc02.polyot.ru   # <<< УЗНАТЬ
AD_USE_SSL=true                             # true = LDAPS, порт 636 (рекомендуется)
AD_DOMAIN=POLYOT                            # короткое (NetBIOS) имя домена
AD_DOMAIN_FQDN=polyot.ru                    # полное имя домена
AD_BASE_DN=DC=polyot,DC=ru                  # ветка поиска пользователей  <<< УЗНАТЬ
AD_BIND_USER=POLYOT\svc-servicedesk         # сервисная учётка (только чтение)  <<< УЗНАТЬ
AD_BIND_PASSWORD=пароль_сервисной_учётки    # <<< УЗНАТЬ
AD_AUTH_METHOD=NTLM
AD_DEFAULT_ROLE=user
# AD_GROUP_ROLE_MAP=ServiceDesk-Classifiers=classifier;ServiceDesk-Executors=executor
```
Сгенерировать случайный ключ: `.venv/bin/python -c "import secrets; print(secrets.token_hex(32))"`.
После сохранения верните владельца: `chown servicedesk:servicedesk /opt/servicedesk/.env`.

> 💡 Готовый шаблон со всеми пояснениями — файл `.env.example` (скопировали в п.4).
> Можно: `cp .env.example .env` и отредактировать.

> ⚠️ Несколько адресов в `AD_LDAP_SERVER` (через запятую) работают ТОЛЬКО с
> обновлённым `services/ad_service.py`. Со старым — оставьте один адрес, иначе
> будет ошибка «invalid server address».

---

## 7. LDAPS: доверие сертификату домена (при AD_USE_SSL=true)

При защищённом LDAPS контроллер домена предъявляет сертификат, выданный
**корневым удостоверяющим центром (ЦС) домена**. Чтобы приложение ему доверяло,
этот корневой сертификат нужно добавить в доверенные:
```bash
cp polyot-root-ca.crt /etc/pki/ca-trust/source/anchors/
update-ca-trust
```
Проверить, что соединение по LDAPS вообще устанавливается:
```bash
openssl s_client -connect srv01002.polyot.ru:636
```
Должна показаться цепочка сертификатов (а не ошибка). Если ошибка доверия —
значит корневой ЦС ещё не добавлен; если соединение не открывается — закрыт порт
636 или LDAPS не включён на контроллере (уточните у сисадмина).

> Понять, какой из выданных файлов — корневой ЦС: `openssl x509 -in файл -noout -subject -issuer`.
> У корневого `subject` и `issuer` совпадают.

---

## 8. Создать таблицы и выгрузить пользователей из AD

```bash
cd /opt/servicedesk
sudo -u servicedesk .venv/bin/python init_db.py
sudo -u servicedesk .venv/bin/python sync_ad_users.py
```
- `init_db.py` — создаёт таблицы (и запасного админа из `BOOTSTRAP_ADMIN_*`);
- `sync_ad_users.py` — первичная выгрузка пользователей из AD по LDAP. Отключённые
  в AD учётки помечаются неактивными, но не удаляются.

> Если `sync_ad_users.py` пишет про «неправильный/invalid LDAP-сервер»: чаще всего
> (1) несколько адресов через запятую при СТАРОМ `ad_service.py` — поставьте новый
> или оставьте один адрес; (2) не добавлен корневой ЦС для LDAPS (раздел 7);
> (3) рассогласование `ldaps://` и `AD_USE_SSL`; (4) DNS/порт 636. Точную причину
> подскажет текст ошибки.

---

## 9. Автозапуск приложения (служба systemd)

```bash
cp /opt/servicedesk/deploy/servicedesk.service /etc/systemd/system/servicedesk.service
systemctl daemon-reload
systemctl enable --now servicedesk
systemctl status servicedesk
```
- кладём описание службы, перечитываем, включаем автозапуск и проверяем
  (`active (running)`; выход — `q`).

> В файле службы прописано `WorkingDirectory=/opt/servicedesk` и
> `gunicorn ... run:app` — совпадает с нашей раскладкой. Логи приложения:
> `journalctl -u servicedesk -e`.

Быстрая проверка локально (приложение слушает 127.0.0.1:8000):
```bash
curl -I http://127.0.0.1:8000/login
```
Должен прийти ответ HTTP (например `302` или `200`).

---

## 10. Kerberos для входа по домену (SSO)

**Keytab** — файл с секретным ключом «служебной учётки» веб-сервера в Kerberos
(принципал `HTTP/srv01061.polyot.ru@POLYOT.RU`). Он позволяет Apache проверять
доменные билеты пользователей без пароля. Сам keytab читает только Apache.

1. **Файлы keytab выдаёт сисадмин** (создаёт на контроллере домена). Посмотреть,
   что внутри:
   ```bash
   klist -kt /путь/к/файлу.keytab
   ```
   В колонке Principal должно быть `HTTP/srv01061.polyot.ru@POLYOT.RU`.

   **Если выдали несколько файлов keytab** (например, по одному на каждый FQDN) —
   объедините в один:
   ```bash
   ktutil
     rkt /путь/keytab1
     rkt /путь/keytab2
     wkt /etc/httpd2/servicedesk.keytab
     quit
   ```
   - `rkt` — прочитать очередной keytab; `wkt` — записать объединённый.
   > Если сайт открывают по нескольким именам (FQDN) — в итоговом keytab должны
   > быть принципалы `HTTP/<имя>` для КАЖДОГО имени, иначе на «непокрытом» имени
   > автоматический вход не сработает.

2. Настройте `/etc/krb5.conf`:
   ```ini
   [libdefaults]
       default_realm = POLYOT.RU
       dns_lookup_realm = false
       dns_lookup_kdc = true

   [realms]
       POLYOT.RU = {
           kdc = dc01.polyot.ru
           admin_server = dc01.polyot.ru
       }

   [domain_realm]
       .polyot.ru = POLYOT.RU
       polyot.ru = POLYOT.RU
   ```

3. Права на keytab (читает веб-сервер):
   ```bash
   chown root:apache2 /etc/httpd2/servicedesk.keytab
   chmod 640 /etc/httpd2/servicedesk.keytab
   ```
   (группа веб-сервера в ALT обычно `apache2` — проверьте `id apache2`.)

---

## 11. Apache (httpd2): HTTPS, несколько FQDN и Kerberos

Получаете от сисадмина набор TLS-сертификатов (обычно 2–3 файла):

| Файл (примерно) | Что это | Куда в Apache |
|---|---|---|
| `servicedesk.crt` | сертификат сервера | `SSLCertificateFile` |
| `servicedesk.key` | закрытый ключ (СЕКРЕТНЫЙ!) | `SSLCertificateKeyFile` |
| `chain.crt` | цепочка ЦС (промежуточный+корневой) | `SSLCertificateChainFile` |

Определить назначение файла: `openssl x509 -in файл -noout -subject -issuer`
(`subject`=имя сервера → сертификат сервера; `subject`=`issuer` → корневой ЦС).

Разложите и закройте ключ:
```bash
mkdir -p /etc/ssl/servicedesk
cp servicedesk.crt chain.crt servicedesk.key /etc/ssl/servicedesk/
chmod 600 /etc/ssl/servicedesk/servicedesk.key
chown -R root:root /etc/ssl/servicedesk
```

Конфиг сайта `/etc/httpd2/conf/sites-available/servicedesk.conf`:
```apache
# HTTPS (порт 443)
<VirtualHost *:443>
    ServerName  srv01061.polyot.ru
    ServerAlias servicedesk.polyot.ru sd.polyot.ru     # все остальные FQDN через пробел

    SSLEngine on
    SSLCertificateFile      /etc/ssl/servicedesk/servicedesk.crt
    SSLCertificateKeyFile   /etc/ssl/servicedesk/servicedesk.key
    SSLCertificateChainFile /etc/ssl/servicedesk/chain.crt

    ProxyPreserveHost On
    ProxyPass        / http://127.0.0.1:8000/
    ProxyPassReverse / http://127.0.0.1:8000/

    # Kerberos-вход (на HTTPS):
    <Location />
        AuthType GSSAPI
        AuthName "Domain Login"
        GssapiCredStore keytab:/etc/httpd2/servicedesk.keytab
        Require valid-user
    </Location>

    ErrorLog  ${APACHE_LOG_DIR}/servicedesk_error.log
    CustomLog ${APACHE_LOG_DIR}/servicedesk_access.log combined
</VirtualHost>

# HTTP (порт 80) — перенаправление на HTTPS
<VirtualHost *:80>
    ServerName  srv01061.polyot.ru
    ServerAlias servicedesk.polyot.ru sd.polyot.ru
    Redirect permanent / https://srv01061.polyot.ru/
</VirtualHost>
```
Включаем модули и сайт:
```bash
a2enmod ssl proxy proxy_http headers auth_gssapi
a2ensite servicedesk
a2dissite 000-default        # отключить стартовую страницу Apache, если включена
systemctl restart httpd2
```
- служба Apache в ALT — **`httpd2`**;
- если папок `sites-available/` нет — посмотрите `ls /etc/httpd2/conf/`.

**Несколько FQDN:** приложению ничего настраивать не нужно (оно отвечает на любое
имя). Имена перечисляются в `ServerAlias` (выше), и они же должны быть:
- в **keytab** (раздел 10) — принципал `HTTP/<имя>` на каждое имя;
- в **сертификате** — все имена в SAN. Проверить:
  `openssl x509 -in /etc/ssl/servicedesk/servicedesk.crt -noout -text | grep -A1 "Subject Alternative Name"`.

> Если HTTPS пока не настраиваете — можно временно оставить только блок на порту 80
> с `ProxyPass` и `<Location>`-блоком Kerberos (вход будет работать по HTTP в сети).

---

## 12. Проверка

1. Приложение: `systemctl status servicedesk` → `active (running)`.
2. Apache: `systemctl status httpd2` → `active (running)`.
3. С **доменного** ПК откройте `https://srv01061.polyot.ru` — должен произойти
   автоматический вход под доменной учёткой (если сайт в зоне «Местная интрасеть»).
4. Если просит логин/пароль — проверьте: время (`timedatectl`), DNS на контроллер,
   keytab (`klist -kt`), и что имя из адреса есть в keytab и в `ServerAlias`.

---

## 13. Ночная синхронизация пользователей (cron)

Чтобы новые/уволенные сотрудники подтягивались автоматически:
```bash
crontab -u servicedesk -e
```
Строка (каждую ночь в 03:00):
```
0 3 * * * cd /opt/servicedesk && /opt/servicedesk/.venv/bin/python sync_ad_users.py >> /opt/servicedesk/sync.log 2>&1
```

---

## 14. Как обновлять приложение

**Помните про раскладку:** «движок» кладётся в `app/…`, скрипты — в корень.

| Что изменилось | Куда на сервере |
|----------------|-----------------|
| `services/…`, `models/…`, `blueprints/…`, `extensions.py`, `static/…`, `templates/…` | `/opt/servicedesk/app/…` |
| `run.py`, `config.py`, `init_db.py`, `sync_ad_users.py`, `requirements.txt` | `/opt/servicedesk/` |

**Обычное обновление кода:**
```bash
# 1) резервная копия (на случай отката)
cp -r /opt/servicedesk /opt/servicedesk_backup_$(date +%F)

# 2) положить новые файлы из /home/user/servicedesk_usr на их места (пример)
cp /home/user/servicedesk_usr/services/ticket_service.py /opt/servicedesk/app/services/ticket_service.py
cp /home/user/servicedesk_usr/config.py                  /opt/servicedesk/config.py

# 3) вернуть владельца и перезапустить
chown -R servicedesk:servicedesk /opt/servicedesk
systemctl restart servicedesk
```
Apache (httpd2) перезапускать не нужно.

**Если добавились библиотеки:** обновите `requirements.txt`, затем
`pip install` (вариант A или B из раздела 5) и `systemctl restart servicedesk`.

**Если изменилась МОДЕЛЬ (структура таблиц):** в проекте есть Flask-Migrate.
Сначала резервная копия базы:
```bash
runuser -u postgres -- pg_dump servicedesk > /root/servicedesk_$(date +%F).sql
```
Затем:
```bash
cd /opt/servicedesk
sudo -u servicedesk FLASK_APP=run.py .venv/bin/flask db init     # один раз, если папки migrations нет
sudo -u servicedesk FLASK_APP=run.py .venv/bin/flask db migrate -m "что изменили"
sudo -u servicedesk FLASK_APP=run.py .venv/bin/flask db upgrade
systemctl restart servicedesk
```

---

## 15. Шпаргалка по Linux (ALT)

### Просмотр и перемещение (безопасно)
| Команда | Что делает |
|--------|------------|
| `pwd` | где я сейчас |
| `ls` / `ls -la` | список файлов / подробно со скрытыми |
| `cd папка` / `cd ..` / `cd ~` | зайти / вверх / домой |
| `cat файл` / `less файл` | показать файл (в `less` выход — `q`) |
| `tail -f файл` | смотреть файл «вживую» (выход — `Ctrl+C`) |

### Файлы и права
| Команда | Что делает |
|--------|------------|
| `cp откуда куда` (`-r` — папку) | копировать |
| `mv откуда куда` | переместить/переименовать |
| `rm файл` / `rm -r папка` | удалить (БЕЗ корзины!) |
| `chown -R польз:группа путь` | назначить владельца |
| `chmod 640 файл` | права доступа |

### Пакеты (ALT — apt-get поверх RPM)
| Команда | Что делает |
|--------|------------|
| `apt-get update` | обновить список пакетов |
| `apt-get install -y имя` | установить пакет |
| `apt-cache search слово` | найти пакет по слову |

### Службы
| Команда | Что делает |
|--------|------------|
| `systemctl start/stop/restart имя` | запустить/остановить/перезапустить |
| `systemctl enable --now имя` | автозапуск + запуск |
| `systemctl status имя` | работает ли (выход — `q`) |
| `journalctl -u имя -e` | последние логи службы |

Наши службы: **`servicedesk`** (приложение), **`httpd2`** (Apache), **`postgresql`** (база).

### Если что-то пошло не так
| Проблема | Что проверить |
|----------|---------------|
| `No module named 'app'` | пакет должен лежать в `/opt/servicedesk/app/`, скрипты — в `/opt/servicedesk/` (раздел 0) |
| Сайт не открывается | `systemctl status servicedesk`; логи `journalctl -u servicedesk -e` |
| `502 Bad Gateway` | приложение не запущено — почините службу `servicedesk` |
| Не подключается к базе | `DATABASE_URL` в `.env` и `systemctl status postgresql` |
| `postgresql.service failed` | кластер не инициализирован — `initdb` через `runuser` (раздел 3) |
| `su: exec failed` / `root отсутствует в sudoers` | используйте `runuser -u postgres -- …`; вы и так root — уберите `sudo` |
| sync_ad: `invalid server address` | несколько адресов при старом `ad_service.py` — поставьте новый или оставьте один (раздел 6) |
| sync_ad: ошибка LDAPS/сертификата | добавьте корневой ЦС домена (раздел 7) или временно `AD_USE_SSL=false` |
| Kerberos не пускает | время, DNS на контроллер, keytab (`klist -kt`), имя в `ServerAlias` |
| Kerberos на одном FQDN работает, на другом нет | в keytab нет `HTTP/<это-имя>` (раздел 10) |
| HTTPS не открывается | включён ли `a2enmod ssl`, пути к `.crt/.key/chain`, права на ключ (раздел 11) |
| `Невозможно найти пакет` | уточните имя: `apt-cache search слово` |
| Нет пакета `apache2-mod_proxy` | так и должно быть — `mod_proxy` встроен в `apache2` |
