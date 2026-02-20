import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/services.dart';

/// Провайдер для AI чата
class ChatProvider extends ChangeNotifier {
  final OpenRouterService _openrouterService = OpenRouterService();
  final StorageService _storageService = StorageService();

  List<Message> _messages = [];
  bool _isLoading = false;
  String? _error;

  List<Message> get messages => _messages;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Инициализация
  Future<void> init() async {
    final apiKey = _storageService.openrouterApiKey;
    if (apiKey != null && apiKey.isNotEmpty) {
      _openrouterService.init(apiKey);
    }
    
    // Загружаем историю из хранилища
    _messages = _storageService.getChatHistory(limit: 50);
    notifyListeners();
  }

  /// Отправить сообщение
  Future<void> sendMessage(String content) async {
    if (content.trim().isEmpty) return;

    _error = null;
    _isLoading = true;
    notifyListeners();

    try {
      // Создаем сообщение пользователя
      final userMessage = Message(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: content,
        role: MessageRole.user,
        timestamp: DateTime.now(),
      );

      _messages.add(userMessage);
      await _storageService.saveMessage(userMessage);
      notifyListeners();

      // Получаем ответ от AI
      final responseContent = await _openrouterService.sendMessage(
        history: _messages,
        maxTokens: 1000,
      );

      // Создаем сообщение ассистента
      final assistantMessage = Message(
        id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
        content: responseContent,
        role: MessageRole.assistant,
        timestamp: DateTime.now(),
      );

      _messages.add(assistantMessage);
      await _storageService.saveMessage(assistantMessage);
    } catch (e) {
      _error = e.toString();
      
      // Добавляем сообщение об ошибке
      final errorMessage = Message(
        id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
        content: '❌ Ошибка: $e',
        role: MessageRole.system,
        timestamp: DateTime.now(),
      );
      _messages.add(errorMessage);
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// DeepSeek R1 (/gpt4)
  Future<void> sendToDeepSeek(String content) async {
    if (content.trim().isEmpty) return;

    _error = null;
    _isLoading = true;
    notifyListeners();

    try {
      final userMessage = Message(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: content,
        role: MessageRole.user,
        timestamp: DateTime.now(),
      );

      _messages.add(userMessage);
      await _storageService.saveMessage(userMessage);
      notifyListeners();

      final responseContent = await _openrouterService.sendToDeepSeek(
        message: content,
        history: _messages.take(10).toList(),
      );

      final assistantMessage = Message(
        id: (DateTime.now().millisecondsSinceEpoch + 1).toString(),
        content: responseContent,
        role: MessageRole.assistant,
        timestamp: DateTime.now(),
      );

      _messages.add(assistantMessage);
      await _storageService.saveMessage(assistantMessage);
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Очистить историю
  Future<void> clearHistory() async {
    await _storageService.clearChatHistory();
    _messages.clear();
    notifyListeners();
  }

  /// Удалить сообщение
  Future<void> removeMessage(String messageId) async {
    _messages.removeWhere((m) => m.id == messageId);
    notifyListeners();
  }

  /// Сохранить API ключ
  Future<void> saveApiKey(String key) async {
    await _storageService.saveOpenrouterApiKey(key);
    _openrouterService.init(key);
  }
}
