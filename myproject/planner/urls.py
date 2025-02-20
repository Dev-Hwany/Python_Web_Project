from django.urls import path
from . import views

urlpatterns = [
    path('', views.main_page, name='main_page'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('password_reset/', views.password_reset_view, name='password_reset'),
    path('my_page/', views.my_page_view, name='my_page'),
    path('my_schedule/', views.my_schedule_view, name='my_schedule'),
    path('schedule/<int:plan_no>/delete/', views.schedule_delete_view, name='schedule_delete'),
    path('schedule/<int:plan_no>/', views.schedule_detail_view, name='schedule_detail'),
    path('update_profile/', views.update_profile_view, name='update_profile'),
    path('delete_profile/', views.delete_profile_view, name='delete_profile'),
    path('plan_schedule/', views.plan_schedule_view, name='plan_schedule'),
    path('save_schedule/', views.save_schedule_view, name='save_schedule'),
    path('update_destination/', views.update_destination_view, name='update_destination'),
    path("chatbot/", views.chatbot, name="chatbot"),
    # 피드 관련 URL
    path('feed/', views.feed_main, name='feed_main'),
    path('feed/upload', views.upload_feed, name='upload_feed'),
    path('feed/reply', views.upload_reply, name='upload_reply'),
    path('feed/like', views.toggle_like, name='toggle_like'),
    path('feed/bookmark', views.toggle_bookmark, name='toggle_bookmark'),
    path('feed/detail/<int:feed_id>/', views.feed_detail_modal, name='feed_detail_modal'),

    # 댓글 답글 기능을 위한 URL 패턴 등록
    path('feed/comment_reply/<int:parent_id>/', views.comment_reply, name='comment_reply'),

    # 댓글 수정/삭제 URL도 필요하면 추가
    path('feed/comment_update/<int:comment_id>/', views.comment_update, name='comment_update'),
    path('feed/comment_delete/<int:comment_id>/', views.comment_delete, name='comment_delete'),
]