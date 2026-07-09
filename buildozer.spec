[app]

# (str) Title of your application
title = Otagh Choobi

# (str) Package name
package.name = otaghchoobi

# (str) Package domain
package.domain = com.amirhossein.otagchoobi

# (str) Source code directory
source.dir = .

# (list) Source files to include
source.include_exts = py,png,jpg,jpeg,kv,atlas,ttf,zip,json,mp3,wav,ogg

# (str) Application version
version = 1.0

# (list) Application requirements
requirements = python3,kivy,pyjnius,arabic-reshaper,python-bidi

# (str) Icon of the application
# اگر این فایل را داری، کامنت را بردار:
# icon.filename = %(source.dir)s/assets/ui/logo.png

# (list) Supported orientations
orientation = portrait

# (list) Services to declare
services = MusicService:service.py:foreground

#
# Android specific
#

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,FOREGROUND_SERVICE,WAKE_LOCK,READ_MEDIA_AUDIO,READ_EXTERNAL_STORAGE

# (int) Minimum API your APK will support
android.minapi = 24

# (int) Target Android API
android.api = 33

# (list) The Android archs to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android auto backup feature
android.allow_backup = True

# (str) The format used to package the app for debug mode
android.debug_artifact = apk

# (bool) Copy library instead of making a libpymodules.so
android.copy_libs = 1

# (str) Android logcat filters
android.logcat_filters = *:S python:D


#
# iOS specific
#

ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.12.2
ios.codesign.allowed = false


[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root
warn_on_root = 1
