import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from azure.identity import DefaultAzureCredential
from azure.servicebus import ServiceBusClient, ServiceBusMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self):
        self.namespace = settings.SERVICE_BUS_NAMESPACE
        self.queue_name = settings.SERVICE_BUS_QUEUE
        self.client = None

        if not self.namespace or not self.queue_name:
            logger.info("Service Bus notification publishing is not configured.")
            return

        fully_qualified_namespace = self.namespace
        if not fully_qualified_namespace.endswith(".servicebus.windows.net"):
            fully_qualified_namespace = f"{fully_qualified_namespace}.servicebus.windows.net"

        try:
            self.client = ServiceBusClient(
                fully_qualified_namespace=fully_qualified_namespace,
                credential=DefaultAzureCredential()
            )
            logger.info("Service Bus notification publisher initialized.")
        except Exception as exc:
            logger.error(f"Failed to initialize Service Bus notification publisher: {exc}")

    def publish(self, event_type: str, payload: Dict[str, Any]) -> bool:
        if not self.client:
            return False

        message_body = {
            "event_type": event_type,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "payload": payload
        }

        try:
            message = ServiceBusMessage(json.dumps(message_body))
            message.application_properties = {"event_type": event_type}
            with self.client.get_queue_sender(queue_name=self.queue_name) as sender:
                sender.send_messages(message)
            return True
        except Exception as exc:
            logger.error(f"Failed to publish Service Bus notification '{event_type}': {exc}")
            return False


notification_service = NotificationService()
