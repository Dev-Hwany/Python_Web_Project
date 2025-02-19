from django.db import models
from django.utils import timezone
from django.contrib.auth.hashers import make_password


# Create your models here.
# 1) 회원 테이블
class Signup(models.Model):
    email = models.EmailField(primary_key=True)
    password = models.CharField(max_length=100)
    name = models.CharField(max_length=50)
    birth = models.DateField(null=True, blank=True)
    addr = models.CharField(max_length=200, blank=True)
    phone_num = models.CharField(max_length=20, blank=True)

    # 회원 활성화 여부: True이면 활성, False이면 비활성 (탈퇴한 상태)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.email

    # 편의를 위해 set_password 메서드를 추가할 수도 있습니다.
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self.save()

# 2) 여행 일정 테이블
class Planner(models.Model):
    plan_no = models.AutoField(primary_key=True)
    region = models.CharField(max_length=100, blank=True)
    plan_img = models.CharField(max_length=200, blank=True)  # 이미지 경로 또는 파일명
    sdate = models.DateField(null=True, blank=True)
    edate = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Planner {self.plan_no} - {self.region}"

# 3) 관광지 정보 테이블
class Tourlist(models.Model):
    title = models.CharField(max_length=200, primary_key=True)
    addr1 = models.CharField(max_length=200, blank=True)
    areacode = models.IntegerField(null=True, blank=True)
    sigungucode = models.IntegerField(null=True, blank=True)
    image2 = models.CharField(max_length=200, blank=True)
    readcount = models.IntegerField(default=0)
    ping = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return self.title

# 4) 일정 상세 테이블
class PlannerDetail(models.Model):
    pd_no = models.AutoField(primary_key=True)
    plan_name = models.CharField(max_length=200)  # 상세 일정 제목 (예: "1일차 계획")
    planner = models.ForeignKey(Planner, on_delete=models.CASCADE, db_column='planner_fk')
    signup = models.ForeignKey(Signup, on_delete=models.CASCADE)
    title = models.ForeignKey(Tourlist, on_delete=models.CASCADE)
    wdate = models.CharField(max_length=200, null=True, blank=True)
    actual_date = models.DateField(null=True, blank=True)  # 실제 날짜 (YYYY-MM-DD)
    memo = models.TextField(blank=True)

    def __str__(self):
        return self.plan_name

# 게시판 기능
class Board(models.Model):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    # 작성자는 Signup 모델과 FK 관계로 연결 (비로그인 시 작성 불가)
    author = models.ForeignKey('Signup', on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

# 댓글 기능
class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    board = models.ForeignKey('Board', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(Signup, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Comment {self.id} by {self.author.email}"
