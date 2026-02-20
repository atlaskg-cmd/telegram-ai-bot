import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/settings_provider.dart';
import '../providers/chat_provider.dart';
import '../providers/news_provider.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('⚙️ Настройки'),
      ),
      body: Consumer<SettingsProvider>(
        builder: (context, settingsProvider, child) {
          return ListView(
            padding: const EdgeInsets.all(16),
            children: [
              // Профиль
              _buildProfileCard(context, settingsProvider),
              const SizedBox(height: 24),
              // Внешний вид
              _buildSectionTitle('Внешний вид'),
              Card(
                child: Column(
                  children: [
                    SwitchListTile(
                      title: const Text('Тёмная тема'),
                      subtitle: const Text('Использовать тёмную тему оформления'),
                      value: settingsProvider.themeMode == ThemeMode.dark,
                      onChanged: (value) {
                        settingsProvider.toggleDarkMode(value);
                      },
                      secondary: const Icon(Icons.dark_mode_outlined),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Язык'),
                      subtitle: const Text('Русский'),
                      trailing: const Icon(Icons.language),
                      onTap: () {
                        ScaffoldMessenger.of(context).showSnackBar(
                          const SnackBar(content: Text('Смена языка в разработке')),
                        );
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // AI и Голос
              _buildSectionTitle('AI и Голос'),
              Card(
                child: Column(
                  children: [
                    SwitchListTile(
                      title: const Text('Голосовые ответы'),
                      subtitle: const Text('Озвучивать ответы AI'),
                      value: settingsProvider.voiceModeEnabled,
                      onChanged: (value) {
                        settingsProvider.toggleVoiceMode(value);
                      },
                      secondary: const Icon(Icons.volume_up_outlined),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Голос для озвучки'),
                      subtitle: Text(settingsProvider.preferredVoice),
                      trailing: const Icon(Icons.mic),
                      onTap: () {
                        _showVoiceSelectionDialog(context, settingsProvider);
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // Новости
              _buildSectionTitle('Новости'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      title: const Text('Интересы'),
                      subtitle: const Text('Выберите категории новостей'),
                      trailing: const Icon(Icons.interests),
                      onTap: () {
                        _showInterestsDialog(context, settingsProvider);
                      },
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Время дайджеста'),
                      subtitle: Text(
                        settingsProvider.digestScheduleTime ?? 'Не настроено',
                      ),
                      trailing: const Icon(Icons.schedule),
                      onTap: () {
                        _showDigestTimeDialog(context, settingsProvider);
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // API Ключи
              _buildSectionTitle('API Ключи'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      title: const Text('OpenRouter API'),
                      subtitle: Text(
                        settingsProvider.openrouterApiKey != null &&
                                settingsProvider.openrouterApiKey!.isNotEmpty
                            ? '✓ Настроен'
                            : 'Не настроен',
                      ),
                      trailing: const Icon(Icons.key),
                      onTap: () {
                        _showApiKeyDialog(
                          context,
                          'OpenRouter API Key',
                          settingsProvider.openrouterApiKey ?? '',
                          (value) => settingsProvider.saveApiKey(
                            'openrouter_api_key',
                            value,
                          ),
                        );
                      },
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Weather API'),
                      subtitle: Text(
                        settingsProvider.weatherApiKey != null &&
                                settingsProvider.weatherApiKey!.isNotEmpty
                            ? '✓ Настроен'
                            : 'Не настроен',
                      ),
                      trailing: const Icon(Icons.cloud),
                      onTap: () {
                        _showApiKeyDialog(
                          context,
                          'Weather API Key',
                          settingsProvider.weatherApiKey ?? '',
                          (value) => settingsProvider.saveApiKey(
                            'weather_api_key',
                            value,
                          ),
                        );
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // О приложении
              _buildSectionTitle('О приложении'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      title: const Text('Версия'),
                      subtitle: const Text('1.0.0'),
                      trailing: const Icon(Icons.info_outline),
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('GitHub'),
                      trailing: const Icon(Icons.code),
                      onTap: () async {
                        final url = Uri.parse(
                          'https://github.com/your-username/telegram-ai-bot',
                        );
                        if (await canLaunchUrl(url)) {
                          await launchUrl(url, mode: LaunchMode.externalApplication);
                        }
                      },
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Политика конфиденциальности'),
                      trailing: const Icon(Icons.privacy_tip_outlined),
                      onTap: () {
                        _showPrivacyPolicyDialog(context);
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // Данные
              _buildSectionTitle('Данные'),
              Card(
                child: Column(
                  children: [
                    ListTile(
                      title: const Text('Очистить историю чата'),
                      subtitle: const Text('Удалить все сообщения'),
                      trailing: const Icon(Icons.delete_outline, color: Colors.red),
                      onTap: () {
                        _confirmClearChatHistory(context);
                      },
                    ),
                    const Divider(height: 1),
                    ListTile(
                      title: const Text('Сбросить все настройки'),
                      subtitle: const Text('Вернуть настройки по умолчанию'),
                      trailing: const Icon(Icons.restore, color: Colors.orange),
                      onTap: () {
                        _confirmResetSettings(context, settingsProvider);
                      },
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 80),
            ],
          );
        },
      ),
    );
  }

  Widget _buildProfileCard(
    BuildContext context,
    SettingsProvider settingsProvider,
  ) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            CircleAvatar(
              radius: 30,
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: const Text('👤', style: TextStyle(fontSize: 32)),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Пользователь',
                    style: Theme.of(context).textTheme.titleMedium,
                  ),
                  Text(
                    settingsProvider.telegramId ?? 'Не авторизован',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
                ],
              ),
            ),
            IconButton(
              icon: const Icon(Icons.edit_outlined),
              onPressed: () {
                _showTelegramIdDialog(context, settingsProvider);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 12),
      child: Text(
        title,
        style: Theme.of(context).textTheme.titleMedium?.copyWith(
          fontWeight: FontWeight.bold,
          color: Theme.of(context).colorScheme.primary,
        ),
      ),
    );
  }

  void _showVoiceSelectionDialog(
    BuildContext context,
    SettingsProvider settingsProvider,
  ) {
    final voices = [
      {'id': 'ru-RU-SvetlanaNeural', 'name': 'Светлана (Женский)'},
      {'id': 'ru-RU-DmitryNeural', 'name': 'Дмитрий (Мужской)'},
    ];

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Выберите голос'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: voices.map((voice) {
            return ListTile(
              title: Text(voice['name']!),
              selected: settingsProvider.preferredVoice == voice['id'],
              onTap: () {
                settingsProvider.setPreferredVoice(voice['id']!);
                Navigator.pop(context);
              },
            );
          }).toList(),
        ),
      ),
    );
  }

  void _showInterestsDialog(
    BuildContext context,
    SettingsProvider settingsProvider,
  ) {
    final interests = context.read<NewsProvider>().interests;
    final categories = [
      {'id': 'kyrgyzstan', 'name': 'Кыргызстан', 'icon': '🇰🇬'},
      {'id': 'technology', 'name': 'Технологии', 'icon': '💻'},
      {'id': 'ai', 'name': 'ИИ', 'icon': '🤖'},
      {'id': 'science', 'name': 'Наука', 'icon': '🔬'},
      {'id': 'world', 'name': 'Мир', 'icon': '🌍'},
      {'id': 'sports', 'name': 'Спорт', 'icon': '⚽'},
      {'id': 'economy', 'name': 'Экономика', 'icon': '💰'},
      {'id': 'crypto', 'name': 'Крипто', 'icon': '₿'},
    ];

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Мои интересы'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: categories.map((category) {
              final isSelected = interests.hasInterest(category['id']!);
              return CheckboxListTile(
                title: Text('${category['icon']} ${category['name']}'),
                value: isSelected,
                onChanged: (value) {
                  context.read<NewsProvider>().toggleInterest(category['id']!);
                },
              );
            }).toList(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Готово'),
          ),
        ],
      ),
    );
  }

  void _showDigestTimeDialog(
    BuildContext context,
    SettingsProvider settingsProvider,
  ) {
    final time = settingsProvider.digestScheduleTime ?? '09:00';
    final hours = int.parse(time.split(':')[0]);
    final minutes = int.parse(time.split(':')[1]);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Время дайджеста'),
        content: StatefulBuilder(
          builder: (context, setDialogState) {
            return Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text('Выберите время для получения дайджеста'),
                const SizedBox(height: 16),
                Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.schedule, size: 48),
                    const SizedBox(width: 16),
                    Text(
                      '$hours:${minutes.toString().padLeft(2, '0')}',
                      style: Theme.of(context).textTheme.headlineMedium,
                    ),
                  ],
                ),
              ],
            );
          },
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () {
              settingsProvider.setDigestScheduleTime(time);
              Navigator.pop(context);
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  void _showApiKeyDialog(
    BuildContext context,
    String title,
    String currentValue,
    Function(String) onSave,
  ) {
    final controller = TextEditingController(text: currentValue);

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(title),
        content: TextField(
          controller: controller,
          decoration: const InputDecoration(
            hintText: 'Введите API ключ',
            border: OutlineInputBorder(),
          ),
          obscureText: true,
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () {
              onSave(controller.text.trim());
              Navigator.pop(context);
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  void _showTelegramIdDialog(
    BuildContext context,
    SettingsProvider settingsProvider,
  ) {
    final controller = TextEditingController(
      text: settingsProvider.telegramId ?? '',
    );

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Telegram ID'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Укажите ваш Telegram ID для синхронизации с ботом',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: controller,
              decoration: const InputDecoration(
                hintText: '123456789',
                border: OutlineInputBorder(),
              ),
              keyboardType: TextInputType.number,
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () {
              settingsProvider.setTelegramId(controller.text.trim());
              Navigator.pop(context);
            },
            child: const Text('Сохранить'),
          ),
        ],
      ),
    );
  }

  void _confirmClearChatHistory(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Очистить историю?'),
        content: const Text(
          'Это действие удалит все сообщения из истории чата. Продолжить?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () {
              context.read<ChatProvider>().clearHistory();
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('История очищена')),
              );
            },
            style: FilledButton.styleFrom(
              backgroundColor: Theme.of(context).colorScheme.error,
            ),
            child: const Text('Очистить'),
          ),
        ],
      ),
    );
  }

  void _confirmResetSettings(
    BuildContext context,
    SettingsProvider settingsProvider,
  ) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Сброс настроек?'),
        content: const Text(
          'Это действие сбросит все настройки к значениям по умолчанию. Продолжить?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () {
              settingsProvider.clearAllData();
              Navigator.pop(context);
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Настройки сброшены')),
              );
            },
            style: FilledButton.styleFrom(
              backgroundColor: Colors.orange,
            ),
            child: const Text('Сбросить'),
          ),
        ],
      ),
    );
  }

  void _showPrivacyPolicyDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Политика конфиденциальности'),
        content: SingleChildScrollView(
          child: Text(
            'Это приложение не собирает и не хранит ваши персональные данные.\n\n'
            'Все сообщения сохраняются только на вашем устройстве.\n\n'
            'API ключи хранятся в защищенном хранилище устройства.\n\n'
            'Для работы приложения используются сторонние сервисы:\n'
            '• OpenRouter AI - для AI чата\n'
            '• Open-Meteo - для погоды\n'
            '• Exchangerate API - для курсов валют\n'
            '• CoinGecko - для криптовалют\n',
          ),
        ),
        actions: [
          FilledButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Понятно'),
          ),
        ],
      ),
    );
  }
}
