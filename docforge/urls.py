from django.urls import path

from .views import (
    DocumentDownloadView,
    GenerateView,
    PacksView,
    RecordDetailView,
    SessionDetailView,
    SessionListView,
    SessionZipDownloadView,
    SweepView,
    UploadView,
)

urlpatterns = [
    path('packs/', PacksView.as_view()),
    path('upload/', UploadView.as_view()),
    path('sessions/', SessionListView.as_view()),
    path('sessions/<uuid:session_id>/', SessionDetailView.as_view()),
    path('sessions/<uuid:session_id>/generate/', GenerateView.as_view()),
    path('sessions/<uuid:session_id>/download/', SessionZipDownloadView.as_view()),
    path('records/<int:record_id>/', RecordDetailView.as_view()),
    path('documents/<int:document_id>/download/', DocumentDownloadView.as_view()),
    path('_internal/sweep/', SweepView.as_view()),
]
