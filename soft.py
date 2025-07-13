# main.py
import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import GetContactsRequest
import os
import socks
from config import PROXY, MESSAGE, TELEGRAM


class TurboSender:
    def __init__(self):
        self.client = None
        self.saved_message = None

    async def create_client(self):
        """Создаем клиент с учетом прокси"""
        proxy = None

        if PROXY['enable']:
            if PROXY['type'] == 'socks5':
                proxy = (socks.SOCKS5, PROXY['host'], PROXY['port'],
                         True, PROXY['username'], PROXY['password'])
            elif PROXY['type'] == 'http':
                proxy = (socks.HTTP, PROXY['host'], PROXY['port'],
                         True, PROXY['username'], PROXY['password'])
            elif PROXY['type'] == 'mtproto':
                proxy = (PROXY['host'], PROXY['port'], PROXY['password'])

        self.client = TelegramClient(
            TELEGRAM['session_name'],
            TELEGRAM['api_id'],
            TELEGRAM['api_hash'],
            proxy=proxy
        )

    async def connect_account(self):
        """Подключение к аккаунту"""
        await self.create_client()

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
            print(f"\n✅ Авторизован как: {me.first_name}")
            return True

        except Exception as e:
            print(f"\n❌ Ошибка подключения: {type(e).__name__}: {str(e)}")
            return False

    async def create_template(self):
        """Создание шаблона сообщения"""
        print("\n📝 Создание шаблона...")
        try:
            if MESSAGE['apk_path'] and os.path.exists(MESSAGE['apk_path']):
                msg = await self.client.send_file(
                    'me',
                    MESSAGE['apk_path'],
                    caption=MESSAGE['text'],
                    force_document=True
                )
                self.saved_message = msg
                print(f"✅ Сообщение+APK сохранено (ID: {msg.id})")
            else:
                msg = await self.client.send_message('me', MESSAGE['text'])
                self.saved_message = msg
                print("✅ Текст сохранен")
        except Exception as e:
            print(f"❌ Ошибка создания шаблона: {str(e)}")
            return False
        return True

    async def get_recipients(self):
        """Получение списка получателей"""
        print("\n👥 Получаем контакты...")
        recipients = []

        # Получаем диалоги
        async for dialog in self.client.iter_dialogs():
            if dialog.is_user and not dialog.entity.bot:
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

        print(f"Найдено {len(unique_recipients)} получателей")
        return unique_recipients

    async def start_mailing(self):
        """Запуск рассылки"""
        if not await self.create_template():
            return

        recipients = await self.get_recipients()
        if not recipients:
            print("❌ Нет получателей")
            return

        confirm = input(f"Начать рассылку для {len(recipients)} получателей? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Отменено")
            return

        print("\n🚀 Начинаем рассылку...")
        success = 0

        for recipient in recipients:
            try:
                await self.client.forward_messages(recipient, self.saved_message)
                name = getattr(recipient, 'first_name', 'Unknown')
                print(f"✓ Отправлено: {name}")
                success += 1
            except Exception as e:
                print(f"✕ Ошибка: {type(e).__name__}")

        print(f"\n🔥 Готово! Успешно: {success}/{len(recipients)}")


async def main():
    sender = TurboSender()
    if await sender.connect_account():
        await sender.start_mailing()


if __name__ == '__main__':
    try:
        import socks
    except ImportError:
        print("❌ Требуется PySocks: pip install pysocks")
        exit(1)

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Остановлено пользователем")
    finally:
        input("\nНажмите Enter для выхода...")