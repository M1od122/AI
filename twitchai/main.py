import asyncio
import sys
import yaml
from datetime import datetime, timedelta
from twitch_reader import TwitchChatReader
from ai_engine import generate_ai_reply
from mystrm import send_message_via_mystrm

# Загрузка конфигурации
with open("config.yaml", "r", encoding="utf-8") as f:
    CONFIG = yaml.safe_load(f)

CHANNEL_STATE = {
    name: {"chat_history": [], "last_msg_time": datetime.now(), "mood": "neutral"}
    for name in CONFIG["channels"]
}

# Глобальные переменные для управления
readers = []
running = True

async def handle_incoming_message(channel: str, username: str, message: str, timestamp: datetime):
    print(f"📨 Получено: [{channel}] {username}: {message}")
    if not running:
        return
    state = CHANNEL_STATE[channel]
    state["chat_history"].append((username, message, timestamp))
    state["last_msg_time"] = timestamp
    if len(state["chat_history"]) > CONFIG["memory"]["history_length"]:
        state["chat_history"].pop(0)

    active = sum(1 for _, _, t in state["chat_history"] if (datetime.now() - t).seconds < 60)
    state["mood"] = "energetic" if active > 5 else "bored" if (datetime.now() - state["last_msg_time"]).seconds > 45 else "friendly"

    should_respond = "бот" in message.lower() or hash(message) % 100 < 15
    if should_respond:
        cfg = CONFIG["channels"][channel]
        reply = generate_ai_reply(
            username, message, state["chat_history"],
            state["mood"], cfg["personality"], cfg["llm_model"],
            CONFIG["llm"]["endpoint"]
        )
        if reply:
            send_message_via_mystrm(cfg["mystrm_token"], reply, CONFIG["mystrm"]["api_url"])

async def silence_watcher():
    while running:
        await asyncio.sleep(CONFIG["memory"]["timeout_for_silence_sec"])
        if not running:
            break
        for ch, state in CHANNEL_STATE.items():
            if (datetime.now() - state["last_msg_time"]).seconds > CONFIG["memory"]["timeout_for_silence_sec"]:
                cfg = CONFIG["channels"][ch]
                reply = generate_ai_reply(
                    None, None, state["chat_history"],
                    state["mood"], cfg["personality"], cfg["llm_model"],
                    CONFIG["llm"]["endpoint"]
                )
                if reply:
                    send_message_via_mystrm(cfg["mystrm_token"], reply, CONFIG["mystrm"]["api_url"])

async def shutdown():
    global running
    if not running:
        return
    print("\n🔄 Завершаем работу бота...")
    running = False

    # Останавливаем всех ботов
    for reader in readers:
        try:
            await reader.bot.close()
        except Exception as e:
            pass  # Игнорируем ошибки при закрытии

    # Даем время на корректное завершение
    await asyncio.sleep(0.5)
    print("✅ Работа завершена.")

async def main():
    global readers
    # Запуск читателей
    for cfg in CONFIG["channels"].values():
        reader = TwitchChatReader(cfg["twitch_name"], handle_incoming_message)
        readers.append(reader)
        asyncio.create_task(reader.start())

    # Запуск наблюдателя за тишиной
    sw_task = asyncio.create_task(silence_watcher())

    print("🤖 Бот запущен. Нажмите Ctrl+C для остановки.")
    try:
        # Блокируем main, пока не будет исключения
        await asyncio.Future()  # бесконечное ожидание
    except asyncio.CancelledError:
        pass
    finally:
        await shutdown()
        sw_task.cancel()
        try:
            await sw_task
        except asyncio.CancelledError:
            pass

# Точка входа
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Получен сигнал прерывания (Ctrl+C).")
        # asyncio.run уже завершится, shutdown вызовется внутри
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {e}")
        sys.exit(1)

