import discord
from discord import option
from discord.ext import commands
from typing import Optional

from core import settings


class SettingsCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # pulls from model_names list and makes some sort of dynamic list to bypass Discord 25 choices limit
    # these are used also by stablecog /draw command
    # this also updates list when using /settings "refresh" option
    def model_autocomplete(self: discord.AutocompleteContext):
        return [
            model for model in settings.global_var.model_info
        ]

    # do for any other lists that may exceed 25 values
    def style_autocomplete(self: discord.AutocompleteContext):
        return [
            style for style in settings.global_var.style_names
        ]

    def hyper_autocomplete(self: discord.AutocompleteContext):
        return [
            hyper for hyper in settings.global_var.hyper_names
        ]

    def lora_autocomplete(self: discord.AutocompleteContext):
        return [
            lora for lora in settings.global_var.lora_names
        ]

    def extra_net_autocomplete(self: discord.AutocompleteContext):
        return [
            network for network in settings.global_var.extra_nets
        ]

    def upscaler_autocomplete(self: discord.AutocompleteContext):
        return [
            upscaler for upscaler in settings.global_var.upscaler_names
        ]

    def hires_autocomplete(self: discord.AutocompleteContext):
        return [
            hires for hires in settings.global_var.hires_upscaler_names
        ]

    @commands.slash_command(name='settings', description='Просмотр и изменение настроек по умолчанию для канала', guild_only=True)
    @option(
        'current_settings',
        bool,
        description='Показать текущие настройки для канала.',
        required=False,
    )
    @option(
        'n_prompt',
        str,
        description='Нежелательное описание (напишите "reset" чтоб вернуть к пустому)',
        required=False,
    )
    @option(
        'data_model',
        str,
        description='Модель',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(model_autocomplete),
    )
    @option(
        'steps',
        int,
        description='Колличество шагов',
        min_value=1,
        required=False,
    )
    @option(
        'max_steps',
        int,
        description='Максимальное колличество шагов',
        min_value=1,
        required=False,
    )
    @option(
        'width',
        int,
        description='Ширина изображения',
        required=False,
        choices=[x for x in range(512, 1312, 32)]
    )
    @option(
        'height',
        int,
        description='Высота изображения',
        required=False,
        choices=[x for x in range(512, 1312, 32)]
    )
    @option(
        'guidance_scale',
        str,
        description='Значение CFG Scale.',
        required=False,
    )
    @option(
        'sampler',
        str,
        description='Сэмплер',
        required=False,
        choices=settings.global_var.sampler_names,
    )
    @option(
        'styles',
        str,
        description='Стиль',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(style_autocomplete),
    )
    @option(
        'hypernet',
        str,
        description='Гиперсеть',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(hyper_autocomplete),
    )
    @option(
        'lora',
        str,
        description='LoRA',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(lora_autocomplete),
    )
    @option(
        'facefix',
        str,
        description='Восстановление лиц.',
        required=False,
        choices=settings.global_var.facefix_models,
    )
    @option(
        'highres_fix',
        str,
        description='Увеличениие разрешения',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(hires_autocomplete),
    )
    @option(
        'clip_skip',
        int,
        description='CLIP skip',
        required=False,
        choices=[x for x in range(1, 13, 1)]
    )
    @option(
        'strength',
        str,
        description='Сила (для init_img) в пределах (0.0 to 1.0).'
    )
    @option(
        'batch',
        str,
        description='batch (компановка) (колличество,размер)',
        required=False,
    )
    @option(
        'max_batch',
        str,
        description='Максимальный batch (компановка) (колличество,размер)',
        required=False,
    )
    @option(
        'upscaler_1',
        str,
        description='Модель увеличения изображения.',
        required=True,
        autocomplete=discord.utils.basic_autocomplete(upscaler_autocomplete),
    )
    @option(
        'refresh',
        bool,
        description='Используйте для обновления всех списков (модели, стили, embeddings, и т.д.)',
        required=False,
    )
    async def settings_handler(self, ctx,
                               current_settings: Optional[bool] = True,
                               n_prompt: Optional[str] = None,
                               data_model: Optional[str] = None,
                               steps: Optional[int] = None,
                               max_steps: Optional[int] = 1,
                               width: Optional[int] = None, height: Optional[int] = None,
                               guidance_scale: Optional[str] = None,
                               sampler: Optional[str] = None,
                               styles: Optional[str] = None,
                               hypernet: Optional[str] = None,
                               lora: Optional[str] = None,
                               facefix: Optional[str] = None,
                               highres_fix: Optional[str] = None,
                               clip_skip: Optional[int] = None,
                               strength: Optional[str] = None,
                               batch: Optional[str] = None,
                               max_batch: Optional[str] = None,
                               upscaler_1: Optional[str] = None,
                               refresh: Optional[bool] = False):
        # get the channel id and check if a settings file exists
        channel = '% s' % ctx.channel.id
        settings.check(channel)
        reviewer = settings.read(channel)
        # create the embed for the reply
        embed = discord.Embed(title="Все настройки канала", description="")
        embed.set_footer(text=f'id канала: {channel}')
        embed.colour = settings.global_var.embed_color
        current, new, new_n_prompt = '', '', ''
        dummy_prompt, lora_multi, hyper_multi = '', 0.85, 0.85
        set_new = False

        if current_settings:
            cur_set = settings.read(channel)
            for key, value in cur_set.items():
                if key == 'negative_prompt':
                    pass
                else:
                    if value == '':
                        value = ' '
                    current += f'\n{key} - ``{value}``'
            embed.add_field(name=f'Текущие значения', value=current, inline=True)
            # put negative prompt on new field for hosts who like massive negative prompts
            cur_n_prompt = f'{cur_set["negative_prompt"]}'
            if cur_n_prompt == '':
                cur_n_prompt = ' '
            elif len(cur_n_prompt) > 1024:
                cur_n_prompt = f'{cur_n_prompt[:1010]}....'
            embed.add_field(name=f'Нежелательное описание', value=f'``{cur_n_prompt}``', inline=True)

        # run function to update global variables
        if refresh:
            settings.global_var.model_info.clear()
            settings.global_var.sampler_names.clear()
            settings.global_var.facefix_models.clear()
            settings.global_var.style_names.clear()
            settings.global_var.embeddings_1.clear()
            settings.global_var.embeddings_2.clear()
            settings.global_var.hyper_names.clear()
            settings.global_var.lora_names.clear()
            settings.global_var.upscaler_names.clear()
            settings.populate_global_vars()
            embed.add_field(name=f'Обновлено!', value=f'Все списки обновлены', inline=False)

        # run through each command and update the defaults user selects
        if n_prompt is not None:
            new_n_prompt = f'{n_prompt}'
            if n_prompt == 'reset':
                n_prompt = ''
                new_n_prompt = ' '
            elif len(new_n_prompt) > 1024:
                new_n_prompt = f'{new_n_prompt[:1010]}....'
            settings.update(channel, 'negative_prompt', n_prompt)

        if data_model is not None:
            settings.update(channel, 'data_model', data_model)
            new += f'\nМодель: ``"{data_model}"``'
            set_new = True

        if max_steps != 1:
            settings.update(channel, 'max_steps', max_steps)
            new += f'\nМаксимум шагов: ``{max_steps}``'
            # automatically lower default steps if max steps goes below it
            if max_steps < reviewer['steps']:
                settings.update(channel, 'steps', max_steps)
                new += f'\nСлишком большое значение шагов! Снижаю до ``{max_steps}``.'
            set_new = True

        if width is not None:
            settings.update(channel, 'width', width)
            new += f'\nШирина: ``"{width}"``'
            set_new = True

        if height is not None:
            settings.update(channel, 'height', height)
            new += f'\nВысота: ``"{height}"``'
            set_new = True

        if guidance_scale is not None:
            try:
                float(guidance_scale)
                settings.update(channel, 'guidance_scale', guidance_scale)
                new += f'\nGuidance Scale: ``{guidance_scale}``'
            except(Exception,):
                settings.update(channel, 'guidance_scale', '7.0')
                new += f'\nНе удалось установить Guidance Scale! Устанавливаю по умолчанию `7.0`.'
            set_new = True

        if sampler is not None:
            settings.update(channel, 'sampler', sampler)
            new += f'\nСэмплер: ``"{sampler}"``'
            set_new = True

        if styles is not None:
            settings.update(channel, 'style', styles)
            new += f'\nСтиль: ``"{styles}"``'
            set_new = True

        if facefix is not None:
            settings.update(channel, 'facefix', facefix)
            new += f'\nВосстановление лиц: ``"{facefix}"``'
            set_new = True

        if highres_fix is not None:
            settings.update(channel, 'highres_fix', highres_fix)
            new += f'\nУвеличение изображения: ``"{highres_fix}"``'
            set_new = True

        if clip_skip is not None:
            settings.update(channel, 'clip_skip', clip_skip)
            new += f'\nCLIP skip: ``{clip_skip}``'
            set_new = True

        if hypernet is not None:
            message = ''
            if ':' in hypernet:
                dummy_prompt, hypernet, hyper_multi = settings.extra_net_check(dummy_prompt, hypernet, hyper_multi)
                settings.update(channel, 'hypernet_multi', hyper_multi)
                message = f' (multiplier: ``{hyper_multi}``)'
            settings.update(channel, 'hypernet', hypernet)
            new += f'\nГиперсеть: ``"{hypernet}"``{message}'
            set_new = True

        if lora is not None:
            message = ''
            if ':' in lora:
                dummy_prompt, lora, lora_multi = settings.extra_net_check(dummy_prompt, lora, lora_multi)
                settings.update(channel, 'lora_multi', lora_multi)
                message = f' (multiplier: ``{lora_multi}``)'
            settings.update(channel, 'lora', lora)
            new += f'\nLoRA: ``"{lora}"``{message}'
            set_new = True

        if strength is not None:
            settings.update(channel, 'strength', strength)
            new += f'\nСила: ``"{strength}"``'
            set_new = True

        if upscaler_1 is not None:
            settings.update(channel, 'upscaler_1', upscaler_1)
            new += f'\nУвеличение изображений 1: ``"{upscaler_1}"``'
            set_new = True

        if max_batch is not None:
            batch_check = settings.batch_format(reviewer['batch'])
            max_batch = settings.batch_format(max_batch)

            settings.update(channel, 'max_batch', f'{max_batch[0]},{max_batch[1]}')
            new += f'\nМаксимальный batch (колличество,размер): ``{max_batch[0]},{max_batch[1]}``'
            # automatically lower default batch if max batch goes below it
            if max_batch[0] < batch_check[0]:
                settings.update(channel, 'batch', f'{max_batch[0]},{batch_check[1]}')
                new += f'\nКолличество batch слишком большое! Снижаю до ``{max_batch[0]}``.'
            if max_batch[1] < batch_check[1]:
                if max_batch[0] < batch_check[0]:
                    settings.update(channel, 'batch', f'{max_batch[0]},{max_batch[1]}')
                else:
                    settings.update(channel, 'batch', f'{batch_check[0]},{max_batch[1]}')
                new += f'\nРазмер batch слишком большой! Снижаю до ``{max_batch[1]}``.'
            set_new = True

        # review settings again in case user is trying to set steps/counts and max steps/counts simultaneously
        reviewer = settings.read(channel)
        if steps is not None:
            if steps > reviewer['max_steps']:
                new += f"\nМаксимум шагов ``{reviewer['max_steps']}``! Вы не можете установить больше!"
            else:
                settings.update(channel, 'steps', steps)
                new += f'\nШаги: ``{steps}``'
            set_new = True

        if batch is not None:
            batch = settings.batch_format(batch)
            max_batch_check = settings.batch_format(reviewer['max_batch'])

            if batch[0] > max_batch_check[0]:
                new += f"\nМаксимальное колличесво batch ``{max_batch_check[0]}``! Вы не можете установить больше!"
            elif batch[1] > max_batch_check[1]:
                new += f"\nМаксимальный размер batch ``{max_batch_check[1]}``! Вы не можете установить больше!"
            else:
                settings.update(channel, 'batch', f'{batch[0]},{batch[1]}')
                new += f'\nbatch (колличество,размер): ``{batch[0]},{batch[1]}``'
            set_new = True

        if set_new:
            embed.add_field(name=f'Новые значения', value=new, inline=False)
        if new_n_prompt:
            embed.add_field(name=f'Новое нежелательное описание', value=f'``{new_n_prompt}``', inline=False)

        await ctx.send_response(embed=embed, ephemeral=True)


def setup(bot):
    bot.add_cog(SettingsCog(bot))
