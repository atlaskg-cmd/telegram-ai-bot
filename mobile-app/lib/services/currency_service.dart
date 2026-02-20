import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

/// Сервис конвертера валют
class CurrencyService {
  static final CurrencyService _instance = CurrencyService._internal();
  factory CurrencyService() => _instance;
  CurrencyService._internal();

  /// Получить основные курсы валют
  Future<MainCurrencyRates> getMainRates() async {
    try {
      debugPrint('[Currency] Запрос курсов валют...');

      // Запрашиваем USD как базовую
      final usdResponse = await http.get(
        Uri.parse('https://api.exchangerate-api.com/v4/latest/USD'),
      ).timeout(const Duration(seconds: 15));

      if (usdResponse.statusCode != 200) {
        throw Exception('Ошибка API валют: ${usdResponse.statusCode}');
      }

      final usdData = jsonDecode(usdResponse.body) as Map<String, dynamic>;
      final usdRates = usdData['rates'] as Map<String, dynamic>;

      final usdToKgs = (usdRates['KGS'] as num).toDouble();
      final usdToRub = (usdRates['RUB'] as num).toDouble();
      final usdToEur = (usdRates['EUR'] as num).toDouble();

      // Запрашиваем CNY как базовую
      final cnyResponse = await http.get(
        Uri.parse('https://api.exchangerate-api.com/v4/latest/CNY'),
      ).timeout(const Duration(seconds: 15));

      double cnyToKgs;
      
      if (cnyResponse.statusCode == 200) {
        final cnyData = jsonDecode(cnyResponse.body) as Map<String, dynamic>;
        final cnyRates = cnyData['rates'] as Map<String, dynamic>;
        cnyToKgs = (cnyRates['KGS'] as num).toDouble();
      } else {
        // Fallback: расчет через USD
        final cnyToUsd = (usdRates['CNY'] as num).toDouble();
        cnyToKgs = usdToKgs / cnyToUsd;
      }

      // EUR к KGS
      final eurToKgs = usdToKgs * usdToEur;

      return MainCurrencyRates(
        usdToKgs: usdToKgs,
        usdToRub: usdToRub,
        cnyToKgs: cnyToKgs,
        eurToKgs: eurToKgs,
        timestamp: DateTime.now(),
      );
    } catch (e) {
      debugPrint('[Currency] Ошибка: $e');
      rethrow;
    }
  }

  /// Конвертировать CNY в KGS
  Future<double> cnyToKgs(double amount) async {
    final rates = await getMainRates();
    return amount * rates.cnyToKgs;
  }

  /// Конвертировать KGS в CNY
  Future<double> kgsToCny(double amount) async {
    final rates = await getMainRates();
    return amount / rates.cnyToKgs;
  }

  /// Конвертировать USD в KGS
  Future<double> usdToKgs(double amount) async {
    final rates = await getMainRates();
    return amount * rates.usdToKgs;
  }

  /// Конвертировать EUR в KGS
  Future<double> eurToKgs(double amount) async {
    final rates = await getMainRates();
    return amount * rates.eurToKgs;
  }

  /// Форматировать число с пробелами (1 000.00)
  String formatNumber(num value) {
    return value.toStringAsFixed(2).replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]} ',
    );
  }
}
