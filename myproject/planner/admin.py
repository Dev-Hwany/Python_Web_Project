from django.contrib import admin
from django.contrib.auth.hashers import make_password
from .models import Signup, Planner, Tourlist, PlannerDetail, Board

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

admin.site.register(Signup, SignupAdmin)
admin.site.register(Planner)
admin.site.register(Tourlist)
admin.site.register(PlannerDetail)
admin.site.register(Board)
