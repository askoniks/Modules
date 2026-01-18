# meta developer: @tyn_mods
# scope: hikka_only
# scope: hikka_min 1.3.0

import io
import re
from .. import loader, utils

@loader.tds
class MetaChangerMod(loader.Module):
    """Модуль для изменения мета-тега разработчика в файлах модулей."""
    
    strings = {
        "name": "MetaChanger",
        "no_reply": "<b>❌ Ответьте на .py файл!</b>",
        "not_py": "<b>❌ Это не Python файл!</b>",
        "downloading": "<b>📥 Скачиваю файл...</b>",
        "processing": "<b>⚙️ Обрабатываю...</b>",
        "success": "<b>✅ Готово! Мета разработчика изменена на:</b> <code>{}</code>",
        "args_err": "<b>⚠️ Не удалось определить нового автора.</b>"
    }

    async def client_ready(self, client, db):
        self.client = client

    @loader.unrestricted
    async def setmetacmd(self, message):
        """<автор> (в ответ на файл) — Изменить автора модуля.
        Если автор не указан, будет использован ваш @username."""
        
        reply = await message.get_reply_message()
        if not reply or not reply.file:
            await utils.answer(message, self.strings("no_reply"))
            return

        if not reply.file.name or not reply.file.name.endswith(".py"):
            await utils.answer(message, self.strings("not_py"))
            return

        # Получаем аргументы (нового автора)
        args = utils.get_args_raw(message)
        
        if not args:
            # Если аргументов нет, берем юзернейм текущего пользователя
            me = await self.client.get_me()
            if me.username:
                new_author = f"@{me.username}"
            else:
                new_author = me.first_name
        else:
            new_author = args

        await utils.answer(message, self.strings("downloading"))

        # Скачиваем файл в байты
        code_bytes = await reply.download_media(bytes)
        try:
            content = code_bytes.decode("utf-8")
        except UnicodeDecodeError:
            await utils.answer(message, "<b>❌ Ошибка кодировки файла (не UTF-8).</b>")
            return

        # Регулярка для поиска строки # meta developer: ...
        # Ищет: начало строки, решетка, meta, developer:, любой текст до конца строки
        pattern = re.compile(r"^(#\s*meta\s+developer:\s*)(.*)$", re.MULTILINE)

        if pattern.search(content):
            # Если нашли — заменяем
            new_content = pattern.sub(f"\\1{new_author}", content)
        else:
            # Если не нашли — добавляем в самое начало файла
            new_content = f"# meta developer: {new_author}\n{content}"

        # Создаем файл в памяти для отправки
        out_file = io.BytesIO(new_content.encode("utf-8"))
        out_file.name = reply.file.name  # Сохраняем оригинальное имя

        await utils.answer(message, self.strings("success").format(new_author))
        
        # Отправляем файл
        await message.respond(file=out_file, force_document=True)