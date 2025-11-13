[app]
title = Investment App
package.name = investmentapp
package.domain = com.investment
icon.filename = assets/icon.png
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,txt
version = 1.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0

# Android specific
android.permissions = INTERNET
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21
android.archs = arm64-v8a, armeabi-v7a

[buildozer]
log_level = 2

# iOS specific
[ios]
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.ios_deploy_url = https://github.com/phonegap/ios-deploy
ios.ios_deploy_branch = 1.7.0