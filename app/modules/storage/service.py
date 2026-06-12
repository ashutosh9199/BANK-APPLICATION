import os
import uuid
import logging
from azure.storage.blob import BlobServiceClient, ContentSettings
from azure.identity import DefaultAzureCredential
from app.core.config import settings

logger = logging.getLogger(__name__)

class StorageService:
    def __init__(self):
        self.conn_str = settings.AZURE_STORAGE_CONNECTION_STRING
        self.account_url = settings.AZURE_STORAGE_ACCOUNT_URL
        self.container_name = settings.AZURE_CONTAINER_NAME
        self.require_azure_storage = settings.REQUIRE_AZURE_STORAGE
        self.client = None
        self.init_error = None
        
        if self.conn_str and self.conn_str.strip():
            try:
                self.client = BlobServiceClient.from_connection_string(self.conn_str)
                container_client = self.client.get_container_client(self.container_name)
                # Attempt to create the container in case it does not exist
                try:
                    container_client.create_container()
                except Exception:
                    # Container might already exist
                    pass
                logger.info("Azure Blob Storage initialized successfully.")
            except Exception as e:
                self.init_error = e
                logger.error(f"Failed to initialize Azure Blob Storage: {e}")
        elif self.account_url and self.account_url.strip():
            try:
                self.client = BlobServiceClient(
                    account_url=self.account_url,
                    credential=DefaultAzureCredential()
                )
                container_client = self.client.get_container_client(self.container_name)
                try:
                    container_client.create_container()
                except Exception:
                    pass
                logger.info("Azure Blob Storage initialized with managed identity.")
            except Exception as e:
                self.init_error = e
                logger.error(f"Failed to initialize Azure Blob Storage with managed identity: {e}")

    def upload_file(self, file_content: bytes, filename: str, content_type: str) -> dict:
        ext = os.path.splitext(filename)[1].lower()
        unique_filename = f"{uuid.uuid4()}{ext}"
        
        if self.client:
            try:
                blob_client = self.client.get_blob_client(container=self.container_name, blob=unique_filename)
                content_settings = ContentSettings(content_type=content_type)
                blob_client.upload_blob(file_content, overwrite=True, content_settings=content_settings)
                return {"url": blob_client.url, "blob_name": unique_filename}
            except Exception as e:
                if self.require_azure_storage:
                    raise RuntimeError(f"Azure Blob upload failed: {e}") from e
                logger.error(f"Azure upload failed, falling back to local storage: {e}")
                return self._local_fallback_upload(file_content, unique_filename)
        else:
            if self.require_azure_storage:
                if self.init_error:
                    raise RuntimeError(f"Azure Blob Storage is required but initialization failed: {self.init_error}") from self.init_error
                raise RuntimeError("Azure Blob Storage is required but no storage client is configured.")
            return self._local_fallback_upload(file_content, unique_filename)

    def _local_fallback_upload(self, file_content: bytes, unique_filename: str) -> dict:
        os.makedirs("uploads", exist_ok=True)
        local_path = os.path.join("uploads", unique_filename)
        with open(local_path, "wb") as f:
            f.write(file_content)
        url = f"/api/uploads/{unique_filename}"
        return {"url": url, "blob_name": unique_filename}

    def delete_file(self, blob_name: str) -> bool:
        if self.client:
            try:
                blob_client = self.client.get_blob_client(container=self.container_name, blob=blob_name)
                blob_client.delete_blob()
                return True
            except Exception as e:
                logger.error(f"Azure delete failed: {e}")
                return False
        else:
            local_path = os.path.join("uploads", blob_name)
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                    return True
                except Exception:
                    return False
            return False

storage_service = StorageService()
