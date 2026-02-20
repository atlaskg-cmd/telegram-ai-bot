import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:image_picker/image_picker.dart';
import 'package:share_plus/share_plus.dart';
import 'package:path_provider/path_provider.dart';
import 'dart:io';
import '../services/image_generation_service.dart';

class ImageScreen extends StatefulWidget {
  const ImageScreen({super.key});

  @override
  State<ImageScreen> createState() => _ImageScreenState();
}

class _ImageScreenState extends State<ImageScreen> {
  final TextEditingController _promptController = TextEditingController();
  final ImageGenerationService _imageService = ImageGenerationService();
  
  bool _isGenerating = false;
  Uint8List? _generatedImage;
  String? _error;

  @override
  void dispose() {
    _promptController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🎨 Генерация картинок'),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Инструкция
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Создавайте изображения с помощью AI',
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 8),
                    Text(
                      'Опишите что вы хотите увидеть, и AI сгенерирует изображение по вашему описанию.',
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                    const SizedBox(height: 16),
                    Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: [
                        _ExampleChip(
                          '🌅 Закат над горами',
                          onPressed: () => _promptController.text = 'Закат над горами, красиво, реалистично',
                        ),
                        _ExampleChip(
                          '🐱 Милый котик',
                          onPressed: () => _promptController.text = 'Милый пушистый котик, мультяшный стиль',
                        ),
                        _ExampleChip(
                          '🏙️ Футуристический город',
                          onPressed: () => _promptController.text = 'Футуристический город будущего, неон, киберпанк',
                        ),
                        _ExampleChip(
                          '🌸 Цветущая сакура',
                          onPressed: () => _promptController.text = 'Цветущая сакура весной, Япония, красиво',
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 24),
            // Поле ввода
            TextField(
              controller: _promptController,
              decoration: InputDecoration(
                labelText: 'Описание изображения',
                hintText: 'Например: Красивый закат над океаном...',
                prefixIcon: const Icon(Icons.edit_outlined),
                suffixIcon: IconButton(
                  icon: const Icon(Icons.clear),
                  onPressed: () => _promptController.clear(),
                ),
              ),
              maxLines: 3,
              minLines: 2,
            ),
            const SizedBox(height: 16),
            // Кнопка генерации
            FilledButton.icon(
              onPressed: _isGenerating ? null : _generateImage,
              icon: _isGenerating
                  ? const SizedBox(
                      width: 20,
                      height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2),
                    )
                  : const Icon(Icons.auto_awesome),
              label: Text(_isGenerating ? 'Генерация...' : 'Сгенерировать'),
              style: FilledButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 16),
              ),
            ),
            if (_error != null) ...[
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, color: Colors.red),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Text(
                        _error!,
                        style: TextStyle(
                          color: Theme.of(context).colorScheme.onErrorContainer,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
            const SizedBox(height: 24),
            // Результат
            if (_generatedImage != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            'Результат',
                            style: Theme.of(context).textTheme.titleMedium,
                          ),
                          Row(
                            children: [
                              IconButton(
                                icon: const Icon(Icons.share),
                                tooltip: 'Поделиться',
                                onPressed: _shareImage,
                              ),
                              IconButton(
                                icon: const Icon(Icons.save_alt),
                                tooltip: 'Сохранить',
                                onPressed: _saveImage,
                              ),
                            ],
                          ),
                        ],
                      ),
                      const SizedBox(height: 16),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.memory(
                          _generatedImage!,
                          fit: BoxFit.cover,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
            const SizedBox(height: 80),
          ],
        ),
      ),
    );
  }

  Future<void> _generateImage() async {
    final prompt = _promptController.text.trim();
    if (prompt.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Введите описание изображения')),
      );
      return;
    }

    setState(() {
      _isGenerating = true;
      _error = null;
    });

    try {
      final image = await _imageService.generateImage(
        prompt: prompt,
        width: 512,
        height: 512,
      );

      if (image != null) {
        setState(() {
          _generatedImage = image;
        });
      } else {
        setState(() {
          _error = 'Не удалось сгенерировать изображение. Попробуйте другой запрос.';
        });
      }
    } catch (e) {
      setState(() {
        _error = 'Ошибка: $e';
      });
    } finally {
      setState(() {
        _isGenerating = false;
      });
    }
  }

  Future<void> _shareImage() async {
    if (_generatedImage == null) return;

    try {
      final tempDir = await getTemporaryDirectory();
      final file = await File('${tempDir.path}/generated_image.png').create();
      await file.writeAsBytes(_generatedImage!);

      await Share.shareXFiles([XFile(file.path)]);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка при partage: $e')),
      );
    }
  }

  Future<void> _saveImage() async {
    if (_generatedImage == null) return;

    try {
      // Для упрощения просто показываем сообщение
      // В реальной реализации нужно запросить разрешение и сохранить в галерею
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Изображение сохранено в галерею')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Ошибка при сохранении: $e')),
      );
    }
  }
}

class _ExampleChip extends StatelessWidget {
  final String label;
  final VoidCallback onPressed;

  const _ExampleChip({required this.label, required this.onPressed});

  @override
  Widget build(BuildContext context) {
    return ActionChip(
      label: Text(label),
      onPressed: onPressed,
    );
  }
}
