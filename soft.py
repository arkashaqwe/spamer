import asyncio
from telethon import TelegramClient, errors
from telethon.tl.functions.contacts import GetContactsRequest
import os


class TurboForwardSender:
    def __init__(self):
        self.client = None
        self.api_id = 2040
        self.api_hash = "b18441a1ff607e10a989891a5462e627"
        self.saved_message = None  # Сохраним сообщение для пересылки

    async def connect_account(self):
        """Авторизация в аккаунте"""
        print("\n🔐 Подключение к аккаунту...")
        self.client = TelegramClient('session_name', self.api_id, self.api_hash)

        try:
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

    async def create_template_message(self):
        """Создаем шаблонное сообщение в Избранном"""
        print("\n📝 Создание шаблона для рассылки...")
        message = input("Введите текст сообщения: ")

        # Сначала отправляем текст
        await self.client.send_message('me', message)
        print("✅ Текст сохранен в Избранное")

        # Если есть APK - прикрепляем
        apk_path = input("Введите путь к APK (или Enter чтобы пропустить): ").strip()
        if apk_path and os.path.exists(apk_path):
            msg = await self.client.send_file(
                'me',
                apk_path,
                caption=message,
                force_document=True
            )
            self.saved_message = msg
            print(f"✅ Сообщение+APK сохранено (ID: {msg.id})")
        else:
            print("ℹ️ APK не прикреплен")

    async def get_recipients(self):
        """Получаем список получателей"""
        print("\n👥 Получаем список контактов...")
        recipients = []

        # Диалоги
        async for dialog in self.client.iter_dialogs():
            if dialog.is_user and not dialog.entity.bot:
                recipients.append(dialog.entity)

        # Контакты
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

    async def fast_forward(self):
        """Быстрая рассылка пересылкой"""
        if not self.saved_message:
            await self.create_template_message()

        recipients = await self.get_recipients()
        if not recipients:
            print("❌ Нет получателей для рассылки")
            return

        confirm = input(f"Начать рассылку для {len(recipients)} получателей? (y/n): ")
        if confirm.lower() != 'y':
            print("❌ Рассылка отменена")
            return

        print("\n🚀 Начинаем БЫСТРУЮ рассылку...")
        success = 0

        for recipient in recipients:
            try:
                await self.client.forward_messages(recipient, self.saved_message)
                name = getattr(recipient, 'first_name', None) or getattr(recipient, 'title', f"ID:{recipient.id}")
                print(f"✓ Переслано: {name}")
                success += 1
            except Exception as e:
                print(f"✕ Ошибка: {type(e).__name__}")

        print(f"\n🔥 Рассылка завершена! Успешно: {success}/{len(recipients)}")


async def main():
    print("""
    ██████╗ ██╗   ██╗    █████╗ ██████╗ ██╗  ██╗ █████╗ ███████╗██╗  ██╗ █████╗ 
    ██╔══██╗╚██╗ ██╔╝   ██╔══██╗██╔══██╗██║ ██╔╝██╔══██╗██╔════╝██║  ██║██╔══██╗
    ██████╔╝ ╚████╔╝    ███████║██████╔╝█████╔╝ ███████║███████╗███████║███████║
    ██╔══██╗  ╚██╔╝     ██╔══██║██╔══██╗██╔═██╗ ██╔══██║╚════██║██╔══██║██╔══██║
    ██████╔╝   ██║      ██║  ██║██║  ██║██║  ██╗██║  ██║███████║██║  ██║██║  ██║
    ╚═════╝    ╚═╝      ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝
    """)

    sender = TurboForwardSender()
    if await sender.connect_account():
        await sender.fast_forward()


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Программа прервана пользователем")
    finally:
        input("\nНажмите Enter для выхода...")