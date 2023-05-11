# Маруся

Discord бот для Stable Diffusion

<img src=https://github.com/sebaxakerhtc/sebaxakerhtc.github.io/raw/master/images/%D0%9C%D0%B0%D1%80%D1%83%D1%81%D1%8F.png  width=30% height=30%>

This fork is for me and my friends. Original project [here](https://github.com/Kilvoctu/aiyabot)!

## Использование

Для генерации картинки из текста используйте команду /draw и заполните описание запроса.

<img src=https://github.com/sebaxakerhtc/sebaxakerhtc.github.io/raw/master/images/livepreview.png width=50% height=50%>

### Поддерживаемые функции

- (new!) live preview | генерация в реальном времени
- negative prompts | нежелательное описание
- swap model/checkpoint | смена модели (_[see wiki](https://github.com/Kilvoctu/aiyabot/wiki/Model-swapping)_)
- sampling steps | шаги
- width/height | ширина/высота
- CFG scale
- sampling method | сэмплер
- seed
- Web UI styles | стили
- extra networks (hypernetwork, LoRA)
- face restoration | восстановление лиц
- high-res fix | исправление для изображений большого разрешения
- CLIP skip
- img2img | картинка в картинку
- denoising strength
- batch count, batch size | компановка (колличество и размер)

#### Дополнительные функции

- /settings command - установка значений по умолчанию для канала (_[see Notes](https://github.com/Kilvoctu/aiyabot#notes)!_):
  - так же можно здать максиму шагов, компановки и др.
  - refresh (обновляет опции Маруси из Web UI)
- /identify command - получает описание изображения.
- /stats command - показывает сколько раз использовалась команда /draw .
- /info command - Здесь объяснаются основы использования и запросов.
- /upscale command - увеличение изображения.
- кнопки - сообщения будут содержать следующие кнопки.
  - 🖋 - Эта кнопка вызывает всплывающее окно, позволяющее изменить некоторые параметры и сгенерировать новые изображения с этими изменениями.
  - 🎲 - Используйте эту кнопку чтобы сгенерировать другие изображения с теми же параметрами.
  - 📋 - Эта кнопка показывает информацию о генерации изображенийи даже позволяет скопировать команду для генерации!
  - ➡️ - New! В режиме просмотра Live preview эта кнопка пропускает генерацию (batch) и переходит к следующей
  - ❌ - Крест используется для удаления любых нежелательных изображений. Если эта кнопка не работает, вы можете добавить реакцию ❌ вместо этого.
  New! В режиме просмотра Live prevew эта же кнопка преращает задание.
- конткстное меню - попробуйте эти команды на любом сообщении.
  - Информация - просмотр сведений об изображении, сгенерированным в Stable Diffusion.
  - Быстрое увеличение - увеличение изображения без указания настроек.
- [configuration file](https://github.com/Kilvoctu/aiyabot/wiki/Configuration) - can change some of AIYA's operational aspects. 


## Setup requirements

- Установите [лучший форк AUTOMATIC1111]([https://github.com/AUTOMATIC1111/stable-diffusion-webui](https://github.com/vladmandic/automatic)).
- Запустите интерфейс с доступом к API (`COMMANDLINE_ARGS= --api`).
- Clone this repo.
- Create a file in your cloned repo called ".env", formatted like so:
```dotenv
# .env
TOKEN = put your bot token here
```
- Run AIYA by running launch.bat (or launch.sh for Linux)

## Notes

- [See wiki for notes on additional configuration.](https://github.com/Kilvoctu/aiyabot/wiki/Configuration)
- [See wiki for notes on swapping models.](https://github.com/Kilvoctu/aiyabot/wiki/Model-swapping)
- Ensure AIYA has `bot` and `application.commands` scopes when inviting to your Discord server, and intents are enabled.
- As /settings can be abused, consider reviewing who can access the command. This can be done through Apps -> Integrations in your Server Settings. Read more about /settings [here.](https://github.com/Kilvoctu/aiyabot/wiki/settings-command)
- AIYA uses Web UI's legacy high-res fix method. To ensure this works correctly, in your Web UI settings, enable this option: `For hires fix, use width/height sliders to set final resolution rather than first pass`


## Credits

AIYA only exists thanks to these awesome people:
- AUTOMATIC1111, and all the contributors to the Web UI repo.
  - https://github.com/AUTOMATIC1111/stable-diffusion-webui
- harubaru, my entryway into Stable Diffusion (with Waifu Diffusion) and foundation for the AIYA Discord bot.
  - https://github.com/harubaru/waifu-diffusion
  - https://github.com/harubaru/discord-stable-diffusion
- gingivere0, for PayloadFormatter class for the original API. Without that, I'd have given up from the start. Also has a great Discord bot as a no-slash-command alternative.
  - https://github.com/gingivere0/dalebot
- You, for using AIYA and contributing with PRs, bug reports, feedback, and more!
