import 'package:flutter/foundation.dart';

/// Модель криптовалюты
@immutable
class CryptoCoin {
  final String id;
  final String symbol;
  final String name;
  final double price;
  final double priceChange24h;
  final double marketCap;
  final double volume24h;
  final DateTime timestamp;

  const CryptoCoin({
    required this.id,
    required this.symbol,
    required this.name,
    required this.price,
    required this.priceChange24h,
    required this.marketCap,
    required this.volume24h,
    required this.timestamp,
  });

  /// Получить индикатор изменения цены
  String get priceChangeIndicator {
    if (priceChange24h > 0) return '🟢';
    if (priceChange24h < 0) return '🔴';
    return '⚪';
  }

  /// Форматированное изменение цены
  String get formattedPriceChange {
    final sign = priceChange24h >= 0 ? '+' : '';
    return '$sign${priceChange24h.toStringAsFixed(2)}%';
  }

  CryptoCoin copyWith({
    String? id,
    String? symbol,
    String? name,
    double? price,
    double? priceChange24h,
    double? marketCap,
    double? volume24h,
    DateTime? timestamp,
  }) {
    return CryptoCoin(
      id: id ?? this.id,
      symbol: symbol ?? this.symbol,
      name: name ?? this.name,
      price: price ?? this.price,
      priceChange24h: priceChange24h ?? this.priceChange24h,
      marketCap: marketCap ?? this.marketCap,
      volume24h: volume24h ?? this.volume24h,
      timestamp: timestamp ?? this.timestamp,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'symbol': symbol,
      'name': name,
      'price': price,
      'priceChange24h': priceChange24h,
      'marketCap': marketCap,
      'volume24h': volume24h,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory CryptoCoin.fromJson(Map<String, dynamic> json) {
    return CryptoCoin(
      id: json['id'] as String,
      symbol: json['symbol'] as String,
      name: json['name'] as String,
      price: (json['price'] as num).toDouble(),
      priceChange24h: (json['priceChange24h'] as num).toDouble(),
      marketCap: (json['marketCap'] as num).toDouble(),
      volume24h: (json['volume24h'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  @override
  String toString() => 'CryptoCoin($symbol: \$$price, ${formattedPriceChange})';
}

/// Модель позиции в портфеле
@immutable
class CryptoPortfolioItem {
  final String coinId;
  final String symbol;
  final String name;
  final double amount;
  final double avgBuyPrice;
  final double currentPrice;

  const CryptoPortfolioItem({
    required this.coinId,
    required this.symbol,
    required this.name,
    required this.amount,
    required this.avgBuyPrice,
    required this.currentPrice,
  });

  /// Текущая стоимость позиции
  double get currentValue => amount * currentPrice;

  /// Стоимость покупки
  double get buyValue => amount * avgBuyPrice;

  /// Прибыль/убыток
  double get profitLoss => currentValue - buyValue;

  /// Процент прибыли/убытка
  double get profitLossPercent {
    if (buyValue == 0) return 0;
    return ((currentValue - buyValue) / buyValue) * 100;
  }

  /// Индикатор прибыли/убытка
  String get profitLossIndicator {
    if (profitLoss > 0) return '🟢';
    if (profitLoss < 0) return '🔴';
    return '⚪';
  }

  CryptoPortfolioItem copyWith({
    String? coinId,
    String? symbol,
    String? name,
    double? amount,
    double? avgBuyPrice,
    double? currentPrice,
  }) {
    return CryptoPortfolioItem(
      coinId: coinId ?? this.coinId,
      symbol: symbol ?? this.symbol,
      name: name ?? this.name,
      amount: amount ?? this.amount,
      avgBuyPrice: avgBuyPrice ?? this.avgBuyPrice,
      currentPrice: currentPrice ?? this.currentPrice,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'coinId': coinId,
      'symbol': symbol,
      'name': name,
      'amount': amount,
      'avgBuyPrice': avgBuyPrice,
      'currentPrice': currentPrice,
    };
  }

  factory CryptoPortfolioItem.fromJson(Map<String, dynamic> json) {
    return CryptoPortfolioItem(
      coinId: json['coinId'] as String,
      symbol: json['symbol'] as String,
      name: json['name'] as String,
      amount: (json['amount'] as num).toDouble(),
      avgBuyPrice: (json['avgBuyPrice'] as num).toDouble(),
      currentPrice: (json['currentPrice'] as num).toDouble(),
    );
  }

  @override
  String toString() => 'CryptoPortfolioItem($symbol: $amount шт, \$$currentValue)';
}

/// Модель портфеля
@immutable
class CryptoPortfolio {
  final List<CryptoPortfolioItem> items;

  const CryptoPortfolio({required this.items});

  /// Общая стоимость портфеля
  double get totalValue {
    return items.fold(0, (sum, item) => sum + item.currentValue);
  }

  /// Общая прибыль/убыток
  double get totalProfitLoss {
    return items.fold(0, (sum, item) => sum + item.profitLoss);
  }

  /// Процент прибыли/убытка
  double get totalProfitLossPercent {
    final totalBuy = items.fold(0.0, (sum, item) => sum + item.buyValue);
    if (totalBuy == 0) return 0;
    return (totalProfitLoss / totalBuy) * 100;
  }

  CryptoPortfolio copyWith({List<CryptoPortfolioItem>? items}) {
    return CryptoPortfolio(items: items ?? this.items);
  }

  Map<String, dynamic> toJson() {
    return {
      'items': items.map((item) => item.toJson()).toList(),
    };
  }

  factory CryptoPortfolio.fromJson(Map<String, dynamic> json) {
    return CryptoPortfolio(
      items: (json['items'] as List<dynamic>)
          .map((item) => CryptoPortfolioItem.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }

  @override
  String toString() => 'CryptoPortfolio(total: \$$totalValue)';
}

/// Популярные криптовалюты
class PopularCrypto {
  static const List<Map<String, String>> coins = [
    {'id': 'bitcoin', 'symbol': 'BTC', 'name': 'Bitcoin'},
    {'id': 'ethereum', 'symbol': 'ETH', 'name': 'Ethereum'},
    {'id': 'tether', 'symbol': 'USDT', 'name': 'Tether'},
    {'id': 'binancecoin', 'symbol': 'BNB', 'name': 'BNB'},
    {'id': 'solana', 'symbol': 'SOL', 'name': 'Solana'},
    {'id': 'ripple', 'symbol': 'XRP', 'name': 'XRP'},
    {'id': 'cardano', 'symbol': 'ADA', 'name': 'Cardano'},
    {'id': 'dogecoin', 'symbol': 'DOGE', 'name': 'Dogecoin'},
  ];
}
