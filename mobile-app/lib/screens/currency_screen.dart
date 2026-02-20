import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import '../providers/currency_provider.dart';

class CurrencyScreen extends StatefulWidget {
  const CurrencyScreen({super.key});

  @override
  State<CurrencyScreen> createState() => _CurrencyScreenState();
}

class _CurrencyScreenState extends State<CurrencyScreen> {
  final TextEditingController _cnyController = TextEditingController();
  final TextEditingController _kgsController = TextEditingController();
  bool _isCnyFocused = true; // true = CNY → KGS, false = KGS → CNY

  @override
  void dispose() {
    _cnyController.dispose();
    _kgsController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('💱 Конвертер валют'),
        actions: [
          Consumer<CurrencyProvider>(
            builder: (context, provider, child) {
              return IconButton(
                icon: const Icon(Icons.refresh),
                tooltip: 'Обновить курсы',
                onPressed: provider.isLoading ? null : () => provider.refresh(),
              );
            },
          ),
        ],
      ),
      body: Consumer<CurrencyProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.rates.usdToKgs == 0) {
            return const Center(child: CircularProgressIndicator());
          }

          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Основные курсы
                _buildMainRatesCard(provider),
                const SizedBox(height: 24),
                // Конвертер CNY ↔ KGS
                _buildConverterCard(provider),
                const SizedBox(height: 24),
                // Информация
                _buildInfoCard(provider),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildMainRatesCard(CurrencyProvider provider) {
    final rates = provider.rates;
    final lastUpdated = provider.lastUpdated;

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Основные курсы',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                if (lastUpdated != null)
                  Text(
                    'Обновлено: ${DateFormat('HH:mm').format(lastUpdated)}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 16),
            _RateRow(
              flag: '🇺🇸',
              currency: 'USD',
              name: 'Доллар США',
              rate: provider.formatNumber(rates.usdToKgs),
            ),
            const Divider(height: 24),
            _RateRow(
              flag: '🇪🇺',
              currency: 'EUR',
              name: 'Евро',
              rate: provider.formatNumber(rates.eurToKgs),
            ),
            const Divider(height: 24),
            _RateRow(
              flag: '🇷🇺',
              currency: 'RUB',
              name: 'Российский рубль',
              rate: '${provider.formatNumber(rates.usdToRub)} за \$1',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConverterCard(CurrencyProvider provider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Конвертер валют',
              style: Theme.of(context).textTheme.titleMedium,
            ),
            const SizedBox(height: 16),
            // Переключатель направления
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment(
                  value: true,
                  label: Text('🇨🇳 Юань → Сом'),
                  icon: Icon(Icons.arrow_forward),
                ),
                ButtonSegment(
                  value: false,
                  label: Text('🇰🇬 Сом → Юань'),
                  icon: Icon(Icons.arrow_back),
                ),
              ],
              selected: {_isCnyFocused},
              onSelectionChanged: (selected) {
                setState(() {
                  _isCnyFocused = selected.first;
                  _cnyController.clear();
                  _kgsController.clear();
                });
              },
            ),
            const SizedBox(height: 24),
            // Поля ввода
            Row(
              children: [
                // CNY
                Expanded(
                  child: TextField(
                    controller: _cnyController,
                    decoration: InputDecoration(
                      labelText: 'CNY',
                      prefixText: '🇨🇳 ',
                      border: const OutlineInputBorder(),
                    ),
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    onChanged: (value) {
                      if (_isCnyFocused && value.isNotEmpty) {
                        final cny = double.tryParse(value) ?? 0;
                        final kgs = provider.cnyToKgs(cny);
                        _kgsController.text = kgs.toStringAsFixed(2);
                      } else if (!_isCnyFocused && value.isNotEmpty) {
                        final kgs = double.tryParse(value) ?? 0;
                        final cny = provider.kgsToCny(kgs);
                        _cnyController.text = cny.toStringAsFixed(2);
                      }
                    },
                  ),
                ),
                const SizedBox(width: 16),
                // Кнопка обмена
                IconButton(
                  onPressed: () {
                    setState(() {
                      _isCnyFocused = !_isCnyFocused;
                      final temp = _cnyController.text;
                      _cnyController.text = _kgsController.text;
                      _kgsController.text = temp;
                    });
                  },
                  icon: const Icon(Icons.swap_horiz),
                  style: IconButton.styleFrom(
                    backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                  ),
                ),
                const SizedBox(width: 16),
                // KGS
                Expanded(
                  child: TextField(
                    controller: _kgsController,
                    decoration: InputDecoration(
                      labelText: 'KGS',
                      prefixText: '🇰🇬 ',
                      border: const OutlineInputBorder(),
                    ),
                    keyboardType: const TextInputType.numberWithOptions(
                      decimal: true,
                    ),
                    onChanged: (value) {
                      if (!_isCnyFocused && value.isNotEmpty) {
                        final kgs = double.tryParse(value) ?? 0;
                        final cny = provider.kgsToCny(kgs);
                        _cnyController.text = cny.toStringAsFixed(2);
                      } else if (_isCnyFocused && value.isNotEmpty) {
                        final cny = double.tryParse(value) ?? 0;
                        final kgs = provider.cnyToKgs(cny);
                        _kgsController.text = kgs.toStringAsFixed(2);
                      }
                    },
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),
            // Текущий курс
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Theme.of(context).colorScheme.primaryContainer,
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  const Text('📊 '),
                  Text(
                    '1 CNY = ${provider.rates.cnyToKgs.toStringAsFixed(2)} KGS',
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoCard(CurrencyProvider provider) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'ℹ️ Информация',
              style: Theme.of(context).textTheme.titleSmall,
            ),
            const SizedBox(height: 8),
            Text(
              'Курсы валют предоставляются Exchangerate API и обновляются автоматически каждые 5 минут.',
              style: Theme.of(context).textTheme.bodySmall,
            ),
            const SizedBox(height: 12),
            Text(
              'Для конвертации используются актуальные рыночные курсы.',
              style: Theme.of(context).textTheme.bodySmall?.copyWith(
                color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _RateRow extends StatelessWidget {
  final String flag;
  final String currency;
  final String name;
  final String rate;

  const _RateRow({
    required this.flag,
    required this.currency,
    required this.name,
    required this.rate,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Text(flag, style: const TextStyle(fontSize: 24)),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                currency,
                style: Theme.of(context).textTheme.titleSmall?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              Text(
                name,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                ),
              ),
            ],
          ),
        ),
        Text(
          rate,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
      ],
    );
  }
}
