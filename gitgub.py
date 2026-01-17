# meta developer: tynnawi
# meta description: Upload files and photos to GitHub with config via .cfg

import base64
import os
import requests

from .. import loader, utils


API_URL = "https://api.github.com"


@loader.tds
class GitHubUploadMod(loader.Module):
    """Загрузка файлов и фото в GitHub"""

    strings = {"name": "GitHubUpload"}

    def __init__(self):
        self.config = loader.ModuleConfig(
            loader.ConfigValue(
                "token",
                "",
                "GitHub Personal Access Token",
                validator=loader.validators.Hidden(),
            ),
            loader.ConfigValue(
                "repo",
                "",
                "GitHub repository (username/repo)",
            ),
            loader.ConfigValue(
                "branch",
                "main",
                "Repository branch",
            ),
            loader.ConfigValue(
                "path",
                "",
                "Path inside repository (optional)",
            ),
        )

    async def guploadcmd(self, message):
        """Загрузить файл или фото в GitHub"""
        reply = await message.get_reply_message()
        if not reply or not reply.media:
            await utils.answer(message, "❌ Ответь на файл или фото")
            return

        token = self.config["token"]
        repo = self.config["repo"]
        branch = self.config["branch"]
        path = self.config["path"]

        if not token or not repo:
            await utils.answer(message, "❌ Заполни token и repo в .cfg")
            return

        await utils.answer(message, "⬆️ Загружаю в GitHub...")

        file_path = await reply.download_media()

        # Имя файла
        if reply.file and reply.file.name:
            filename = reply.file.name
        else:
            filename = f"photo_{reply.id}.jpg"

        repo_path = f"{path}/{filename}" if path else filename
        url = f"{API_URL}/repos/{repo}/contents/{repo_path}"

        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

        # Проверка существования файла
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None

        with open(file_path, "rb") as f:
            content = base64.b64encode(f.read()).decode()

        data = {
            "message": f"upload {filename}",
            "content": content,
            "branch": branch,
        }

        if sha:
            data["sha"] = sha

        r = requests.put(url, headers=headers, json=data)

        if r.status_code not in (200, 201):
            await utils.answer(
                message,
                f"❌ Ошибка GitHub:\n<code>{r.text}</code>",
            )
            return

        raw_url = (
            f"https://raw.githubusercontent.com/"
            f"{repo}/{branch}/{repo_path}"
        )

        os.remove(file_path)

        await utils.answer(
            message,
            "✅ <b>Загружено!</b>\n\n"
            f"🔗 <code>{raw_url}</code>",
        )
