import 'package:flutter/foundation.dart';

/// Модель новости
@immutable
class NewsArticle {
  final String id;
  final String title;
  final String summary;
  final String link;
  final String sourceName;
  final String category;
  final DateTime publishedAt;
  final Sentiment sentiment;
  final double sentimentScore;
  final String? imageUrl;

  const NewsArticle({
    required this.id,
    required this.title,
    required this.summary,
    required this.link,
    required this.sourceName,
    required this.category,
    required this.publishedAt,
    this.sentiment = Sentiment.neutral,
    this.sentimentScore = 0.0,
    this.imageUrl,
  });

  /// Получить эмодзи тональности
  String get sentimentEmoji {
    switch (sentiment) {
      case Sentiment.positive:
        return '😊';
      case Sentiment.negative:
        return '😢';
      case Sentiment.neutral:
        return '😐';
    }
  }

  /// Получить цвет тональности
  String get sentimentColor {
    switch (sentiment) {
      case Sentiment.positive:
        return 'green';
      case Sentiment.negative:
        return 'red';
      case Sentiment.neutral:
        return 'gray';
    }
  }

  NewsArticle copyWith({
    String? id,
    String? title,
    String? summary,
    String? link,
    String? sourceName,
    String? category,
    DateTime? publishedAt,
    Sentiment? sentiment,
    double? sentimentScore,
    String? imageUrl,
  }) {
    return NewsArticle(
      id: id ?? this.id,
      title: title ?? this.title,
      summary: summary ?? this.summary,
      link: link ?? this.link,
      sourceName: sourceName ?? this.sourceName,
      category: category ?? this.category,
      publishedAt: publishedAt ?? this.publishedAt,
      sentiment: sentiment ?? this.sentiment,
      sentimentScore: sentimentScore ?? this.sentimentScore,
      imageUrl: imageUrl ?? this.imageUrl,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'summary': summary,
      'link': link,
      'sourceName': sourceName,
      'category': category,
      'publishedAt': publishedAt.toIso8601String(),
      'sentiment': sentiment.name,
      'sentimentScore': sentimentScore,
      'imageUrl': imageUrl,
    };
  }

  factory NewsArticle.fromJson(Map<String, dynamic> json) {
    return NewsArticle(
      id: json['id'] as String,
      title: json['title'] as String,
      summary: json['summary'] as String,
      link: json['link'] as String,
      sourceName: json['sourceName'] as String,
      category: json['category'] as String,
      publishedAt: DateTime.parse(json['publishedAt'] as String),
      sentiment: Sentiment.values.firstWhere(
        (e) => e.name == json['sentiment'],
        orElse: () => Sentiment.neutral,
      ),
      sentimentScore: (json['sentimentScore'] as num?)?.toDouble() ?? 0.0,
      imageUrl: json['imageUrl'] as String?,
    );
  }

  @override
  String toString() => 'NewsArticle(title: $title, sentiment: $sentiment)';
}

/// Тональность новости
enum Sentiment {
  positive,
  neutral,
  negative,
}

extension SentimentExtension on Sentiment {
  String get displayName {
    switch (this) {
      case Sentiment.positive:
        return 'Позитивная';
      case Sentiment.neutral:
        return 'Нейтральная';
      case Sentiment.negative:
        return 'Негативная';
    }
  }
}

/// Модель AI дайджеста
@immutable
class NewsDigest {
  final DateTime date;
  final List<NewsArticle> articles;
  final String aiSummary;
  final Map<String, int> categoryCounts;

  const NewsDigest({
    required this.date,
    required this.articles,
    required this.aiSummary,
    required this.categoryCounts,
  });

  /// Получить топ категории
  String get topCategory {
    if (categoryCounts.isEmpty) return 'Другое';
    return categoryCounts.entries.reduce((a, b) => a.value > b.value ? a : b).key;
  }

  /// Общее количество новостей
  int get totalCount => articles.length;

  NewsDigest copyWith({
    DateTime? date,
    List<NewsArticle>? articles,
    String? aiSummary,
    Map<String, int>? categoryCounts,
  }) {
    return NewsDigest(
      date: date ?? this.date,
      articles: articles ?? this.articles,
      aiSummary: aiSummary ?? this.aiSummary,
      categoryCounts: categoryCounts ?? this.categoryCounts,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'date': date.toIso8601String(),
      'articles': articles.map((a) => a.toJson()).toList(),
      'aiSummary': aiSummary,
      'categoryCounts': categoryCounts,
    };
  }

  factory NewsDigest.fromJson(Map<String, dynamic> json) {
    return NewsDigest(
      date: DateTime.parse(json['date'] as String),
      articles: (json['articles'] as List<dynamic>)
          .map((a) => NewsArticle.fromJson(a as Map<String, dynamic>))
          .toList(),
      aiSummary: json['aiSummary'] as String,
      categoryCounts: Map<String, int>.from(json['categoryCounts'] as Map),
    );
  }

  @override
  String toString() => 'NewsDigest(date: $date, articles: $totalCount)';
}

/// Категории новостей
class NewsCategory {
  final String id;
  final String name;
  final String icon;

  const NewsCategory({
    required this.id,
    required this.name,
    required this.icon,
  });

  static const List<NewsCategory> categories = [
    NewsCategory(id: 'technology', name: 'Технологии', icon: '💻'),
    NewsCategory(id: 'ai', name: 'ИИ', icon: '🤖'),
    NewsCategory(id: 'science', name: 'Наука', icon: '🔬'),
    NewsCategory(id: 'kyrgyzstan', name: 'Кыргызстан', icon: '🇰🇬'),
    NewsCategory(id: 'world', name: 'Мир', icon: '🌍'),
    NewsCategory(id: 'sports', name: 'Спорт', icon: '⚽'),
    NewsCategory(id: 'economy', name: 'Экономика', icon: '💰'),
    NewsCategory(id: 'crypto', name: 'Крипто', icon: '₿'),
  ];

  static NewsCategory fromId(String id) {
    return categories.firstWhere(
      (c) => c.id == id,
      orElse: () => const NewsCategory(id: 'other', name: 'Другое', icon: '📁'),
    );
  }
}

/// Интересы пользователя
@immutable
class UserInterests {
  final List<String> categoryIds;

  const UserInterests({required this.categoryIds});

  bool hasInterest(String categoryId) => categoryIds.contains(categoryId);

  UserInterests toggleInterest(String categoryId) {
    if (hasInterest(categoryId)) {
      return UserInterests(categoryIds: categoryIds.where((id) => id != categoryId).toList());
    } else {
      return UserInterests(categoryIds: [...categoryIds, categoryId]);
    }
  }

  Map<String, dynamic> toJson() {
    return {'categoryIds': categoryIds};
  }

  factory UserInterests.fromJson(Map<String, dynamic> json) {
    return UserInterests(
      categoryIds: (json['categoryIds'] as List<dynamic>).cast<String>(),
    );
  }

  factory UserInterests.defaultInterests() {
    return const UserInterests(categoryIds: ['kyrgyzstan', 'technology', 'ai']);
  }
}
