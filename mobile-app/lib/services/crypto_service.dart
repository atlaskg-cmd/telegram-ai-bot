import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

/// Сервис криптовалют (CoinGecko API)
class CryptoService {
  static final CryptoService _instance = CryptoService._internal();
  factory CryptoService() => _instance;
  CryptoService._internal();

  final String _baseUrl = 'https://api.coingecko.com/api/v3';

  /// Получить курсы популярных криптовалют
  Future<List<CryptoCoin>> getPopularCoins() async {
    try {
      debugPrint('[Crypto] Запрос курсов криптовалют...');

      final ids = PopularCrypto.coins.map((c) => c['id']).join(',');
      final url = Uri.parse(
        '$_baseUrl/coins/markets/usd'
        '?ids=$ids'
        '&vs_currency=usd'
        '&order=market_cap_desc'
        '&price_change_percentage=24h',
      );

      final response = await http.get(url).timeout(const Duration(seconds: 30));

      if (response.statusCode != 200) {
        throw Exception('Ошибка CoinGecko API: ${response.statusCode}');
      }

      final data = jsonDecode(response.body) as List<dynamic>;
      
      return data.map((item) {
        return CryptoCoin(
          id: item['id'] as String,
          symbol: (item['symbol'] as String).toUpperCase(),
          name: item['name'] as String,
          price: (item['current_price'] as num).toDouble(),
          priceChange24h: (item['price_change_percentage_24h'] as num?)?.toDouble() ?? 0.0,
          marketCap: (item['market_cap'] as num).toDouble(),
          volume24h: (item['total_volume'] as num).toDouble(),
          timestamp: DateTime.now(),
        );
      }).toList();
    } catch (e) {
      debugPrint('[Crypto] Ошибка: $e');
      rethrow;
    }
  }

  /// Получить конкретную криптовалюту
  Future<CryptoCoin?> getCoin(String coinId) async {
    try {
      final coins = await getPopularCoins();
      return coins.firstWhere((c) => c.id == coinId);
    } catch (e) {
      debugPrint('[Crypto] Ошибка получения $coinId: $e');
      return null;
    }
  }

  /// Получить портфель пользователя из базы данных
  /// (в реальной реализации - запрос к backend API)
  Future<CryptoPortfolio> getPortfolio(String telegramId) async {
    // TODO: Интеграция с backend API для получения портфеля из БД
    // Пока возвращаем пустой портфель
    return const CryptoPortfolio(items: []);
  }

  /// Добавить монету в портфель
  Future<bool> addToPortfolio({
    required String telegramId,
    required String coinId,
    required String symbol,
    required String name,
    required double amount,
    required double avgBuyPrice,
  }) async {
    // TODO: Интеграция с backend API
    debugPrint('[Crypto] Добавить в портфель: $symbol, $amount шт, \$$avgBuyPrice');
    return true;
  }

  /// Удалить монету из портфеля
  Future<bool> removeFromPortfolio({
    required String telegramId,
    required String coinId,
  }) async {
    // TODO: Интеграция с backend API
    debugPrint('[Crypto] Удалить из портфеля: $coinId');
    return true;
  }

  /// Обновить цену монеты в портфеле
  Future<CryptoPortfolioItem?> updatePortfolioItemPrice(
    CryptoPortfolioItem item,
    double newPrice,
  ) async {
    return item.copyWith(currentPrice: newPrice);
  }

  /// Получить историю цены для графика
  Future<Map<String, double>> getPriceHistory({
    required String coinId,
    required int days,
  }) async {
    try {
      final url = Uri.parse(
        '$_baseUrl/coins/$coinId/market_chart'
        '?vs_currency=usd'
        '&days=$days',
      );

      final response = await http.get(url).timeout(const Duration(seconds: 30));

      if (response.statusCode != 200) {
        return {};
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final prices = data['prices'] as List<dynamic>;

      return Map.fromEntries(
        prices.map((item) {
          final timestamp = DateTime.fromMillisecondsSinceEpoch(item[0] as int);
          final price = (item[1] as num).toDouble();
          return MapEntry(timestamp.toIso8601String(), price);
        }),
      );
    } catch (e) {
      debugPrint('[Crypto] Ошибка получения истории: $e');
      return {};
    }
  }
}
