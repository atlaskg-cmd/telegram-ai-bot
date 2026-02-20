import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/services.dart';

/// Провайдер для криптовалют
class CryptoProvider extends ChangeNotifier {
  final CryptoService _cryptoService = CryptoService();
  final StorageService _storageService = StorageService();

  List<CryptoCoin> _coins = [];
  CryptoPortfolio _portfolio = const CryptoPortfolio(items: []);
  bool _isLoading = false;
  String? _error;
  DateTime? _lastUpdated;

  List<CryptoCoin> get coins => _coins;
  CryptoPortfolio get portfolio => _portfolio;
  bool get isLoading => _isLoading;
  String? get error => _error;
  DateTime? get lastUpdated => _lastUpdated;

  /// Загрузить курсы криптовалют
  Future<void> loadCoins() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _coins = await _cryptoService.getPopularCoins();
      _lastUpdated = DateTime.now();
      
      // Обновляем цены в портфеле
      await _updatePortfolioPrices();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Загрузить портфель
  Future<void> loadPortfolio() async {
    try {
      final telegramId = _storageService.telegramId ?? 'default';
      _portfolio = await _cryptoService.getPortfolio(telegramId);
      
      // Если есть локальные данные
      final localItems = _storageService.getPortfolio();
      if (localItems.isNotEmpty) {
        _portfolio = CryptoPortfolio(items: localItems);
      }
      
      await _updatePortfolioPrices();
    } catch (e) {
      _error = e.toString();
    }
    notifyListeners();
  }

  /// Обновить цены в портфеле
  Future<void> _updatePortfolioPrices() async {
    final updatedItems = <CryptoPortfolioItem>[];
    
    for (final item in _portfolio.items) {
      final coin = _coins.firstWhere(
        (c) => c.id == item.coinId,
        orElse: () => CryptoCoin(
          id: item.coinId,
          symbol: item.symbol,
          name: item.name,
          price: item.currentPrice,
          priceChange24h: 0,
          marketCap: 0,
          volume24h: 0,
          timestamp: DateTime.now(),
        ),
      );
      
      updatedItems.add(item.copyWith(currentPrice: coin.price));
    }
    
    if (updatedItems.isNotEmpty) {
      _portfolio = _portfolio.copyWith(items: updatedItems);
    }
  }

  /// Добавить в портфель
  Future<void> addToPortfolio({
    required String coinId,
    required String symbol,
    required String name,
    required double amount,
    required double avgBuyPrice,
  }) async {
    try {
      final telegramId = _storageService.telegramId ?? 'default';
      
      await _cryptoService.addToPortfolio(
        telegramId: telegramId,
        coinId: coinId,
        symbol: symbol,
        name: name,
        amount: amount,
        avgBuyPrice: avgBuyPrice,
      );

      // Сохраняем локально
      final existingIndex = _portfolio.items.indexWhere(
        (item) => item.coinId == coinId,
      );

      if (existingIndex >= 0) {
        // Обновляем существующую позицию
        final existing = _portfolio.items[existingIndex];
        final newAmount = existing.amount + amount;
        final newAvgPrice = ((existing.amount * existing.avgBuyPrice) + (amount * avgBuyPrice)) / newAmount;
        
        final updatedItem = existing.copyWith(
          amount: newAmount,
          avgBuyPrice: newAvgPrice,
        );
        
        final newItems = List<CryptoPortfolioItem>.from(_portfolio.items);
        newItems[existingIndex] = updatedItem;
        _portfolio = _portfolio.copyWith(items: newItems);
        
        await _storageService.savePortfolioItem(updatedItem);
      } else {
        // Добавляем новую позицию
        final newItem = CryptoPortfolioItem(
          coinId: coinId,
          symbol: symbol,
          name: name,
          amount: amount,
          avgBuyPrice: avgBuyPrice,
          currentPrice: avgBuyPrice,
        );
        
        final newItems = List<CryptoPortfolioItem>.from(_portfolio.items)..add(newItem);
        _portfolio = _portfolio.copyWith(items: newItems);
        
        await _storageService.savePortfolioItem(newItem);
      }
      
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  /// Удалить из портфеля
  Future<void> removeFromPortfolio(String coinId) async {
    try {
      final telegramId = _storageService.telegramId ?? 'default';
      await _cryptoService.removeFromPortfolio(
        telegramId: telegramId,
        coinId: coinId,
      );

      _portfolio = CryptoPortfolio(
        items: _portfolio.items.where((item) => item.coinId != coinId).toList(),
      );
      
      await _storageService.removePortfolioItem(coinId);
      
      notifyListeners();
    } catch (e) {
      _error = e.toString();
      notifyListeners();
    }
  }

  /// Очистить портфель
  Future<void> clearPortfolio() async {
    await _storageService.clearPortfolio();
    _portfolio = const CryptoPortfolio(items: []);
    notifyListeners();
  }

  /// Обновить всё
  Future<void> refresh() async {
    await loadCoins();
    await loadPortfolio();
  }

  /// Получить монету по ID
  CryptoCoin? getCoin(String coinId) {
    return _coins.firstWhere(
      (c) => c.id == coinId,
      orElse: () => throw Exception('Монета не найдена'),
    );
  }
}
