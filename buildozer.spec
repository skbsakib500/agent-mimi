[app]
title = Agent Mimi - Life OS
package.name = agentmimi
package.domain = dev.skb
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,json,db,sql
version = 12.0.0
requirements = python3,kivy,sqlite3,requests,certifi

orientation = portrait
osx.kivy_version = 2.2.1
fullscreen = 0
android.presplash_color = #0F172A

# Android Permissions & API Config
android.permissions = INTERNET, READ_EXTERNAL_STORAGE, WRITE_EXTERNAL_STORAGE
android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a, armeabi-v7a
android.allow_backup = True

[buildozer]
log_level = 2
warn_on_root = 1
