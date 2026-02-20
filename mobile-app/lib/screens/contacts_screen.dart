import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/settings_provider.dart';

class ContactsScreen extends StatefulWidget {
  const ContactsScreen({super.key});

  @override
  State<ContactsScreen> createState() => _ContactsScreenState();
}

class _ContactsScreenState extends State<ContactsScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  // Временные контакты (в реальной версии - из БД)
  final List<Map<String, String>> _contacts = [
    {'name': 'Алексей Иванов', 'phone': '+996 555 123 456'},
    {'name': 'Мария Петрова', 'phone': '+996 777 654 321'},
    {'name': 'Дмитрий Сидоров', 'phone': '+7 999 123 45 67'},
    {'name': 'Елена Козлова', 'phone': '+996 500 987 654'},
  ];

  List<Map<String, String>> get _filteredContacts {
    if (_searchQuery.isEmpty) return _contacts;
    return _contacts.where((contact) {
      final name = contact['name']!.toLowerCase();
      final phone = contact['phone']!.toLowerCase();
      final query = _searchQuery.toLowerCase();
      return name.contains(query) || phone.contains(query);
    }).toList();
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('📇 Контакты'),
        actions: [
          IconButton(
            icon: const Icon(Icons.person_add_outlined),
            tooltip: 'Добавить контакт',
            onPressed: () => _showAddContactDialog(),
          ),
        ],
      ),
      body: Column(
        children: [
          // Поиск
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: InputDecoration(
                hintText: 'Поиск контактов...',
                prefixIcon: const Icon(Icons.search),
                suffixIcon: _searchQuery.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          setState(() {
                            _searchQuery = '';
                            _searchController.clear();
                          });
                        },
                      )
                    : null,
              ),
              onChanged: (value) {
                setState(() {
                  _searchQuery = value;
                });
              },
            ),
          ),
          // Статистика
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 16),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Контактов: ${_filteredContacts.length}',
                  style: Theme.of(context).textTheme.bodySmall,
                ),
              ],
            ),
          ),
          const SizedBox(height: 8),
          // Список контактов
          Expanded(
            child: _filteredContacts.isEmpty
                ? _buildEmptyState()
                : ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: _filteredContacts.length,
                    itemBuilder: (context, index) {
                      final contact = _filteredContacts[index];
                      return _ContactCard(
                        name: contact['name']!,
                        phone: contact['phone']!,
                        onTap: () => _showContactDetails(contact),
                        onCall: () => _makeCall(contact['phone']!),
                        onMessage: () => _sendMessage(contact['phone']!),
                      );
                    },
                  ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddContactDialog(),
        icon: const Icon(Icons.person_add),
        label: const Text('Добавить'),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.contacts_outlined,
            size: 80,
            color: Theme.of(context).colorScheme.primary.withOpacity(0.5),
          ),
          const SizedBox(height: 24),
          Text(
            _searchQuery.isEmpty ? 'Контакты пусты' : 'Ничего не найдено',
            style: Theme.of(context).textTheme.titleLarge,
          ),
          const SizedBox(height: 8),
          if (_searchQuery.isEmpty)
            Text(
              'Добавьте первый контакт',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          if (_searchQuery.isEmpty) ...[
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => _showAddContactDialog(),
              icon: const Icon(Icons.person_add),
              label: const Text('Добавить контакт'),
            ),
          ],
        ],
      ),
    );
  }

  void _showAddContactDialog() {
    final nameController = TextEditingController();
    final phoneController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Добавить контакт'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(
              controller: nameController,
              decoration: const InputDecoration(
                labelText: 'Имя',
                prefixIcon: Icon(Icons.person_outline),
              ),
              autofocus: true,
            ),
            const SizedBox(height: 16),
            TextField(
              controller: phoneController,
              decoration: const InputDecoration(
                labelText: 'Телефон',
                prefixIcon: Icon(Icons.phone_outlined),
              ),
              keyboardType: TextInputType.phone,
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
              setState(() {
                _contacts.add({
                  'name': nameController.text.trim(),
                  'phone': phoneController.text.trim(),
                });
              });
              Navigator.pop(context);
            },
            child: const Text('Добавить'),
          ),
        ],
      ),
    );
  }

  void _showContactDetails(Map<String, String> contact) {
    showModalBottomSheet(
      context: context,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            CircleAvatar(
              radius: 40,
              backgroundColor: Theme.of(context).colorScheme.primaryContainer,
              child: Text(
                contact['name']![0].toUpperCase(),
                style: Theme.of(context).textTheme.headlineMedium,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              contact['name']!,
              style: Theme.of(context).textTheme.headlineSmall,
            ),
            const SizedBox(height: 8),
            Text(
              contact['phone']!,
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 24),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceEvenly,
              children: [
                _ActionButton(
                  icon: Icons.phone,
                  label: 'Позвонить',
                  onPressed: () {
                    Navigator.pop(context);
                    _makeCall(contact['phone']!);
                  },
                ),
                _ActionButton(
                  icon: Icons.message,
                  label: 'SMS',
                  onPressed: () {
                    Navigator.pop(context);
                    _sendMessage(contact['phone']!);
                  },
                ),
                _ActionButton(
                  icon: Icons.copy,
                  label: 'Копия',
                  onPressed: () {
                    Clipboard.setData(ClipboardData(text: contact['phone']!));
                    Navigator.pop(context);
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(content: Text('Номер скопирован')),
                    );
                  },
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _makeCall(String phoneNumber) async {
    final url = Uri.parse('tel:$phoneNumber');
    if (await canLaunchUrl(url)) {
      await launchUrl(url);
    } else {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Не удалось открыть телефон')),
      );
    }
  }

  Future<void> _sendMessage(String phoneNumber) async {
    // Открываем WhatsApp или SMS
    final whatsappUrl = Uri.parse('https://wa.me/$phoneNumber');
    if (await canLaunchUrl(whatsappUrl)) {
      await launchUrl(whatsappUrl);
    } else {
      final smsUrl = Uri.parse('sms:$phoneNumber');
      if (await canLaunchUrl(smsUrl)) {
        await launchUrl(smsUrl);
      }
    }
  }
}

class _ContactCard extends StatelessWidget {
  final String name;
  final String phone;
  final VoidCallback onTap;
  final VoidCallback onCall;
  final VoidCallback onMessage;

  const _ContactCard({
    required this.name,
    required this.phone,
    required this.onTap,
    required this.onCall,
    required this.onMessage,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        onTap: onTap,
        leading: CircleAvatar(
          backgroundColor: Theme.of(context).colorScheme.primaryContainer,
          child: Text(
            name[0].toUpperCase(),
            style: Theme.of(context).textTheme.titleMedium,
          ),
        ),
        title: Text(name),
        subtitle: Text(phone),
        trailing: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            IconButton(
              icon: const Icon(Icons.phone_outlined),
              onPressed: onCall,
              tooltip: 'Позвонить',
            ),
            IconButton(
              icon: const Icon(Icons.message_outlined),
              onPressed: onMessage,
              tooltip: 'Сообщение',
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionButton extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onPressed;

  const _ActionButton({
    required this.icon,
    required this.label,
    required this.onPressed,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Container(
          width: 56,
          height: 56,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            shape: BoxShape.circle,
          ),
          child: IconButton(
            icon: Icon(icon),
            onPressed: onPressed,
          ),
        ),
        const SizedBox(height: 8),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}
