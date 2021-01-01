from io import IOBase as FileType
from io import BytesIO
from enum import Enum

import json
import os
import six

from .objects import Object
from .library import assets, init_async

class uploader:
    __slots__ = ('__api', '__http')

    def __init__(self, api):
        self.__api = api
        self.__http = api.http


    async def photo_messages(self, photos):
        response = await self.__api.photos.getMessagesUploadServer(peer_id = 0)
        response = self.__http.post(response.upload_url, data = self.convertAsset(photos))

        return self.__api.photos.saveMessagesPhoto(**response)

        
    async def photo_group_widget(self, photo, image_type):
        response = await self.__api.appWidgets.getGroupImageUploadServer(image_type = image_type)
        response = self.__http.post(response.upload_url, data = self.convertAsset(photo))

        return self.__api.appWidgets.saveGroupImage(**response)


    async def photo_chat(self, photo, peer_id):
        if peer_id < 2000000000: 
            raise ValueError("Incorrect peer_id")

        else: 
            values = dict()
            values['chat_id'] = peer_id - 2000000000

        response = await self.__api.photos.getChatUploadServer(**values)
        response = self.__http.post(url.upload_url, data = self.convertAsset(photo))

        return self.__api.messages.setChatPhoto(file = response['response'])


    async def document(self, document, title=None, tags=None, peer_id=None, doc_type = 'doc', to_wall = None):
        values = {
            'peer_id': peer_id,
            'type': doc_type
        }
        
        response = await self.__api.docs.getMessagesUploadServer(**values) # vk.com/dev/docs.getMessagesUploadServer
        response = self.__http.post(response.upload_url, data = self.convertAsset(document, sign = 'file'))
        if title: response['title'] = title 
        if tags: response['tags'] = tags

        return await self.__api.docs.save(**response) 


    async def audio_message(self, audio, peer_id=None):
        return await self.document(
            audio,
            doc_type = 'audio_message',
            peer_id = peer_id
            )


    async def story(self, file, file_type,
              reply_to_story=None, link_text=None,
              link_url=None):
        # переписал функцию для историй, так как адаптированная версия с VK_api под aiohttp 
        # выдавала тупо сам результат запроса. Сделал как фреймворку нужно :3

        if file_type == 'photo':
            method = self.__api.stories.getPhotoUploadServer

        elif file_type == 'video':
            method = self.__api.stories.getVideoUploadServer

        else:
            raise ValueError('type should be either photo or video')

        if (not link_text) != (not link_url):
            raise ValueError(
                'Either both link_text and link_url or neither one are required'
            )

        if link_url and not link_url.startswith('__https://vk.com'):
            raise ValueError(
                'Only internal __https://vk.com links are allowed for link_url'
            )

        if link_url and len(link_url) > 2048:
            raise ValueError('link_url is too long. Max length - 2048')

        values = dict()

        values['add_to_news'] = True
        if reply_to_story: values['reply_to_story'] = reply_to_story
        if link_text: values['link_text'] = link_text
        if link_url: values['link_url'] = link_url

        response = await method(**values)
        response = self.__http.post(response.upload_url, data = self.convertAsset(file, 'file' if file_type == "photo" else 'video_file'))
        
        return await self.__api.stories.save(upload_results = response.response.upload_result)


    def convertAsset(self, files, sign = 'file'):
        if isinstance(files, (str, bytes)) or issubclass(type(files), FileType):
            response = None

            if isinstance(files, str): 
                response = assets(files, 'rb', buffering = 0)
            elif isinstance(files, bytes): 
                response = BytesIO(files)
            else:
                response = files

            return {
                sign: response
            }

        elif isinstance(files, list):
            files_dict = {}

            for i in range(min(len(files), 5)): # ограничение в пять файлов
                if isinstance(files[i], (str, bytes)) or issubclass(type(files[i]), FileType):
                    response = None

                    if isinstance(files[i], str): 
                        response = self.assets(files[i], 'rb', buffering = 0)
                    elif isinstance(files[i], bytes): 
                        response = BytesIO(files[i])
                    else:
                        response = files[i]

                    files_dict[sign + str(i+1)] = response

                else:
                    raise TypeError("Only str, bytes or file-like objects")

            return files_dict

        else:
            raise TypeError("Only str, bytes or file-like objects")


MAX_BUTTONS_ON_LINE = 5
MAX_DEFAULT_LINES = 10
MAX_INLINE_LINES = 6

def sjson_dumps(*args, **kwargs):
    kwargs['ensure_ascii'] = False
    kwargs['separators'] = (',', ':')

    return json.dumps(*args, **kwargs)


class keyboardcolor(Enum):
    PRIMARY = 'primary' # blue
    SECONDARY = 'secondary' # white
    NEGATIVE = 'negative' # red
    POSITIVE = 'positive' # green


class keyboardbutton(Enum):
    TEXT = "text"
    LOCATION = "location"
    VKPAY = "vkpay"
    VKAPPS = "open_app"
    OPENLINK = "open_link"
    CALLBACK = "callback"


class keyboard:
    __slots__ = ('one_time', 'lines', 'keyboard', 'inline')

    def __init__(self, one_time=False, inline=False):
        self.one_time = one_time
        self.inline = inline
        self.lines = [[]]

        self.keyboard = {
            'one_time': self.one_time,
            'inline': self.inline,
            'buttons': self.lines
        }

    def get_keyboard(self):
        return sjson_dumps(self.keyboard)

    @classmethod
    def get_empty_keyboard(cls):
        keyboard = cls()
        keyboard.keyboard['buttons'] = []
        return keyboard.get_keyboard()

    def add_button(self, label, color=keyboardcolor.SECONDARY, payload=None):
        current_line = self.lines[-1]

        if len(current_line) >= MAX_BUTTONS_ON_LINE:
            raise ValueError(f'Max {MAX_BUTTONS_ON_LINE} buttons on a line')

        color_value = color

        if isinstance(color, keyboardcolor):
            color_value = color_value.value

        if payload is not None and not isinstance(payload, six.string_types):
            payload = sjson_dumps(payload)

        button_type = keyboardbutton.TEXT.value

        current_line.append({
            'color': color_value,
            'action': {
                'type': button_type,
                'payload': payload,
                'label': label,
            }
        })

    def add_callback_button(self, label, color=keyboardcolor.SECONDARY, payload=None):
        current_line = self.lines[-1]

        if len(current_line) >= MAX_BUTTONS_ON_LINE:
            raise ValueError(f'Max {MAX_BUTTONS_ON_LINE} buttons on a line')

        color_value = color

        if isinstance(color, keyboardcolor):
            color_value = color_value.value

        if payload is not None and not isinstance(payload, six.string_types):
            payload = sjson_dumps(payload)

        button_type = keyboardbutton.CALLBACK.value

        current_line.append({
            'color': color_value,
            'action': {
                'type': button_type,
                'payload': payload,
                'label': label,
            }
        })

    def add_location_button(self, payload=None):
        current_line = self.lines[-1]

        if len(current_line) != 0:
            raise ValueError(
                'This type of button takes the entire width of the line'
            )

        if payload is not None and not isinstance(payload, six.string_types):
            payload = sjson_dumps(payload)

        button_type = keyboardbutton.LOCATION.value

        current_line.append({
            'action': {
                'type': button_type,
                'payload': payload
            }
        })

    def add_vkpay_button(self, hash, payload=None):
        current_line = self.lines[-1]

        if len(current_line) != 0:
            raise ValueError(
                'This type of button takes the entire width of the line'
            )

        if payload is not None and not isinstance(payload, six.string_types):
            payload = sjson_dumps(payload)

        button_type = keyboardbutton.VKPAY.value

        current_line.append({
            'action': {
                'type': button_type,
                'payload': payload,
                'hash': hash
            }
        })

    def add_vkapps_button(self, app_id, owner_id, label, hash, payload=None):
        current_line = self.lines[-1]

        if len(current_line) != 0:
            raise ValueError(
                'This type of button takes the entire width of the line'
            )

        if payload is not None and not isinstance(payload, six.string_types):
            payload = sjson_dumps(payload)

        button_type = keyboardbutton.VKAPPS.value

        current_line.append({
            'action': {
                'type': button_type,
                'app_id': app_id,
                'owner_id': owner_id,
                'label': label,
                'payload': payload,
                'hash': hash
            }
        })

    def add_openlink_button(self, label, link, payload=None):
        current_line = self.lines[-1]

        if len(current_line) >= MAX_BUTTONS_ON_LINE:
            raise ValueError(f'Max {MAX_BUTTONS_ON_LINE} buttons on a line')

        if payload is not None and not isinstance(payload, six.string_types):
            payload = sjson_dumps(payload)

        button_type = keyboardbutton.OPENLINK.value

        current_line.append({
            'action': {
                'type': button_type,
                'link': link,
                'label': label,
                'payload': payload
            }
        })

    def add_line(self):
        if self.inline:
            if len(self.lines) >= MAX_INLINE_LINES:
                raise ValueError(f'Max {MAX_INLINE_LINES} lines for inline keyboard')
        else:
            if len(self.lines) >= MAX_DEFAULT_LINES:
                raise ValueError(f'Max {MAX_DEFAULT_LINES} lines for default keyboard')

        self.lines.append([])