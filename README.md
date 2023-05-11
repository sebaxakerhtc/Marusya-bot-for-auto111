# Маруся

Discord бот для Stable Diffusion

<img src=https://sebaxakerhtc.github.io/images/%D0%9C%D0%B0%D1%80%D1%83%D1%81%D1%8F.png  width=40% height=40%>

This fork is for me and my friends. Original project [here](https://github.com/Kilvoctu/aiyabot)!

## Использование

Для генерации картинки из текста используйте команду /draw и заполните описание запроса.

<img src=https://sebaxakerhtc.github.io/images/live_preview.png width=40% height=40%>

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


## Установка

- Установите [лучший форк AUTOMATIC1111](https://github.com/vladmandic/automatic).
- Запустите интерфейс с доступом к API (`COMMANDLINE_ARGS= --api`).
- Склонируйте этот репозиторий.
- Создайте в клонированном репозитории файл ".env" и заполните так:
```dotenv
# .env
TOKEN = put your bot token here
```
- Запустите Марусю используя launch.bat (или launch.sh для Linux)

## Заметки

- [Дополнительная настройка (English).](https://github.com/Kilvoctu/aiyabot/wiki/Configuration)
- [Переключение моделей (English).](https://github.com/Kilvoctu/aiyabot/wiki/Model-swapping)
- Убедитесь, что Маруся имеет `bot`, `application.commands` и необходимые разрешения, приглашая её в свой Discord сервер.
- Так как командой /settings можно злоупотреблять - проверьте, кто может использовать эту команду. Перейдите в Apps -> Integrations в настройках сервера. Подробнее о /settings [здесь.(English)](https://github.com/Kilvoctu/aiyabot/wiki/settings-command)
- Маруся использует устаревший high-res fix из Web UI. Чтоб он работал правильно, в настройках Web UI включите опцию: `For hires fix, use width/height sliders to set final resolution rather than first pass`


## Credits (original)

AIYA only exists thanks to these awesome people:
- [Original project](https://github.com/Kilvoctu/aiyabot) - it's from me!
- AUTOMATIC1111, and all the contributors to the Web UI repo.
  - https://github.com/AUTOMATIC1111/stable-diffusion-webui
- harubaru, my entryway into Stable Diffusion (with Waifu Diffusion) and foundation for the AIYA Discord bot.
  - https://github.com/harubaru/waifu-diffusion
  - https://github.com/harubaru/discord-stable-diffusion
- gingivere0, for PayloadFormatter class for the original API. Without that, I'd have given up from the start. Also has a great Discord bot as a no-slash-command alternative.
  - https://github.com/gingivere0/dalebot
- You, for using AIYA and contributing with PRs, bug reports, feedback, and more!
