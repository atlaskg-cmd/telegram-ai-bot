import 'package:flutter/foundation.dart';

/// Модель погодных данных
@immutable
class WeatherData {
  final String city;
  final double temperature;
  final String description;
  final int weatherCode;
  final double feelsLike;
  final int humidity;
  final double windSpeed;
  final DateTime timestamp;

  const WeatherData({
    required this.city,
    required this.temperature,
    required this.description,
    required this.weatherCode,
    required this.feelsLike,
    required this.humidity,
    required this.windSpeed,
    required this.timestamp,
  });

  /// Получить эмодзи погоды на основе weather code
  String get weatherEmoji {
    switch (weatherCode) {
      case 0:
        return '☀️';
      case 1:
        return '🌤️';
      case 2:
        return '⛅';
      case 3:
        return '☁️';
      case 45:
      case 48:
        return '🌫️';
      case 51:
      case 53:
      case 55:
      case 61:
      case 63:
      case 65:
      case 80:
      case 81:
      case 82:
        return '🌧️';
      case 56:
      case 57:
      case 66:
      case 67:
        return '🧊';
      case 71:
      case 73:
      case 75:
      case 77:
      case 85:
      case 86:
        return '❄️';
      case 95:
      case 96:
      case 99:
        return '⛈️';
      default:
        return '❓';
    }
  }

  /// Получить описание на русском
  String get localizedDescription {
    switch (weatherCode) {
      case 0:
        return 'Ясно';
      case 1:
        return 'Преимущественно ясно';
      case 2:
        return 'Переменная облачность';
      case 3:
        return 'Пасмурно';
      case 45:
        return 'Туман';
      case 48:
        return 'Изморось';
      case 51:
        return 'Мелкий дождь';
      case 53:
        return 'Дождь';
      case 55:
        return 'Сильный дождь';
      case 56:
      case 57:
        return 'Ледяной дождь';
      case 61:
        return 'Небольшой дождь';
      case 63:
        return 'Дождь';
      case 65:
        return 'Сильный дождь';
      case 66:
      case 67:
        return 'Ледяной дождь';
      case 71:
        return 'Небольшой снег';
      case 73:
        return 'Снег';
      case 75:
        return 'Сильный снег';
      case 77:
        return 'Снежные зерна';
      case 80:
        return 'Небольшой дождь';
      case 81:
        return 'Дождь';
      case 82:
        return 'Сильный дождь';
      case 85:
        return 'Небольшой снег';
      case 86:
        return 'Сильный снег';
      case 95:
        return 'Гроза';
      case 96:
        return 'Гроза с градом';
      case 99:
        return 'Сильная гроза с градом';
      default:
        return 'Неизвестно';
    }
  }

  WeatherData copyWith({
    String? city,
    double? temperature,
    String? description,
    int? weatherCode,
    double? feelsLike,
    int? humidity,
    double? windSpeed,
    DateTime? timestamp,
  }) {
    return WeatherData(
      city: city ?? this.city,
      temperature: temperature ?? this.temperature,
      description: description ?? this.description,
      weatherCode: weatherCode ?? this.weatherCode,
      feelsLike: feelsLike ?? this.feelsLike,
      humidity: humidity ?? this.humidity,
      windSpeed: windSpeed ?? this.windSpeed,
      timestamp: timestamp ?? this.timestamp,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'city': city,
      'temperature': temperature,
      'description': description,
      'weatherCode': weatherCode,
      'feelsLike': feelsLike,
      'humidity': humidity,
      'windSpeed': windSpeed,
      'timestamp': timestamp.toIso8601String(),
    };
  }

  factory WeatherData.fromJson(Map<String, dynamic> json) {
    return WeatherData(
      city: json['city'] as String,
      temperature: (json['temperature'] as num).toDouble(),
      description: json['description'] as String,
      weatherCode: json['weatherCode'] as int,
      feelsLike: (json['feelsLike'] as num).toDouble(),
      humidity: json['humidity'] as int,
      windSpeed: (json['windSpeed'] as num).toDouble(),
      timestamp: DateTime.parse(json['timestamp'] as String),
    );
  }

  @override
  String toString() => 'WeatherData(city: $city, temperature: $temperature°C, $description)';
}

/// Список городов для погоды
class WeatherCity {
  final String id;
  final String name;
  final String displayName;
  final double latitude;
  final double longitude;

  const WeatherCity({
    required this.id,
    required this.name,
    required this.displayName,
    required this.latitude,
    required this.longitude,
  });

  static const List<WeatherCity> cities = [
    WeatherCity(
      id: 'bishkek',
      name: 'Bishkek',
      displayName: 'Бишкек',
      latitude: 42.8746,
      longitude: 74.5698,
    ),
    WeatherCity(
      id: 'moscow',
      name: 'Moscow',
      displayName: 'Москва',
      latitude: 55.7558,
      longitude: 37.6173,
    ),
    WeatherCity(
      id: 'issyk_kul',
      name: 'Issyk-Kul',
      displayName: 'Иссык-Куль',
      latitude: 42.6167,
      longitude: 76.8500,
    ),
    WeatherCity(
      id: 'bokonbaevo',
      name: 'Bokonbaevo',
      displayName: 'Бөкөнбаево',
      latitude: 42.3833,
      longitude: 76.3833,
    ),
    WeatherCity(
      id: 'ton',
      name: 'Ton',
      displayName: 'Тон',
      latitude: 42.3167,
      longitude: 77.5167,
    ),
  ];
}
