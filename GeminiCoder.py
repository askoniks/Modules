# meta developer: @tyn_mods
# FILENAME: GeminiCoder.py

from .. import loader, utils


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
        
        # Сообщение при установке модуля
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
        
        # Показываем сообщение только один раз при первой установке/запуске
        if not db.get(main.__name__, "shown_install_msg", False):
            try:
                await self.client.send_message(
                    "me",
                    self.strings("install_msg")
                )
                db.set(main.__name__, "shown_install_msg", True)
            except Exception:
                pass  # если вдруг не получится отправить в избранное — просто тихо пропустим


    # ---------- GENERATE ----------

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
            STRICT_HEROKU_PROMPT
            + "\n\nUSER TASK:\n"
            + prompt,
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

    # ---------- FIX ----------

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
            + "\n\nORIGINAL TASK:\n"
            + self._last_prompt
            + "\n\nFIX REQUEST:\n"
            + fix_text
            + "\n\nCURRENT CODE:\n"
            + self._last_code,
            generation_config={"temperature": self.config["temperature"]}
        )

        new_code = re.sub(r"```.*?```", "", response.text, flags=re.S).strip()
        if "# meta" in new_code:
            new_code = new_code[new_code.find("# meta"):]

        self._last_code = new_code

        file = io.BytesIO(new_code.encode("utf-8"))
        file.name = self._last_filename

        await self.client.send_file(
            message.peer_id,
            file,
            caption="✅ <b>Исправленный модуль</b>"
        )
