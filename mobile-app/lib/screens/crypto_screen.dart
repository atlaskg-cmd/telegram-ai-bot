import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:fl_chart/fl_chart.dart';
import '../providers/crypto_provider.dart';
import '../models/models.dart';

class CryptoScreen extends StatefulWidget {
  const CryptoScreen({super.key});

  @override
  State<CryptoScreen> createState() => _CryptoScreenState();
}

class _CryptoScreenState extends State<CryptoScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('💰 Криптовалюты'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: '📈 Рынок', icon: Icon(Icons.trending_up)),
            Tab(text: '📊 Портфель', icon: Icon(Icons.account_balance_wallet)),
          ],
        ),
        actions: [
          Consumer<CryptoProvider>(
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
      body: Consumer<CryptoProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.coins.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildMarketTab(provider),
              _buildPortfolioTab(provider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildMarketTab(CryptoProvider provider) {
    if (provider.coins.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.error_outline,
              size: 64,
              color: Theme.of(context).colorScheme.error,
            ),
            const SizedBox(height: 16),
            Text('Не удалось загрузить данные'),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => provider.loadCoins(),
              icon: const Icon(Icons.refresh),
              label: const Text('Попробовать снова'),
            ),
          ],
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: provider.coins.length,
      itemBuilder: (context, index) {
        final coin = provider.coins[index];
        return _CryptoCard(coin: coin);
      },
    );
  }

  Widget _buildPortfolioTab(CryptoProvider provider) {
    final portfolio = provider.portfolio;

    if (portfolio.items.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.account_balance_wallet_outlined,
              size: 80,
              color: Theme.of(context).colorScheme.primary.withOpacity(0.5),
            ),
            const SizedBox(height: 24),
            Text(
              'Ваш портфель пуст',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            const SizedBox(height: 8),
            Text(
              'Добавьте криптовалюты для отслеживания',
              style: Theme.of(context).textTheme.bodyMedium,
            ),
            const SizedBox(height: 24),
            FilledButton.icon(
              onPressed: () => _showAddToPortfolio(context, provider),
              icon: const Icon(Icons.add),
              label: const Text('Добавить монету'),
            ),
          ],
        ),
      );
    }

    final totalValue = portfolio.totalValue;
    final totalProfitLoss = portfolio.totalProfitLoss;
    final profitLossPercent = portfolio.totalProfitLossPercent;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Общая стоимость
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Text(
                    'Общая стоимость',
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '\$${totalValue.toStringAsFixed(2)}',
                    style: Theme.of(context).textTheme.headlineMedium?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                  const SizedBox(height: 12),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                    decoration: BoxDecoration(
                      color: totalProfitLoss >= 0
                          ? Colors.green.withOpacity(0.1)
                          : Colors.red.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          totalProfitLoss >= 0 ? '🟢' : '🔴',
                        ),
                        const SizedBox(width: 6),
                        Text(
                          '${totalProfitLoss >= 0 ? '+' : ''}\$${totalProfitLoss.toStringAsFixed(2)} (${profitLossPercent.toStringAsFixed(2)}%)',
                          style: TextStyle(
                            color: totalProfitLoss >= 0 ? Colors.green : Colors.red,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Ваши активы',
            style: Theme.of(context).textTheme.titleMedium,
          ),
          const SizedBox(height: 12),
          // Список позиций
          ...portfolio.items.map((item) => _PortfolioItemCard(item: item)),
          const SizedBox(height: 80),
        ],
      ),
    );
  }

  void _showAddToPortfolio(BuildContext context, CryptoProvider provider) {
    final coinIdController = TextEditingController();
    final amountController = TextEditingController();
    final priceController = TextEditingController();

    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Добавить в портфель'),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              DropdownButtonFormField<String>(
                decoration: const InputDecoration(labelText: 'Монета'),
                items: provider.coins.map((coin) {
                  return DropdownMenuItem(
                    value: coin.id,
                    child: Text('${coin.name} (${coin.symbol})'),
                  );
                }).toList(),
                onChanged: (value) {
                  coinIdController.text = value ?? '';
                },
              ),
              const SizedBox(height: 16),
              TextField(
                controller: amountController,
                decoration: const InputDecoration(
                  labelText: 'Количество',
                  prefixIcon: Icon(Icons.account_balance_wallet),
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
              const SizedBox(height: 16),
              TextField(
                controller: priceController,
                decoration: const InputDecoration(
                  labelText: 'Средняя цена покупки (\$)',
                  prefixIcon: Icon(Icons.attach_money),
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
              ),
            ],
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Отмена'),
          ),
          FilledButton(
            onPressed: () {
              final coin = provider.coins.firstWhere(
                (c) => c.id == coinIdController.text,
              );
              provider.addToPortfolio(
                coinId: coin.id,
                symbol: coin.symbol,
                name: coin.name,
                amount: double.tryParse(amountController.text) ?? 0,
                avgBuyPrice: double.tryParse(priceController.text) ?? coin.price,
              );
              Navigator.pop(context);
            },
            child: const Text('Добавить'),
          ),
        ],
      ),
    );
  }
}

class _CryptoCard extends StatelessWidget {
  final CryptoCoin coin;

  const _CryptoCard({required this.coin});

  @override
  Widget build(BuildContext context) {
    final isPositive = coin.priceChange24h >= 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: Container(
          width: 48,
          height: 48,
          decoration: BoxDecoration(
            color: Theme.of(context).colorScheme.primaryContainer,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Center(
            child: Text(
              coin.symbol[0],
              style: Theme.of(context).textTheme.titleLarge?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
          ),
        ),
        title: Text(
          coin.name,
          style: Theme.of(context).textTheme.titleMedium,
        ),
        subtitle: Text(coin.symbol),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          crossAxisAlignment: CrossAxisAlignment.end,
          children: [
            Text(
              '\$${coin.price.toStringAsFixed(coin.price < 1 ? 6 : 2)}',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: isPositive
                    ? Colors.green.withOpacity(0.1)
                    : Colors.red.withOpacity(0.1),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(isPositive ? '🟢' : '🔴'),
                  const SizedBox(width: 4),
                  Text(
                    coin.formattedPriceChange,
                    style: TextStyle(
                      color: isPositive ? Colors.green : Colors.red,
                      fontWeight: FontWeight.bold,
                      fontSize: 12,
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
}

class _PortfolioItemCard extends StatelessWidget {
  final CryptoPortfolioItem item;

  const _PortfolioItemCard({required this.item});

  @override
  Widget build(BuildContext context) {
    final isPositive = item.profitLoss >= 0;

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          children: [
            Row(
              children: [
                Container(
                  width: 48,
                  height: 48,
                  decoration: BoxDecoration(
                    color: Theme.of(context).colorScheme.primaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Center(
                    child: Text(
                      item.symbol[0],
                      style: Theme.of(context).textTheme.titleLarge?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        item.name,
                        style: Theme.of(context).textTheme.titleMedium,
                      ),
                      Text(
                        '${item.amount} ${item.symbol}',
                        style: Theme.of(context).textTheme.bodySmall,
                      ),
                    ],
                  ),
                ),
                Column(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      '\$${item.currentValue.toStringAsFixed(2)}',
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    Text(
                      '${isPositive ? '🟢' : '🔴'} ${item.profitLossPercent.toStringAsFixed(2)}%',
                      style: TextStyle(
                        color: isPositive ? Colors.green : Colors.red,
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  ],
                ),
              ],
            ),
            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _InfoColumn(
                  label: 'Куплено',
                  value: '\$${item.buyValue.toStringAsFixed(2)}',
                ),
                _InfoColumn(
                  label: 'Прибыль',
                  value: '${item.profitLoss >= 0 ? '+' : ''}\$${item.profitLoss.toStringAsFixed(2)}',
                  isProfit: item.profitLoss >= 0,
                ),
                _InfoColumn(
                  label: 'Цена',
                  value: '\$${item.currentPrice.toStringAsFixed(2)}',
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoColumn extends StatelessWidget {
  final String label;
  final String value;
  final bool? isProfit;

  const _InfoColumn({
    required this.label,
    required this.value,
    this.isProfit,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall?.copyWith(
            color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
            fontWeight: FontWeight.bold,
            color: isProfit == true
                ? Colors.green
                : isProfit == false
                    ? Colors.red
                    : null,
          ),
        ),
      ],
    );
  }
}
