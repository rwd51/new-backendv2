import json
import logging
import os
import time
import uuid
import redis

from django.conf import settings
from error_handling.error_list import CUSTOM_ERROR_LIST

logger = logging.getLogger(__name__)

LUA_SCRIPT_DIR = '../accounts/lua_scripts'
ACQUIRE_LOCK_FILE = 'lock.lua'
RELEASE_LOCK_FILE = 'unlock.lua'
WEBHOOK_RELEASE_LOCK_FILE = 'webhook_unlock.lua'


class AbstractSingleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(AbstractSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class RedisClient(metaclass=AbstractSingleton):
    def __init__(self):
        self.client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)

    def set_list(self, key, value):
        self.client.rpush(key, *value)

    def exists(self, key):
        return self.client.exists(key)

    def delete(self, key):
        self.client.delete(key)


class LuaClient(metaclass=AbstractSingleton):
    def __init__(self):
        self.client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        self.scripts = {
            'acquire_lock': self.client.register_script(self.load_lua_script(ACQUIRE_LOCK_FILE)),
            'release_lock': self.client.register_script(self.load_lua_script(RELEASE_LOCK_FILE)),
            'webhook_release_lock': self.client.register_script(self.load_lua_script(WEBHOOK_RELEASE_LOCK_FILE)),
        }

    @classmethod
    def load_lua_script(cls, file_name):
        fp = os.path.realpath(os.path.dirname(__file__))
        return open(os.path.join(fp, LUA_SCRIPT_DIR, file_name)).read()

    def acquire_lock(self, lock_name):
        return self.scripts['acquire_lock'](keys=[lock_name])

    def release_lock(self, lock_name):
        return self.scripts['release_lock'](keys=[lock_name])

    def webhook_release_lock(self, lock_name, synctera_id):
        return self.scripts['webhook_release_lock'](keys=[lock_name, synctera_id])


class EntityManager(metaclass=AbstractSingleton):

    @classmethod
    def generate_lock_name(cls, lock_prefix, entity_id):
        return f'LOCK_{lock_prefix}_{entity_id}'

    @classmethod
    def acquire_lock(cls, lock_name):
        lua_client = LuaClient()
        return lua_client.acquire_lock(lock_name)

    @classmethod
    def release_lock(cls, lock_name):
        lua_client = LuaClient()
        return lua_client.release_lock(lock_name)

    @classmethod
    def generate_and_save_idempotent_key(cls, key_prefix, view_class_name, request_data):
        key_prefix = key_prefix if key_prefix else 'potent'
        idempotent_key = f'IDEM_{key_prefix[:9].upper()}_{int(time.time() * 1000)}_{uuid.uuid4().hex}'
        redis_client = RedisClient()
        redis_client.set_list(idempotent_key, [view_class_name, json.dumps(request_data)])
        return idempotent_key

    @classmethod
    def erase_idempotent_key(cls, idempotent_key):
        redis_client = RedisClient()
        redis_client.delete(idempotent_key)

    @classmethod
    def pub_to_channel(cls, channel_name, response_json):
        pubsub_client = PubSubClient()
        logger.debug(f'publishing to channel {channel_name}')
        pubsub_client.publish_to_channel(channel=channel_name, data=response_json)

    @classmethod
    def idempotent_key_exists(cls, idempotent_key):
        redis_client = RedisClient()
        return redis_client.exists(idempotent_key)


class PubSubClient(metaclass=AbstractSingleton):
    def __init__(self):
        self.redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)
        self.sub_timeout = float(settings.REDIS_SUB_TIMEOUT)
        self.sub_sleep = float(settings.REDIS_SUB_SLEEP)

    def publish_to_channel(self, channel, data):
        try:
            self.redis_client.publish(channel, data)
        except Exception as ex:
            logger.error('Pub failed', exc_info=True)

    def create_channel_name(self, channel_prefix, channel_key):
        return f'{channel_prefix}_{channel_key}_{uuid.uuid4()}'

    def get_response_from_channel(self, channel_name):
        pubsub = self.redis_client.pubsub()
        pubsub.subscribe(channel_name)

        stop_time = time.time() + self.sub_timeout
        while time.time() < stop_time:
            message = pubsub.get_message()
            if message and message['type'] == 'message':
                return json.loads(message['data'])
            time.sleep(self.sub_sleep)
        raise CUSTOM_ERROR_LIST.PUBSUB_TIMEOUT_ERROR_4005
