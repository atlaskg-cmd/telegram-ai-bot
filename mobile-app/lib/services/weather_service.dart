import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../models/models.dart';

/// Сервис погоды (Open-Meteo API)
class WeatherService {
  static final WeatherService _instance = WeatherService._internal();
  factory WeatherService() => _instance;
  WeatherService._internal();

  final String _baseUrl = 'https://api.open-meteo.com/v1';

  /// Получить погоду для города
  Future<WeatherData> getWeather(WeatherCity city) async {
    try {
      debugPrint('[Weather] Запрос погоды для: ${city.displayName}');

      final url = Uri.parse(
        '$_baseUrl/forecast'
        '?latitude=${city.latitude}'
        '&longitude=${city.longitude}'
        '&current_weather=true'
        '&hourly=relativehumidity_2m,apparent_temperature'
        '&timezone=auto',
      );

      final response = await http.get(url).timeout(const Duration(seconds: 30));

      if (response.statusCode != 200) {
        throw Exception('Ошибка API погоды: ${response.statusCode}');
      }

      final data = jsonDecode(response.body) as Map<String, dynamic>;
      final currentWeather = data['current_weather'] as Map<String, dynamic>;
      final hourly = data['hourly'] as Map<String, dynamic>?;

      // Получаем текущий час для humidity и feels like
      final now = DateTime.now();
      final currentHour = now.hour;
      
      double feelsLike = currentWeather['temperature'] as double;
      int humidity = 50; // Значение по умолчанию

      if (hourly != null) {
        final timeList = hourly['time'] as List<dynamic>?;
        if (timeList != null) {
          // Находим индекс текущего часа
          int index = 0;
          for (int i = 0; i < timeList.length; i++) {
            final time = DateTime.parse(timeList[i] as String);
            if (time.hour == currentHour) {
              index = i;
              break;
            }
          }
          
          final temp2m = hourly['apparent_temperature'] as List<dynamic>?;
          final humidity2m = hourly['relativehumidity_2m'] as List<dynamic>?;
          
          if (temp2m != null && index < temp2m.length) {
            feelsLike = (temp2m[index] as num).toDouble();
          }
          if (humidity2m != null && index < humidity2m.length) {
            humidity = (humidity2m[index] as num).toInt();
          }
        }
      }

      final weatherCode = currentWeather['weathercode'] as int;
      final temperature = currentWeather['temperature'] as num;
      final windSpeed = currentWeather['windspeed'] as num;

      return WeatherData(
        city: city.displayName,
        temperature: temperature.toDouble(),
        description: _getDescription(weatherCode),
        weatherCode: weatherCode,
        feelsLike: feelsLike,
        humidity: humidity,
        windSpeed: windSpeed.toDouble(),
        timestamp: DateTime.now(),
      );
    } catch (e) {
      debugPrint('[Weather] Ошибка: $e');
      rethrow;
    }
  }

  /// Получить погоду для всех городов
  Future<Map<String, WeatherData>> getAllCitiesWeather() async {
    final results = <String, WeatherData>{};
    
    for (final city in WeatherCity.cities) {
      try {
        final weather = await getWeather(city);
        results[city.id] = weather;
      } catch (e) {
        debugPrint('[Weather] Не удалось получить погоду для ${city.displayName}: $e');
      }
    }
    
    return results;
  }

  /// Получить описание погоды на русском
  String _getDescription(int weatherCode) {
    switch (weatherCode) {
      case 0: return 'Ясно';
      case 1: return 'Преимущественно ясно';
      case 2: return 'Переменная облачность';
      case 3: return 'Пасмурно';
      case 45:
      case 48: return 'Туман';
      case 51:
      case 53:
      case 55: return 'Дождь';
      case 56:
      case 57: return 'Ледяной дождь';
      case 61: return 'Небольшой дождь';
      case 63: return 'Дождь';
      case 65: return 'Сильный дождь';
      case 66:
      case 67: return 'Ледяной дождь';
      case 71: return 'Небольшой снег';
      case 73: return 'Снег';
      case 75: return 'Сильный снег';
      case 77: return 'Снежные зерна';
      case 80: return 'Небольшой дождь';
      case 81: return 'Дождь';
      case 82: return 'Сильный дождь';
      case 85: return 'Небольшой снег';
      case 86: return 'Сильный снег';
      case 95: return 'Гроза';
      case 96:
      case 99: return 'Гроза с градом';
      default: return 'Неизвестно';
    }
  }
}
