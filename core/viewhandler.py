import discord
import random
import re
import requests
from discord.ui import InputText, Modal, View

from core import ctxmenuhandler
from core import infocog
from core import queuehandler
from core import settings
from core import stablecog

'''
The input_tuple index reference
input_tuple[0] = ctx
[1] = simple_prompt
[2] = prompt
[3] = negative_prompt
[4] = data_model
[5] = steps
[6] = width
[7] = height
[8] = guidance_scale
[9] = sampler
[10] = seed
[11] = strength
[12] = init_image
[13] = batch
[14] = style
[15] = facefix
[16] = highres_fix
[17] = clip_skip
[18] = extra_net
'''
tuple_names = ['ctx', 'simple_prompt', 'prompt', 'negative_prompt', 'data_model', 'steps', 'width', 'height',
               'guidance_scale', 'sampler', 'seed', 'strength', 'init_image', 'batch', 'styles', 'facefix',
               'highres_fix', 'clip_skip', 'extra_net']


# the modal that is used for the 🖋 button
class DrawModal(Modal):
    def __init__(self, input_tuple) -> None:
        super().__init__(title="Change Prompt!")
        self.input_tuple = input_tuple

        # run through mod function to get clean negative since I don't want to add it to stablecog tuple
        self.clean_negative = input_tuple[3]
        if settings.global_var.negative_prompt_prefix:
            mod_results = settings.prompt_mod(input_tuple[2], input_tuple[3])
            if settings.global_var.negative_prompt_prefix and mod_results[0] == "Mod":
                self.clean_negative = mod_results[3]

        self.add_item(
            InputText(
                label='Описание запроса',
                value=input_tuple[1],
                style=discord.InputTextStyle.long
            )
        )
        self.add_item(
            InputText(
                label='Нежелательное описание запроса(необязательно)',
                style=discord.InputTextStyle.long,
                value=self.clean_negative,
                required=False
            )
        )
        self.add_item(
            InputText(
                label='Тот же seed? Удалите для случайного значения',
                style=discord.InputTextStyle.short,
                value=input_tuple[10],
                required=False
            )
        )

        # set up parameters for full edit mode. first get model display name
        display_name = 'Default'
        index_start = 5
        for model in settings.global_var.model_info.items():
            if model[1][0] == input_tuple[4]:
                display_name = model[0]
                break
        # expose each available (supported) option, even if output didn't use them
        ex_params = f'data_model:{display_name}'
        for index, value in enumerate(tuple_names[index_start:], index_start):
            if index == 10 or 12 <= index <= 13 or index == 16:
                continue
            ex_params += f'\n{value}:{input_tuple[index]}'

        self.add_item(
            InputText(
                label='Расширеннэ настройки (для продвинутых!)',
                style=discord.InputTextStyle.long,
                value=ex_params,
                required=False
            )
        )

    async def callback(self, interaction: discord.Interaction):
        # update the tuple with new prompts
        pen = list(self.input_tuple)
        pen[2] = pen[2].replace(pen[1], self.children[0].value)
        pen[1] = self.children[0].value
        pen[3] = self.children[1].value

        # update the tuple new seed (random if invalid value set)
        try:
            pen[10] = int(self.children[2].value)
        except ValueError:
            pen[10] = random.randint(0, 0xFFFFFFFF)
        if (self.children[2].value == "-1") or (self.children[2].value == ""):
            pen[10] = random.randint(0, 0xFFFFFFFF)

        # prepare a validity checker
        new_model, new_token, bad_input = '', '', ''
        model_found = False
        invalid_input = False
        infocog_view = infocog.InfoView()
        net_multi, new_net_multi = 0.85, 0
        embed_err = discord.Embed(title="Я не могу перерисовать это!", description="")
        # if extra network is used, find the multiplier
        if pen[18]:
            if pen[18] in pen[2]:
                net_multi = re.search(f'{pen[18]}:(.*)>', pen[2]).group(1)

        # iterate through extended edit for any changes
        for line in self.children[3].value.split('\n'):
            if 'data_model:' in line:
                new_model = line.split(':', 1)[1]
                # if keeping the "Default" model, don't attempt a model swap
                if new_model == 'Default':
                    pass
                else:
                    for model in settings.global_var.model_info.items():
                        if model[0] == new_model:
                            pen[4] = model[1][0]
                            model_found = True
                            # grab the new activator token
                            new_token = f'{model[1][3]} '.lstrip(' ')
                            break
                    if not model_found:
                        embed_err.add_field(name=f"`{line.split(':', 1)[1]}` не найдено.",
                                            value="Я использовала команду info для вас! Попробуйте одну из этих моделей!")
                        await interaction.response.send_message(embed=embed_err, ephemeral=True)
                        await infocog.InfoView.button_model(infocog_view, '', interaction)
                        return

            if 'steps:' in line:
                max_steps = settings.read('% s' % pen[0].channel.id)['max_steps']
                if 0 < int(line.split(':', 1)[1]) <= max_steps:
                    pen[5] = line.split(':', 1)[1]
                else:
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` значение шагов за границей доступных!",
                                        value=f"Шаги должны быть между `0` и `{max_steps}`.", inline=False)
            if 'width:' in line:
                try:
                    pen[6] = int(line.split(':', 1)[1])
                except(Exception,):
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` неподходящая ширина! Вот ширина, которая может быть.",
                                        value=', '.join(['`%s`' % x for x in settings.global_var.size_range]),
                                        inline=False)
            if 'height:' in line:
                try:
                    pen[7] = int(line.split(':', 1)[1])
                except(Exception,):
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` неподходящая высота! Вот высота, которая может быть.",
                                        value=', '.join(['`%s`' % x for x in settings.global_var.size_range]),
                                        inline=False)
            if 'guidance_scale:' in line:
                try:
                    pen[8] = float(line.split(':', 1)[1].replace(",", "."))
                except(Exception,):
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` не подходит для guidance scale!",
                                        value='Убедитесь, что вводите цифры.', inline=False)
            if 'sampler:' in line:
                if line.split(':', 1)[1] in settings.global_var.sampler_names:
                    pen[9] = line.split(':', 1)[1]
                else:
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` не распознан. Мне известны следущие сэмплеры!",
                                        value=', '.join(['`%s`' % x for x in settings.global_var.sampler_names]),
                                        inline=False)
            if 'strength:' in line:
                try:
                    pen[11] = float(line.split(':', 1)[1].replace(",", "."))
                except(Exception,):
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` не подходит для силы!.",
                                        value='Убедитесь, что вводите цифры (предпочтительно от 0.0 до 1.0).',
                                        inline=False)
            if 'styles:' in line:
                if line.split(':', 1)[1] in settings.global_var.style_names.keys():
                    pen[14] = line.split(':', 1)[1]
                else:
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` не мой стиль.",
                                        value="Я загрузила список стилей для вас используя команду info!")
                    await interaction.response.send_message(embed=embed_err, ephemeral=True)
                    await infocog.InfoView.button_style(infocog_view, '', interaction)
                    return

            if 'facefix:' in line:
                if line.split(':', 1)[1] in settings.global_var.facefix_models:
                    pen[15] = line.split(':', 1)[1]
                else:
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` невозможно восстановить лица! У меня есть предложения.",
                                        value=', '.join(['`%s`' % x for x in settings.global_var.facefix_models]),
                                        inline=False)
            if 'clip_skip:' in line:
                try:
                    pen[17] = [x for x in range(1, 14, 1) if x == int(line.split(':', 1)[1])][0]
                except(Exception,):
                    invalid_input = True
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` слишком много CLIP для пропуска!",
                                        value='Значение должно быть от `1` до `12`.', inline=False)
            if 'extra_net:' in line:
                if line.count(':') == 2:
                    net_check = re.search(':(.*):', line).group(1)
                    if net_check in settings.global_var.extra_nets:
                        pen[18] = line.split(':', 1)[1]
                elif line.count(':') == 1 and line.split(':', 1)[1] in settings.global_var.extra_nets:
                    pen[18] = line.split(':', 1)[1]
                else:
                    embed_err.add_field(name=f"`{line.split(':', 1)[1]}` неизвестная extra network!",
                                        value="Я использовала команду info для вас! Пожалуйста проверьте гиперсети и LoRAs.")
                    await interaction.response.send_message(embed=embed_err, ephemeral=True)
                    await infocog.InfoView.button_hyper(infocog_view, '', interaction)
                    return

        # stop and give a useful message if any extended edit values aren't recognized
        if invalid_input:
            await interaction.response.send_message(embed=embed_err, ephemeral=True)
        else:
            # run through mod function if any moderation values are set in config
            new_clean_negative = ''
            if settings.global_var.prompt_ban_list or settings.global_var.prompt_ignore_list or settings.global_var.negative_prompt_prefix:
                mod_results = settings.prompt_mod(self.children[0].value, self.children[1].value)
                if settings.global_var.prompt_ban_list and mod_results[0] == "Stop":
                    await interaction.response.send_message(f"Мне не позволено использовать слово {mod_results[1]}!", ephemeral=True)
                    return
                if settings.global_var.prompt_ignore_list or settings.global_var.negative_prompt_prefix and mod_results[0] == "Mod":
                    if settings.global_var.display_ignored_words == "False":
                        pen[1] = mod_results[1]
                    pen[2] = mod_results[1]
                    pen[3] = mod_results[2]
                    new_clean_negative = mod_results[3]

            # update the prompt again if a valid model change is requested
            if model_found:
                pen[2] = new_token + pen[1]
            # figure out what extra_net was used
            if pen[18] != 'None':
                pen[2], pen[18], new_net_multi = settings.extra_net_check(pen[2], pen[18], net_multi)
            channel = '% s' % pen[0].channel.id
            pen[2] = settings.extra_net_defaults(pen[2], channel)
            # set batch to 1
            if settings.global_var.batch_buttons == "False":
                pen[13] = [1, 1]

            # the updated tuple to send to queue
            prompt_tuple = tuple(pen)
            draw_dream = stablecog.StableCog(self)

            # message additions if anything was changed
            prompt_output = f'\nНовое описание: ``{pen[1]}``'
            if new_clean_negative != '' and new_clean_negative != self.clean_negative:
                prompt_output += f'\nНовое нежелательное описание: ``{new_clean_negative}``'
            if str(pen[4]) != str(self.input_tuple[4]):
                prompt_output += f'\nНовая модель: ``{new_model}``'
            index_start = 5
            for index, value in enumerate(tuple_names[index_start:], index_start):
                if index == 13 or index == 16 or index == 18:
                    continue
                if str(pen[index]) != str(self.input_tuple[index]):
                    prompt_output += f'\nНовое значение {value}: ``{pen[index]}``'
            if str(pen[18]) != 'None':
                if str(pen[18]) != str(self.input_tuple[18]) and new_net_multi != net_multi or new_net_multi != net_multi:
                    prompt_output += f'\nНовая extra network: ``{pen[18]}`` (multiplier: ``{new_net_multi}``)'
                elif str(pen[18]) != str(self.input_tuple[18]):
                    prompt_output += f'\nНовая extra network: ``{pen[18]}``'

            print(f'Redraw -- {interaction.user.name}#{interaction.user.discriminator} -- Prompt: {pen[1]}')

            # check queue again, but now we know user is not in queue
            if queuehandler.GlobalQueue.dream_thread.is_alive():
                queuehandler.GlobalQueue.queue.append(queuehandler.DrawObject(stablecog.StableCog(self), *prompt_tuple, DrawView(prompt_tuple)))
            else:
                await queuehandler.process_dream(draw_dream, queuehandler.DrawObject(stablecog.StableCog(self), *prompt_tuple, DrawView(prompt_tuple)))
            await interaction.response.send_message(f'<@{interaction.user.id}>, {settings.messages()}\nЗапрос: ``{len(queuehandler.GlobalQueue.queue)}``{prompt_output}')
            
            
# view that holds the interrupt button for progress
class ProgressView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        custom_id="button-interrupt",
        emoji="❌"
    )
    async def interrupt(self, button, interaction):
        try:
            if str(interaction.user.id) not in interaction.message.content:
                await interaction.response.send_message("Я не могу прекратить процесс других людей!", ephemeral=True)
                return
            button.disabled = True
            s = requests.Session()
            s.post(url=f'{settings.global_var.url}/sdapi/v1/interrupt')
            await interaction.message.delete()
        except Exception as e:
            button.disabled = True
            await interaction.response.send_message("Не знаю, почему, но я сломалась. Может быть запрос потерялся "
                                                    "где-то "
                                                    "или у меня в кеше больше нет сообщения.\n"
                                                    f"Удачи:\n`{str(e)}`", ephemeral=True)

# creating the view that holds the buttons for /draw output
class DrawView(View):
    def __init__(self, input_tuple):
        super().__init__(timeout=None)
        self.input_tuple = input_tuple

    # the 🖋 button will allow a new prompt and keep same parameters for everything else
    @discord.ui.button(
        custom_id="button_re-prompt",
        emoji="🖋")
    async def button_draw(self, button, interaction):
        try:
            # check if the output is from the person who requested it
            if interaction.user.id == self.input_tuple[0].author.id:
                # if there's room in the queue, open up the modal
                user_queue_limit = settings.queue_check(interaction.user)
                if queuehandler.GlobalQueue.dream_thread.is_alive():
                    if user_queue_limit == "Stop":
                        await interaction.response.send_message(content=f"Пожалуйста, ждите! Вы исчерпали лимит запросов: {settings.global_var.queue_limit}.", ephemeral=True)
                    else:
                        await interaction.response.send_modal(DrawModal(self.input_tuple))
                else:
                    await interaction.response.send_modal(DrawModal(self.input_tuple))
            else:
                await interaction.response.send_message("Вы не можете использовать 🖋 других людей!", ephemeral=True)
        except Exception as e:
            print('The pen button broke: ' + str(e))
            # if interaction fails, assume it's because aiya restarted (breaks buttons)
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("Вероятно я была перезапущена. Эта кнопка больше не работает.", ephemeral=True)

    # the 🎲 button will take the same parameters for the image, change the seed, and add a task to the queue
    @discord.ui.button(
        custom_id="button_re-roll",
        emoji="🎲")
    async def button_roll(self, button, interaction):
        try:
            # check if the output is from the person who requested it
            if interaction.user.id == self.input_tuple[0].author.id:
                # update the tuple with a new seed
                new_seed = list(self.input_tuple)
                new_seed[10] = random.randint(0, 0xFFFFFFFF)
                # set batch to 1
                if settings.global_var.batch_buttons == "False":
                    new_seed[13] = [1, 1]
                seed_tuple = tuple(new_seed)

                print(f'Reroll -- {interaction.user.name}#{interaction.user.discriminator} -- Prompt: {seed_tuple[1]}')

                # set up the draw dream and do queue code again for lack of a more elegant solution
                draw_dream = stablecog.StableCog(self)
                user_queue_limit = settings.queue_check(interaction.user)
                if queuehandler.GlobalQueue.dream_thread.is_alive():
                    if user_queue_limit == "Stop":
                        await interaction.response.send_message(content=f"Пожалуйста, ждите! Вы исчерпали лимит запросов: {settings.global_var.queue_limit}.", ephemeral=True)
                    else:
                        queuehandler.GlobalQueue.queue.append(queuehandler.DrawObject(stablecog.StableCog(self), *seed_tuple, DrawView(seed_tuple)))
                else:
                    await queuehandler.process_dream(draw_dream, queuehandler.DrawObject(stablecog.StableCog(self), *seed_tuple, DrawView(seed_tuple)))

                if user_queue_limit != "Stop":
                    await interaction.response.send_message(
                        f'<@{interaction.user.id}>, {settings.messages()}\nЗапрос: '
                        f'``{len(queuehandler.GlobalQueue.queue)}`` - ``{seed_tuple[1]}``'
                        f'\nНовый Seed:``{seed_tuple[10]}``')
            else:
                await interaction.response.send_message("Вы не можете использовать 🎲 других людей!", ephemeral=True)
        except Exception as e:
            print('The dice roll button broke: ' + str(e))
            # if interaction fails, assume it's because aiya restarted (breaks buttons)
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("Вероятно я была перезапущена. Эта кнопка больше не работает.", ephemeral=True)

    # the 📋 button will let you review the parameters of the generation
    @discord.ui.button(
        custom_id="button_review",
        emoji="📋")
    async def button_review(self, button, interaction):
        # reuse "read image info" command from ctxmenuhandler
        init_url = None
        try:
            attachment = self.message.attachments[0]
            if self.input_tuple[12]:
                init_url = self.input_tuple[12].url
            embed = await ctxmenuhandler.parse_image_info(init_url, attachment.url, "button")
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            print('The clipboard button broke: ' + str(e))
            # if interaction fails, assume it's because aiya restarted (breaks buttons)
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("Вероятно я была перезапущена. Эта кнопка больше не работает.\n"
                                            "Вы можете получить информацию об изображении в контекстном меню или через **/identify**.",
                                            ephemeral=True)

    # the button to delete generated images
    @discord.ui.button(
        custom_id="button_x",
        emoji="❌")
    async def delete(self, button, interaction):
        try:
            # check if the output is from the person who requested it
            if interaction.user.id == self.input_tuple[0].author.id:
                await interaction.message.delete()
            else:
                await interaction.response.send_message("Вы не можете удалять изображения других людей!", ephemeral=True)
        except(Exception,):
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("Вероятно я была перезапущена. Эта кнопка больше не работает.\n"
                                            "Вы можете поставить реакцию ❌ для удаления изображений.", ephemeral=True)


class DeleteView(View):
    def __init__(self, input_tuple):
        super().__init__(timeout=None)
        self.input_tuple = input_tuple

    @discord.ui.button(
        custom_id="button_x_solo",
        emoji="❌")
    async def delete(self, button, interaction):
        try:
            # check if the output is from the person who requested it
            if interaction.user.id == self.input_tuple[0].author.id:
                await interaction.message.delete()
            else:
                await interaction.response.send_message("Вы не можете удалять изображения других людей!", ephemeral=True)
        except(Exception,):
            button.disabled = True
            await interaction.response.edit_message(view=self)
            await interaction.followup.send("Вероятно я была перезапущена. Эта кнопка больше не работает.\n"
                                            "Вы можете поставить реакцию ❌ для удаления изображений.", ephemeral=True)
