from prometheus_client import Counter, disable_created_metrics

disable_created_metrics()

KAFKA_CONSUMER_MESSAGES_PROCESSED = Counter(
    namespace="warehouse",
    name="kafka_consumer_messages_processed",
    documentation="Number of messages processed by the kafka consumer",
    labelnames=["topic", "status"],
)
