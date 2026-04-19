# Инструкция по настройке GitHub и CI/CD

## 1. Создай репозиторий на GitHub

1. Зайди на https://github.com/new
2. Название: `TraiderBot`
3. Приватный или публичный — на твой выбор
4. **НЕ** создавай README, .gitignore или лицензию (они уже есть)
5. Нажми "Create repository"

## 2. Подключи локальный репозиторий

```bash
# Замени YOUR_USERNAME на свой GitHub username
git remote add origin https://github.com/YOUR_USERNAME/TraiderBot.git
git branch -M main
git push -u origin main
```

## 3. Настрой GitHub Secrets для автодеплоя

Зайди в Settings → Secrets and variables → Actions → New repository secret

Добавь:
- **DEPLOY_HOST** — IP или домен сервера (например: `123.45.67.89`)
- **DEPLOY_USER** — SSH пользователь (например: `root` или `ubuntu`)
- **DEPLOY_SSH_KEY** — приватный SSH ключ (содержимое файла `~/.ssh/id_rsa`)
- **DEPLOY_URL** — URL для проверки (например: `https://traiderbot.alexbudanov.ru`)

## 4. Подготовь сервер

```bash
# На сервере
sudo apt update && sudo apt install -y docker.io docker-compose git

# Создай директорию
sudo mkdir -p /opt/traiderbot
sudo chown $USER:$USER /opt/traiderbot

# Клонируй репозиторий (после push в GitHub)
cd /opt/traiderbot
git clone https://github.com/YOUR_USERNAME/TraiderBot.git .

# Создай .env
cp .env.example .env
nano .env  # Заполни все переменные

# Первый запуск
docker-compose up -d
```

## 5. Готово! 🎉

Теперь при каждом `git push origin main`:
1. ✅ Запустятся тесты
2. ✅ Соберётся Docker образ
3. ✅ Автоматически задеплоится на сервер
4. ✅ Проверится health check

## Cloudflare Tunnel (для Mini App)

Если нужен постоянный HTTPS URL:

```bash
# На сервере
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o cloudflared
chmod +x cloudflared
sudo mv cloudflared /usr/local/bin/

# Запусти туннель
cloudflared tunnel --url http://localhost:8000
```

Скопируй URL (например `https://xxx.trycloudflare.com`) и добавь в `.env`:
```
TELEGRAM_MINI_APP_URL=https://xxx.trycloudflare.com/api/v1/telegram/miniapp
```

Перезапусти бота:
```bash
docker-compose restart telegram-bot
```
