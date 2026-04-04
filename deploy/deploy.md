# Деплой SKLAD на сервер (Ubuntu)

## 1. Установка пакетов

```bash
sudo apt update && sudo apt install -y python3-pip python3-venv nginx supervisor postgresql postgresql-contrib
```

---

## 2. PostgreSQL — создать БД и пользователя

```bash
sudo -u postgres psql
```

Внутри psql:
```sql
CREATE DATABASE sklad_db;
CREATE USER postgres WITH PASSWORD '8743';
GRANT ALL PRIVILEGES ON DATABASE sklad_db TO postgres;
\q
```

---

## 3. Создать пользователя и загрузить проект

```bash
sudo useradd -m -s /bin/bash sklad
sudo su - sklad

# Загрузить проект (через git или scp)
git clone <твой_репозиторий> sklad
# или скопировать папку вручную через scp/FileZilla
```

---

## 4. Виртуальное окружение и зависимости

```bash
cd /home/sklad/sklad
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

---

## 5. settings.py — изменить для продакшна

Открыть `config/settings.py` и изменить:

```python
DEBUG = False
ALLOWED_HOSTS = ['твой_IP_или_домен']
SECRET_KEY = 'сгенерируй_новый_ключ'  # python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 6. Собрать статику и мигрировать

```bash
source venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
```

---

## 7. Nginx

```bash
sudo cp /home/sklad/sklad/deploy/nginx.conf /etc/nginx/sites-available/sklad
sudo ln -s /etc/nginx/sites-available/sklad /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

---

## 8. Supervisor

```bash
sudo cp /home/sklad/sklad/deploy/supervisor.conf /etc/supervisor/conf.d/sklad.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start sklad
```

---

## 9. Проверить статус

```bash
sudo supervisorctl status sklad
sudo systemctl status nginx
```

---

## Полезные команды

```bash
# Перезапустить приложение после изменений
sudo supervisorctl restart sklad

# Логи приложения
sudo tail -f /var/log/supervisor/sklad_error.log

# Логи nginx
sudo tail -f /var/log/nginx/error.log
```
