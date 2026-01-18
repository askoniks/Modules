# meta developer: @tyn_mods
# FILENAME: GeminiCoder.py

import io
import re
import time
import google.generativeai as genai

from .. import loader, utils


STRICT_HEROKU_PROMPT = """
YOU ARE GENERATING A MODULE FOR THE HEROKU USERBOT (coddrago fork).

THIS IS NOT HIKKA, NOT FTG, NOT TELETHON RAW.
ONLY USE HEROKU-SUPPORTED SYNTAX.

================= ABSOLUTE RULES =================

1. OUTPUT ONLY VALID PYTHON CODE.
2. DO NOT USE MARKDOWN.
3. DO NOT ADD EXPLANATIONS.
4. DO NOT ADD TEXT OUTSIDE CODE.
5. FIRST LINE MUST BE:
   # meta developer: @username

================= ALLOWED IMPORTS =================

from .. import loader, utils

NO OTHER IMPORTS FOR HEROKU LOGIC.

================= MODULE STRUCTURE =================

@loader.tds
class MyModule(loader.Module):
    strings = {"name": "ModuleName"}

    async def client_ready(self, client, db):
        self.client = client

================= COMMAND SYNTAX =================

@loader.unrestricted
async def testcmd(self, message):
    \"\"\"Описание команды\"\"\"
    await utils.answer(message, "text")

COMMAND NAME RULES:
- command must end with `cmd`
- command is called as `.test`

================= MESSAGE HANDLING =================

✔ CORRECT:
await utils.answer(message, "text")

✘ INCORRECT:
message.reply()
message.edit()
client.send_message()

================= CONFIG =================

self.config = loader.ModuleConfig(
    loader.ConfigValue(
        "param",
        "default",
        "description"
    )
)

================= FILE NAMING =================

YOU MUST INCLUDE A LINE:
# FILENAME: module_name.py

================= EXAMPLES =================

EXAMPLE 1:

# meta developer: @tyn_mods
# FILENAME: hello.py

from .. import loader, utils

@loader.tds
class HelloMod(loader.Module):
    strings = {"name": "Hello"}

    @loader.unrestricted
    async def hellocmd(self, message):
        await utils.answer(message, "Hello world")

================= FINAL REQUIREMENT =================

RETURN ONLY PYTHON CODE.
NO EXTRA TEXT.
"""


@loader.tds
class GeminiCoderMod(loader.Module):
    """Gemini генератор модулей Heroku с жёстким промптом"""

    strings = {
        "name": "GeminiCoder",
        "no_args": "💎 Укажи описание модуля.",
        "no_api": "❌ Укажи API ключ в .config GeminiCoder",
        "thinking": "🧠 Gemini пишет код...",
        "no_last": "❌ Нет предыдущего файла для фикса",
        "fix_no_args": "❌ Укажи, что нужно исправить",
        "install_msg": (
            "💎 <b>GeminiCoder успешно установлен!</b>\n\n"
            "Поддержи разработчика подпиской:\n"
            "➤ @tyn_mods\n\n"
            "Спасибо за использование ♥"
        )
    }

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "api_key",
                None,
                "Google AI Studio API key",
                validator=loader.validators.Hidden()
            ),
            loader.ConfigValue(
                "model",
                "gemini-1.5-flash",
                "Gemini model"
            ),
            loader.ConfigValue(
                "temperature",
                0.05,
                "Creativity (LOW for correctness)"
            )
        )

        self._last_code = None
        self._last_filename = None
        self._last_prompt = None

    async def client_ready(self, client, db):
        self.client = client

        # Показываем сообщение подписки только один раз
        if not db.get("GeminiCoder", "install_msg_shown", False):
            try:
                await client.send_message(
                    "me",
                    self.strings("install_msg")
                )
                db.set("GeminiCoder", "install_msg_shown", True)
            except Exception:
                pass  # Если не получилось отправить — просто пропускаем

    @loader.unrestricted
    async def gemmodcmd(self, message):
        """<описание> — создать модуль"""
        prompt = utils.get_args_raw(message)
        if not prompt:
            return await utils.answer(message, self.strings["no_args"])

        if not self.config["api_key"]:
            return await utils.answer(message, self.strings["no_api"])

        await utils.answer(message, self.strings["thinking"])

        genai.configure(api_key=self.config["api_key"])
        model = genai.GenerativeModel(self.config["model"])

        response = await model.generate_content_async(
            STRICT_HEROKU_PROMPT + "\n\nUSER TASK:\n" + prompt,
            generation_config={"temperature": self.config["temperature"]}
        )

        code = re.sub(r"```.*?```", "", response.text, flags=re.S).strip()
        if "# meta" in code:
            code = code[code.find("# meta"):]

        fn = re.search(r"# FILENAME: (.+?\.py)", code)
        filename = fn.group(1) if fn else f"module_{int(time.time())}.py"

        self._last_code = code
        self._last_filename = filename
        self._last_prompt = prompt

        file = io.BytesIO(code.encode("utf-8"))
        file.name = filename

        await self.client.send_file(
            message.peer_id,
            file,
            caption=f"💎 <b>Gemini Module</b>\n📄 <code>{filename}</code>"
        )

    @loader.unrestricted
    async def gemfixcmd(self, message):
        """<что исправить> — исправить последний модуль"""
        fix_text = utils.get_args_raw(message)
        if not fix_text:
            return await utils.answer(message, self.strings["fix_no_args"])

        if not self._last_code:
            return await utils.answer(message, self.strings["no_last"])

        await utils.answer(message, "🛠 Исправляю...")

        genai.configure(api_key=self.config["api_key"])
        model = genai.GenerativeModel(self.config["model"])

        response = await model.generate_content_async(
            STRICT_HEROKU_PROMPT
            + "\n\nORIGINAL TASK:\n" + (self._last_prompt or "неизвестно")
            + "\n\nFIX REQUEST:\n" + fix_text
            + "\n\nCURRENT CODE:\n" + self._last_code,
            generation_config={"temperature": self.config["temperature"]}
        )

        new_code = re.sub(r"```.*?```", "", response.text, flags=re.S).strip()
        if "# meta" in new_code:
            new_code = new_code[new_code.find("# meta"):]

        self._last_code = new_code

        file = io.BytesIO(new_code.encode("utf-8"))
        file.name = self._last_filename or f"fixed_module_{int(time.time())}.py"

        await self.client.send_file(
            message.peer_id,
            file,
            caption="✅ <b>Исправленный модуль</b>"
        )
