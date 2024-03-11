import base64
import contextlib
import threading
import discord
import io
import math
import random
import requests
import time
import traceback
from PIL import Image, PngImagePlugin
from discord import option
from discord.ext import commands
from typing import Optional

from core import queuehandler
from core import faceviewhandler
from core import settings
from core import settingscog
from threading import Thread

debug_progress = False


async def update_progress(event_loop, status_message_task, s, queue_object, tries=0, any_job=False, tries_since_no_progress=0, last_file=None):
    status_message = status_message_task.result()
    user_id, user_name = settings.fuzzy_get_id_name(queue_object.ctx)
    try:
        progress_data = s.get(url=f'{settings.global_var.url}/sdapi/v1/progress').json()
        job_name = progress_data.get('state').get('job')
        if debug_progress:
            step = progress_data.get("state").get("sampling_step")
            has_last_file = last_file is not None
            print(f'Job: {job_name} | Step: {step} | Tries: {tries} | Any Job: {any_job} | Tries Since No Job: {tries_since_no_progress} | Last File: {has_last_file}')

        if job_name != '':
            any_job = True

        if job_name == '':
            if any_job:
                if tries_since_no_progress >= 2:
                    if debug_progress:
                        print('Exiting progress, no job in last 2 tries')
                    return

                if debug_progress:
                    print(f'No job in try,sleeping for {settings.global_var.preview_update_interval}')
                time.sleep(settings.global_var.preview_update_interval)
                event_loop.create_task(
                    update_progress(event_loop, status_message_task, s, queue_object, tries + 1, any_job, tries_since_no_progress + 1, last_file))
                return
            else:
                # escape hatch
                if tries > 10:
                    if debug_progress:
                        print('escape hatch exit')
                    return

                if debug_progress:
                    print(f'Have not seen a job yet, sleeping for {settings.global_var.preview_update_interval}')
                time.sleep(settings.global_var.preview_update_interval)
                event_loop.create_task(
                    update_progress(event_loop, status_message_task, s, queue_object, tries + 1, any_job, tries_since_no_progress, last_file))
                return

        file = None
        if progress_data["current_image"] is not None:
            if debug_progress:
                print('updating progress => Preview image in progress data')
            image = Image.open(io.BytesIO(base64.b64decode(progress_data["current_image"])))

            with contextlib.ExitStack() as stack:
                buffer = stack.enter_context(io.BytesIO())
                image.save(buffer, 'PNG')
                buffer.seek(0)
                filename = f'{queue_object.seed}.png'
                if queue_object.spoiler:
                    filename = f'SPOILER_{queue_object.seed}.png'
                fp = buffer
                file = discord.File(fp, filename)
                last_file = {
                    'name': filename,
                    'buffer': fp
                }
        elif last_file is not None:
            if debug_progress:
                print('updating progress => No preview image in progress data, but had last_file')
            last_file['buffer'].seek(0)
            file = discord.File(last_file['buffer'], last_file['name'])
        elif debug_progress:
            print('updating progress => No preview or last_image')

        ips = '?'
        if progress_data["eta_relative"] != 0:
            ips = round(
                (int(queue_object.steps) - progress_data["state"]["sampling_step"]) / progress_data["eta_relative"], 2)

        view = faceviewhandler.ProgressView()

        files = []
        if file is not None:
            files = [file]

        await status_message.edit(
            content=f'**Author**: {user_id} ({user_name})\n'
                    f'**Prompt**: `{queue_object.prompt}`\n**Progress**: {round(progress_data.get("progress") * 100, 2)}% '
                    f'\n{progress_data.get("state").get("sampling_step")}/{queue_object.steps} iterations, '
                    f'~{ips} it/s'
                    f'\n**Relative ETA**: {round(progress_data.get("eta_relative"), 2)} seconds',
            files=files, view=view)
    except Exception as e:
        print('Something goes wrong...', str(e))
        if tries_since_no_progress >= 3:
            print('Exiting progress due too many tries without progress')
            return
        time.sleep(settings.global_var.preview_update_interval)
        event_loop.create_task(
            update_progress(event_loop, status_message_task, s, queue_object, tries + 1, any_job, tries_since_no_progress + 1, last_file))
        return

    if debug_progress:
        print(f'sleeping for {settings.global_var.preview_update_interval}')
    time.sleep(settings.global_var.preview_update_interval)
    event_loop.create_task(
        update_progress(event_loop, status_message_task, s, queue_object, tries + 1, any_job, 0, last_file))

class ReactorCog(commands.Cog, name='ReActor extension', description='Fast and Simple Face Swap Extension.'):
    ctx_parse = discord.ApplicationContext

    def __init__(self, bot):
        self.bot = bot

    if len(settings.global_var.size_range) == 0:
        size_auto = discord.utils.basic_autocomplete(settingscog.SettingsCog.size_autocomplete)
    else:
        size_auto = None

    @commands.Cog.listener()
    async def on_ready(self):
        self.bot.add_view(faceviewhandler.DrawView(self))

    @commands.slash_command(name='swapface', description='Replace the face with ReActor', guild_only=True)
    @option(
        'prompt',
        str,
        description='A prompt to condition the model with.',
        required=True,
    )
    @option(
        'negative_prompt',
        str,
        description='Negative prompts to exclude from output.',
        required=False,
    )
    @option(
        'data_model',
        str,
        description='Select the data model for image generation.',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(settingscog.SettingsCog.model_autocomplete),
    )
    @option(
        'steps',
        int,
        description='The amount of steps to sample the model.',
        min_value=1,
        required=False,
    )
    @option(
        'width',
        int,
        description='Width of the generated image.',
        required=False,
        autocomplete=size_auto,
        choices=settings.global_var.size_range
    )
    @option(
        'height',
        int,
        description='Height of the generated image.',
        required=False,
        autocomplete=size_auto,
        choices=settings.global_var.size_range
    )
    @option(
        'guidance_scale',
        str,
        description='Classifier-Free Guidance scale.',
        required=False,
    )
    @option(
        'sampler',
        str,
        description='The sampler to use for generation.',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(settingscog.SettingsCog.sampler_autocomplete),
    )
    @option(
        'seed',
        int,
        description='The seed to use for reproducibility.',
        required=False,
    )
    @option(
        'styles',
        str,
        description='Apply a predefined style to the generation.',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(settingscog.SettingsCog.style_autocomplete),
    )
    @option(
        'extra_net',
        str,
        description='Apply an extra network to influence the output. To set multiplier, add :# (# = 0.0 - 1.0)',
        required=False,
        autocomplete=discord.utils.basic_autocomplete(settingscog.SettingsCog.extra_net_autocomplete),
    )
    @option(
        'clip_skip',
        int,
        description='Number of last layers of CLIP model to skip.',
        required=False,
        choices=[x for x in range(1, 13, 1)]
    )
    @option(
        'strength',
        str,
        description='The amount in which init_image will be altered (0.0 to 1.0). 0.0 is recomended for face swap only'
    )
    @option(
        'init_image',
        discord.Attachment,
        description='The starter image for generation. Remember to set strength value!',
        required=False,
    )
    @option(
        'init_url',
        str,
        description='The starter URL image for generation. This overrides init_image!',
        required=False,
    )
    @option(
        'batch',
        str,
        description='The number of images to generate. Batch format: count,size',
        required=False,
    )
    @option(
        'spoiler',
        bool,
        description='Mark generated image as spoiler?',
        required=False,
    )
    @option(
        'face_model',
        str,
        description='Face model name of object for swaping (without .safetensors). Owerwrites face_url or face_image',
        required=False,
    )
    @option(
        'face_no_source',
        str,
        description='Comma separated face number(s) from swap-source image',
        required=False,
    )
    @option(
        'face_no_target',
        str,
        description='Comma separated face number(s) for target image (result)',
        required=False,
    )
    @option(
        'face_image',
        discord.Attachment,
        description='The face image for swaping. If you want - you can set strength value!',
        required=False,
    )
    @option(
        'face_url',
        str,
        description='The starter URL image for generation. This overrides init_face_image!',
        required=False,
    )
    @option(
        'face_restorer',
        str,
        description='Face resorer: Codeformer or GFPGAN',
        required=False,
        choices=['CodeFormer', 'GFPGAN']
    )
    @option(
        'codeformer_weight',
        str,
        description='CodeFormer weight (0.0 to 1.0).',
        required=False,
    )
    async def dream_handler(self, ctx: discord.ApplicationContext, *,
                            prompt: str, negative_prompt: str = None,
                            data_model: Optional[str] = None,
                            steps: Optional[int] = None,
                            width: Optional[int] = None, height: Optional[int] = None,
                            guidance_scale: Optional[str] = None,
                            sampler: Optional[str] = None,
                            seed: Optional[int] = -1,
                            styles: Optional[str] = None,
                            extra_net: Optional[str] = None,
                            clip_skip: Optional[int] = None,
                            strength: Optional[str] = "0.0",
                            init_image: Optional[discord.Attachment] = None,
                            init_url: Optional[str],
                            batch: Optional[str] = None,
                            spoiler: Optional[bool] = None,
                            face_model: Optional[str] = None,
                            face_no_source: Optional[str] = "0",
                            face_no_target: Optional[str] = "0",
                            face_image: Optional[discord.Attachment] = None,
                            face_url: Optional[str],
                            face_restorer: Optional[str] = "CodeFormer",
                            codeformer_weight: Optional[str] = "0.5"
                            ):

        # update defaults with any new defaults from settingscog
        channel = '% s' % ctx.channel.id
        settings.check(channel)
        if negative_prompt is None:
            negative_prompt = settings.read(channel)['negative_prompt']
        if steps is None:
            steps = settings.read(channel)['steps']
        if width is None:
            width = settings.read(channel)['width']
        if height is None:
            height = settings.read(channel)['height']
        if guidance_scale is None:
            guidance_scale = settings.read(channel)['guidance_scale']
        if sampler is None:
            sampler = settings.read(channel)['sampler']
        if styles is None:
            styles = settings.read(channel)['style']
        if clip_skip is None:
            clip_skip = settings.read(channel)['clip_skip']
        if batch is None:
            batch = settings.read(channel)['batch']
        if spoiler is None:
            spoiler = settings.read(channel)['spoiler']

        derived_spoiler = spoiler
        spoiler_role = settings.read(channel)['spoiler_role']
        if not derived_spoiler and spoiler_role is not None:
            for role in ctx.author.roles:
                if str(role.id) == spoiler_role:
                    derived_spoiler = True
                    break

        # if a model is not selected, do nothing
        model_name = 'Default'
        if data_model is None:
            data_model = settings.read(channel)['data_model']

        simple_prompt = prompt
        # run through mod function if any moderation values are set in config
        clean_negative = negative_prompt
        if settings.global_var.prompt_ban_list or settings.global_var.prompt_ignore_list or settings.global_var.negative_prompt_prefix:
            mod_results = settings.prompt_mod(simple_prompt, negative_prompt)
            if mod_results[0] == "Stop":
                await ctx.respond(f"I'm not allowed to draw the word {mod_results[1]}!", ephemeral=True)
                return
            if mod_results[0] == "Mod":
                if settings.global_var.display_ignored_words == "False":
                    simple_prompt = mod_results[1]
                prompt = mod_results[1]
                negative_prompt = mod_results[2]
                clean_negative = mod_results[3]

        # take selected data_model and get model_name, then update data_model with the full name
        for model in settings.global_var.model_info.items():
            if model[0] == data_model:
                model_name = model[0]
                data_model = model[1][0]
                # look at the model for activator token and prepend prompt with it
                if model[1][3]:
                    prompt = model[1][3] + " " + prompt
                break

        net_multi = 0.85
        if extra_net is not None:
            prompt, extra_net, net_multi = settings.extra_net_check(prompt, extra_net, net_multi)
        prompt = settings.extra_net_defaults(prompt, channel)

        if data_model != '':
            print(f'Request -- {ctx.author.name}#{ctx.author.discriminator}'
                  f' -- Prompt: {prompt} -- Spoiler: {derived_spoiler}')
        else:
            print(f'Request -- {ctx.author.name}#{ctx.author.discriminator}'
                  f' -- Prompt: {prompt} -- Using model: {data_model} -- Spoiler: {derived_spoiler}')


        if seed == -1:
            seed = random.randint(0, 0xFFFFFFFF)

        # url *will* override init image for compatibility, can be changed here
        if init_url:
            try:
                init_image = requests.get(init_url)
            except(Exception,):
                await ctx.send_response('URL image not found!\nI will do my best without it!')
                
        if face_url:
            try:
                face_image = requests.get(face_url)
            except(Exception,):
                await ctx.send_response('URL face image not found!\nI will do my best without it!')

        if face_image is None and face_model is None:
            await ctx.respond(f"I need a face! Add face_model, face_image or face_url", ephemeral=True)
            return

        # verify values and format aiya initial reply
        reply_adds = ''
        if (width != 512) or (height != 512):
            reply_adds += f' - Size: ``{width}``x``{height}``'
        reply_adds += f' - Seed: ``{seed}``'

        # lower step value to the highest setting if user goes over max steps
        if steps > settings.read(channel)['max_steps']:
            steps = settings.read(channel)['max_steps']
            reply_adds += f'\nExceeded maximum of ``{steps}`` steps! This is the best I can do...'
        if model_name != 'Default':
            reply_adds += f'\nModel: ``{model_name}``'
        if clean_negative != settings.read(channel)['negative_prompt']:
            reply_adds += f'\nNegative Prompt: ``{clean_negative}``'
        if guidance_scale != settings.read(channel)['guidance_scale']:
            # try to convert string to Web UI-friendly float
            try:
                guidance_scale = guidance_scale.replace(",", ".")
                float(guidance_scale)
                reply_adds += f'\nGuidance Scale: ``{guidance_scale}``'
            except(Exception,):
                reply_adds += f"\nGuidance Scale can't be ``{guidance_scale}``! Setting to default of `7.0`."
                guidance_scale = 7.0
        if sampler != settings.read(channel)['sampler']:
            reply_adds += f'\nSampler: ``{sampler}``'
        if init_image:
            # try to convert string to Web UI-friendly float
            try:
                strength = strength.replace(",", ".")
                float(strength)
                reply_adds += f'\nStrength: ``{strength}``'
            except(Exception,):
                reply_adds += f"\nStrength can't be ``{strength}``! Setting to default of `0.0`."
                strength = 0.0
            reply_adds += f'\nURL Init Image: ``{init_image.url}``'
        reply_adds += f'\nFace restorer: ``{face_restorer}``'
        if face_restorer == "CodeFormer":
            # try to convert string to Web UI-friendly float
            try:
                codeformer_weight = codeformer_weight.replace(",", ".")
                float(codeformer_weight)
                reply_adds += f'\nCodeFormer weight: ``{codeformer_weight}``'
            except(Exception,):
                reply_adds += f"\nCodeFormer weight can't be ``{codeformer_weight}``! Setting to default of `0.5`."
                codeformer_weight = 0.5
        # try to convert batch to usable format
        batch_check = settings.batch_format(batch)
        batch = list(batch_check)
        if batch[0] != 1 or batch[1] != 1:
            max_batch = settings.batch_format(settings.read(channel)['max_batch'])
            # if only one number is provided, try to generate the requested amount, prioritizing batch size
            if batch[2] == 1:
                # if over the limits, cut the number in half and let AIYA scale down
                total = max_batch[0] * max_batch[1]
                # add hard limit of 10 images until I can figure how to bypass this discord limit - single value edition
                if batch[0] > 10:
                    batch[0] = 10
                    if total > 10:
                        total = 10
                    reply_adds += f"\nI'm currently limited to a max of 10 drawings per post..."
                if batch[0] > total:
                    batch[0] = math.ceil(batch[0] / 2)
                    batch[1] = math.ceil(batch[0] / 2)
                else:
                    # do... math
                    difference = math.ceil(batch[0] / max_batch[1])
                    multiple = int(batch[0] / difference)
                    new_total = difference * multiple
                    requested = batch[0]
                    batch[0], batch[1] = difference, multiple
                    if requested % difference != 0:
                        reply_adds += f"\nI can't draw exactly ``{requested}`` pictures! Settling for ``{new_total}``."
            # check batch values against the maximum limits
            if batch[0] > max_batch[0]:
                reply_adds += f"\nThe max batch count I'm allowed here is ``{max_batch[0]}``!"
                batch[0] = max_batch[0]
            if batch[1] > max_batch[1]:
                reply_adds += f"\nThe max batch size I'm allowed here is ``{max_batch[1]}``!"
                batch[1] = max_batch[1]
                # add hard limit of 10 images until I can figure how to bypass this discord limit - multi value edition
                if batch[0] * batch[1] > 10:
                    while batch[0] * batch[1] > 10:
                        if batch[0] != 1:
                            batch[0] -= 1
                        if batch[1] != 1:
                            batch[1] -= 1
                    reply_adds += f"\nI'm currently limited to a max of 10 drawings per post..."
            reply_adds += f'\nBatch count: ``{batch[0]}`` - Batch size: ``{batch[1]}``'
        if styles != settings.read(channel)['style']:
            reply_adds += f'\nStyle: ``{styles}``'
        if extra_net is not None and extra_net != 'None':
            reply_adds += f'\nExtra network: ``{extra_net}``'
            if net_multi != 0.85:
                reply_adds += f' (multiplier: ``{net_multi}``)'
        if clip_skip != settings.read(channel)['clip_skip']:
            reply_adds += f'\nCLIP skip: ``{clip_skip}``'

        if derived_spoiler or derived_spoiler != settings.read(channel)['spoiler']:
            bool_emoji = ':white_check_mark:' if derived_spoiler else ':negative_squared_cross_mark:'
            reply_adds += f'\nSpoiler: {bool_emoji}'

        epoch_time = int(time.time())

        # set up tuple of parameters to pass into the Discord view
        input_tuple = (
            ctx, simple_prompt, prompt, negative_prompt, data_model, steps, width, height, guidance_scale, sampler,
            seed, strength, init_image, batch, styles, clip_skip, extra_net, derived_spoiler,
            face_model, face_no_source, face_no_target, face_image, face_restorer, codeformer_weight, epoch_time)

        view = faceviewhandler.DrawView(input_tuple)
        # setup the queue
        user_queue_limit = settings.queue_check(ctx.author)
        if queuehandler.GlobalQueue.dream_thread.is_alive():
            if user_queue_limit == "Stop":
                await ctx.send_response(
                    content=f"Please wait! You're past your queue limit of {settings.global_var.queue_limit}.",
                    ephemeral=True)
            else:
                queuehandler.GlobalQueue.queue.append(queuehandler.SwapObject(self, *input_tuple, view))
        else:
            await queuehandler.process_dream(self, queuehandler.SwapObject(self, *input_tuple, view))
        if user_queue_limit != "Stop":
            await ctx.send_response(
                f'<@{ctx.author.id}>, {settings.messages()}\nQueue: ``{len(queuehandler.GlobalQueue.queue)}``'
                f' - ``{simple_prompt}``\nSteps: ``{steps}``{reply_adds}')

    # the function to queue Discord posts
    def post(self, event_loop: queuehandler.GlobalQueue.post_event_loop, post_queue_object: queuehandler.PostObject):
        event_loop.create_task(
            post_queue_object.ctx.channel.send(
                content=post_queue_object.content,
                files=post_queue_object.files,
                view=post_queue_object.view
            )
        )
        if queuehandler.GlobalQueue.post_queue:
            self.post(self.event_loop, self.queue.pop(0))

    # generate the image
    def dream(self, event_loop: queuehandler.GlobalQueue.event_loop, queue_object: queuehandler.SwapObject):
        try:
            start_time = time.time()

            user_id, user_name = settings.fuzzy_get_id_name(queue_object.ctx)
            channel = '% s' % queue_object.ctx.channel.id
            live_preview = settings.read(channel)['live_preview']

            if live_preview:
                status_message_task = event_loop.create_task(queue_object.ctx.channel.send(
                    f'**Author**: {user_id} ({user_name})\n'
                    f'**Prompt**: `{queue_object.prompt}`\n**Progress**: initialization...'
                    f'\n0/{queue_object.steps} iteractions, 0.00 it/s'
                    f'\n**Relative ETA**: initialization...'))

                def worker():
                    event_loop.create_task(update_progress(event_loop, status_message_task, s, queue_object))
                    return

                status_thread = threading.Thread(target=worker)

                def start_thread(*args):
                    status_thread.start()

                status_message_task.add_done_callback(start_thread)

            # ReActor settings:
            face_image = None
            face_model = None
            if queue_object.face_image is not None:
                face_image = base64.b64encode(requests.get(queue_object.face_image.url, stream=True).content).decode('utf-8')
                face_source = 0
            if queue_object.face_model is not None:
                face_model = queue_object.face_model + '.safetensors'
                face_image = None
                face_source = 1
            # ReActor arguments:
            reactorargs=[
                face_image, #0
                True, #1 Enable ReActor
                queue_object.face_no_source, #2 Comma separated face number(s) from swap-source image
                queue_object.face_no_target, #3 Comma separated face number(s) for target image (result)
                'inswapper_128.onnx', #4 model path
                queue_object.face_restorer, #4 Restore Face: None; CodeFormer; GFPGAN
                1, #5 Restore visibility value
                True, #7 Restore face -> Upscale
                None, #8 Upscaler (type 'None' if doesn't need), see full list here: http://127.0.0.1:7860/sdapi/v1/script-info -> reactor -> sec.8
                1, #9 Upscaler scale value
                1, #10 Upscaler visibility (if scale = 1)
                False, #11 Swap in source image
                True, #12 Swap in generated image
                1, #13 Console Log Level (0 - min, 1 - med or 2 - max)
                0, #14 Gender Detection (Source) (0 - No, 1 - Female Only, 2 - Male Only)
                0, #15 Gender Detection (Target) (0 - No, 1 - Female Only, 2 - Male Only)
                False, #16 Save the original image(s) made before swapping
                queue_object.codeformer_weight, #17 CodeFormer Weight (0 = maximum effect, 1 = minimum effect), 0.5 - by default
                True, #18 Source Image Hash Check, True - by default
                False, #19 Target Image Hash Check, False - by default
                "CUDA", #20 CPU or CUDA (if you have it), CPU - by default
                False, #21 Face Mask Correction
                face_source, #22 Select Source, 0 - Image, 1 - Face Model, 2 - Source Folder
                face_model, #23 Filename of the face model (from "models/reactor/faces"), e.g. elena.safetensors, don't forger to set #22 to 1
                None, #24 The path to the folder containing source faces images, don't forger to set #22 to 2
                None, #25 skip it for API
                False, #26 Randomly select an image from the path
                False, #27 Force Upscale even if no face found
                0.5, #28 Face Detection Threshold
                2, #29 Maximum number of faces to detect (0 is unlimited)
            ]

            # construct a payload for data model, then the normal payload
            model_payload = {
                "sd_model_checkpoint": queue_object.data_model
            }
            payload = {
                "prompt": queue_object.prompt,
                "negative_prompt": queue_object.negative_prompt,
                "steps": queue_object.steps,
                "width": queue_object.width,
                "height": queue_object.height,
                "cfg_scale": queue_object.guidance_scale,
                "sampler_index": queue_object.sampler,
                "seed": queue_object.seed,
                "seed_resize_from_h": -1,
                "seed_resize_from_w": -1,
                "denoising_strength": "0.0",
                "n_iter": queue_object.batch[0],
                "batch_size": queue_object.batch[1],
                "styles": [
                    queue_object.styles
                ],
                "restore_faces": False,
                "alwayson_scripts": {"reactor":{"args":reactorargs}}
            }

            # update payload if init_img or init_url is used
            if queue_object.init_image is not None:
                image = base64.b64encode(requests.get(queue_object.init_image.url, stream=True).content).decode('utf-8')
                img_payload = {
                    "init_images": [
                        'data:image/png;base64,' + image
                    ],
                    "denoising_strength": queue_object.strength
                }
                payload.update(img_payload)

            # add any options that would go into the override_settings
            override_settings = {"CLIP_stop_at_last_layers": queue_object.clip_skip}

            # update payload with override_settings
            override_payload = {
                "override_settings": override_settings
            }
            payload.update(override_payload)

            # send normal payload to webui and only send model payload if one is defined
            s = settings.authenticate_user()

            if queue_object.data_model != '':
                s.post(url=f'{settings.global_var.url}/sdapi/v1/options', json=model_payload)
            if queue_object.init_image is not None:
                response = s.post(url=f'{settings.global_var.url}/sdapi/v1/img2img', json=payload)
            else:
                response = s.post(url=f'{settings.global_var.url}/sdapi/v1/txt2img', json=payload)
            response_data = response.json()
            end_time = time.time()

            # create safe/sanitized filename
            keep_chars = (' ', '.', '_')
            file_name = "".join(c for c in queue_object.simple_prompt if c.isalnum() or c in keep_chars).rstrip()
            epoch_time = queue_object.epoch_time

            # save local copy of image and prepare PIL images
            pil_images = []
            for i, image_base64 in enumerate(response_data['images']):
                image = Image.open(io.BytesIO(base64.b64decode(image_base64.split(",", 1)[0])))
                pil_images.append(image)

                # grab png info
                png_payload = {
                    "image": "data:image/png;base64," + image_base64
                }
                png_response = s.post(url=f'{settings.global_var.url}/sdapi/v1/png-info', json=png_payload)

                metadata = PngImagePlugin.PngInfo()
                metadata.add_text("parameters", png_response.json().get("info"))
                str_parameters = png_response.json().get("info")

                epoch_time = int(time.time())
                file_path = f'{settings.global_var.dir}/{epoch_time}-{queue_object.seed}-{file_name[0:120]}-{i}.png'
                if settings.global_var.save_outputs == 'True':
                    image.save(file_path, pnginfo=metadata)
                    print(f'Saved image: {file_path}')

                settings.stats_count(queue_object.batch[0]*queue_object.batch[1])


            # set up discord message
            image_count = len(pil_images)
            if live_preview:
                def post_dream():
                    event_loop.create_task(status_message_task.result().delete())
                Thread(target=post_dream, daemon=True).start()

            noun_descriptor = "drawing" if image_count == 1 else f'{image_count} drawings'
            draw_time = '{0:.3f}'.format(end_time - start_time)
            message = f'my {noun_descriptor} of ``{queue_object.simple_prompt}`` took me ``{draw_time}`` seconds!'

            view = queue_object.view

            # post to discord
            with contextlib.ExitStack() as stack:
                buffer_handles = [stack.enter_context(io.BytesIO()) for _ in pil_images]

                for (pil_image, buffer) in zip(pil_images, buffer_handles):
                    pil_image.save(buffer, 'PNG', pnginfo=metadata)
                    buffer.seek(0)

                files = [discord.File(fp=buffer, filename=f'{queue_object.seed}-{i}.png') for (i, buffer) in
                         enumerate(buffer_handles)]
                if queue_object.spoiler:
                    files = [discord.File(fp=buffer, filename=f'SPOILER_{queue_object.seed}-{i}.png') for (i, buffer) in
                         enumerate(buffer_handles)]
                queuehandler.process_post(
                    self, queuehandler.PostObject(
                        self, queue_object.ctx, content=f'<@{queue_object.ctx.author.id}>, {message}', file='',
                        files=files, embed='', view=view))
        except KeyError as e:
            embed = discord.Embed(title='txt2img failed', description=f'An invalid parameter was found!\n{e}',
                                  color=settings.global_var.embed_color)
            event_loop.create_task(queue_object.ctx.channel.send(embed=embed))
        except Exception as e:
            embed = discord.Embed(title='txt2img failed', description=f'{e}\n{traceback.print_exc()}',
                                  color=settings.global_var.embed_color)
            event_loop.create_task(queue_object.ctx.channel.send(embed=embed))

        # check each queue for any remaining tasks
        queuehandler.process_queue()

def setup(bot):
    bot.add_cog(ReactorCog(bot))

def add_metadata_to_image(image, str_parameters, filename):
    with io.BytesIO() as buffer:
        # setup metadata
        metadata = PngImagePlugin.PngInfo()
        metadata.add_text("parameters", str_parameters)
        # save image to buffer
        image.save(buffer, 'PNG', pnginfo=metadata)

        # reset buffer to beginning and return as bytes
        buffer.seek(0)
        file = discord.File(fp=buffer, filename=filename)

    return file
