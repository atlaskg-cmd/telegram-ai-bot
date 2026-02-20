import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/weather_provider.dart';
import '../models/models.dart';

class WeatherScreen extends StatefulWidget {
  const WeatherScreen({super.key});

  @override
  State<WeatherScreen> createState() => _WeatherScreenState();
}

class _WeatherScreenState extends State<WeatherScreen> {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🌤 Погода'),
        actions: [
          Consumer<WeatherProvider>(
            builder: (context, provider, child) {
              return IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Обновить',
                onPressed: provider.isLoading ? null : () => provider.refresh(),
              );
            },
          ),
        ],
      ),
      body: Consumer<WeatherProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.weatherData.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          if (provider.error != null) {
            return Center(
              child: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(
                    Icons.cloud_off_outlined,
                    size: 80,
                    color: Theme.of(context).colorScheme.error,
                  ),
                  const SizedBox(height: 16),
                  Text(
                    'Ошибка загрузки погоды',
                    style: Theme.of(context).textTheme.titleLarge,
                  ),
                  const SizedBox(height: 8),
                  Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 32),
                    child: Text(
                      provider.error!,
                      textAlign: TextAlign.center,
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.error,
                      ),
                    ),
                  ),
                  const SizedBox(height: 24),
                  FilledButton.icon(
                    onPressed: () => provider.loadAllCities(),
                    icon: const Icon(Icons.refresh),
                    label: const Text('Попробовать снова'),
                  ),
                ],
              ),
            );
          }

          return RefreshIndicator(
            onRefresh: () => provider.refresh(),
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                // Заголовок
                Padding(
                  padding: const EdgeInsets.only(bottom: 20),
                  child: Text(
                    'Погода в городах',
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                ),
                // Карточки городов
                ...WeatherCity.cities.map((city) {
                  final weather = provider.getWeatherForCity(city);
                  return _WeatherCard(
                    city: city,
                    weather: weather,
                    onTap: () => _showDetails(context, city, weather),
                  );
                }),
                const SizedBox(height: 80),
              ],
            ),
          );
        },
      ),
    );
  }

  void _showDetails(BuildContext context, WeatherCity city, WeatherData? weather) {
    if (weather == null) return;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        minChildSize: 0.4,
        maxChildSize: 0.9,
        expand: false,
        builder: (context, scrollController) => SingleChildScrollView(
          controller: scrollController,
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.2),
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              Text(
                city.displayName,
                style: Theme.of(context).textTheme.headlineMedium,
              ),
              const SizedBox(height: 8),
              Text(
                'Обновлено: ${DateFormat('dd MMM HH:mm').format(weather.timestamp)}',
                style: Theme.of(context).textTheme.bodySmall,
              ),
              const SizedBox(height: 32),
              // Температура
              Row(
                children: [
                  Text(
                    '${weather.temperature.toStringAsFixed(0)}°',
                    style: Theme.of(context).textTheme.displayLarge?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(width: 16),
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        weather.weatherEmoji,
                        style: const TextStyle(fontSize: 40),
                      ),
                      Text(
                        weather.localizedDescription,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 32),
              // Детали
              _DetailRow(
                icon: Icons.thermometer_outlined,
                label: 'Ощущается как',
                value: '${weather.feelsLike.toStringAsFixed(0)}°',
              ),
              _DetailRow(
                icon: Icons.water_drop_outlined,
                label: 'Влажность',
                value: '${weather.humidity}%',
              ),
              _DetailRow(
                icon: Icons.air_outlined,
                label: 'Ветер',
                value: '${weather.windSpeed.toStringAsFixed(1)} м/с',
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _WeatherCard extends StatelessWidget {
  final WeatherCity city;
  final WeatherData? weather;
  final VoidCallback onTap;

  const _WeatherCard({
    required this.city,
    required this.weather,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              // Иконка погоды
              Container(
                width: 60,
                height: 60,
                decoration: BoxDecoration(
                  color: Theme.of(context).colorScheme.primaryContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Center(
                  child: Text(
                    weather?.weatherEmoji ?? '🌤️',
                    style: const TextStyle(fontSize: 32),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              // Информация
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      city.displayName,
                      style: Theme.of(context).textTheme.titleMedium,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      weather?.localizedDescription ?? 'Загрузка...',
                      style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                        color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  ],
                ),
              ),
              // Температура
              Column(
                children: [
                  Text(
                    weather != null
                        ? '${weather!.temperature.toStringAsFixed(0)}°'
                        : '--°',
                    style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  if (weather != null)
                    Text(
                      'Ощущается ${weather!.feelsLike.toStringAsFixed(0)}°',
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DetailRow extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _DetailRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Row(
        children: [
          Container(
            width: 48,
            height: 48,
            decoration: BoxDecoration(
              color: Theme.of(context).colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(12),
            ),
            child: Icon(icon),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Text(
              label,
              style: Theme.of(context).textTheme.bodyMedium,
            ),
          ),
          Text(
            value,
            style: Theme.of(context).textTheme.titleMedium?.copyWith(
              fontWeight: FontWeight.bold,
            ),
          ),
        ],
      ),
    );
  }
}
