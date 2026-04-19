import requests
import os
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path

# ------------------ CONFIG ------------------
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TEMPO_TOKEN = os.getenv("TEMPO_TOKEN")

if not TELEGRAM_TOKEN or not TEMPO_TOKEN:
    raise ValueError("Tokens não encontrados no arquivo .env")

BASE_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"


# ------------------ BOT ------------------
class TelegramBot:
    def __init__(self):
        self.last_update_id = None  # ✅ corrigido

    def get_updates(self):
        """Busca novas mensagens usando long polling."""
        try:
            params = {"timeout": 30}

            # ✅ só usa offset se já tiver valor
            if self.last_update_id is not None:
                params["offset"] = self.last_update_id + 1

            response = requests.get(
                f"{BASE_URL}/getUpdates",
                params=params,
                timeout=35
            )
            response.raise_for_status()
            data = response.json()

            return data.get("result", [])

        except requests.exceptions.RequestException as e:
            print("Erro ao buscar atualizações:", e)
            return []

    def send_message(self, chat_id, text):
        """Envia mensagem ao usuário."""
        try:
            requests.post(
                f"{BASE_URL}/sendMessage",
                data={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": "Markdown"
                },
                timeout=5
            )
        except requests.exceptions.RequestException as e:
            print("Erro ao enviar mensagem:", e)

    def get_weather(self, city):
        """Busca clima da cidade."""
        print("🔍 Buscando clima para:", city)  # ✅ debug

        url = "https://api.openweathermap.org/data/2.5/weather"

        try:
            response = requests.get(
                url,
                params={
                    "q": city,
                    "appid": TEMPO_TOKEN,
                    "lang": "pt_br",
                    "units": "metric"
                },
                timeout=5
            )

            print("STATUS:", response.status_code)   # ✅ debug
            print("RESPOSTA:", response.text)        # ✅ debug

            response.raise_for_status()
            r = response.json()

        except requests.exceptions.RequestException as e:
            print("ERRO DETALHADO:", e)
            return "❌ Erro ao conectar com o serviço de clima."

        if r.get("cod") != 200:
            return None

        # Dados
        main = r["main"]
        weather = r["weather"][0]

        temp = main["temp"]
        sens = main["feels_like"]
        hum = main["humidity"]
        desc = weather["description"].capitalize()
        wind_speed = r["wind"]["speed"]
        clouds = r["clouds"]["all"]
        visibility = r.get("visibility", 0) / 1000
        sunrise = datetime.fromtimestamp(r["sys"]["sunrise"]).strftime("%H:%M")
        sunset = datetime.fromtimestamp(r["sys"]["sunset"]).strftime("%H:%M")

        return (
            f"🌤 *Clima em {city.title()}*\n\n"
            f"🌡 Temperatura: {temp}°C\n"
            f"🤔 Sensação térmica: {sens}°C\n"
            f"💧 Umidade: {hum}%\n"
            f"📌 Condição: {desc}\n"
            f"🌬 Vento: {wind_speed} m/s\n"
            f"☁️ Nuvens: {clouds}%\n"
            f"👁 Visibilidade: {visibility:.1f} km\n"
            f"🌅 Nascer do sol: {sunrise}\n"
            f"🌇 Pôr do sol: {sunset}"
        )

    def handle_updates(self, updates):
        """Processa mensagens recebidas."""
        for update in updates:
            self.last_update_id = update["update_id"]

            if "message" not in update:
                continue

            message = update["message"]
            chat_id = message["chat"]["id"]

            if "text" not in message:
                self.send_message(chat_id, "⚠️ Envie apenas texto.")
                continue

            text = message["text"].strip()
            print("📩 Mensagem recebida:", text)  # ✅ debug

            # Comando /start
            if text.lower() == "/start":
                self.send_message(
                    chat_id,
                    "👋 Olá! Envie o nome de uma cidade para ver o clima."
                )
                continue

            clima = self.get_weather(text)

            if clima:
                self.send_message(chat_id, clima)
            else:
                self.send_message(chat_id, "❌ Cidade inválida. Tente novamente.")

    def run(self):
        """Loop principal do bot."""
        print("🤖 Bot rodando...")

        while True:
            updates = self.get_updates()
            if updates:
                self.handle_updates(updates)


# ------------------ EXECUÇÃO ------------------
if __name__ == "__main__":
    print("TELEGRAM_TOKEN:", TELEGRAM_TOKEN)  # ✅ debug
    print("TEMPO_TOKEN:", TEMPO_TOKEN)        # ✅ debug

    bot = TelegramBot()
    bot.run()