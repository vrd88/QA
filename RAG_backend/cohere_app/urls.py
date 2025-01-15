# urls.py
from django.urls import path
from .views import *

urlpatterns = [
    path('cohere/generate/', cohere_generate, name='cohere_generate'),
    path('history/', get_prompt_history, name='get_saved_prompts'),
    path('history/<str:session_id>/', get_session_history, name='get_session_history'),  
    path('login/', login_user, name='login'),
    path('logout/', logout_user, name='logout'),
    path('save-comment/<int:pk>/',save_comment, name='save-comment'),
    path('mark_satisfied/<int:pk>/', mark_satisfied, name='mark_satisfied'),
    path('mark_unsatisfied/<int:pk>/', mark_unsatisfied, name='mark_unsatisfied'),
    path('documents/', get_documents),
    path('serve-pdf/<str:filename>/<int:page_number>/', serve_pdf, name='serve_pdf'),
    # path('folder_name/',get_folder),
    # path('documents_by_ps_number', get_documents, name='get_documents_by_ps_number'),

    path('collections/', get_collection_name, name='get_collections'),
    path('collections/<str:collection_name>/files/', collection_files, name='collection-files'),
    path('collections/<str:collection_name>/delete/', delete_collection, name='delete-collection'),
    path('collections/file-delete/<path:source>/<str:collection_name>/', delete_file, name='delete_file'),
    path('collections/create_collection/', create_collection, name='create_collection'),
    path('collections/progress/', get_progress, name='get_progress'),
    path("milvus-data/<str:collection_name>/", get_milvus_data, name="milvus-data"),
    path('current-using-collection/', get_current_using_collection, name='get-current-using-collection'),
    path("update-current-collection/", update_current_collection, name="update-current-collection"),
    path('restart-server/', restart_server, name='restart_server')
]

