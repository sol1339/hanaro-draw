[app]
title = 하나로마트 행운 추첨
package.name = hanaroluckydraw
package.domain = kr.hanaro.event
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,ttf,txt
source.exclude_dirs = tests,bin,.buildozer,__pycache__
version = 1.0.0
requirements = python3,kivy==2.3.1,sqlite3,pyjnius
orientation = landscape
fullscreen = 1
android.api = 35
android.minapi = 23
android.ndk = 28c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.debug_artifact = apk
[buildozer]
log_level = 2
warn_on_root = 0
