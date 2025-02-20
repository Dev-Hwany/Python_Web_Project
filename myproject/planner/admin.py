from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import Signup, Planner, Tourlist, PlannerDetail, Feed, Reply, Like, Bookmark


# Signup 모델 관리자 등록 예시
class SignupAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'birth')
    search_fields = ('email', 'name')
    readonly_fields = ('password',)  # 기본 수정 페이지에서는 password 필드를 직접 수정하지 못하도록 합니다.

    # 예시: 커스텀 액션으로 비밀번호를 변경하는 방법 (여기서는 간단한 액션 예시)
    actions = ['set_temp_password']

    def set_temp_password(self, request, queryset):
        new_password = "TempPass123!"  # 임시 비밀번호 예시
        for user in queryset:
            user.password = make_password(new_password)
            user.save()
        self.message_user(request, "선택한 사용자의 비밀번호가 임시 비밀번호(TempPass123!)로 변경되었습니다.")
    set_temp_password.short_description = "선택한 사용자의 비밀번호 변경 (TempPass123! 사용)"

# Feed 모델 관리자 등록
class FeedAdmin(admin.ModelAdmin):
    list_display = ('id', 'author', 'created_at', 'updated_at')  # 리스트에 표시할 필드
    search_fields = ('author__email', 'content')  # 검색 가능 필드
    list_filter = ('created_at',)  # 필터 옵션
    ordering = ('-created_at',)  # 정렬 기준 (최신 순)

class ReplyAdmin(admin.ModelAdmin):
    list_display = ('id', 'feed', 'author', 'created_at', 'parent')  # 댓글 ID, 원본 피드, 작성자, 생성 시간, 부모 댓글 표시
    search_fields = ('author__email', 'reply_content')  # 작성자 이메일, 댓글 내용 검색 가능
    list_filter = ('created_at',)  # 생성 날짜 기준으로 필터 추가
    ordering = ('-created_at',)  # 최신 댓글이 위에 오도록 정렬

admin.site.register(Signup)
admin.site.register(Planner)
admin.site.register(Tourlist)
admin.site.register(PlannerDetail)
admin.site.register(Feed)
admin.site.register(Reply, ReplyAdmin)
admin.site.register(Like)
admin.site.register(Bookmark)