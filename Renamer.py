# meta developer: tyn_mods
# scope: hikka_only
# scope: hikka_min 1.3.0

import io
from .. import loader, utils

@loader.tds
class FileRenamerMod(loader.Module):
    """Модуль для быстрого переименования файлов в Telegram."""
    
    strings = {
        "name": "FileRenamer",
        "no_reply": "<b>❌ Ответьте на файл!</b>",
        "no_args": "<b>❌ Укажите новое имя файла!</b>",
        "processing": "<b>📝 Скачиваю и переименовываю...</b>",
        "success": "<b>✅ Файл переименован в:</b> <code>{}</code>"
    }

    @loader.unrestricted
    async def renamecmd(self, message):
        """<новое имя> — Переименовать файл (в ответе).
        Можно писать без .py, модуль добавит сам."""
        
        reply = await message.get_reply_message()
        if not reply or not reply.file:
            await utils.answer(message, self.strings("no_reply"))
            return

        args = utils.get_args_raw(message)
        if not args:
            await utils.answer(message, self.strings("no_args"))
            return

        new_name = args.strip()

        # Если переименовываем .py файл и юзер не написал расширение, добавляем его
        if reply.file.name and reply.file.name.endswith(".py"):
            if not new_name.endswith(".py"):
                new_name += ".py"
        
        # Если оригинальный файл не .py, но юзер хочет добавить расширение сам - ок.
        # Если расширения нет вообще, оставляем как есть.

        await utils.answer(message, self.strings("processing"))

        # Скачиваем файл в оперативную память (байты)
        file_data = await reply.download_media(bytes)
        
        # Подготавливаем файл к отправке
        out_file = io.BytesIO(file_data)
        out_file.name = new_name # Присваиваем новое имя атрибуту объекта

        # Отправляем
        await message.respond(
            self.strings("success").format(new_name),
            file=out_file,
            force_document=True
        )