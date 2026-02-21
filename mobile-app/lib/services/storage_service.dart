import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:hive_flutter/hive_flutter.dart';
import '../models/models.dart';

/// Сервис локального хранилища
class StorageService {
  static final StorageService _instance = StorageService._internal();
  factory StorageService() => _instance;
  StorageService._internal();

  static const String _apiKeyBoxName = 'api_keys';
  static const String _settingsBoxName = 'settings';
  static const String _chatHistoryBoxName = 'chat_history';
  static const String _portfolioBoxName = 'portfolio';

  SharedPreferences? _prefs;
  Box? _apiKeysBox;
  Box? _settingsBox;
  Box? _chatHistoryBox;
  Box? _portfolioBox;

  /// Инициализация хранилища
  Future<void> init() async {
    try {
      _prefs = await SharedPreferences.getInstance();
      debugPrint('[Storage] SharedPreferences инициализирован');

      await Hive.initFlutter();

      _apiKeysBox = await Hive.openBox(_apiKeyBoxName);
      _settingsBox = await Hive.openBox(_settingsBoxName);
      _chatHistoryBox = await Hive.openBox(_chatHistoryBoxName);
      _portfolioBox = await Hive.openBox(_portfolioBoxName);

      debugPrint('[Storage] Hive boxes инициализированы');
    } catch (e) {
      debugPrint('[Storage] Ошибка инициализации: $e');
      rethrow;
    }
  }

  // ========== API Keys ==========

  Future<void> saveApiKey(String key, String value) async {
    await _apiKeysBox?.put(key, value);
    debugPrint('[Storage] Сохранен API ключ: $key');
  }

  String? getApiKey(String key) {
    return _apiKeysBox?.get(key) as String?;
  }

  String? get telegramApiToken => getApiKey('telegram_api_token');
  String? get openrouterApiKey => getApiKey('openrouter_api_key');
  String? get weatherApiKey => getApiKey('weather_api_key');
  String? get hfToken => getApiKey('hf_token');
  String? get cfApiToken => getApiKey('cf_api_token');
  String? get cfAccountId => getApiKey('cf_account_id');

  Future<void> saveTelegramApiToken(String value) async {
    await saveApiKey('telegram_api_token', value);
  }

  Future<void> saveOpenrouterApiKey(String value) async {
    await saveApiKey('openrouter_api_key', value);
  }

  Future<void> saveWeatherApiKey(String value) async {
    await saveApiKey('weather_api_key', value);
  }

  // ========== Settings ==========

  Future<void> saveSetting(String key, dynamic value) async {
    await _settingsBox?.put(key, value);
  }

  T? getSetting<T>(String key, {T? defaultValue}) {
    return _settingsBox?.get(key, defaultValue: defaultValue) as T?;
  }

  // Telegram ID пользователя
  String? get telegramId => getSetting<String>('telegram_id');
  Future<void> saveTelegramId(String value) async {
    await saveSetting('telegram_id', value);
  }

  // Интересы для новостей
  List<String> get interests {
    final data = getSetting<List>('interests');
    return data?.cast<String>() ?? ['kyrgyzstan', 'technology', 'ai'];
  }

  Future<void> saveInterests(List<String> value) async {
    await saveSetting('interests', value);
  }

  // Время дайджеста
  String? get digestScheduleTime => getSetting<String>('digest_schedule_time');
  Future<void> saveDigestScheduleTime(String value) async {
    await saveSetting('digest_schedule_time', value);
  }

  // Голосовой режим
  bool get voiceModeEnabled => getSetting<bool>('voice_mode', defaultValue: false) ?? false;
  Future<void> saveVoiceMode(bool value) async {
    await saveSetting('voice_mode', value);
  }

  // Предпочитаемый голос
  String get preferredVoice => getSetting<String>('preferred_voice') ?? 'ru-RU-SvetlanaNeural';
  Future<void> savePreferredVoice(String value) async {
    await saveSetting('preferred_voice', value);
  }

  // Темная тема
  bool get isDarkMode => getSetting<bool>('dark_mode') ?? false;
  Future<void> saveDarkMode(bool value) async {
    await saveSetting('dark_mode', value);
  }

  // Уведомления
  bool get notificationsEnabled => getSetting<bool>('notifications') ?? true;
  Future<void> saveNotifications(bool value) async {
    await saveSetting('notifications', value);
  }

  // ========== Chat History ==========

  Future<void> saveMessage(Message message) async {
    final key = 'msg_${message.id}';
    await _chatHistoryBox?.put(key, message.toJson());

    // Сохраняем порядок сообщений
    final history = getChatHistory();
    if (!history.any((m) => m.id == message.id)) {
      history.add(message);
      await _chatHistoryBox?.put('history_order', history.map((m) => m.id).toList());
    }
  }

  List<Message> getChatHistory({int limit = 50}) {
    final order = _chatHistoryBox?.get('history_order') as List<dynamic>? ?? [];
    final messages = order
        .map((id) => _chatHistoryBox?.get('msg_$id') as Map<dynamic, dynamic>?)
        .where((m) => m != null)
        .map((m) => Message.fromJson(Map<String, dynamic>.from(m!)))
        .toList();
    
    messages.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    
    if (limit > 0 && messages.length > limit) {
      return messages.sublist(0, limit);
    }
    return messages;
  }

  Future<void> clearChatHistory() async {
    final order = _chatHistoryBox?.get('history_order') as List<dynamic>? ?? [];
    for (final id in order) {
      await _chatHistoryBox?.delete('msg_$id');
    }
    await _chatHistoryBox?.delete('history_order');
    debugPrint('[Storage] История чата очищена');
  }

  // ========== Portfolio ==========

  Future<void> savePortfolioItem(CryptoPortfolioItem item) async {
    await _portfolioBox?.put('item_${item.coinId}', item.toJson());
  }

  Future<void> removePortfolioItem(String coinId) async {
    await _portfolioBox?.delete('item_$coinId');
  }

  List<CryptoPortfolioItem> getPortfolio() {
    final keys = _portfolioBox?.keys ?? [];
    return keys
        .where((k) => k.toString().startsWith('item_'))
        .map((k) => _portfolioBox?.get(k) as Map<dynamic, dynamic>?)
        .where((m) => m != null)
        .map((m) => CryptoPortfolioItem.fromJson(Map<String, dynamic>.from(m!)))
        .toList();
  }

  Future<void> clearPortfolio() async {
    final keys = _portfolioBox?.keys ?? [];
    for (final key in keys) {
      if (key.toString().startsWith('item_')) {
        await _portfolioBox?.delete(key);
      }
    }
  }

  // ========== Очистка ==========

  Future<void> clearAll() async {
    await _apiKeysBox?.clear();
    await _settingsBox?.clear();
    await _chatHistoryBox?.clear();
    await _portfolioBox?.clear();
    debugPrint('[Storage] Все данные очищены');
  }

  Future<void> close() async {
    await Hive.close();
    debugPrint('[Storage] Хранилище закрыто');
  }
}
