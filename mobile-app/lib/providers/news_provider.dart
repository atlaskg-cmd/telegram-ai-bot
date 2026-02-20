import 'package:flutter/foundation.dart';
import '../models/models.dart';
import '../services/services.dart';

/// Провайдер для новостей
class NewsProvider extends ChangeNotifier {
  final NewsService _newsService = NewsService();
  final StorageService _storageService = StorageService();

  List<NewsArticle> _news = [];
  NewsDigest? _digest;
  UserInterests _interests = const UserInterests(categoryIds: []);
  bool _isLoading = false;
  String? _error;
  DateTime? _lastUpdated;

  List<NewsArticle> get news => _news;
  NewsDigest? get digest => _digest;
  UserInterests get interests => _interests;
  bool get isLoading => _isLoading;
  String? get error => _error;
  DateTime? get lastUpdated => _lastUpdated;

  /// Инициализация
  Future<void> init() async {
    final interestIds = _storageService.interests;
    _interests = UserInterests(categoryIds: interestIds);
    notifyListeners();
  }

  /// Загрузить новости
  Future<void> loadNews({int limit = 20}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _news = await _newsService.getNewsFromRSS(limit: limit);
      _lastUpdated = DateTime.now();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Загрузить дайджест
  Future<void> loadDigest() async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _digest = await _newsService.getDigest(
        interests: _interests.categoryIds,
      );
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Обновить интересы
  Future<void> updateInterests(List<String> categoryIds) async {
    _interests = UserInterests(categoryIds: categoryIds);
    await _storageService.saveInterests(categoryIds);
    notifyListeners();
    
    // Перезагружаем дайджест с новыми интересами
    await loadDigest();
  }

  /// Переключить интерес
  Future<void> toggleInterest(String categoryId) async {
    _interests = _interests.toggleInterest(categoryId);
    await _storageService.saveInterests(_interests.categoryIds);
    notifyListeners();
  }

  /// Новости Кыргызстана
  Future<void> loadKyrgyzstanNews({int limit = 10}) async {
    _isLoading = true;
    _error = null;
    notifyListeners();

    try {
      _news = await _newsService.getKyrgyzstanNews(limit: limit);
      _lastUpdated = DateTime.now();
    } catch (e) {
      _error = e.toString();
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Обновить
  Future<void> refresh() async {
    await loadNews();
  }

  /// Проверить, устарели ли данные
  bool get isStale {
    if (_lastUpdated == null) return true;
    return DateTime.now().difference(_lastUpdated!).inMinutes > 15;
  }
}
