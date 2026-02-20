import 'package:flutter/foundation.dart';

/// Модель сообщения для AI чата
@immutable
class Message {
  final String id;
  final String content;
  final MessageRole role;
  final DateTime timestamp;
  final String? imageUrl;
  final bool isVoice;
  final Duration? voiceDuration;

  const Message({
    required this.id,
    required this.content,
    required this.role,
    required this.timestamp,
    this.imageUrl,
    this.isVoice = false,
    this.voiceDuration,
  });

  Message copyWith({
    String? id,
    String? content,
    MessageRole? role,
    DateTime? timestamp,
    String? imageUrl,
    bool? isVoice,
    Duration? voiceDuration,
  }) {
    return Message(
      id: id ?? this.id,
      content: content ?? this.content,
      role: role ?? this.role,
      timestamp: timestamp ?? this.timestamp,
      imageUrl: imageUrl ?? this.imageUrl,
      isVoice: isVoice ?? this.isVoice,
      voiceDuration: voiceDuration ?? this.voiceDuration,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'content': content,
      'role': role.name,
      'timestamp': timestamp.toIso8601String(),
      'imageUrl': imageUrl,
      'isVoice': isVoice,
      'voiceDuration': voiceDuration?.inSeconds,
    };
  }

  factory Message.fromJson(Map<String, dynamic> json) {
    return Message(
      id: json['id'] as String,
      content: json['content'] as String,
      role: MessageRole.values.firstWhere(
        (e) => e.name == json['role'],
        orElse: () => MessageRole.user,
      ),
      timestamp: DateTime.parse(json['timestamp'] as String),
      imageUrl: json['imageUrl'] as String?,
      isVoice: json['isVoice'] as bool? ?? false,
      voiceDuration: json['voiceDuration'] != null
          ? Duration(seconds: json['voiceDuration'] as int)
          : null,
    );
  }

  @override
  String toString() => 'Message(id: $id, role: $role, content: ${content.substring(0, 20)}...)';

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Message &&
          runtimeType == other.runtimeType &&
          id == other.id;

  @override
  int get hashCode => id.hashCode;
}

/// Роль отправителя сообщения
enum MessageRole {
  user,
  assistant,
  system,
}

extension MessageRoleExtension on MessageRole {
  String get displayName {
    switch (this) {
      case MessageRole.user:
        return 'Вы';
      case MessageRole.assistant:
        return 'AI';
      case MessageRole.system:
        return 'Система';
    }
  }
}
