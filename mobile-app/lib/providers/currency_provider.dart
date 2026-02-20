import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/services.dart';

/// Провайдер для конвертера валют
class CurrencyProvider extends ChangeNotifier {
  final CurrencyService _currencyService = CurrencyService();

  MainCurrencyRates _rates = MainCurrencyRates.empty();
  bool _isLoading = false;
  String? _error;
  DateTime? _lastUpdated;

  MainCurrencyRates get rates => _rates;
  bool get isLoading => _isLoading;
  String? get error => _error;
  DateTime? get lastUpdated => _lastUpdated;

  /// Загрузить курсы валют
  Future<void> loadRates() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _rates = await _currencyService.getMainRates();
      _lastUpdated = DateTime.now();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Конвертировать CNY в KGS
  double cnyToKgs(double amount) {
    return amount * _rates.cnyToKgs;
  }

  /// Конвертировать KGS в CNY
  double kgsToCny(double amount) {
    return amount / _rates.cnyToKgs;
  }

  /// Конвертировать USD в KGS
  double usdToKgs(double amount) {
    return amount * _rates.usdToKgs;
  }

  /// Конвертировать EUR в KGS
  double eurToKgs(double amount) {
    return amount * _rates.eurToKgs;
  }

  /// Форматировать число
  String formatNumber(num value) {
    return _currencyService.formatNumber(value);
  }

  /// Обновить курсы
  Future<void> refresh() async {
    await loadRates();
  }

  /// Проверить, устарели ли данные (> 5 минут)
  bool get isStale {
    if (_lastUpdated == null) return true;
    return DateTime.now().difference(_lastUpdated!).inMinutes > 5;
  }
}
