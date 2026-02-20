import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../providers/providers.dart';
import 'chat_screen.dart';
import 'weather_screen.dart';
import 'currency_screen.dart';
import 'crypto_screen.dart';
import 'news_screen.dart';
import 'image_screen.dart';
import 'contacts_screen.dart';
import 'settings_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _selectedIndex = 0;

  final List<Widget> _screens = [
    const ChatScreen(),      // AI Чат
    const WeatherScreen(),   // Погода
    const CurrencyScreen(),  // Валюты
    const CryptoScreen(),    // Крипто
    const NewsScreen(),      // Новости
    const ImageScreen(),     // Картинки
    const ContactsScreen(),  // Контакты
    const SettingsScreen(),  // Настройки
  ];

  @override
  void initState() {
    super.initState();
    // Предзагружаем данные
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<WeatherProvider>().loadAllCities();
      context.read<CurrencyProvider>().loadRates();
      context.read<CryptoProvider>().loadCoins();
      context.read<NewsProvider>().loadNews();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _selectedIndex,
        children: _screens,
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _selectedIndex,
        onDestinationSelected: (index) {
          setState(() {
            _selectedIndex = index;
          });
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.smart_toy_outlined),
            selectedIcon: Icon(Icons.smart_toy),
            label: 'AI Чат',
          ),
          NavigationDestination(
            icon: Icon(Icons.cloud_outlined),
            selectedIcon: Icon(Icons.cloud),
            label: 'Погода',
          ),
          NavigationDestination(
            icon: Icon(Icons.currency_exchange_outlined),
            selectedIcon: Icon(Icons.currency_exchange),
            label: 'Валюты',
          ),
          NavigationDestination(
            icon: Icon(Icons.trending_up_outlined),
            selectedIcon: Icon(Icons.trending_up),
            label: 'Крипто',
          ),
          NavigationDestination(
            icon: Icon(Icons.newspaper_outlined),
            selectedIcon: Icon(Icons.newspaper),
            label: 'Новости',
          ),
          NavigationDestination(
            icon: Icon(Icons.image_outlined),
            selectedIcon: Icon(Icons.image),
            label: 'Картинки',
          ),
          NavigationDestination(
            icon: Icon(Icons.contacts_outlined),
            selectedIcon: Icon(Icons.contacts),
            label: 'Контакты',
          ),
          NavigationDestination(
            icon: Icon(Icons.settings_outlined),
            selectedIcon: Icon(Icons.settings),
            label: 'Настройки',
          ),
        ],
      ),
    );
  }
}
