import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/services.dart';

/// Провайдер для погоды
class WeatherProvider extends ChangeNotifier {
  final WeatherService _weatherService = WeatherService();

  Map<String, WeatherData> _weatherData = {};
  bool _isLoading = false;
  String? _error;

  Map<String, WeatherData> get weatherData => _weatherData;
  bool get isLoading => _isLoading;
  String? get error => _error;

  /// Загрузить погоду для всех городов
  Future<void> loadAllCities() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _weatherData = await _weatherService.getAllCitiesWeather();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Загрузить погоду для конкретного города
  Future<void> loadCity(WeatherCity city) async {
    try {
      final weather = await _weatherService.getWeather(city);
      _weatherData[city.id] = weather;
      notifyListeners();
    } catch (e) {
      _error = e.toString();
    }
  }

  /// Обновить все данные
  Future<void> refresh() async {
    await loadAllCities();
  }

  /// Получить погоду для города
  WeatherData? getWeatherForCity(WeatherCity city) {
    return _weatherData[city.id];
  }
}
