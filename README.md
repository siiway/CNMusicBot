# CNMusicBot

开发中, todos 见 [此处](./todo.md)

# requirements

- Python **>= 3.10** (建议: 3.13)
- pyproject.toml 中依赖
- config.yaml / config.toml (喜欢哪个用哪个, 配置项见 [config.py](./config.py))
  - 一个 discord bot - https://discord.com/developers/applications
  - 网易云 音乐 / 解锁 api
  - :ladder: (如果部署在国内机器)
- ffmpeg
- 非美区语音服务器 - https://github.com/Rapptz/discord.py/issues/10207#issuecomment-3013779078
  - waiting for discord.py **v2.6**

# bot commands

- `/list` - 查看当前播放列表
- `/search` - 从网易云搜索音乐
- `/play` - 播放搜索结果中的音乐 (需要先加入一个语音频道)

# useful commands (uv)

```sh
# run program
uv run main.py
# add deps
uv add ...
# install deps
uv sync
# upgrade deps
uv sync --upgrade
uv sync -U # short ver
```