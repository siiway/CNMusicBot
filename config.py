# coding: utf-8
from os.path import exists
from logging import getLogger

from pydantic import BaseModel, ValidationError
from yaml import safe_load as load_yaml
from toml import loads as load_toml

import utils as u

l = getLogger(__name__)


class ConfigModel(BaseModel):
    '''
    主配置
    '''

    debug: bool = False
    '''是否启用调试模式 (显示更多日志)'''

    log_file: str | None = None
    '''日志文件目录 (为空禁用)'''

    token: str
    '''Bot token'''

    ncm_api: str
    '''网易云音乐 api 地址 (结尾不加 /)'''

    unm_api: str
    '''网易云解灰 api 地址 (结尾不加 /)'''

    proxy: str | None = None
    '''代理地址'''


class Config:
    '''
    Config System
    '''

    config: ConfigModel

    def __init__(self):
        try:
            if exists(u.get_path('config.yaml')):
                # load yaml
                with open(u.get_path('config.yaml'), 'r', encoding='utf-8') as f:
                    raw_config: dict = load_yaml(f)
            elif exists(u.get_path('config.toml')):
                # load toml
                with open(u.get_path('config.toml'), 'r', encoding='utf-8') as f:
                    raw_config: dict = load_toml(f.read())
            else:
                # both not found
                raise FileNotFoundError

            # parse config
            self.config = ConfigModel.model_validate(raw_config)
        except FileNotFoundError:
            l.error('Config file config.yaml / config.toml not found!')
            exit(1)
        except ValidationError as e:
            l.error(f'Wrong config file!\n{e}')
            exit(1)
        except Exception as e:
            l.error(f'Error when loading config.toml: {e}')
            exit(1)
