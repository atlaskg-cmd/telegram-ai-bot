import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

/// Сервис для работы с AI (OpenRouter API)
class OpenRouterService {
  static final OpenRouterService _instance = OpenRouterService._internal();
  factory OpenRouterService() => _instance;
  OpenRouterService._internal();

  final String _baseUrl = 'https://openrouter.ai/api/v1';
  
  String? _apiKey;
  
  /// Модели для fallback
  final List<String> _modelsToTry = [
    'arcee-ai/trinity-large-preview:free',
    'deepseek/deepseek-r1-0528:free',
    'microsoft/wizardlm-2-8x22b',
    'anthropic/claude-3-haiku:beta',
    'google/gemini-2.5-flash-lite',
  ];

  /// Инициализация с API ключом
  void init(String apiKey) {
    _apiKey = apiKey;
    debugPrint('[OpenRouter] Инициализирован с ключом длины: ${apiKey.length}');
  }

  /// Проверка наличия ключа
  bool get isInitialized => _apiKey != null && _apiKey!.isNotEmpty;

  /// Отправить сообщение и получить ответ
  Future<String> sendMessage({
    required List<Message> history,
    String? model,
    int maxTokens = 1000,
  }) async {
    if (!isInitialized) {
      throw Exception('OPENROUTER_API_KEY не установлен');
    }

    // Преобразуем историю в формат OpenRouter
    final messages = history.map((msg) => {
      'role': msg.role.name,
      'content': msg.content,
    }).toList();

    // Модели для попытки (указанная или список fallback)
    final models = model != null ? [model] : _modelsToTry;
    
    Exception? lastError;

    for (final modelToTry in models) {
      try {
        debugPrint('[OpenRouter] Попытка модели: $modelToTry');

        final response = await http.post(
          Uri.parse('$_baseUrl/chat/completions'),
          headers: {
            'Authorization': 'Bearer $_apiKey',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/your-app',
            'X-Title': 'AI Bot App',
          },
          body: jsonEncode({
            'model': modelToTry,
            'messages': messages,
            'max_tokens': maxTokens,
          }),
        ).timeout(const Duration(seconds: 60));

        // Rate limit - пробуем следующую модель
        if (response.statusCode == 429) {
          debugPrint('[OpenRouter] Rate limit для $modelToTry, пробуем следующую...');
          continue;
        }

        // Auth error
        if (response.statusCode == 401) {
          throw Exception('Ошибка 401: Неверный API ключ');
        }

        // Bad request - пробуем следующую модель
        if (response.statusCode == 400) {
          debugPrint('[OpenRouter] Модель $modelToTry вернула 400, пробуем следующую...');
          continue;
        }

        if (response.statusCode != 200) {
          throw Exception('Ошибка API: ${response.statusCode} - ${response.body}');
        }

        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final choices = data['choices'] as List<dynamic>;
        
        if (choices.isEmpty) {
          debugPrint('[OpenRouter] Пустой ответ от модели');
          continue;
        }

        final content = choices[0]['message']['content'] as String;
        debugPrint('[OpenRouter] Успех! Модель: $modelToTry');
        return content;

      } on http.ClientException catch (e) {
        debugPrint('[OpenRouter] Ошибка сети: $e');
        lastError = e;
        continue;
      } on FormatException catch (e) {
        debugPrint('[OpenRouter] Ошибка парсинга: $e');
        lastError = e;
        continue;
      } on Exception catch (e) {
        debugPrint('[OpenRouter] Ошибка: $e');
        lastError = e;
        if (e.toString().contains('401')) rethrow; // Не пытаемся при auth error
        continue;
      }
    }

    // Все модели не удалось
    final errorMsg = lastError != null 
        ? '❌ Все модели недоступны. Ошибка: $lastError'
        : '❌ Все модели недоступны';
    
    debugPrint('[OpenRouter] $errorMsg');
    throw Exception(errorMsg);
  }

  /// DeepSeek R1 через /gpt4
  Future<String> sendToDeepSeek({
    required String message,
    List<Message>? history,
  }) async {
    final messages = [
      if (history != null)
        ...history.map((msg) => {'role': msg.role.name, 'content': msg.content}),
      {'role': 'user', 'content': message},
    ];

    return sendMessage(
      history: messages.map((m) => Message(
        id: DateTime.now().millisecondsSinceEpoch.toString(),
        content: m['content'] as String,
        role: MessageRole.values.firstWhere(
          (r) => r.name == m['role'],
          orElse: () => MessageRole.user,
        ),
        timestamp: DateTime.now(),
      )).toList(),
      model: 'deepseek/deepseek-r1-0528:free',
      maxTokens: 2000,
    );
  }

  /// Получить список доступных моделей
  Future<List<String>> getAvailableModels() async {
    if (!isInitialized) return [];

    try {
      final response = await http.get(
        Uri.parse('$_baseUrl/models'),
        headers: {'Authorization': 'Bearer $_apiKey'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body) as Map<String, dynamic>;
        final models = data['data'] as List<dynamic>;
        return models.map((m) => m['id'] as String).toList();
      }
    } catch (e) {
      debugPrint('[OpenRouter] Ошибка получения моделей: $e');
    }
    return [];
  }
}
