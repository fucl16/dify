from flask_login import current_user  # type: ignore
from flask_restful import marshal, reqparse
from werkzeug.exceptions import NotFound

from controllers.service_api import api
from controllers.service_api.wraps import DatasetApiResource, cloud_edition_billing_rate_limit_check
from fields.dataset_fields import dataset_metadata_fields
from services.dataset_service import DatasetService
from services.entities.knowledge_entities.knowledge_entities import (
    MetadataArgs,
    MetadataOperationData,
)
from services.metadata_service import MetadataService


class DatasetMetadataCreateServiceApi(DatasetApiResource):
    @cloud_edition_billing_rate_limit_check("knowledge", "dataset")
    def post(self, tenant_id, dataset_id):
        parser = reqparse.RequestParser()
        parser.add_argument("type", type=str, required=True, nullable=False, location="json")
        parser.add_argument("name", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()
        metadata_args = MetadataArgs(**args)

        dataset_id_str = str(dataset_id)
        dataset = DatasetService.get_dataset(dataset_id_str)
        if dataset is None:
            raise NotFound("Dataset not found.")
        DatasetService.check_dataset_permission(dataset, current_user)

        metadata = MetadataService.create_metadata(dataset_id_str, metadata_args)
        return marshal(metadata, dataset_metadata_fields), 201

    def get(self, tenant_id, dataset_id):
        dataset_id_str = str(dataset_id)
        dataset = DatasetService.get_dataset(dataset_id_str)
        if dataset is None:
            raise NotFound("Dataset not found.")
        return MetadataService.get_dataset_metadatas(dataset), 200


class DatasetMetadataServiceApi(DatasetApiResource):
    @cloud_edition_billing_rate_limit_check("knowledge", "dataset")
    def patch(self, tenant_id, dataset_id, metadata_id):
        parser = reqparse.RequestParser()
        parser.add_argument("name", type=str, required=True, nullable=False, location="json")
        args = parser.parse_args()

        dataset_id_str = str(dataset_id)
        metadata_id_str = str(metadata_id)
        dataset = DatasetService.get_dataset(dataset_id_str)
        if dataset is None:
            raise NotFound("Dataset not found.")
        DatasetService.check_dataset_permission(dataset, current_user)

        metadata = MetadataService.update_metadata_name(dataset_id_str, metadata_id_str, args.get("name"))
        return marshal(metadata, dataset_metadata_fields), 200

    @cloud_edition_billing_rate_limit_check("knowledge", "dataset")
    def delete(self, tenant_id, dataset_id, metadata_id):
        dataset_id_str = str(dataset_id)
        metadata_id_str = str(metadata_id)
        dataset = DatasetService.get_dataset(dataset_id_str)
        if dataset is None:
            raise NotFound("Dataset not found.")
        DatasetService.check_dataset_permission(dataset, current_user)

        MetadataService.delete_metadata(dataset_id_str, metadata_id_str)
        return 204


class DatasetMetadataBuiltInFieldServiceApi(DatasetApiResource):
    def get(self, tenant_id):
        built_in_fields = MetadataService.get_built_in_fields()
        return {"fields": built_in_fields}, 200


class DatasetMetadataBuiltInFieldActionServiceApi(DatasetApiResource):
    @cloud_edition_billing_rate_limit_check("knowledge", "dataset")
    def post(self, tenant_id, dataset_id, action):
        dataset_id_str = str(dataset_id)
        dataset = DatasetService.get_dataset(dataset_id_str)
        if dataset is None:
            raise NotFound("Dataset not found.")
        DatasetService.check_dataset_permission(dataset, current_user)

        if action == "enable":
            MetadataService.enable_built_in_field(dataset)
        elif action == "disable":
            MetadataService.disable_built_in_field(dataset)
        return 200


class DocumentMetadataEditServiceApi(DatasetApiResource):
    @cloud_edition_billing_rate_limit_check("knowledge", "dataset")
    def post(self, tenant_id, dataset_id):
        dataset_id_str = str(dataset_id)
        dataset = DatasetService.get_dataset(dataset_id_str)
        if dataset is None:
            raise NotFound("Dataset not found.")
        DatasetService.check_dataset_permission(dataset, current_user)

        parser = reqparse.RequestParser()
        parser.add_argument("operation_data", type=list, required=True, nullable=False, location="json")
        args = parser.parse_args()
        metadata_args = MetadataOperationData(**args)

        MetadataService.update_documents_metadata(dataset, metadata_args)

        return 200


api.add_resource(DatasetMetadataCreateServiceApi, "/datasets/<uuid:dataset_id>/metadata")
api.add_resource(DatasetMetadataServiceApi, "/datasets/<uuid:dataset_id>/metadata/<uuid:metadata_id>")
api.add_resource(DatasetMetadataBuiltInFieldServiceApi, "/datasets/metadata/built-in")
api.add_resource(
    DatasetMetadataBuiltInFieldActionServiceApi, "/datasets/<uuid:dataset_id>/metadata/built-in/<string:action>"
)
api.add_resource(DocumentMetadataEditServiceApi, "/datasets/<uuid:dataset_id>/documents/metadata")
