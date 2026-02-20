import 'package:flutter/foundation.dart';

/// Модель контакта
@immutable
class Contact {
  final String id;
  final String name;
  final String phone;
  final DateTime createdAt;
  final String? notes;
  final String? avatarUrl;

  const Contact({
    required this.id,
    required this.name,
    required this.phone,
    required this.createdAt,
    this.notes,
    this.avatarUrl,
  });

  /// Получить инициалы для аватара
  String get initials {
    final parts = name.trim().split(' ');
    if (parts.isEmpty) return '?';
    if (parts.length == 1) return parts[0].substring(0, 1).toUpperCase();
    return '${parts[0].substring(0, 1)}${parts[1].substring(0, 1)}'.toUpperCase();
  }

  /// Получить цвет для аватара (на основе имени)
  int get avatarColor {
    final colors = [
      0xFFE57373, // Red
      0xFFF06292, // Pink
      0xFFBA68C8, // Purple
      0xFF9575CD, // Deep Purple
      0xFF7986CB, // Indigo
      0xFF64B5F6, // Blue
      0xFF4FC3F7, // Light Blue
      0xFF4DD0E1, // Cyan
      0xFF4DB6AC, // Teal
      0xFF81C784, // Green
      0xFFFFD54F, // Amber
      0xFFFFB74D, // Orange
    ];
    return colors[name.length % colors.length];
  }

  Contact copyWith({
    String? id,
    String? name,
    String? phone,
    DateTime? createdAt,
    String? notes,
    String? avatarUrl,
  }) {
    return Contact(
      id: id ?? this.id,
      name: name ?? this.name,
      phone: phone ?? this.phone,
      createdAt: createdAt ?? this.createdAt,
      notes: notes ?? this.notes,
      avatarUrl: avatarUrl ?? this.avatarUrl,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'phone': phone,
      'createdAt': createdAt.toIso8601String(),
      'notes': notes,
      'avatarUrl': avatarUrl,
    };
  }

  factory Contact.fromJson(Map<String, dynamic> json) {
    return Contact(
      id: json['id'] as String,
      name: json['name'] as String,
      phone: json['phone'] as String,
      createdAt: DateTime.parse(json['createdAt'] as String),
      notes: json['notes'] as String?,
      avatarUrl: json['avatarUrl'] as String?,
    );
  }

  @override
  String toString() => 'Contact(name: $name, phone: $phone)';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Contact && runtimeType == other.runtimeType && id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Модель пользователя
@immutable
class User {
  final String telegramId;
  final String? username;
  final String? firstName;
  final String? lastName;
  final DateTime createdAt;
  final DateTime lastActive;
  final bool isPremium;

  const User({
    required this.telegramId,
    this.username,
    this.firstName,
    this.lastName,
    required this.createdAt,
    required this.lastActive,
    this.isPremium = false,
  });

  /// Полное имя
  String get fullName {
    final parts = [firstName, lastName].where((s) => s != null && s.isNotEmpty).toList();
    if (parts.isEmpty) return username ?? 'Пользователь';
    return parts.join(' ');
  }

  User copyWith({
    String? telegramId,
    String? username,
    String? firstName,
    String? lastName,
    DateTime? createdAt,
    DateTime? lastActive,
    bool? isPremium,
  }) {
    return User(
      telegramId: telegramId ?? this.telegramId,
      username: username ?? this.username,
      firstName: firstName ?? this.firstName,
      lastName: lastName ?? this.lastName,
      createdAt: createdAt ?? this.createdAt,
      lastActive: lastActive ?? this.lastActive,
      isPremium: isPremium ?? this.isPremium,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'telegramId': telegramId,
      'username': username,
      'firstName': firstName,
      'lastName': lastName,
      'createdAt': createdAt.toIso8601String(),
      'lastActive': lastActive.toIso8601String(),
      'isPremium': isPremium,
    };
  }

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      telegramId: json['telegramId'] as String,
      username: json['username'] as String?,
      firstName: json['firstName'] as String?,
      lastName: json['lastName'] as String?,
      createdAt: DateTime.parse(json['createdAt'] as String),
      lastActive: DateTime.parse(json['lastActive'] as String),
      isPremium: json['isPremium'] as bool? ?? false,
    );
  }

  @override
  String toString() => 'User(telegramId: $telegramId, name: $fullName)';
}

/// Модель настроек пользователя
@immutable
class UserSettings {
  final bool voiceModeEnabled;
  final String preferredVoice;
  final String languageCode;
  final ThemeMode themeMode;
  final bool notificationsEnabled;
  final DateTime? digestScheduleTime;

  const UserSettings({
    this.voiceModeEnabled = false,
    this.preferredVoice = 'ru-RU-SvetlanaNeural',
    this.languageCode = 'ru',
    this.themeMode = ThemeMode.system,
    this.notificationsEnabled = true,
    this.digestScheduleTime,
  });

  UserSettings copyWith({
    bool? voiceModeEnabled,
    String? preferredVoice,
    String? languageCode,
    ThemeMode? themeMode,
    bool? notificationsEnabled,
    DateTime? digestScheduleTime,
  }) {
    return UserSettings(
      voiceModeEnabled: voiceModeEnabled ?? this.voiceModeEnabled,
      preferredVoice: preferredVoice ?? this.preferredVoice,
      languageCode: languageCode ?? this.languageCode,
      themeMode: themeMode ?? this.themeMode,
      notificationsEnabled: notificationsEnabled ?? this.notificationsEnabled,
      digestScheduleTime: digestScheduleTime ?? this.digestScheduleTime,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'voiceModeEnabled': voiceModeEnabled,
      'preferredVoice': preferredVoice,
      'languageCode': languageCode,
      'themeMode': themeMode.index,
      'notificationsEnabled': notificationsEnabled,
      'digestScheduleTime': digestScheduleTime?.toIso8601String(),
    };
  }

  factory UserSettings.fromJson(Map<String, dynamic> json) {
    return UserSettings(
      voiceModeEnabled: json['voiceModeEnabled'] as bool? ?? false,
      preferredVoice: json['preferredVoice'] as String? ?? 'ru-RU-SvetlanaNeural',
      languageCode: json['languageCode'] as String? ?? 'ru',
      themeMode: ThemeMode.values[json['themeMode'] as int? ?? 0],
      notificationsEnabled: json['notificationsEnabled'] as bool? ?? true,
      digestScheduleTime: json['digestScheduleTime'] != null
          ? DateTime.parse(json['digestScheduleTime'] as String)
          : null,
    );
  }

  factory UserSettings.defaultSettings() {
    return const UserSettings();
  }
}

/// Режим темы
enum ThemeMode {
  light,
  dark,
  system,
}
