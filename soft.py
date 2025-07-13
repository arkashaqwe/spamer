import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import GetContactsRequest
from concurrent.futures import ThreadPoolExecutor
import time


class TurboTelegramSender:
    def __init__(self):
        self.client = None
        # Используем официальные API ключи Telegram
        self.api_id = 2040
        self.api_hash = "b18441a1ff607e10a989891a5462e627"
        # Настройка многопоточности (можно регулировать)
        self.threads = 50  # Количество одновременных отправок
        self.executor = ThreadPoolExecutor(max_workers=self.threads)

    async def connect_account(self):
        """Авторизация в аккаунте"""
        print("🟢 Инициализация Turbo рассыльщика...")
        self.client = TelegramClient('turbo_session', self.api_id, self.api_hash)

        try:
            await self.client.connect()

            if not await self.client.is_user_authorized():
                print("\n🔑 Требуется авторизация")
                phone = input("Введите номер телефона (+79991234567): ").strip()

                await self.client.send_code_request(phone)
                code = input("Введите код из Telegram: ").strip()

                try:
                    await self.client.sign_in(phone=phone, code=code)
                except errors.SessionPasswordNeededError:
                    password = input("Введите пароль 2FA: ")
                    await self.client.sign_in(password=password)

            me = await self.client.get_me()
            print(f"\n✅ Авторизованы как: {me.first_name}")
            return True

        except Exception as e:
            print(f"\n❌ Ошибка авторизации: {str(e)}")
            return False

    async def get_all_receivers(self):
        """Получаем всех возможных получателей"""
        print("\n🔍 Сбор получателей...")
        try:
            receivers = []

            # Получаем все диалоги
            dialogs = await self.client.get_dialogs(limit=None)
            receivers.extend(dialog.entity for dialog in dialogs if dialog.entity)

            # Получаем контакты
            contacts = await self.client(GetContactsRequest(hash=0))
            if hasattr(contacts, 'users'):
                receivers.extend(user for user in contacts.users if user not in receivers)

            print(f"👥 Найдено {len(receivers)} получателей")
            return receivers

        except Exception as e:
            print(f"⚠️ Ошибка при сборе получателей: {str(e)}")
            return []

    async def turbo_send(self, receiver, message):
        """Функция отправки сообщения с обработкой ошибок"""
        try:
            await self.client.send_message(receiver, message)
            name = getattr(receiver, 'title', getattr(receiver, 'first_name', f"ID:{receiver.id}"))
            print(f"✉️ Отправлено: {name}")
            return True
        except Exception as e:
            print(f"🚫 Ошибка: {str(e)}")
            return False

    async def mass_turbo_send(self, message):
        """Многопоточная массовая рассылка"""
        receivers = await self.get_all_receivers()
        if not receivers:
            print("❌ Нет получателей для рассылки")
            return

        print(f"\n🚀 Запуск TURBO рассылки на {len(receivers)} получателей...")
        start_time = time.time()

        # Создаем задачи для каждого получателя
        tasks = []
        for receiver in receivers:
            task = asyncio.ensure_future(self.turbo_send(receiver, message))
            tasks.append(task)

        # Запускаем все задачи параллельно
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Статистика
        success = sum(1 for r in results if r is True)
        failed = len(results) - success

        total_time = time.time() - start_time
        speed = len(receivers) / total_time if total_time > 0 else 0

        print(f"\n🔥 Рассылка завершена за {total_time:.2f} сек.")
        print(f"📊 Результат: {success} ✓ | {failed} ✕")
        print(f"⚡ Скорость: {speed:.1f} сообщ./сек.")


async def main():
    print("""
    ██████╗ ██╗   ██╗    █████╗ ██████╗ ██╗  ██╗ █████╗ ███████╗██╗  ██╗ █████╗ 
    ██╔══██╗╚██╗ ██╔╝   ██╔══██╗██╔══██╗██║ ██╔╝██╔══██╗██╔════╝██║  ██║██╔══██╗
    ██████╔╝ ╚████╔╝    ███████║██████╔╝█████╔╝ ███████║███████╗███████║███████║
    ██╔══██╗  ╚██╔╝     ██╔══██║██╔══██╗██╔═██╗ ██╔══██║╚════██║██╔══██║██╔══██║
    ██████╔╝   ██║      ██║  ██║██║  ██║██║  ██╗██║  ██║███████║██║  ██║██║  ██║
    ╚═════╝    ╚═╝      ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
    """)

    sender = TurboTelegramSender()

    if await sender.connect_account():
        message = input("\n💬 Введите сообщение для рассылки: ")
        confirm = input(f"📤 Отправить это сообщение? (y/n): ").lower()

        if confirm == 'y':
            await sender.mass_turbo_send(message)
        else:
            print("❌ Рассылка отменена")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Работа прервана пользователем")
    finally:
        input("\nНажмите Enter для выхода...")