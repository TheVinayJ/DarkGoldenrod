import requests
from requests.auth import HTTPBasicAuth
from .models import RemoteNode
import logging

logger = logging.getLogger(__name__)

# This class was generated from OpenAI, ChatGPT o1-mini
# Prompt: 'Can you make a class to connect to a remote node?'
class RemoteNodeService:
    @staticmethod
    def connect_to_node(node_id):
        try:
            node = RemoteNode.objects.get(id=node_id, is_active=True)
        except RemoteNode.DoesNotExist:
            logger.warning(f"Remote node with id {node_id} not found or inactive.")
            return {"error": "Remote node not found or inactive."}

        try:
            response = requests.get(
                f"{node.url}/api/ping/",  # Example endpoint
                auth=HTTPBasicAuth(node.username, node.password),
                timeout=10  # Timeout after 10 seconds
            )
            response.raise_for_status()
            logger.info(f"Successfully connected to remote node '{node.name}'.")
            return {"success": True, "data": response.json()}
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to connect to remote node '{node.name}': {e}")
            return {"error": str(e)}