import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:intl/intl.dart';
import 'package:url_launcher/url_launcher.dart';
import '../providers/news_provider.dart';
import '../models/models.dart';

class NewsScreen extends StatefulWidget {
  const NewsScreen({super.key});

  @override
  State<NewsScreen> createState() => _NewsScreenState();
}

class _NewsScreenState extends State<NewsScreen> with SingleTickerProviderStateMixin {
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
        title: const Text('📰 Новости'),
        bottom: TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Лента', icon: Icon(Icons.rss_feed)),
            Tab(text: 'AI Дайджест', icon: Icon(Icons.auto_awesome)),
          ],
        ),
        actions: [
          Consumer<NewsProvider>(
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
      body: Consumer<NewsProvider>(
        builder: (context, provider, child) {
          if (provider.isLoading && provider.news.isEmpty) {
            return const Center(child: CircularProgressIndicator());
          }

          return TabBarView(
            controller: _tabController,
            children: [
              _buildNewsFeed(provider),
              _buildDigest(provider),
            ],
          );
        },
      ),
    );
  }

  Widget _buildNewsFeed(NewsProvider provider) {
    if (provider.news.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.newspaper_outlined,
              size: 80,
              color: Theme.of(context).colorScheme.primary.withOpacity(0.5),
            ),
            const SizedBox(height: 24),
            Text('Нет новостей'),
            const SizedBox(height: 16),
            FilledButton.icon(
              onPressed: () => provider.loadNews(),
              icon: const Icon(Icons.refresh),
              label: const Text('Обновить'),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => provider.refresh(),
      child: ListView.builder(
        padding: const EdgeInsets.all(16),
        itemCount: provider.news.length,
        itemBuilder: (context, index) {
          final article = provider.news[index];
          return _NewsCard(article: article);
        },
      ),
    );
  }

  Widget _buildDigest(NewsProvider provider) {
    return Consumer<NewsProvider>(
      builder: (context, provider, child) {
        if (provider.digest == null) {
          return Center(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(
                  Icons.auto_awesome_outlined,
                  size: 80,
                  color: Theme.of(context).colorScheme.primary.withOpacity(0.5),
                ),
                const SizedBox(height: 24),
                Text(
                  'AI Дайджест новостей',
                  style: Theme.of(context).textTheme.titleLarge,
                ),
                const SizedBox(height: 8),
                Text(
                  'Персонализированная подборка новостей\nна основе ваших интересов',
                  textAlign: TextAlign.center,
                  style: Theme.of(context).textTheme.bodyMedium,
                ),
                const SizedBox(height: 24),
                FilledButton.icon(
                  onPressed: () => provider.loadDigest(),
                  icon: const Icon(Icons.auto_awesome),
                  label: const Text('Сгенерировать дайджест'),
                ),
                const SizedBox(height: 24),
                // Интересы
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 32),
                  child: Text(
                    'Настройте интересы в разделе Настройки',
                    textAlign: TextAlign.center,
                    style: TextStyle(fontSize: 12),
                  ),
                ),
              ],
            ),
          );
        }

        final digest = provider.digest!;

        return RefreshIndicator(
          onRefresh: () => provider.loadDigest(),
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Заголовок
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(20),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          children: [
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Theme.of(context).colorScheme.primaryContainer,
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: const Text('📊', style: TextStyle(fontSize: 32)),
                            ),
                            const SizedBox(width: 16),
                            Expanded(
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  Text(
                                    'AI Дайджест',
                                    style: Theme.of(context).textTheme.titleLarge,
                                  ),
                                  Text(
                                    DateFormat('dd MMMM yyyy').format(digest.date),
                                    style: Theme.of(context).textTheme.bodySmall,
                                  ),
                                ],
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 20),
                        // Статистика
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceAround,
                          children: [
                            _StatItem(
                              icon: Icons.newspaper,
                              label: 'Новостей',
                              value: digest.totalCount.toString(),
                            ),
                            _StatItem(
                              icon: Icons.folder,
                              label: 'Категорий',
                              value: digest.categoryCounts.length.toString(),
                            ),
                            _StatItem(
                              icon: Icons.star,
                              label: 'Топ',
                              value: digest.topCategory,
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                // AI Summary
                Text(
                  '🤖 AI Анализ',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Text(
                      digest.aiSummary,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ),
                ),
                const SizedBox(height: 24),
                // Новости по категориям
                Text(
                  '📋 Новости',
                  style: Theme.of(context).textTheme.titleMedium,
                ),
                const SizedBox(height: 12),
                ...digest.articles.map((article) => _NewsCard(article: article)),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _NewsCard extends StatelessWidget {
  final NewsArticle article;

  const _NewsCard({required this.article});

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () async {
          final url = Uri.parse(article.link);
          if (await canLaunchUrl(url)) {
            await launchUrl(url, mode: LaunchMode.externalApplication);
          }
        },
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: Theme.of(context).colorScheme.surfaceContainerHighest,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(
                      NewsCategory.fromId(article.category).icon,
                      style: const TextStyle(fontSize: 16),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      article.sourceName,
                      style: Theme.of(context).textTheme.bodySmall?.copyWith(
                        color: Theme.of(context).colorScheme.onSurface.withOpacity(0.6),
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: _getSentimentColor(article.sentiment).withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(article.sentimentEmoji),
                        const SizedBox(width: 4),
                        Text(
                          article.sentiment.name == 'positive'
                              ? 'Позитив'
                              : article.sentiment.name == 'negative'
                                  ? 'Негатив'
                                  : 'Нейтрально',
                          style: TextStyle(
                            fontSize: 11,
                            color: _getSentimentColor(article.sentiment),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Text(
                article.title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              if (article.summary.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  article.summary,
                  maxLines: 3,
                  overflow: TextOverflow.ellipsis,
                  style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                    color: Theme.of(context).colorScheme.onSurface.withOpacity(0.7),
                  ),
                ),
              ],
              const SizedBox(height: 12),
              Text(
                DateFormat('dd MMM HH:mm').format(article.publishedAt),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Theme.of(context).colorScheme.onSurface.withOpacity(0.5),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Color _getSentimentColor(Sentiment sentiment) {
    switch (sentiment) {
      case Sentiment.positive:
        return Colors.green;
      case Sentiment.negative:
        return Colors.red;
      case Sentiment.neutral:
        return Colors.grey;
    }
  }
}

class _StatItem extends StatelessWidget {
  final IconData icon;
  final String label;
  final String value;

  const _StatItem({
    required this.icon,
    required this.label,
    required this.value,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Icon(icon, size: 28),
        const SizedBox(height: 4),
        Text(
          value,
          style: Theme.of(context).textTheme.titleLarge?.copyWith(
            fontWeight: FontWeight.bold,
          ),
        ),
        Text(
          label,
          style: Theme.of(context).textTheme.bodySmall,
        ),
      ],
    );
  }
}
