# Определение host name компьютера пользователя по его IP (обратный DNS).
#
# Идея: когда человек заходит на сайт, мы знаем его IP. Если у IP есть обратная
# DNS-запись (PTR), по ней можно узнать имя компьютера (host name) и подставить
# его в заявку автоматически.

import socket
from flask import request


def get_client_ip():
    """Реальный IP клиента.

    Сайт работает за Apache (reverse proxy), поэтому request.remote_addr — это
    127.0.0.1. Настоящий адрес клиента Apache (mod_proxy_http) кладёт в заголовок
    X-Forwarded-For (может быть цепочкой "клиент, прокси1, ..." — берём первый).
    """
    forwarded = request.headers.get("X-Forwarded-For", "")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.remote_addr


def resolve_hostname(ip, timeout=0.5):
    """Обратный DNS: по IP возвращает host name компьютера или None.

    timeout ограничивает ожидание ответа DNS, чтобы запрос не «подвисал», если
    обратной записи нет или DNS недоступен. Любая ошибка трактуется как «не
    удалось определить» — это нормально (домашние/внешние адреса без PTR и т. п.).
    """
    if not ip:
        return None

    old_timeout = socket.getdefaulttimeout()
    try:
        socket.setdefaulttimeout(timeout)
        return socket.gethostbyaddr(ip)[0]
    except Exception:
        return None
    finally:
        socket.setdefaulttimeout(old_timeout)
