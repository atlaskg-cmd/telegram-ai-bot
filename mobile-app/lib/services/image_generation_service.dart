import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

/// Сервис генерации изображений (Multi-provider fallback)
class ImageGenerationService {
  static final ImageGenerationService _instance = ImageGenerationService._internal();
  factory ImageGenerationService() => _instance;
  ImageGenerationService._internal();

  String? _hfToken;
  String? _cfApiToken;
  String? _cfAccountId;

  /// Инициализация с токенами
  void init({
    String? hfToken,
    String? cfApiToken,
    String? cfAccountId,
  }) {
    _hfToken = hfToken;
    _cfApiToken = cfApiToken;
    _cfAccountId = cfAccountId;
    debugPrint('[ImageGen] Инициализирован (HF: ${hfToken != null}, CF: ${cfApiToken != null})');
  }

  /// Сгенерировать изображение по описанию
  Future<Uint8List?> generateImage({
    required String prompt,
    int width = 512,
    int height = 512,
  }) async {
    debugPrint('[ImageGen] Генерация изображения: $prompt');

    // Пробуем провайдеры по порядку
    // 1. Hugging Face
    if (_hfToken != null && _hfToken!.isNotEmpty) {
      try {
        final result = await _generateWithHF(prompt, width, height);
        if (result != null) {
          debugPrint('[ImageGen] Успех: Hugging Face');
          return result;
        }
      } catch (e) {
        debugPrint('[ImageGen] HF ошибка: $e');
      }
    }

    // 2. Cloudflare
    if (_cfApiToken != null && _cfAccountId != null) {
      try {
        final result = await _generateWithCloudflare(prompt, width, height);
        if (result != null) {
          debugPrint('[ImageGen] Успех: Cloudflare');
          return result;
        }
      } catch (e) {
        debugPrint('[ImageGen] CF ошибка: $e');
      }
    }

    // 3. Pollinations.ai (всегда бесплатно, без токена)
    try {
      final result = await _generateWithPollinations(prompt, width, height);
      if (result != null) {
        debugPrint('[ImageGen] Успех: Pollinations.ai');
        return result;
      }
    } catch (e) {
      debugPrint('[ImageGen] Pollinations ошибка: $e');
    }

    return null;
  }

  /// Hugging Face (FLUX.1 schnell)
  Future<Uint8List?> _generateWithHF(
    String prompt,
    int width,
    int height,
  ) async {
    if (_hfToken == null) return null;

    final response = await http.post(
      Uri.parse('https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell'),
      headers: {
        'Authorization': 'Bearer $_hfToken',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'inputs': prompt,
        'parameters': {
          'width': width,
          'height': height,
          'num_inference_steps': 4,
        },
      }),
    ).timeout(const Duration(seconds: 60));

    if (response.statusCode == 200) {
      return response.bodyBytes;
    } else if (response.statusCode == 503) {
      // Модель загружается
      debugPrint('[ImageGen] HF модель загружается, пробуем позже...');
      return null;
    } else {
      throw Exception('HF API error: ${response.statusCode}');
    }
  }

  /// Cloudflare Workers AI
  Future<Uint8List?> _generateWithCloudflare(
    String prompt,
    int width,
    int height,
  ) async {
    if (_cfApiToken == null || _cfAccountId == null) return null;

    final response = await http.post(
      Uri.parse(
        'https://api.cloudflare.com/client/v4/accounts/$_cfAccountId'
        '/ai/run/@cf/stabilityai/stable-diffusion-xl-base-1.0',
      ),
      headers: {
        'Authorization': 'Bearer $_cfApiToken',
        'Content-Type': 'application/json',
      },
      body: jsonEncode({
        'prompt': prompt,
        'width': width,
        'height': height,
      }),
    ).timeout(const Duration(seconds: 60));

    if (response.statusCode == 200) {
      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final imageBase64 = data['result']['image'] as String?;
      if (imageBase64 != null) {
        return base64Decode(imageBase64);
      }
      return null;
    } else {
      throw Exception('Cloudflare API error: ${response.statusCode}');
    }
  }

  /// Pollinations.ai (бесплатно, без токена)
  Future<Uint8List?> _generateWithPollinations(
    String prompt,
    int width,
    int height,
  ) async {
    final encodedPrompt = Uri.encodeComponent(prompt);
    final url = 'https://image.pollinations.ai/prompt/$encodedPrompt'
        '?width=$width&height=$height&seed=${DateTime.now().millisecondsSinceEpoch}'
        '&nologo=true';

    final response = await http.get(Uri.parse(url)).timeout(
      const Duration(seconds: 60),
    );

    if (response.statusCode == 200) {
      return response.bodyBytes;
    } else {
      throw Exception('Pollinations error: ${response.statusCode}');
    }
  }

  /// DeepSeek Chat (для /gpt4 команды)
  Future<String> chat({
    required String message,
    List<Message>? history,
  }) async {
    // Используем OpenRouter для DeepSeek
    final openrouter = OpenRouterService();
    return openrouter.sendToDeepSeek(
      message: message,
      history: history,
    );
  }
}
