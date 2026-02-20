import 'package:flutter/material.dart';
import '../services/services.dart';

/// Провайдер для настроек приложения
class SettingsProvider extends ChangeNotifier {
  final StorageService _storageService = StorageService();

  ThemeMode _themeMode = ThemeMode.system;
  bool _voiceModeEnabled = false;
  String _preferredVoice = 'ru-RU-SvetlanaNeural';
  bool _notificationsEnabled = true;
  String? _telegramId;
  String? _digestScheduleTime;
  
  // API Keys
  String? _telegramApiToken;
  String? _openrouterApiKey;
  String? _weatherApiKey;

  ThemeMode get themeMode => _themeMode;
  bool get voiceModeEnabled => _voiceModeEnabled;
  String get preferredVoice => _preferredVoice;
  bool get notificationsEnabled => _notificationsEnabled;
  String? get telegramId => _telegramId;
  String? get digestScheduleTime => _digestScheduleTime;
  String? get telegramApiToken => _telegramApiToken;
  String? get openrouterApiKey => _openrouterApiKey;
  String? get weatherApiKey => _weatherApiKey;

  /// Инициализация
  Future<void> init() async {
    // Загружаем настройки
    _themeMode = ThemeMode.values[_storageService.getSetting<int>('theme_mode') ?? 0];
    _voiceModeEnabled = _storageService.voiceModeEnabled;
    _preferredVoice = _storageService.preferredVoice;
    _notificationsEnabled = _storageService.notificationsEnabled;
    _telegramId = _storageService.telegramId;
    _digestScheduleTime = _storageService.digestScheduleTime;
    
    // Загружаем API ключи
    _telegramApiToken = _storageService.telegramApiToken;
    _openrouterApiKey = _storageService.openrouterApiKey;
    _weatherApiKey = _storageService.weatherApiKey;
    
    notifyListeners();
  }

  /// Переключить тему
  Future<void> setThemeMode(ThemeMode mode) async {
    _themeMode = mode;
    await _storageService.saveSetting('theme_mode', mode.index);
    notifyListeners();
  }

  /// Переключить темную тему
  Future<void> toggleDarkMode(bool value) async {
    _themeMode = value ? ThemeMode.dark : ThemeMode.light;
    await _storageService.saveDarkMode(value);
    notifyListeners();
  }

  /// Переключить голосовой режим
  Future<void> toggleVoiceMode(bool value) async {
    _voiceModeEnabled = value;
    await _storageService.saveVoiceMode(value);
    notifyListeners();
  }

  /// Установить предпочитаемый голос
  Future<void> setPreferredVoice(String voice) async {
    _preferredVoice = voice;
    await _storageService.savePreferredVoice(voice);
    notifyListeners();
  }

  /// Переключить уведомления
  Future<void> toggleNotifications(bool value) async {
    _notificationsEnabled = value;
    await _storageService.saveNotifications(value);
    notifyListeners();
  }

  /// Установить Telegram ID
  Future<void> setTelegramId(String id) async {
    _telegramId = id;
    await _storageService.saveTelegramId(id);
    notifyListeners();
  }

  /// Установить время дайджеста
  Future<void> setDigestScheduleTime(String time) async {
    _digestScheduleTime = time;
    await _storageService.saveDigestScheduleTime(time);
    notifyListeners();
  }

  /// Сохранить API ключ
  Future<void> saveApiKey(String key, String value) async {
    await _storageService.saveApiKey(key, value);
    
    switch (key) {
      case 'telegram_api_token':
        _telegramApiToken = value;
        break;
      case 'openrouter_api_key':
        _openrouterApiKey = value;
        break;
      case 'weather_api_key':
        _weatherApiKey = value;
        break;
    }
    
    notifyListeners();
  }

  /// Очистить все данные
  Future<void> clearAllData() async {
    await _storageService.clearAll();
    await init();
  }
}
