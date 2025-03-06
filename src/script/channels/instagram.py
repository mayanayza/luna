import os
from pathlib import Path

from instagrapi import Client
from instagrapi.exceptions import LoginRequired
from instagrapi.types import Location

from src.script.channels._channel import Channel
from src.script.config import Config
from src.script.constants import Media
from src.script.utils import (
    get_project_media_files,
    get_project_metadata,
    load_personal_info,
)


class InstagramHandler(Channel):

    def __init__(self, config: Config):
        init = {
            'name': __name__,
            'class_name':self.__class__.__name__,
            'config': config
        }
            
        super().__init__(**init)

        self.bot = Client()
        self.bot.delay_range = [1,3]

    def login(self) -> None:

        login_via_session = False
        login_via_pw = False
        session = False
        session_path = Path(f"{os.path.dirname(__file__)}/instagram_session.json")
        if session_path.exists():
            session = self.bot.load_settings(session_path)
        settings = {}

        if session:

            try:
                self.bot.set_settings(session)
                self.bot.login(self.config.instagram_username, self.config.instagram_password)

                try:
                    self.bot.get_timeline_feed()
                except LoginRequired:
                    self.logger.info("Session invalid, login via username and password required")

                    settings = self.bot.get_settings()

                    # use the same device uuids across logins
                    self.bot.set_settings({})
                    self.bot.set_uuids(settings["uuids"])

                login_via_session = True
            except Exception as e:
                self.logger.info(f"Couldn't log in using session: {e}")

        if not login_via_session:
            try:
                verification_code = input("Enter 2FA verification code: ")
                self.bot.login(self.config.instagram_username, self.config.instagram_password, verification_code=verification_code)
                self.bot.dump_settings(session_path)
            except Exception as e:
                self.logger.info(f"Couldn't login user using username and password: {e}")

        if not login_via_session and not login_via_pw:
            raise Exception("Couldn't login user with either password or session")

    def publish(self, name, caption) -> None:
        try:
            # self.login()
            metadata = get_project_metadata(self, name)
            featured_content = metadata['project']['featured_content']

            images = get_project_media_files(self, name, Media.IMAGES.TYPE)

            if featured_content['type'] == 'image': 
                images = sorted(images, key=lambda x: 0 if featured_content['source'] in str(x) else 1)

            if caption == '':
                caption = metadata['project']['tagline']

            personal_info = load_personal_info(self)
            location_name = personal_info['location']

            self.bot.album_upload(
                images, 
                caption, 
                location=Location(name=location_name)
            )

            self.logger.info("Published instagram")
        except Exception as e:
            self.logger.error(f"Failed to publish instagram: {e}")
            raise

    def stage(self, name: str) -> str:
        self.logger.error(f"No stage method for Instagram ({name})")
    
    def rename(self, old_name: str, new_name: str) -> None:
        self.logger.error(f"No rename method for Instagram ({old_name})")

    def delete(self, name: str) -> None:
        self.logger.error(f"No delete method for Instagram ({name})")

