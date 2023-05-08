import discord
import math
import os
from discord.ext import commands
from discord.ui import View

from core import settings


class InfoView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.page = 0
        self.contents = []

    def disable_nav_buttons(self):
        button_back = [x for x in self.children if x.custom_id == 'button_back'][0]
        button_back.disabled = True
        button_forward = [x for x in self.children if x.custom_id == 'button_forward'][0]
        button_forward.disabled = True

    def enable_nav_buttons(self):
        button_back = [x for x in self.children if x.custom_id == 'button_back'][0]
        button_back.disabled = False
        button_forward = [x for x in self.children if x.custom_id == 'button_forward'][0]
        button_forward.disabled = False

    @discord.ui.button(
        custom_id="button_model",
        label="Models", row=0)
    async def button_model(self, _button, interaction):
        # initialize settings for each button
        length = len(settings.global_var.model_info)
        batch = 10
        self.page = 0
        self.contents = []

        # enable navigation buttons only when needed
        if length > batch:
            self.enable_nav_buttons()
        else:
            self.disable_nav_buttons()

        # create a subscript-able object for use later
        models = []
        for key in settings.global_var.model_info:
            models.append(key)

        # create each page and place into "contents" list
        for i in range(0, length, batch):
            model_list = ''
            embed_page = discord.Embed(title="Список моделей", colour=settings.global_var.embed_color)
            for key in models[i:i + batch]:
                for keyB, value in settings.global_var.model_info.items():
                    if key == keyB:
                        # strip any folders from model full name
                        filename = value[0].split(os.sep)[-1]
                        model_list += f'\n**{keyB}**\n``{filename}``'
                        break
            embed_page.add_field(name="", value=model_list, inline=True)
            if length > batch:
                embed_page.set_footer(text=f'Страница {self.page + 1} из {math.ceil(length / batch)} - {length}')
            self.contents.append(embed_page)
            self.page += 1
        self.page = 0

        try:
            await interaction.response.edit_message(view=self, embed=self.contents[0])
        except(Exception,):
            await interaction.followup.send(view=self, embed=self.contents[0], ephemeral=True)

    @discord.ui.button(
        custom_id="button_styles",
        label="Стили", row=0)
    async def button_style(self, _button, interaction):
        length = len(settings.global_var.style_names)
        batch = 8
        self.page = 0
        self.contents = []
        desc = 'В **style names** включены ``words`` чтобы ускорить запросы описаний.'

        if length > batch:
            self.enable_nav_buttons()
        else:
            self.disable_nav_buttons()

        styles = []
        for key in settings.global_var.style_names:
            styles.append(key)

        for i in range(0, length, batch):
            embed_page = discord.Embed(title="Список стилей", description=desc, colour=settings.global_var.embed_color)
            for key in styles[i:i + batch]:
                for keyB, value in settings.global_var.style_names.items():
                    if key == keyB:
                        if value == '':
                            value = ' '
                        elif len(value) > 1024:
                            value = f'{value[:1000]}....'
                        embed_page.add_field(name=f"**{key}**", value=f"``{value}``", inline=False)
                        break
            if length > batch:
                embed_page.set_footer(text=f'Страница {self.page + 1} из {math.ceil(length / batch)} - {length}')
            self.contents.append(embed_page)
            self.page += 1
        self.page = 0

        try:
            await interaction.response.edit_message(view=self, embed=self.contents[0])
        except(Exception,):
            await interaction.followup.send(view=self, embed=self.contents[0], ephemeral=True)

    @discord.ui.button(
        custom_id="button_hyper",
        label="Гиперсети", row=0)
    async def button_hyper(self, _button, interaction):
        length = len(settings.global_var.hyper_names)
        batch = 16
        self.page = 0
        self.contents = []
        desc = 'Выберите с помощью опции `extra_network`.\n' \
               'Чтобы самостоятельно добавить в описание, используйте <hypernet:``name``:``#``>\n``#`` = Сила еффекта (0.0 - 1.0)'

        if length > batch * 2:
            self.enable_nav_buttons()
        else:
            self.disable_nav_buttons()

        for i in range(0, length, batch * 2):
            hyper_column_a, hyper_column_b = '', ''
            embed_page = discord.Embed(title="Список гиперсетей", description=desc, colour=settings.global_var.embed_color)
            for value in settings.global_var.hyper_names[i:i + batch]:
                hyper_column_a += f'\n``{value}``'
            embed_page.add_field(name="", value=hyper_column_a, inline=True)
            i += batch
            for value in settings.global_var.hyper_names[i:i + batch]:
                hyper_column_b += f'\n``{value}``'
            embed_page.add_field(name="", value=hyper_column_b, inline=True)
            if length > batch * 2:
                embed_page.set_footer(text=f'Страница {self.page + 1} из {math.ceil(length / (batch * 2))} - {length}')
            self.contents.append(embed_page)
            self.page += 1
        self.page = 0

        try:
            await interaction.response.edit_message(view=self, embed=self.contents[0])
        except(Exception,):
            await interaction.followup.send(view=self, embed=self.contents[0], ephemeral=True)

    @discord.ui.button(
        custom_id="button_lora",
        label="LoRAs", row=0)
    async def button_lora(self, _button, interaction):
        length = len(settings.global_var.lora_names)
        batch = 16
        self.page = 0
        self.contents = []
        desc = 'Выберите с помощью опции `extra_network`.\n' \
               'Чтобы самостоятельно добавить в описание, используйте <lora:``name``:``#``>\n``#`` = Сила еффекта (0.0 - 1.0)'

        if length > batch * 2:
            self.enable_nav_buttons()
        else:
            self.disable_nav_buttons()

        for i in range(0, length, batch * 2):
            lora_column_a, lora_column_b = '', ''
            embed_page = discord.Embed(title="Список LoRA моделей", description=desc, colour=settings.global_var.embed_color)
            for value in settings.global_var.lora_names[i:i+batch]:
                lora_column_a += f'\n``{value}``'
            embed_page.add_field(name="", value=lora_column_a, inline=True)
            i += batch
            for value in settings.global_var.lora_names[i:i+batch]:
                lora_column_b += f'\n``{value}``'
            embed_page.add_field(name="", value=lora_column_b, inline=True)
            if length > batch*2:
                embed_page.set_footer(text=f'Страница {self.page + 1} из {math.ceil(length / (batch * 2))} - {length}')
            self.contents.append(embed_page)
            self.page += 1
        self.page = 0

        await interaction.response.edit_message(view=self, embed=self.contents[0])

    @discord.ui.button(
        custom_id="button_embed",
        label="TIs", row=0)
    async def button_embed(self, _button, interaction):
        sd1_length = len(settings.global_var.embeddings_1)
        sd2_length = len(settings.global_var.embeddings_2)
        total_length = sd1_length + sd2_length
        batch = 16
        self.page = 0
        self.contents = []
        total_pages = math.ceil(sd1_length / (batch * 2)) + math.ceil(sd2_length / (batch * 2))
        desc = 'To use, simply add the name to your prompt.'

        if total_length > batch * 2:
            self.enable_nav_buttons()
        else:
            self.disable_nav_buttons()

        for i in range(0, sd1_length, batch * 2):
            embed_column_a, embed_column_b = '', ''
            embed_page = discord.Embed(title="Список Textual Inversion embeddings",
                                       description=f"{desc}\nThese embeddings are for **SD 1.X** models.",
                                       colour=settings.global_var.embed_color)
            for value in settings.global_var.embeddings_1[i:i + batch]:
                embed_column_a += f'\n``{value}``'
            embed_page.add_field(name='', value=embed_column_a, inline=True)
            i += batch
            for value in settings.global_var.embeddings_1[i:i + batch]:
                embed_column_b += f'\n``{value}``'
            embed_page.add_field(name='', value=embed_column_b, inline=True)
            if total_length > batch * 2:
                embed_page.set_footer(text=f'Page {self.page + 1} of {total_pages} - {total_length} total')
            self.contents.append(embed_page)
            self.page += 1

        for i in range(0, sd2_length, batch * 2):
            embed_column_a, embed_column_b = '', ''
            embed_page = discord.Embed(title="Список Textual Inversion embeddings",
                                       description=f"{desc}\nThese embeddings are for **SD 2.X** models.",
                                       colour=settings.global_var.embed_color)
            for value in settings.global_var.embeddings_2[i:i + batch]:
                embed_column_a += f'\n``{value}``'
            embed_page.add_field(name='', value=embed_column_a, inline=True)
            i += batch
            for value in settings.global_var.embeddings_2[i:i + batch]:
                embed_column_b += f'\n``{value}``'
            embed_page.add_field(name='', value=embed_column_b, inline=True)
            if total_length > batch * 2:
                embed_page.set_footer(text=f'Page {self.page + 1} of {total_pages} - {total_length} total')
            self.contents.append(embed_page)
            self.page += 1

        self.page = 0

        await interaction.response.edit_message(view=self, embed=self.contents[0])

    @discord.ui.button(
        custom_id="button_tips",
        label="Документация", row=1)
    async def button_tips(self, _button, interaction):
        self.enable_nav_buttons()
        self.page = 0

        embed_tips1 = discord.Embed(title="Документация", description="Добро пожаловать в документацию! Здесь объяснаются основы использования и запросов.",
                                    colour=settings.global_var.embed_color)
        embed_tips1.add_field(name="txt2img", value="Текст в изображение. Используйте команду /draw. Просто опишите, что хотите получить и отправьте запрос!"
                                                          "\nЕсть множество дополнительных опций, но они автоматически устанавливаются согласно предустановок. Они необязательны, но помогают улучшить результат.")
        embed_tips1.add_field(name="img2img", value="Изображение в изображение. Используйте команду /draw, опция **init_img** позволяет загрузить изображение с устройства, а **init_url** использовать ссылку на изображение."
                                                           "\nПомните что **strength** взаимодействует с img2img. Значения от 0.0 до 1.0, большее значение больше воздействует на изображение.")
        embed_tips1.add_field(name="\u200B", value="\u200B")
        embed_tips1.add_field(name="команда /identify", value="Эта команда создаёт описание изображения. Стандартное описание генерируется фразами, а выбрав Тэги выполучте ключевые слова.")
        embed_tips1.add_field(name="команда /upscale", value="Простая команда для увеличения изображения! Выможете увеличить изображение до 4x кратного.")
        embed_tips1.add_field(name="\u200B", value="\u200B")

        embed_tips2 = discord.Embed(title="Базовые подсказки по описанию запросов", colour=settings.global_var.embed_color)
        embed_tips2.add_field(name="prompt",
                              value="Описание запроса. Порядок слов меняет изображение. Написав `cat, dog` выполучите больше кота."
                                   "\nПомните об этом составляя длинное описание.",)
        embed_tips2.add_field(name="Steps",
                              value="Шаги. Как много циклов сделает ИИ для создания изображения. Большее колличество шагов часто ведёт к более удачному изображению, но не всегда!",)
        embed_tips2.add_field(name="\u200B", value="\u200B")
        embed_tips2.add_field(name="Guidance (CFG) Scale",
                              value="отвечает за то, насколько искуственный интеллект должен приблизиться к буквальному изображению запроса. Чем ниже Cfg Scale — тем креативнее будет ИИ. Чем выше Cfg Scale тем более точно ИИ будет пытаться изобразить запрос.",)
        embed_tips2.add_field(name="Seed",
                              value="Это ключ, используемый для генерации изображений. Значения от 0 до 4294967295. Может использоваться для повторной генерации изображения.",)
        embed_tips2.add_field(name="\u200B", value="\u200B")

        embed_tips3 = discord.Embed(title="Основы описания запросов", description="Вот некоторые синтаксы для использования в описаниях.",
                                    colour=settings.global_var.embed_color)
        embed_tips3.add_field(name="Выделения",
                              value="`(word)`- каждое `()` увеличивает внимание к `word` в 1.1x"
                                   "\n`[word]`- каждое `[]` уменьшает внимание к `word` в 1.1x"
                                   "\n`(word:1.5)`- увеличивает внимание к `word` в 1.5x"
                                   "\n`(word:0.25)`- уменьшает внимание к `word` в 4x"
                                   "\n`\\(word\\)`- использует непосредственно символы () в описании.",
                              inline=False)
        embed_tips3.add_field(name="Переход",
                              value="`[word1:word2:steps]`"
                                   "\nПри создании изображения, ИИ начнёт с `word1`, а после указанного значения шагов `steps`, перейдёт на `word2`. Порядок слов важен.",
                              inline=False)
        embed_tips3.add_field(name="Слияние",
                              value="`[word1|word2]`"
                                   "\nПри создании изображения, ИИ будет смешивать word1 и word2. Порядок слов так же важен.",
                              inline=False)

        embed_tips4 = discord.Embed(title="Кнопки", description="Сгенерированные изображения содержат кнопки!",
                                    colour=settings.global_var.embed_color)
        embed_tips4.add_field(name="🖋️",
                              value="Эта кнопка вызывает всплывающее окно, позволяющее изменить некоторые параметры и сгенерировать новые изображения с этими изменениями.")
        embed_tips4.add_field(name="🎲",
                              value="Используйте эту кнопку чтобы сгенерировать другие изображения с теми же параметрами.")
        embed_tips4.add_field(name="\u200B", value="\u200B")
        embed_tips4.add_field(name="📋",
                              value="Эта кнопка показывает информацию о генерации изображенийи даже позволяет скопировать команду для генерации!")
        embed_tips4.add_field(name="❌",
                              value="Крест используется для удаления любых нежелательных изображений. Если эта кнопка не работает, вы можете добавить реакцию ❌ вместо этого.")
        embed_tips4.add_field(name="\u200B", value="\u200B")

        embed_tips5 = discord.Embed(title="Контекстное меню",
                                    description="У вас есть возможность использовать команды из контекстного меню!\n"
                                                "Чтоб использовать эти команды, клик правой кнопкой мышки (или нажать и держать) на любом сообщении. Вы найдёте меня в 'Приложения'.\n"
                                                "\nКонтекстное меню полезно, когда вам необходимо взаимодействие с изображением, но кнопки отсутствуют или не работают, или даже с изображениями, которые созданы не мной.",
                                    colour=settings.global_var.embed_color)
        # For those who fork AIYA, feel free to edit or add to this per your needs,
        # but please don't just delete me from credits and claim my work as yours.
        url = 'https://github.com/Kilvoctu/aiyabot'
        thumb = 'https://github.com/sebaxakerhtc/sebaxakerhtc.github.io/raw/master/images/%D0%9C%D0%B0%D1%80%D1%83%D1%81%D0%B5%D0%BD%D1%8C%D0%BA%D0%B0.png'
        wiki = 'https://github.com/Kilvoctu/aiyabot/wiki#using-aiya'
        embed_tips6 = discord.Embed(title="Дополнительная информация",
                                    description=f"Более подробная документация на английском языкедоступна в [wiki]({wiki}) оригинального проекта [home]({url})!\n\n"
                                                f"Не стесняйтесь делиться ошибками и отзывами! Я - Маруся, Discord бот на базе Python, разработанный *Kilvoctu#1238*. Перевод/Миграция от *sebaxakerhtc*."
                                                f"\n\nНаслаждайтесь созданием ИИ искусств со мной!",
                                    colour=settings.global_var.embed_color)
        embed_tips6.set_thumbnail(url=thumb)
        embed_tips6.set_footer(text='Приятного времяпровождения!', icon_url=thumb)

        self.page = 0
        self.contents = [
            embed_tips1,
            embed_tips2,
            embed_tips3,
            embed_tips4,
            embed_tips5,
            embed_tips6
        ]

        await interaction.response.edit_message(view=self, embed=self.contents[0])

    @discord.ui.button(
        custom_id="button_back", label="◀️", row=1, disabled=True)
    async def button_back(self, _button, interaction):
        try:
            self.page -= 1
            await interaction.response.edit_message(view=self, embed=self.contents[self.page])
        except(Exception,):
            self.page = len(self.contents)-1
            await interaction.response.edit_message(view=self, embed=self.contents[self.page])

    @discord.ui.button(
        custom_id="button_forward", label="▶️", row=1, disabled=True)
    async def button_forward(self, _button, interaction):
        try:
            self.page += 1
            await interaction.response.edit_message(view=self, embed=self.contents[self.page])
        except(Exception,):
            self.page = 0
            await interaction.response.edit_message(view=self, embed=self.contents[self.page])


class InfoCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(InfoView())

    @commands.slash_command(name="info", description="Много полезной информации!")
    async def info(self, ctx):
        first_embed = discord.Embed(title='Выберите кнопку!',
                                    description='Вы можете проверить списки дополнительного контента, загруженного мной!'
                                                '\nТак же проверьте документацию о взаимодействии!',
                                    colour=settings.global_var.embed_color)
        first_embed.set_footer(text='Используйте ◀️ и ▶️ для переключения страниц, когда это доступно')

        await ctx.respond(embed=first_embed, view=InfoView(), ephemeral=True)


def setup(bot):
    bot.add_cog(InfoCog(bot))
