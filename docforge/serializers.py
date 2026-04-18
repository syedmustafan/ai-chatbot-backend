from rest_framework import serializers

from .models import ExtractedRecord, GeneratedDocument, UploadSession


class GeneratedDocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedDocument
        fields = ['id', 'template_key', 'display_name', 'created_at']


class ExtractedRecordSerializer(serializers.ModelSerializer):
    documents = GeneratedDocumentSerializer(many=True, read_only=True)

    class Meta:
        model = ExtractedRecord
        fields = ['id', 'row_index', 'data', 'missing_fields', 'documents']
        read_only_fields = ['row_index', 'missing_fields', 'documents']


class UploadSessionSerializer(serializers.ModelSerializer):
    records = ExtractedRecordSerializer(many=True, read_only=True)
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = UploadSession
        fields = [
            'id',
            'original_filename',
            'template_pack',
            'privacy_mode',
            'status',
            'created_at',
            'expires_at',
            'downloaded_at',
            'record_count',
            'records',
        ]
        read_only_fields = [
            'id',
            'original_filename',
            'status',
            'created_at',
            'expires_at',
            'downloaded_at',
            'record_count',
            'records',
        ]

    def get_record_count(self, obj):
        return obj.records.count()


class UploadSessionListSerializer(serializers.ModelSerializer):
    record_count = serializers.SerializerMethodField()

    class Meta:
        model = UploadSession
        fields = [
            'id',
            'original_filename',
            'template_pack',
            'privacy_mode',
            'status',
            'created_at',
            'expires_at',
            'downloaded_at',
            'record_count',
        ]

    def get_record_count(self, obj):
        return obj.records.count()
