# 📥 Установка Flutter SDK на Windows

## ⚠️ Проблема
Flutter SDK не установлен в системе. Без него невозможно запустить мобильное приложение.

---

## 🔧 Шаг 1: Системные требования

- **ОС:** Windows 10 или выше (64-битная)
- **Место на диске:** 2.8 ГБ
- **Инструменты:** PowerShell 5.0+
- **Git:** для установки через git

---

## 🔧 Шаг 2: Скачивание Flutter

### Вариант A: Через Git (рекомендуется)

1. **Откройте PowerShell от имени администратора**

2. **Создайте папку для Flutter:**
   ```powershell
   mkdir C:\flutter
   cd C:\flutter
   ```

3. **Клонируйте репозиторий:**
   ```powershell
   git clone https://github.com/flutter/flutter.git -b stable
   ```

4. **Добавьте Flutter в PATH:**
   - Откройте "Панель управления" → "Система" → "Дополнительные параметры системы"
   - Нажмите "Переменные среды"
   - В "Системные переменные" найдите `Path`
   - Нажмите "Изменить" → "Создать"
   - Добавьте: `C:\flutter\bin`
   - Нажмите "OK"

### Вариант B: Прямое скачивание

1. **Скачайте Flutter SDK:**
   - Перейдите на https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.24.0-stable.zip
   - Или найдите последнюю версию на https://github.com/flutter/flutter/releases

2. **Распакуйте в `C:\flutter`**

3. **Добавьте в PATH** (как в Варианте A)

---

## 🔧 Шаг 3: Проверка установки

1. **Откройте новый терминал** (важно! чтобы PATH обновился)

2. **Проверьте Flutter:**
   ```bash
   flutter --version
   ```

3. **Запустите диагностику:**
   ```bash
   flutter doctor
   ```

---

## 🔧 Шаг 4: Принятие лицензий Android

```bash
flutter doctor --android-licenses
```

Нажимайте `y` для принятия всех лицензий.

---

## 🔧 Шаг 5: Установка Android Studio

### Для запуска Android приложения нужен Android Studio:

1. **Скачайте Android Studio:**
   - https://developer.android.com/studio

2. **Установите:**
   - Запустите установщик
   - Следуйте инструкциям

3. **Установите Android SDK:**
   - Откройте Android Studio
   - Tools → SDK Manager
   - Установите:
     - Android SDK Platform (последняя версия)
     - Android SDK Build-Tools
     - Android Emulator

4. **Настройте переменные среды:**
   - `ANDROID_HOME` = `C:\Users\%USERNAME%\AppData\Local\Android\Sdk`
   - Добавьте в Path: `%ANDROID_HOME%\platform-tools`
   - Добавьте в Path: `%ANDROID_HOME%\emulator`

---

## 🔧 Шаг 6: Создание эмулятора

1. **В Android Studio:**
   - Tools → Device Manager
   - Create Device
   - Выберите устройство (например, Pixel 6)
   - Скачайте образ системы (рекомендуется x86_64)
   - Finish

2. **Или через командную строку:**
   ```bash
   avdmanager create avd -n my_avd -k "system-images;android-34;google_apis_playstore;x86_64"
   ```

---

## 🔧 Шаг 7: Финальная проверка

```bash
flutter doctor -v
```

**Ожидаемый результат:**
```
[✓] Flutter (Channel stable, 3.x.x, on Windows)
[✓] Windows Version (10/11)
[✓] Android toolchain - develop for Android devices
[✓] Chrome - develop for the web
[✓] Visual Studio - develop Windows apps
[✓] Android Studio
[✓] Connected device (3 available)
[✓] Network resources
```

---

## 🚀 Быстрая установка (автоматическая)

Создайте файл `install_flutter.ps1`:

```powershell
# Установить Flutter через winget
winget install --id Google.Flutter --exact

# Добавить в PATH (требует перезапуска терминала)
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Проверить
flutter --version
```

Запустите:
```powershell
.\install_flutter.ps1
```

---

## 📝 После установки Flutter

Вернитесь в папку проекта и выполните:

```bash
cd C:\tegi\mobile-app
flutter create . --platforms=android,ios
flutter pub get
flutter run
```

---

## ❓ Проблемы и решения

### "Flutter не является внутренней или внешней командой"
- Перезапустите терминал после добавления в PATH
- Проверьте: `echo %PATH%`

### "Android license status unknown"
- Запустите: `flutter doctor --android-licenses`
- Установите Android Studio

### "Unable to locate Android SDK"
- Установите Android Studio
- Настройте `ANDROID_HOME`

### Git не найден
- Скачайте: https://git-scm.com/download/win
- Установите и перезапустите терминал

---

## 📞 Поддержка

- Официальная документация: https://docs.flutter.dev/
- Русскоязычное сообщество: https://t.me/flutter_ru
- Stack Overflow: https://stackoverflow.com/questions/tagged/flutter

---

**Время установки:** ~30-60 минут  
**Размер на диске:** ~5-10 ГБ
