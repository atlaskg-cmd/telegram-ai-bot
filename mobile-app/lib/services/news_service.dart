import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:xml/xml.dart';
import '../models/models.dart';

/// Сервис новостей (RSS + AI анализ)
class NewsService {
  static final NewsService _instance = NewsService._internal();
  factory NewsService() => _instance;
  NewsService._internal();

  final List<String> _rssFeeds = [
    'https://kaktus.media/?rss',
    'https://www.bbc.com/russian/news/index.xml',
    'https://lenta.ru/rss/news',
    'https://ria.ru/export/rss2/news/index.xml',
  ];

  /// Получить новости из RSS
  Future<List<NewsArticle>> getNewsFromRSS({String? category, int limit = 20}) async {
    try {
      debugPrint('[News] Запрос новостей из RSS...');

      final articles = <NewsArticle>[];

      for (final feedUrl in _rssFeeds) {
        try {
          final response = await http.get(Uri.parse(feedUrl)).timeout(
            const Duration(seconds: 15),
          );

          if (response.statusCode == 200) {
            final parsedArticles = _parseRSS(response.body, feedUrl);
            articles.addAll(parsedArticles);
          }
        } catch (e) {
          debugPrint('[News] Ошибка получения $feedUrl: $e');
        }

        if (articles.length >= limit * 2) break; // Получили достаточно
      }

      // Сортируем по дате и берем top N
      articles.sort((a, b) => b.publishedAt.compareTo(a.publishedAt));
      
      final limited = articles.take(limit).toList();
      
      // Добавляем AI анализ тональности
      return _analyzeSentimentBatch(limited);
    } catch (e) {
      debugPrint('[News] Ошибка: $e');
      rethrow;
    }
  }

  /// Парсинг RSS
  List<NewsArticle> _parseRSS(String xmlString, String sourceUrl) {
    try {
      final document = XmlDocument.parse(xmlString);
      final items = document.findAllElements('item');

      return items.map((item) {
        final title = item.findElements('title').firstOrNull?.text ?? 'Без заголовка';
        final link = item.findElements('link').firstOrNull?.text ?? '';
        final description = item.findElements('description').firstOrNull?.text ?? '';
        final pubDateStr = item.findElements('pubDate').firstOrNull?.text ?? '';
        
        DateTime publishedAt;
        try {
          publishedAt = DateTime.parse(pubDateStr);
        } catch (_) {
          publishedAt = DateTime.now();
        }

        // Определяем категорию по источнику
        String category;
        if (sourceUrl.contains('kaktus')) {
          category = 'kyrgyzstan';
        } else if (sourceUrl.contains('lenta') || sourceUrl.contains('ria')) {
          category = 'world';
        } else {
          category = 'other';
        }

        return NewsArticle(
          id: link.isEmpty ? DateTime.now().millisecondsSinceEpoch.toString() : link,
          title: title,
          summary: _stripHtml(description),
          link: link,
          sourceName: _getSourceName(sourceUrl),
          category: category,
          publishedAt: publishedAt,
          sentiment: Sentiment.neutral,
          sentimentScore: 0.0,
        );
      }).toList();
    } catch (e) {
      debugPrint('[News] Ошибка парсинга RSS: $e');
      return [];
    }
  }

  /// Удалить HTML теги
  String _stripHtml(String html) {
    return html
        .replaceAll(RegExp(r'<[^>]*>'), '')
        .replaceAll('&nbsp;', ' ')
        .replaceAll('&quot;', '"')
        .replaceAll('&#39;', "'")
        .replaceAll('&amp;', '&')
        .trim();
  }

  /// Получить имя источника
  String _getSourceName(String url) {
    if (url.contains('kaktus')) return 'Kaktus.media';
    if (url.contains('bbc')) return 'BBC News';
    if (url.contains('lenta')) return 'Lenta.ru';
    if (url.contains('ria')) return 'RIA.ru';
    return 'News';
  }

  /// AI анализ тональности (batch)
  List<NewsArticle> _analyzeSentimentBatch(List<NewsArticle> articles) {
    // Простая эвристика для определения тональности
    // В продакшене - вызов AI API
    final positiveWords = [
      'успех', 'победа', 'рост', 'положительный', 'хороший',
      'лучший', 'прогресс', 'достижение', 'рекорд', 'благо',
    ];
    final negativeWords = [
      'проблема', 'кризис', 'падение', 'отрицательный', 'плохой',
      'худший', 'катастрофа', 'трагедия', 'смерть', 'война',
    ];

    return articles.map((article) {
      final text = (article.title + ' ' + article.summary).toLowerCase();
      
      int positiveCount = 0;
      int negativeCount = 0;

      for (final word in positiveWords) {
        if (text.contains(word)) positiveCount++;
      }
      for (final word in negativeWords) {
        if (text.contains(word)) negativeCount++;
      }

      Sentiment sentiment;
      double score;

      if (positiveCount > negativeCount) {
        sentiment = Sentiment.positive;
        score = (positiveCount - negativeCount) / (positiveCount + negativeCount + 1);
      } else if (negativeCount > positiveCount) {
        sentiment = Sentiment.negative;
        score = -(negativeCount - positiveCount) / (positiveCount + negativeCount + 1);
      } else {
        sentiment = Sentiment.neutral;
        score = 0.0;
      }

      return article.copyWith(
        sentiment: sentiment,
        sentimentScore: score,
      );
    }).toList();
  }

  /// Получить AI дайджест
  Future<NewsDigest> getDigest({
    required List<String> interests,
    DateTime? date,
  }) async {
    try {
      debugPrint('[News] Генерация дайджеста для интересов: $interests');

      // Получаем новости
      final allNews = await getNewsFromRSS(limit: 50);

      // Фильтруем по интересам
      final filteredNews = allNews.where((article) {
        if (interests.isEmpty) return true;
        return interests.contains(article.category);
      }).take(20).toList();

      // Группируем по категориям
      final categoryCounts = <String, int>{};
      for (final article in filteredNews) {
        categoryCounts[article.category] = (categoryCounts[article.category] ?? 0) + 1;
      }

      // Генерируем AI summary
      final aiSummary = _generateAISummary(filteredNews);

      return NewsDigest(
        date: date ?? DateTime.now(),
        articles: filteredNews,
        aiSummary: aiSummary,
        categoryCounts: categoryCounts,
      );
    } catch (e) {
      debugPrint('[News] Ошибка генерации дайджеста: $e');
      rethrow;
    }
  }

  /// Генерация AI summary
  String _generateAISummary(List<NewsArticle> articles) {
    if (articles.isEmpty) return 'Нет новостей для анализа.';

    final topNews = articles.take(5);
    final summary = StringBuffer();
    
    summary.writeln('📰 **Главные новости дня**:\n');
    
    int i = 1;
    for (final article in topNews) {
      summary.writeln('$i. ${article.title}');
      summary.writeln('   _${article.sourceName}_ ${article.sentimentEmoji}\n');
      i++;
    }

    summary.writeln('━━━━━━━━━━━━━━━━━━━━');
    summary.writeln('Всего новостей: ${articles.length}');
    
    return summary.toString();
  }

  /// Новости Кыргызстана
  Future<List<NewsArticle>> getKyrgyzstanNews({int limit = 10}) async {
    return getNewsFromRSS(category: 'kyrgyzstan', limit: limit);
  }
}
