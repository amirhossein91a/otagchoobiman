# -*- coding: utf-8 -*-

import os
import random
import re
import threading
import zipfile
import shutil
from urllib.request import urlretrieve

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, FadeTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.slider import Slider
from kivy.uix.progressbar import ProgressBar
from kivy.core.audio import SoundLoader
from kivy.core.window import Window
from kivy.utils import get_color_from_hex, platform
from kivy.core.text import LabelBase
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.animation import Animation

import arabic_reshaper
from bidi.algorithm import get_display


FONT_FARSI_PATH = os.path.join('assets', 'fonts', 'vazir.ttf')
if os.path.exists(FONT_FARSI_PATH):
    LabelBase.register(name='FarsiFont', fn_regular=FONT_FARSI_PATH)
else:
    print(f"Warning: Farsi font file not found at {FONT_FARSI_PATH}")

FONT_ENGLISH_PATH = os.path.join('assets', 'fonts', 'english.ttf')
if os.path.exists(FONT_ENGLISH_PATH):
    LabelBase.register(name='EnglishFont', fn_regular=FONT_ENGLISH_PATH)
else:
    print(f"Warning: English font file not found at {FONT_ENGLISH_PATH}")


ARABIC_RE = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')


def format_text_and_font(text):
    if not text:
        return "", 'FarsiFont'

    if ARABIC_RE.search(text):
        try:
            reshaped = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped)
            return bidi_text, 'FarsiFont'
        except Exception as e:
            print(f"Error reshaping text: {e}")
            return text, 'FarsiFont'

    return text, 'EnglishFont'


COLOR_BG = get_color_from_hex('#F9F5F0')
COLOR_CARD = get_color_from_hex('#FFFFFF')
COLOR_WOOD_LIGHT = get_color_from_hex('#A27B5C')
COLOR_WOOD_DARK = get_color_from_hex('#634832')
COLOR_TEXT = get_color_from_hex('#3E2723')
COLOR_LIGHT_TEXT = get_color_from_hex('#FFFFFF')


CATEGORIES = {
    '01_morning_light': {'title': 'پنجره صبح', 'desc': 'شروعی آرام با نور سپیده دم و صدای زهی ملایم.'},
    '02_warm_sunset': {'title': 'غروب چوبی', 'desc': 'گرمی خورشید در حال فرورفتن در میان شاخه‌های درختان.'},
    '03_study_corner': {'title': 'کنج مطالعه', 'desc': 'تمرکزی عمیق در میان کتاب‌های قدیمی و بوی کاغذ.'},
    '04_night_lamp': {'title': 'چراغ روشن', 'desc': 'آرامش شبانه زیر نور زرد و گرم چراغ مطالعه.'},
    '05_pure_reverie': {'title': 'خیال', 'desc': 'سفری کوتاه به دنیای رویاهای بی‌پایان.'},
    '06_rainy_glass': {'title': 'باران پشت شیشه', 'desc': 'صدای برخورد قطرات با شیشه و ملودی‌های غمگین و زیبا.'},
    '07_fire_whisper': {'title': 'نجوای هیزم', 'desc': 'صدای ترک خوردن هیزم در شومینه و ویولن‌سل آرام.'}
}


AUDIO_ZIP_URL = "http://192.168.1.103:8000/audio.zip"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
AUDIO_DIR = os.path.join(ASSETS_DIR, 'audio')
ZIP_PATH = os.path.join(BASE_DIR, 'audio.zip')
TEMP_EXTRACT_DIR = os.path.join(BASE_DIR, '_audio_extract_temp')


def has_audio_assets():
    return os.path.exists(AUDIO_DIR) and any(os.listdir(AUDIO_DIR))


def find_audio_folder(root_dir):
    direct = os.path.join(root_dir, 'audio')
    if os.path.exists(direct):
        return direct

    for root, dirs, files in os.walk(root_dir):
        if os.path.basename(root) == 'audio':
            return root

    return None


class RoundedButton(Button):
    def __init__(self, bg_color=(0.4, 0.3, 0.2, 1), radius=14, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_down = ''
        self.background_color = (0, 0, 0, 0)
        self._bg_color = bg_color
        self._radius = radius

        with self.canvas.before:
            Color(*self._bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])

        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self._rect.pos = self.pos
        self._rect.size = self.size

    def set_bg_color(self, color):
        self._bg_color = color
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._bg_color)
            self._rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])


class InfoDrawer(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 0
        self.opacity = 0
        self.padding = [15, 15, 15, 15]
        self.spacing = 8

        with self.canvas.before:
            Color(*COLOR_CARD)
            self.bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[18, 18, 18, 18])
            Color(0.2, 0.1, 0, 0.1)
            self.border = RoundedRectangle(pos=self.pos, size=self.size, radius=[18, 18, 18, 18])

        self.bind(pos=self._update_bg, size=self._update_bg)

        self.title_lbl = Label(
            text='',
            font_name='FarsiFont',
            color=COLOR_TEXT,
            font_size='18sp',
            bold=True,
            size_hint_y=0.3,
            halign='center'
        )

        self.desc_lbl = Label(
            text='',
            font_name='FarsiFont',
            color=COLOR_TEXT,
            font_size='14sp',
            size_hint_y=0.7,
            halign='center',
            valign='middle'
        )
        self.desc_lbl.bind(size=self.desc_lbl.setter('text_size'))

        self.add_widget(self.title_lbl)
        self.add_widget(self.desc_lbl)

    def _update_bg(self, *args):
        self.bg.pos = self.pos
        self.bg.size = self.size
        self.border.pos = (self.pos[0] - 1, self.pos[1] - 1)
        self.border.size = (self.size[0] + 2, self.size[1] + 2)

    def open(self, title, desc):
        self.title_lbl.text = title
        self.desc_lbl.text = desc
        self.opacity = 1
        Animation(height=130, d=0.25, t='out_quad').start(self)

    def close(self):
        anim = Animation(height=0, d=0.2, t='out_quad')
        anim.bind(on_complete=lambda *x: setattr(self, 'opacity', 0))
        anim.start(self)


class FloatingCard(BoxLayout):
    def __init__(self, folder, info, callback, info_callback, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = 360
        self.padding = 15
        self.spacing = 10
        self.folder = folder
        self.info_callback = info_callback
        self.info = info

        with self.canvas.before:
            Color(0.1, 0.05, 0, 0.05)
            self.shadow = RoundedRectangle(radius=[15])
            Color(*COLOR_CARD)
            self.rect = RoundedRectangle(radius=[15])

        self.bind(pos=self.update_canvas, size=self.update_canvas)

        img_path = f'assets/images/{folder}.jpg'
        self.add_widget(Image(source=img_path, size_hint_y=0.55, allow_stretch=True, keep_ratio=True))

        t_text, t_font = format_text_and_font(info['title'])
        self.add_widget(Label(
            text=t_text,
            font_name=t_font,
            color=COLOR_TEXT,
            font_size='18sp',
            bold=True,
            size_hint_y=0.15,
            halign='center'
        ))

        btn_box = BoxLayout(size_hint_y=0.3, spacing=10)

        info_btn_text, info_btn_font = format_text_and_font('اطلاعات')
        self.info_btn = RoundedButton(
            text=info_btn_text,
            font_name=info_btn_font,
            bg_color=COLOR_WOOD_LIGHT,
            radius=12,
            color=COLOR_LIGHT_TEXT,
            size_hint_x=0.4
        )
        self.info_btn.bind(on_press=self.on_info_pressed)

        enter_btn_text, enter_btn_font = format_text_and_font('دیدن آلبوم')
        enter_btn = RoundedButton(
            text=enter_btn_text,
            font_name=enter_btn_font,
            bg_color=COLOR_WOOD_DARK,
            radius=12,
            color=COLOR_LIGHT_TEXT
        )
        enter_btn.bind(on_press=lambda x: callback(folder))

        btn_box.add_widget(self.info_btn)
        btn_box.add_widget(enter_btn)
        self.add_widget(btn_box)

    def update_canvas(self, *args):
        margin = 10
        self.shadow.pos = (self.x + margin - 2, self.y + margin - 4)
        self.shadow.size = (self.width - (margin * 2) + 4, self.height - (margin * 2) + 4)
        self.rect.pos = (self.x + margin, self.y + margin)
        self.rect.size = (self.width - (margin * 2), self.height - (margin * 2))

    def on_info_pressed(self, *args):
        is_closing = self.info_callback(self.info, self)
        if is_closing:
            txt, fnt = format_text_and_font('اطلاعات')
            self.info_btn.text = txt
            self.info_btn.font_name = fnt
            self.info_btn.set_bg_color(COLOR_WOOD_LIGHT)
        else:
            txt, fnt = format_text_and_font('بستن')
            self.info_btn.text = txt
            self.info_btn.font_name = fnt
            self.info_btn.set_bg_color(COLOR_WOOD_DARK)

    def reset_info_btn(self):
        txt, fnt = format_text_and_font('اطلاعات')
        self.info_btn.text = txt
        self.info_btn.font_name = fnt
        self.info_btn.set_bg_color(COLOR_WOOD_LIGHT)


class DownloadScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.layout = BoxLayout(orientation='vertical', padding=[30, 40, 30, 40], spacing=20)

        with self.layout.canvas.before:
            Color(*COLOR_BG)
            self.bg = RoundedRectangle(size=Window.size, pos=(0, 0))
        self.bind(size=self._update_bg)

        title_txt, title_fnt = format_text_and_font('اتاق چوبی')
        self.title_label = Label(
            text=title_txt,
            font_name=title_fnt,
            color=COLOR_TEXT,
            font_size='28sp',
            bold=True,
            size_hint_y=0.25
        )

        status_txt, status_fnt = format_text_and_font('در حال آماده‌سازی...')
        self.status_label = Label(
            text=status_txt,
            font_name=status_fnt,
            color=COLOR_TEXT,
            font_size='18sp',
            size_hint_y=0.2
        )

        self.progress = ProgressBar(
            max=100,
            value=0,
            size_hint_y=None,
            height=24
        )

        self.percent_label = Label(
            text='0%',
            font_name='EnglishFont',
            color=COLOR_WOOD_DARK,
            font_size='16sp',
            size_hint_y=0.15
        )

        self.message_label = Label(
            text='',
            font_name='EnglishFont',
            color=COLOR_TEXT,
            font_size='13sp',
            size_hint_y=0.2
        )

        self.layout.add_widget(Label(size_hint_y=0.15))
        self.layout.add_widget(self.title_label)
        self.layout.add_widget(self.status_label)
        self.layout.add_widget(self.progress)
        self.layout.add_widget(self.percent_label)
        self.layout.add_widget(self.message_label)
        self.layout.add_widget(Label(size_hint_y=0.25))

        self.add_widget(self.layout)
        self._started = False

    def _update_bg(self, instance, value):
        self.bg.size = value

    def on_enter(self):
        if self._started:
            return
        self._started = True
        threading.Thread(target=self.prepare_assets, daemon=True).start()

    def set_status(self, text, percent=None, message=''):
        def _update(dt):
            status_txt, status_fnt = format_text_and_font(text)
            self.status_label.text = status_txt
            self.status_label.font_name = status_fnt

            if percent is not None:
                self.progress.value = max(0, min(100, percent))
                self.percent_label.text = f'{int(percent)}%'

            self.message_label.text = message

        Clock.schedule_once(_update, 0)

    def finish_success(self):
        def _go(dt):
            self.manager.current = 'main'
        Clock.schedule_once(_go, 0.4)

    def finish_error(self, error_text):
        self.set_status('خطا در آماده‌سازی فایل‌ها', 0, str(error_text))

    def prepare_assets(self):
        if has_audio_assets():
            self.set_status('فایل‌ها آماده هستند', 100, 'ورود به برنامه...')
            self.finish_success()
            return

        try:
            os.makedirs(ASSETS_DIR, exist_ok=True)

            self.set_status('در حال دانلود...', 5, AUDIO_ZIP_URL)

            def reporthook(block_num, block_size, total_size):
                if total_size <= 0:
                    return
                downloaded = block_num * block_size
                percent = int((downloaded / total_size) * 70)
                self.set_status('در حال دانلود...', min(percent, 70), AUDIO_ZIP_URL)

            if os.path.exists(ZIP_PATH):
                os.remove(ZIP_PATH)

            urlretrieve(AUDIO_ZIP_URL, ZIP_PATH, reporthook)

            self.set_status('در حال استخراج...', 80, 'audio.zip')

            if os.path.exists(TEMP_EXTRACT_DIR):
                shutil.rmtree(TEMP_EXTRACT_DIR)
            os.makedirs(TEMP_EXTRACT_DIR, exist_ok=True)

            with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
                zip_ref.extractall(TEMP_EXTRACT_DIR)

            extracted_audio_dir = find_audio_folder(TEMP_EXTRACT_DIR)
            if not extracted_audio_dir or not os.path.exists(extracted_audio_dir):
                raise FileNotFoundError('پوشه audio داخل فایل zip پیدا نشد')

            if os.path.exists(AUDIO_DIR):
                shutil.rmtree(AUDIO_DIR)

            shutil.move(extracted_audio_dir, AUDIO_DIR)

            if os.path.exists(TEMP_EXTRACT_DIR):
                shutil.rmtree(TEMP_EXTRACT_DIR, ignore_errors=True)

            if os.path.exists(ZIP_PATH):
                os.remove(ZIP_PATH)

            self.set_status('فایل‌ها آماده شدند', 100, 'ورود به برنامه...')
            self.finish_success()

        except Exception as e:
            print(f'Asset prepare error: {e}')

            try:
                if os.path.exists(TEMP_EXTRACT_DIR):
                    shutil.rmtree(TEMP_EXTRACT_DIR, ignore_errors=True)
            except Exception:
                pass

            self.finish_error(e)


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_active_card = None

        self.root_layout = BoxLayout(orientation='vertical')

        with self.root_layout.canvas.before:
            Color(*COLOR_BG)
            self.bg = RoundedRectangle(size=Window.size, pos=(0, 0))
        self.bind(size=self._update_bg)

        title_txt, title_fnt = format_text_and_font('اتاق چوبی')
        self.root_layout.add_widget(Label(
            text=title_txt,
            font_name=title_fnt,
            color=COLOR_TEXT,
            font_size='24sp',
            size_hint_y=0.1,
            bold=True
        ))

        self.scroll = ScrollView(do_scroll_x=False, do_scroll_y=True, bar_width=0)
        self.container = GridLayout(cols=1, spacing=15, size_hint_y=None, padding=[10, 5, 10, 20])
        self.container.bind(minimum_height=self.container.setter('height'))

        for folder, info in CATEGORIES.items():
            card = FloatingCard(folder, info, self.open_album, self.toggle_info)
            self.container.add_widget(card)

        self.scroll.add_widget(self.container)
        self.root_layout.add_widget(self.scroll)

        self.info_drawer = InfoDrawer()
        self.root_layout.add_widget(self.info_drawer)

        self.add_widget(self.root_layout)

    def _update_bg(self, instance, value):
        self.bg.size = value

    def open_album(self, folder):
        if self.current_active_card:
            self.current_active_card.reset_info_btn()
            self.current_active_card = None

        self.info_drawer.close()
        self.manager.get_screen('player').setup_album(folder)
        self.manager.current = 'player'

    def toggle_info(self, info, card):
        if self.current_active_card and self.current_active_card != card:
            self.current_active_card.reset_info_btn()
            self.current_active_card = None

        if self.info_drawer.height > 0:
            self.info_drawer.close()
            self.current_active_card = None
            return True

        title_t, _ = format_text_and_font(info['title'])
        desc_t, _ = format_text_and_font(info['desc'])
        self.info_drawer.open(title_t, desc_t)
        self.current_active_card = card
        return False


class PlayerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.playlist = []
        self.index = -1
        self.sound = None

        self.is_repeat = False
        self.is_random = False
        self.switching_track = False
        self.progress_event = None

        self.is_seeking = False
        self.is_paused = False
        self.paused_pos = 0

        self.main_layout = BoxLayout(orientation='vertical')

        with self.main_layout.canvas.before:
            Color(*COLOR_BG)
            self.bg = RoundedRectangle(size=Window.size, pos=(0, 0))
        self.bind(size=self._update_bg)

        nav_box = BoxLayout(size_hint_y=0.08, padding=[15, 5])

        back_txt, back_fnt = format_text_and_font('بازگشت')
        back_btn = RoundedButton(
            text=back_txt,
            font_name=back_fnt,
            size_hint_x=0.25,
            bg_color=COLOR_WOOD_DARK,
            radius=10,
            color=COLOR_LIGHT_TEXT
        )
        back_btn.bind(on_press=self.go_back)

        nav_box.add_widget(back_btn)
        nav_box.add_widget(Label(size_hint_x=0.75))
        self.main_layout.add_widget(nav_box)

        self.scroll = ScrollView(bar_width=0)
        self.content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=15, padding=[15, 10])
        self.content.bind(minimum_height=self.content.setter('height'))

        self.cover = Image(source='', size_hint_y=None, height=220, allow_stretch=True, keep_ratio=True)
        self.content.add_widget(self.cover)

        self.track_list_ui = GridLayout(cols=1, spacing=8, size_hint_y=None)
        self.track_list_ui.bind(minimum_height=self.track_list_ui.setter('height'))
        self.content.add_widget(self.track_list_ui)

        self.scroll.add_widget(self.content)
        self.main_layout.add_widget(self.scroll)

        self.controls = BoxLayout(orientation='vertical', size_hint_y=0.24, padding=12, spacing=5)

        with self.controls.canvas.before:
            Color(*COLOR_CARD)
            self.ctrl_bg = RoundedRectangle(radius=[20, 20, 0, 0])
        self.controls.bind(pos=self.update_ctrl_bg, size=self.update_ctrl_bg)

        self.now_playing_layout = BoxLayout(orientation='horizontal', size_hint_y=0.25, spacing=5)

        status_txt, status_fnt = format_text_and_font('وضعیت:')
        self.status_label = Label(
            text=status_txt,
            font_name=status_fnt,
            color=COLOR_WOOD_LIGHT,
            font_size='14sp',
            bold=True,
            size_hint_x=0.3,
            halign='right'
        )

        self.track_name_label = Label(
            text="",
            font_name='EnglishFont',
            color=COLOR_TEXT,
            font_size='14sp',
            bold=True,
            size_hint_x=0.7,
            halign='left'
        )

        self.now_playing_layout.add_widget(self.track_name_label)
        self.now_playing_layout.add_widget(self.status_label)
        self.controls.add_widget(self.now_playing_layout)

        self.seek_bar = Slider(
            min=0,
            max=100,
            value=0,
            cursor_size=(16, 16),
            value_track=True,
            value_track_color=COLOR_WOOD_DARK
        )
        self.seek_bar.bind(on_touch_down=self._on_seek_touch_down)
        self.seek_bar.bind(on_touch_up=self._on_seek_touch_up)
        self.controls.add_widget(self.seek_bar)

        btn_box = BoxLayout(spacing=10, size_hint_y=0.45)

        rnd_txt, rnd_fnt = format_text_and_font('تصادفی')
        self.btn_rnd = RoundedButton(
            text=rnd_txt,
            font_name=rnd_fnt,
            bg_color=COLOR_WOOD_LIGHT,
            radius=12,
            color=COLOR_LIGHT_TEXT
        )
        self.btn_rnd.bind(on_press=self.toggle_random)

        play_txt, play_fnt = format_text_and_font('پخش')
        self.btn_play = RoundedButton(
            text=play_txt,
            font_name=play_fnt,
            bold=True,
            bg_color=COLOR_WOOD_DARK,
            radius=12,
            color=COLOR_LIGHT_TEXT
        )
        self.btn_play.bind(on_press=self.toggle_audio)

        rep_txt, rep_fnt = format_text_and_font('تکرار')
        self.btn_rep = RoundedButton(
            text=rep_txt,
            font_name=rep_fnt,
            bg_color=COLOR_WOOD_LIGHT,
            radius=12,
            color=COLOR_LIGHT_TEXT
        )
        self.btn_rep.bind(on_press=self.toggle_repeat)

        btn_box.add_widget(self.btn_rnd)
        btn_box.add_widget(self.btn_play)
        btn_box.add_widget(self.btn_rep)
        self.controls.add_widget(btn_box)

        self.main_layout.add_widget(self.controls)
        self.add_widget(self.main_layout)

    def _update_bg(self, instance, value):
        self.bg.size = value

    def update_ctrl_bg(self, *args):
        self.ctrl_bg.pos = self.controls.pos
        self.ctrl_bg.size = self.controls.size

    def setup_album(self, folder):
        self._stop_current_sound()

        self.cover.source = f'assets/images/{folder}.jpg'
        path = os.path.join('assets', 'audio', folder)

        self.playlist = []
        if os.path.exists(path):
            self.playlist = [
                os.path.join(path, f)
                for f in sorted(os.listdir(path))
                if f.lower().endswith(('.mp3', '.wav', '.ogg'))
            ]

        self.track_list_ui.clear_widgets()

        for i, track in enumerate(self.playlist):
            name = os.path.splitext(os.path.basename(track))[0]
            track_name_processed, font_to_use = format_text_and_font(name)

            track_card = BoxLayout(size_hint_y=None, height=50, padding=[10, 5])

            with track_card.canvas.before:
                Color(*COLOR_CARD)
                track_card.rect = RoundedRectangle(radius=[8])
            track_card.bind(pos=self._update_track_rect, size=self._update_track_rect)

            btn = Button(
                text=track_name_processed,
                font_name=font_to_use,
                background_normal='',
                background_color=(0, 0, 0, 0),
                color=COLOR_TEXT,
                halign='center',
                valign='middle'
            )
            btn.bind(size=btn.setter('text_size'))
            btn.bind(on_press=lambda x, idx=i: self.play_track(idx))

            track_card.add_widget(btn)
            self.track_list_ui.add_widget(track_card)

        self.index = -1
        self.is_paused = False
        self.paused_pos = 0
        self.is_seeking = False

        self.seek_bar.value = 0
        self.seek_bar.max = 100
        self.track_name_label.text = ""

        status_t, status_f = format_text_and_font("آماده پخش")
        self.status_label.font_name = status_f
        self.status_label.text = status_t

        play_txt, play_f = format_text_and_font("پخش")
        self.btn_play.font_name = play_f
        self.btn_play.text = play_txt

    def _update_track_rect(self, instance, value):
        instance.rect.pos = instance.pos
        instance.rect.size = instance.size

    def _stop_current_sound(self):
        if self.progress_event:
            Clock.unschedule(self.progress_event)
            self.progress_event = None

        if self.sound:
            try:
                self.sound.stop()
            except Exception as e:
                print(f"Stop sound error: {e}")

        self.sound = None

    def _safe_get_pos(self):
        if not self.sound:
            return self.seek_bar.value

        try:
            pos = self.sound.get_pos()
            if pos is None or pos < 0:
                return self.seek_bar.value
            return pos
        except Exception as e:
            print(f"Get position error: {e}")
            return self.seek_bar.value

    def _safe_stop_for_pause(self):
        try:
            if self.sound:
                self.sound.stop()
        except Exception as e:
            print(f"Stop fallback failed: {e}")

    def _safe_pause(self):
        if not self.sound:
            return

        try:
            pause_method = getattr(self.sound, 'pause', None)
            if callable(pause_method):
                pause_method()
            else:
                self._safe_stop_for_pause()
        except Exception as e:
            print(f"Pause failed, using stop fallback: {e}")
            self._safe_stop_for_pause()

    def _set_play_button(self):
        btn_pause_txt, btn_pause_font = format_text_and_font('توقف')
        self.btn_play.font_name = btn_pause_font
        self.btn_play.text = btn_pause_txt

    def _set_pause_button(self):
        btn_play_txt, btn_play_font = format_text_and_font('پخش')
        self.btn_play.font_name = btn_play_font
        self.btn_play.text = btn_play_txt

    def _set_status_playing(self):
        status_t, status_f = format_text_and_font("در حال پخش:")
        self.status_label.font_name = status_f
        self.status_label.text = status_t

    def _set_status_paused(self):
        status_t, status_f = format_text_and_font("متوقف شده:")
        self.status_label.font_name = status_f
        self.status_label.text = status_t

    def play_track(self, idx):
        if not self.playlist or idx < 0 or idx >= len(self.playlist) or self.switching_track:
            return

        self.switching_track = True
        self.index = idx
        self.is_paused = False
        self.paused_pos = 0
        self.is_seeking = False

        track_path = self.playlist[self.index]
        name = os.path.splitext(os.path.basename(track_path))[0]

        def _load_process(dt):
            try:
                new_sound = SoundLoader.load(track_path)

                if not new_sound:
                    err_txt, err_font = format_text_and_font("خطا در فایل")
                    self.status_label.font_name = err_font
                    self.status_label.text = err_txt
                    self.track_name_label.text = ""
                    return

                if self.sound:
                    try:
                        self.sound.stop()
                    except Exception as e:
                        print(f"Previous sound stop error: {e}")

                self.sound = new_sound

                try:
                    self.sound.play()
                except Exception as e:
                    print(f"Sound play error: {e}")
                    err_txt, err_font = format_text_and_font("خطا در پخش")
                    self.status_label.font_name = err_font
                    self.status_label.text = err_txt
                    return

                play_name_processed, name_font = format_text_and_font(name)
                self.track_name_label.font_name = name_font
                self.track_name_label.text = play_name_processed

                self._set_status_playing()
                self._set_play_button()

                if self.progress_event:
                    Clock.unschedule(self.progress_event)

                self.progress_event = Clock.schedule_interval(self.update_progress, 0.25)

            except Exception as e:
                print(f"Playback error: {e}")
                err_txt, err_font = format_text_and_font("خطا در پخش")
                self.status_label.font_name = err_font
                self.status_label.text = err_txt
                self.track_name_label.text = ""

            finally:
                self.switching_track = False

        Clock.schedule_once(_load_process, 0.05)

    def toggle_audio(self, *args):
        if not self.sound:
            if self.playlist:
                self.play_track(0)
            return

        try:
            if self.sound.state == 'play':
                self.paused_pos = max(0, self._safe_get_pos())
                self.is_paused = True

                self._safe_pause()
                self._set_pause_button()
                self._set_status_paused()
                return

            self.sound.play()

            if self.is_paused and self.paused_pos > 0:
                resume_pos = self.paused_pos

                def _resume_seek(dt):
                    try:
                        if self.sound:
                            self.sound.seek(resume_pos)
                    except Exception as e:
                        print(f"Resume seek failed: {e}")

                Clock.schedule_once(_resume_seek, 0.15)

            self.is_paused = False
            self._set_play_button()
            self._set_status_playing()

            if not self.progress_event:
                self.progress_event = Clock.schedule_interval(self.update_progress, 0.25)

        except Exception as e:
            print(f"Toggle audio error: {e}")
            err_txt, err_font = format_text_and_font("خطا در کنترل پخش")
            self.status_label.font_name = err_font
            self.status_label.text = err_txt

    def update_progress(self, dt):
        if not self.sound or self.is_paused:
            return

        try:
            if self.sound.state == 'play' and self.sound.length > 0:
                current_pos = self.sound.get_pos()

                if current_pos is None or current_pos < 0:
                    current_pos = 0

                if not self.is_seeking:
                    self.seek_bar.max = self.sound.length
                    self.seek_bar.value = current_pos

                if current_pos >= self.sound.length - 0.4:
                    self.auto_next()

        except Exception as e:
            print(f"Progress update error: {e}")

    def _on_seek_touch_down(self, instance, touch):
        if instance.collide_point(*touch.pos):
            self.is_seeking = True

    def _on_seek_touch_up(self, instance, touch):
        if not self.is_seeking:
            return

        if instance.collide_point(*touch.pos):
            target_pos = max(0, min(instance.value, self.seek_bar.max))
            self.paused_pos = target_pos

            if self.sound:
                try:
                    if self.sound.state == 'play':
                        self.sound.seek(target_pos)
                    else:
                        self.sound.play()

                        def _seek_after_play(dt):
                            try:
                                if self.sound:
                                    self.sound.seek(target_pos)

                                    if self.is_paused:
                                        self._safe_pause()

                            except Exception as e:
                                print(f"Seek while paused failed: {e}")

                        Clock.schedule_once(_seek_after_play, 0.15)

                except Exception as e:
                    print(f"Seek error: {e}")

        def _reset_seek(dt):
            self.is_seeking = False

        Clock.schedule_once(_reset_seek, 0.2)

    def seek_audio(self, instance, touch):
        pass

    def auto_next(self):
        if not self.playlist or self.switching_track:
            return

        if self.is_repeat:
            self.play_track(self.index)
        elif self.is_random and len(self.playlist) > 1:
            next_idx = random.choice([i for i in range(len(self.playlist)) if i != self.index])
            self.play_track(next_idx)
        else:
            self.play_track((self.index + 1) % len(self.playlist))

    def toggle_repeat(self, *args):
        self.is_repeat = not self.is_repeat
        self.btn_rep.set_bg_color(COLOR_WOOD_DARK if self.is_repeat else COLOR_WOOD_LIGHT)

    def toggle_random(self, *args):
        self.is_random = not self.is_random
        self.btn_rnd.set_bg_color(COLOR_WOOD_DARK if self.is_random else COLOR_WOOD_LIGHT)

    def go_back(self, *args):
        self._stop_current_sound()

        self.index = -1
        self.is_paused = False
        self.paused_pos = 0
        self.is_seeking = False

        self.manager.current = 'main'


def start_android_service():
    if platform != 'android':
        return

    try:
        from android import mActivity
        from jnius import autoclass

        PythonService = autoclass('org.kivy.android.PythonService')
        service = PythonService.mService
        if service is None:
            PythonService.start(mActivity, '')
            print("Android background service started.")
    except Exception as e:
        print(f"Service start error: {e}")


class WoodenRoomApp(App):
    def build(self):
        start_android_service()
        sm = ScreenManager(transition=FadeTransition())
        sm.add_widget(DownloadScreen(name='download'))
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(PlayerScreen(name='player'))

        if has_audio_assets():
            sm.current = 'main'
        else:
            sm.current = 'download'

        return sm


if __name__ == '__main__':
    WoodenRoomApp().run()
