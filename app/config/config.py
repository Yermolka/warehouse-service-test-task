import os
from dataclasses import dataclass


@dataclass
class KafkaConfig:
    bootstrap_servers: str
    group_id: str
    auto_offset_reset: str
    enable_auto_commit: bool
    max_poll_records: int
    max_poll_interval_ms: int
    session_timeout_ms: int
    topic_name: str

    def __init__(self):
        self.bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "kafka:9092")
        # self.group_id = os.getenv("KAFKA_GROUP_ID", "test-consumer-group")
        self.group_id = "test-consumer-group"
        self.auto_offset_reset = os.getenv("KAFKA_CONSUMER_AUTO_OFFSET_RESET", "earliest")
        self.enable_auto_commit = bool(os.getenv("KAFKA_CONSUMER_ENABLE_AUTO_COMMIT", "false"))
        self.max_poll_records = int(os.getenv("KAFKA_MAX_POLL_RECORDS", "100"))
        self.max_poll_interval_ms = int(os.getenv("KAFKA_CONSUMER_MAX_POLL_INTERVAL_MS", "30000"))  # 30s
        self.session_timeout_ms = int(os.getenv("KAFKA_CONSUMER_SESSION_TIMEOUT_MS", "30000"))  # 30s
        self.topic_name = os.getenv("KAFKA_TOPIC_NAME", "movements")

    def to_dict(self):
        return {
            "bootstrap.servers": self.bootstrap_servers,
            "group.id": self.group_id,
            "auto.offset.reset": self.auto_offset_reset,
            "enable.auto.commit": self.enable_auto_commit,
        }


@dataclass
class DbConfig:
    host: str
    port: int
    username: str
    password: str
    db_name: str
    pool_size: int
    timeout: int

    def __init__(self):
        self.host = os.getenv("DB_HOST", "postgres")
        self.port = int(os.getenv("DB_PORT", "5432"))
        self.username = os.getenv("DB_USER", "warehouse")
        self.password = os.getenv("DB_PASSWORD", "warehouse")
        self.db_name = os.getenv("DB_NAME", "warehouse")
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "10"))
        self.timeout = int(os.getenv("DB_TIMEOUT", "30"))


@dataclass
class RedisConfig:
    host: str
    port: int
    db: int
    password: str

    def __init__(self):
        self.host = os.getenv("REDIS_HOST", "redis")
        self.port = int(os.getenv("REDIS_PORT", "6379"))
        self.db = int(os.getenv("REDIS_DB", "0"))
        self.password = os.getenv("REDIS_PASSWORD", "")
