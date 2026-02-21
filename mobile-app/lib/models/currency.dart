import 'package:flutter/foundation.dart';

/// Модель данных для конвертера валют
@immutable
class CurrencyRate {
  final String baseCurrency;
  final String targetCurrency;
  final double rate;
  final DateTime timestamp;

  const CurrencyRate({
    required this.baseCurrency,
    required this.targetCurrency,
    required this.rate,
    required this.timestamp,
  });

  /// Конвертировать сумму
  double convert(double amount) => amount * rate;

  /// Обратный курс
  double get inverseRate => 1 / rate;

  Map<String, dynamic> toJson() {
    return {
      'baseCurrency': baseCurrency,
      'targetCurrency': targetCurrency,
      'rate': rate,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory CurrencyRate.fromJson(Map<String, dynamic> json) {
    return CurrencyRate(
      baseCurrency: json['baseCurrency'] as String,
      targetCurrency: json['targetCurrency'] as String,
      rate: (json['rate'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  @override
  String toString() => 'CurrencyRate($baseCurrency → $targetCurrency: $rate)';
}

/// Модель для основных валют
@immutable
class MainCurrencyRates {
  final double usdToKgs;
  final double usdToRub;
  final double cnyToKgs;
  final double eurToKgs;
  final DateTime timestamp;

  const MainCurrencyRates({
    required this.usdToKgs,
    required this.usdToRub,
    required this.cnyToKgs,
    required this.eurToKgs,
    required this.timestamp,
  });

  MainCurrencyRates copyWith({
    double? usdToKgs,
    double? usdToRub,
    double? cnyToKgs,
    double? eurToKgs,
    DateTime? timestamp,
  }) {
    return MainCurrencyRates(
      usdToKgs: usdToKgs ?? this.usdToKgs,
      usdToRub: usdToRub ?? this.usdToRub,
      cnyToKgs: cnyToKgs ?? this.cnyToKgs,
      eurToKgs: eurToKgs ?? this.eurToKgs,
      timestamp: timestamp ?? this.timestamp,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'usdToKgs': usdToKgs,
      'usdToRub': usdToRub,
      'cnyToKgs': cnyToKgs,
      'eurToKgs': eurToKgs,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory MainCurrencyRates.fromJson(Map<String, dynamic> json) {
    return MainCurrencyRates(
      usdToKgs: (json['usdToKgs'] as num).toDouble(),
      usdToRub: (json['usdToRub'] as num).toDouble(),
      cnyToKgs: (json['cnyToKgs'] as num).toDouble(),
      eurToKgs: (json['eurToKgs'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  factory MainCurrencyRates.empty() {
    return MainCurrencyRates(
      usdToKgs: 0,
      usdToRub: 0,
      cnyToKgs: 0,
      eurToKgs: 0,
      timestamp: DateTime.fromMillisecondsSinceEpoch(0),
    );
  }

  @override
  String toString() => 'MainCurrencyRates(USD→KGS: $usdToKgs, CNY→KGS: $cnyToKgs)';
}

/// Валюты с флагами и символами
class CurrencyInfo {
  final String code;
  final String name;
  final String symbol;
  final String flag;

  const CurrencyInfo({
    required this.code,
    required this.name,
    required this.symbol,
    required this.flag,
  });

  static const CurrencyInfo usd = CurrencyInfo(
    code: 'USD',
    name: 'Доллар США',
    symbol: '\$',
    flag: '🇺🇸',
  );

  static const CurrencyInfo kgs = CurrencyInfo(
    code: 'KGS',
    name: 'Кыргызский сом',
    symbol: 'с',
    flag: '🇰🇬',
  );

  static const CurrencyInfo rub = CurrencyInfo(
    code: 'RUB',
    name: 'Российский рубль',
    symbol: '₽',
    flag: '🇷🇺',
  );

  static const CurrencyInfo cny = CurrencyInfo(
    code: 'CNY',
    name: 'Китайский юань',
    symbol: '¥',
    flag: '🇨🇳',
  );

  static const CurrencyInfo eur = CurrencyInfo(
    code: 'EUR',
    name: 'Евро',
    symbol: '€',
    flag: '🇪🇺',
  );

  static Map<String, CurrencyInfo> get all => {
        'USD': usd,
        'KGS': kgs,
        'RUB': rub,
        'CNY': cny,
        'EUR': eur,
      };
}
