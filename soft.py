import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import GetContactsRequest
import os
import time


class TurboTelegramSender:
    def __init__(self):
        self.client = None
        self.api_id = 2040
        self.api_hash = "b18441a1ff607e10a989891a5462e627"
        self.apk_path = None

    async def connect_account(self):
        """Улучшенная авторизация с обработкой всех ошибок"""
        print("\n🔐 Подключение к аккаунту...")
        try:
            self.client = TelegramClient('session_name', self.api_id, self.api_hash)
            await self.client.start()

            if not await self.client.is_user_authorized():
                phone = input("Введите номер телефона (+79991234567): ").strip()
                await self.client.send_code_request(phone)
                code = input("Введите код из Telegram: ").strip()

                try:
                    await self.client.sign_in(phone=phone, code=code)
                except errors.SessionPasswordNeededError:
                    password = input("Введите пароль 2FA: ")
                    await self.client.sign_in(password=password)

            me = await self.client.get_me()
            print(f"✅ Успешная авторизация: {me.first_name}")
            return True

        except Exception as e:
            print(f"❌ Ошибка авторизации: {type(e).__name__}: {str(e)}")
            return False

    async def find_apk_file(self):
        """Поиск APK файла с подробной диагностикой"""
        print("\n🔍 Поиск APK файла...")
        apk_name = input("Введите имя APK файла (например: app.apk): ").strip()

        # Проверяем возможные расположения файла
        locations = [
            apk_name,
            os.path.join(os.getcwd(), apk_name),
            os.path.join(os.getcwd(), "apk", apk_name),
            os.path.join(os.path.dirname(__file__), apk_name)
        ]

        for path in locations:
            if os.path.exists(path):
                file_size = os.path.getsize(path) / (1024 * 1024)
                print(f"✅ Найден APK: {path} ({file_size:.2f} MB)")
                self.apk_path = path
                return True

        print("❌ Файл не найден в следующих местах:")
        for loc in locations:
            print(f"- {loc}")
        return False

    async def send_to_recipient(self, recipient, message):
        """Улучшенная отправка с детальным логгированием"""
        try:
            name = getattr(recipient, 'title', getattr(recipient, 'first_name', f"ID:{recipient.id}"))

            if self.apk_path:
                print(f"\n🔄 Отправка APK для {name}...")
                start_time = time.time()

                await self.client.send_file(
                    entity=recipient,
                    file=self.apk_path,
                    caption=message,
                    allow_cache=False,
                    part_size_kb=512,
                    force_document=True
                )

                speed = os.path.getsize(self.apk_path) / (1024 * (time.time() - start_time))
                print(f"📤 Успешно отправлен APK ({speed:.2f} KB/s)")
            else:
                await self.client.send_message(recipient, message)
                print(f"✉️ Отправлено сообщение: {name}")

            return True

        except errors.FloodWaitError as e:
            print(f"⏳ Лимит отправки. Ждем {e.seconds} сек...")
            await asyncio.sleep(e.seconds)
            return await self.send_to_recipient(recipient, message)
        except Exception as e:
            print(f"❌ Ошибка при отправке для {name}: {type(e).__name__}: {str(e)}")
            return False

    async def mass_send(self):
        """Улучшенная массовая рассылка с диагностикой"""
        message = input("\n💬 Введите текст сообщения: ")

        if not await self.find_apk_file():
            confirm = input("Продолжить без APK файла? (y/n): ")
            if confirm.lower() != 'y':
                return

        print("\n📋 Получаем список контактов...")
        try:
            recipients = []

            # Получаем диалоги
            async for dialog in self.client.iter_dialogs(limit=None):
                if dialog.entity:
                    recipients.append(dialog.entity)

            # Получаем контакты
            contacts = await self.client(GetContactsRequest(hash=0))
            if hasattr(contacts, 'users'):
                recipients.extend(contacts.users)

            # Удаляем дубликаты
            unique_recipients = []
            seen_ids = set()
            for r in recipients:
                if hasattr(r, 'id') and r.id not in seen_ids:
                    seen_ids.add(r.id)
                    unique_recipients.append(r)

            print(f"👥 Найдено {len(unique_recipients)} получателей")

            # Подтверждение перед отправкой
            confirm = input(f"Начать рассылку для {len(unique_recipients)} получателей? (y/n): ")
            if confirm.lower() != 'y':
                print("❌ Рассылка отменена")
                return

            # Отправка
            success = 0
            start_time = time.time()

            for i, recipient in enumerate(unique_recipients, 1):
                result = await self.send_to_recipient(recipient, message)
                if result:
                    success += 1

                # Статус каждые 10 отправок
                if i % 10 == 0:
                    print(f"\n📊 Прогресс: {i}/{len(unique_recipients)}")
                    print(f"✅ Успешно: {success}")
                    print(f"⏱ Время: {time.time() - start_time:.2f} сек")

            print("\n🔥 Рассылка завершена!")
            print(f"📈 Результат: {success} успешно | {len(unique_recipients) - success} ошибок")
            print(f"⏱ Общее время: {time.time() - start_time:.2f} сек")

        except Exception as e:
            print(f"‼️ Критическая ошибка: {type(e).__name__}: {str(e)}")


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
        await sender.mass_send()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Программа прервана пользователем")
    finally:
        input("\nНажмите Enter для выхода...")