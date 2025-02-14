import json
import re
import random
import string

import openai
import requests  # 실제 API 호출 시 사용
from datetime import datetime, timedelta  # 추가: 날짜 계산을 위해
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.core.paginator import Paginator
from .models import Signup, Planner, Tourlist, PlannerDetail, Board, Comment
from django.core.mail import send_mail  # 실제 메일 전송 시 사용 (설정 필요)
from django.contrib.auth.hashers import make_password, check_password  # 해시 처리를 위한 함수
from .email_utils import send_email_dynamic


def main_page(request):
    regions = [
        {"name": "서울", "img": "seoul.jpg"},
        {"name": "부산", "img": "busan.jpg"},
        {"name": "제주도", "img": "jeju.jpg"},
        {"name": "강릉", "img": "gangneung.jpg"},
        {"name": "경주", "img": "gyeongju.jpg"},
        {"name": "영월", "img": "yeongwol.jpg"},
        {"name": "전주", "img": "jeonju.jpg"},
        {"name": "여수", "img": "yeosu.jpg"},
        {"name": "인천", "img": "incheon.jpg"},
        {"name": "속초", "img": "sokcho.jpg"},
        {"name": "대구", "img": "daegu.jpg"},
        {"name": "춘천", "img": "chuncheon.jpg"}
    ]
    context = {
        "regions": regions,
    }
    return render(request, "planner/main_page.html", context)


@csrf_exempt
def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        name = request.POST.get('name')
        birth = request.POST.get('birth')
        addr = request.POST.get('addr')
        phone_num = request.POST.get('phone_num')

        # 서버 측 검증

        # 이메일 검증
        var_email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(var_email_pattern, email):
            return JsonResponse({'status': 'error', 'message': '유효하지 않은 이메일 형식입니다.'}, status=400)

        # 비밀번호 검증: 8~16자, 영문 대소문자, 숫자, 특수문자 포함
        var_password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\'":\\|,.<>\/?]).{8,16}$'
        if not re.match(var_password_pattern, password):
            return JsonResponse({'status': 'error', 'message': '비밀번호는 8~16자 영문 대소문자, 숫자, 특수문자를 포함해야 합니다.'}, status=400)

        if password != password_confirm:
            return JsonResponse({'status': 'error', 'message': '비밀번호와 비밀번호 재확인이 일치하지 않습니다.'}, status=400)

        # 중복 가입 검사:
        # 만약 해당 이메일로 가입한 사용자가 있다면,
        # - is_active가 True이면 이미 가입된 계정이므로 에러를 반환하고,
        # - is_active가 False이면 해당 레코드를 업데이트하여 재가입(재활성화) 처리
        try:
            existing_user = Signup.objects.get(email=email)
            if existing_user.is_active:
                return JsonResponse({'status': 'error', 'message': '이미 가입된 이메일입니다.'}, status=400)
            else:
                # 탈퇴된 계정이면 업데이트하여 재가입 처리
                existing_user.password = make_password(password)
                existing_user.name = name
                existing_user.birth = birth if birth else None
                existing_user.addr = addr
                existing_user.phone_num = phone_num
                existing_user.is_active = True
                existing_user.save()
                return JsonResponse({'status': 'success', 'message': '회원가입 성공'})
        except Signup.DoesNotExist:
            # 존재하지 않는 경우에는 새로 생성
            Signup.objects.create(
                email=email,
                password=make_password(password),
                name=name,
                birth=birth if birth else None,
                addr=addr,
                phone_num=phone_num,
                is_active=True
            )
            return JsonResponse({'status': 'success', 'message': '회원가입 성공'})
    else:
        return render(request, 'planner/signup.html')


@csrf_exempt
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        try:
            user = Signup.objects.get(email=email)
            # 활성화 상태가 아니면 로그인 실패 처리
            if not user.is_active:
                return JsonResponse({"status": "error", "message": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=403)
            if check_password(password, user.password):
                request.session["user_email"] = user.email
                request.session["user_name"] = user.name
                return JsonResponse({"status": "success", "user_name": user.name})
            else:
                raise Signup.DoesNotExist
        except Signup.DoesNotExist:
            return JsonResponse({"status": "error", "message": "아이디 또는 비밀번호가 올바르지 않습니다."}, status=400)
    else:
        return JsonResponse({"status": "error", "message": "POST 요청만 허용됩니다."}, status=405)


def logout_view(request):
    request.session.flush()  # 세션 데이터 초기화
    return redirect('main_page')


@csrf_exempt
def password_reset_view(request):
    """
    비밀번호 찾기:
    사용자가 본인의 이메일과 이름을 입력하면, 해당 회원 정보를 확인하고,
    임시 비밀번호(8자리)를 생성하여 회원의 비밀번호를 해시 처리한 후 업데이트하고,
    전용 발신자 계정을 사용하여 임시 비밀번호를 이메일로 전송합니다.
    """
    if request.method == "POST":
        email = request.POST.get("email")
        name = request.POST.get("name")
        try:
            user = Signup.objects.get(email=email, name=name)
        except Signup.DoesNotExist:
            return JsonResponse({"status": "error", "message": "해당 회원 정보를 찾을 수 없습니다."}, status=400)

        # 임시 비밀번호 생성 (8자리)
        temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

        # 비밀번호 해시 처리 후 업데이트
        user.password = make_password(temp_password)
        user.save()

        # 이메일 전송 (전용 발신자 계정을 사용하여 settings.py의 EMAIL 설정에 따라 처리됨)
        subject = "여행 플래너 임시 비밀번호 안내"
        message = (
            f"안녕하세요, {user.name}님.\n\n"
            f"요청하신 임시 비밀번호는 {temp_password} 입니다.\n"
            "로그인 후 반드시 비밀번호를 변경해 주세요.\n\n"
            "감사합니다."
        )
        recipient_list = [user.email]

        try:
            send_mail(subject, message, None, recipient_list, fail_silently=False)
            # 발신자 정보를 생략하면 settings.py의 DEFAULT_FROM_EMAIL이 사용됩니다.
        except Exception as e:
            return JsonResponse({"status": "error", "message": f"이메일 전송에 실패했습니다: {e}"}, status=500)

        return JsonResponse({"status": "success", "message": "임시 비밀번호가 이메일로 전송되었습니다. 이메일을 확인해 주세요."})
    else:
        return render(request, 'planner/password_reset.html')


def search_view(request):
    """
    검색 페이지:
    사용자가 여행지명을 입력하여 검색할 수 있도록 하는 페이지입니다.
    폼 제출 시 GET 방식으로 plan_schedule 뷰에 destination 파라미터를 전달합니다.
    """
    return render(request, 'planner/search.html')


def my_page_view(request):
    """
    마이페이지: 로그인한 사용자의 회원정보와 '나의 일정' (추후 구현 예정)을 표시합니다.
    """
    user_email = request.session.get('user_email')
    if not user_email:
        return redirect('login')
    try:
        user = Signup.objects.get(email=user_email)
    except Signup.DoesNotExist:
        return redirect('login')
    return render(request, 'planner/my_page.html', {'user': user})


@csrf_exempt
def update_profile_view(request):
    """
    회원정보 수정: 로그인한 사용자의 정보를 업데이트합니다.
    선택적으로 새 비밀번호와 새 비밀번호 재확인을 입력하여 비밀번호를 변경할 수 있습니다.
    """
    user_email = request.session.get('user_email')
    if not user_email:
        return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)
    try:
        user = Signup.objects.get(email=user_email)
    except Signup.DoesNotExist:
        return JsonResponse({"status": "error", "message": "회원 정보를 찾을 수 없습니다."}, status=400)

    if request.method == 'POST':
        user.name = request.POST.get('name', user.name)
        user.addr = request.POST.get('addr', user.addr)
        user.phone_num = request.POST.get('phone_num', user.phone_num)
        birth = request.POST.get('birth')
        if birth:
            user.birth = birth

        # 새 비밀번호 업데이트 (선택적)
        new_password = request.POST.get('new_password')
        new_password_confirm = request.POST.get('new_password_confirm')
        if new_password or new_password_confirm:
            if new_password != new_password_confirm:
                return JsonResponse({"status": "error", "message": "새 비밀번호와 재확인이 일치하지 않습니다."}, status=400)
            # 비밀번호 형식 검증: 8~16자, 영문 대소문자, 숫자, 특수문자 포함
            var_password_pattern = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_+\-=\[\]{};\'":\\|,.<>\/?]).{8,16}$'
            if not re.match(var_password_pattern, new_password):
                return JsonResponse({"status": "error", "message": "새 비밀번호는 8~16자 영문 대소문자, 숫자, 특수문자를 포함해야 합니다."},
                                    status=400)
            user.password = make_password(new_password)

        user.save()
        return JsonResponse({"status": "success", "message": "회원정보가 업데이트 되었습니다."})
    else:
        return render(request, 'planner/update_profile.html', {'user': user})


@csrf_exempt
def delete_profile_view(request):
    """
    회원탈퇴: 로그인한 사용자가 자신의 회원정보를 탈퇴 처리합니다.
    실제로 데이터를 삭제하는 대신, is_active 값을 False로 설정합니다.
    """
    user_email = request.session.get('user_email')
    if not user_email:
        return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)
    try:
        user = Signup.objects.get(email=user_email)
    except Signup.DoesNotExist:
        return JsonResponse({"status": "error", "message": "회원 정보를 찾을 수 없습니다."}, status=400)
    if request.method == 'POST':
        # 탈퇴 시 is_active를 False로 변경
        user.is_active = False
        user.save()
        # 세션 초기화
        request.session.flush()
        return JsonResponse({"status": "success", "message": "회원탈퇴가 완료되었습니다."})
    else:
        return render(request, 'planner/delete_profile.html', {'user': user})


# Open AI API 키
openai.api_key = "YOUR_OPENAI_API_KEY"
# Google Maps API
GOOGLE_MAPS_API_KEY = "AIzaSyCrrpnBOa4XrAStl7Uw3AEmWcT2Q-iPJNI"
# 한국관광공사 API 키
KTO_API_KEY = "fc1HFmKUklspTCNZJzscwboSHKb0DufegHrGXRcsPKYZeNG7xkuJIYeNG2ZufrSk4GSNyeajxAjrhnTY8o3Y9w=="

@csrf_protect
def plan_schedule_view(request):
    """
    일정 만들기 페이지:
    - GET 요청 시:
      여행지명(destination)을 GET 파라미터로 받아,
      Google Places API와 한국관광공사 API를 이용해 추천 장소 목록을 수집하고,
      첫 검색 결과의 좌표를 지도 중심 좌표(map_center)로 설정하여 템플릿에 전달합니다.
    - POST 요청 시:
      AJAX로 전송된 JSON 데이터를 파싱하여, 로그인한 사용자의 여행 일정(Planner)과
      각 일정 항목(PlannerDetail)을 생성합니다.

      전달되는 payload 예시:
      {
         "travel_title": "여행 제목",
         "start_date": "2025-03-01",
         "end_date": "2025-03-05",
         "destination": "서울",
         "itineraries": {
             "1": [
                  {"name": "N서울타워", "address": "서울특별시 용산구...", "description": [...], "lat": 37.5512, "lng": 126.9882, "memo": ""},
                  ...
             ],
             "2": [ ... ],
             ...
         }
      }

      PlannerDetail의 'plan_name'은 DB의 기본키로, 여기서는 전체 여행 제목, DAY 번호, 그리고 해당 DAY 내의 항목 인덱스를 조합하여 생성합니다.
      또한, wdate 필드에는 시작일을 기준으로 해당 DAY에 해당하는 날짜가 저장됩니다.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"status": "error", "message": "잘못된 JSON 데이터입니다."}, status=400)

        travel_title = data.get("travel_title")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        destination = data.get("destination")
        itineraries = data.get("itineraries", {})  # 예: {"1": [ {...}, {...} ], "2": [ ... ], ...}

        if not all([travel_title, start_date, end_date, destination]):
            return JsonResponse({"status": "error", "message": "필수 필드가 누락되었습니다."}, status=400)

        user_email = request.session.get("user_email")
        if not user_email:
            return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)
        try:
            user = Signup.objects.get(email=user_email)
        except Signup.DoesNotExist:
            return JsonResponse({"status": "error", "message": "회원 정보를 찾을 수 없습니다."}, status=400)

        # Planner 객체 생성 (Planner 테이블에 일정 기본 정보 저장)
        planner = Planner.objects.create(
            region=destination,
            plan_img="",
            sdate=start_date,
            edate=end_date
        )

        # 시작일을 datetime 객체로 변환 (형식: YYYY-MM-DD)
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            return JsonResponse({"status": "error", "message": "시작일 형식이 올바르지 않습니다."}, status=400)

        # 각 DAY의 itinerary 항목에 대해 PlannerDetail 레코드 생성
        for day, items in itineraries.items():
            try:
                day_int = int(day)
            except ValueError:
                continue
            # 각 DAY에 해당하는 날짜를 계산 (DAY 1은 시작일, DAY 2는 시작일+1일 등)
            wdate_value = (start_date_obj + timedelta(days=day_int - 1)).date()

            for index, item in enumerate(items, start=1):
                tour_title = item.get("name")
                if not tour_title:
                    continue
                try:
                    tour = Tourlist.objects.get(title=tour_title)
                except Tourlist.DoesNotExist:
                    tour = Tourlist.objects.create(
                        title=tour_title,
                        addr1=item.get("address", ""),
                        areacode=None,
                        sigungucode=None,
                        image2="",
                        readcount=0,
                        ping=0,
                    )
                # 고유한 PlannerDetail의 기본키(plan_name) 생성
                plan_detail_name = f"{travel_title} - DAY {day} - {index}"
                memo_value = item.get("memo", "")
                PlannerDetail.objects.create(
                    plan_name=plan_detail_name,  # 고유 기본키
                    planner=planner,
                    signup=user,
                    title=tour,  # Tourlist 객체 (기본키: title)
                    wdate=f"DAY {day_int} - {index}",  # 계산된 날짜
                    memo=memo_value
                )
        return JsonResponse({"status": "success", "message": "일정이 저장되었습니다."})
    else:
        # GET 요청 처리: 기존 코드 그대로 추천 장소 수집 등
        destination = request.GET.get("destination", "")
        recommended_places = []
        search_lat, search_lng = None, None

        if destination:
            # 1. Google Places API - Text Search
            google_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={destination}&language=ko&key={GOOGLE_MAPS_API_KEY}"
            google_response = requests.get(google_url)
            google_places = google_response.json()
            if "results" in google_places and google_places["results"]:
                first_place = google_places["results"][0]
                search_lat = first_place["geometry"]["location"]["lat"]
                search_lng = first_place["geometry"]["location"]["lng"]
                for place in google_places["results"]:
                    recommended_places.append({
                        "name": place["name"],
                        "address": place.get("formatted_address", ""),
                        "description": place.get("types", []),
                        "lat": place["geometry"]["location"]["lat"],
                        "lng": place["geometry"]["location"]["lng"],
                    })
            # 2. Google Places API - Nearby Search
            if search_lat and search_lng:
                nearby_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={search_lat},{search_lng}&radius=2000&language=ko&key={GOOGLE_MAPS_API_KEY}"
                nearby_response = requests.get(nearby_url)
                nearby_places = nearby_response.json()
                for place in nearby_places.get("results", []):
                    recommended_places.append({
                        "name": place["name"],
                        "address": place.get("vicinity", ""),
                        "description": place.get("types", []),
                        "lat": place["geometry"]["location"]["lat"],
                        "lng": place["geometry"]["location"]["lng"],
                    })
            # 3. 한국관광공사 API
            api_url = "http://apis.data.go.kr/B551011/KorService1/searchKeyword1"
            params = {
                "serviceKey": KTO_API_KEY,
                "keyword": destination,
                "numOfRows": 100,
                "pageNo": 1,
                "MobileOS": "ETC",
                "MobileApp": "AppTest",
                "_type": "json"
            }
            try:
                ktour_response = requests.get(api_url, params=params)
                ktour_response.raise_for_status()  # HTTP 오류 시 예외 발생
                ktour_places = ktour_response.json()
                # 디버깅: 서버 콘솔에 API 응답 출력
                print("KTO API 응답:", json.dumps(ktour_places, indent=2, ensure_ascii=False))
                items = ktour_places.get("response", {}).get("body", {}).get("items", {}).get("item", [])

                # items가 딕셔너리인 경우 리스트로 변환
                if isinstance(items, dict):
                    items = [items]

                for place in items:
                    recommended_places.append({
                        "name": place.get("title", ""),
                        "address": place.get("addr1", ""),
                        "description": place.get("contenttypeid", "설명 없음"),
                        "firstimage2": place.get("firstimage2", "https://via.placeholder.com/200?text=No+Image"),
                        "lat": place.get("mapx", ""),
                        "lng": place.get("mapy", ""),
                        "source": "kto"
                    })
            except requests.exceptions.RequestException as e:
                print(f"한국관광공사 API 요청 중 오류 발생: {e}")

        if search_lat is None or search_lng is None:
            map_center = {"lat": 36.5, "lng": 127.5}
        else:
            map_center = {"lat": search_lat, "lng": search_lng}
        context = {
            "destination": destination,
            "recommended_places": recommended_places,
            "recommended_json": json.dumps(recommended_places),
            "google_map_api_key": GOOGLE_MAPS_API_KEY,
            "map_center": map_center,
        }
        return render(request, 'planner/plan_schedule.html', context)


@csrf_exempt
def save_schedule_view(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
        except Exception as e:
            return JsonResponse({"status": "error", "message": "잘못된 데이터 형식입니다."}, status=400)

        travel_title = data.get("travel_title")
        start_date = data.get("start_date")
        end_date = data.get("end_date")
        destination = data.get("destination")
        itineraries = data.get("itineraries", {})  # 예: {"1": [ {...}, {...} ], "2": [ ... ], ...}

        if not all([travel_title, start_date, end_date, destination]):
            return JsonResponse({"status": "error", "message": "필수 필드가 누락되었습니다."}, status=400)

        user_email = request.session.get("user_email")
        if not user_email:
            return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)
        try:
            user = Signup.objects.get(email=user_email)
        except Signup.DoesNotExist:
            return JsonResponse({"status": "error", "message": "회원 정보를 찾을 수 없습니다."}, status=400)

        # Planner 객체 생성 (Planner 테이블은 여행 일정의 기본 정보만 저장)
        planner = Planner.objects.create(
            region=destination,
            plan_img="",
            sdate=start_date,
            edate=end_date
        )

        # 각 DAY의 itinerary 항목에 대해 PlannerDetail 레코드를 생성합니다.
        # PlannerDetail 테이블의 기본키인 plan_name은 고유해야 하므로,
        # 전체 여행 제목, DAY 번호, 그리고 해당 DAY 내의 항목 인덱스를 조합하여 생성합니다.
        for day, items in itineraries.items():
            for index, item in enumerate(items, start=1):
                # item의 "name"은 관광지명으로 가정합니다.
                tour_title = item.get("name")
                if not tour_title:
                    continue  # 이름이 없으면 건너뜁니다.
                try:
                    tour = Tourlist.objects.get(title=tour_title)
                except Tourlist.DoesNotExist:
                    tour = Tourlist.objects.create(
                        title=tour_title,
                        addr1=item.get("address", ""),
                        areacode=None,
                        sigungucode=None,
                        image2="",
                        readcount=0,
                        ping=0,
                    )
                # 고유한 기본키 생성 (예: "여행제목 - DAY 1 - 1")
                plan_detail_name = f"{travel_title} - DAY {day} - {index}"
                memo_value = item.get("memo", "")
                PlannerDetail.objects.create(
                    plan_name=plan_detail_name,  # 고유 기본키 값
                    planner=planner,
                    signup=user,
                    title=tour,  # Tourlist 객체와 연동 (Tourlist의 기본키는 title)
                    wdate=f"DAY {day} - {index}",  # 필요 시 현재 날짜 등으로 설정 가능
                    memo=memo_value
                )
        return JsonResponse({"status": "success", "message": "일정이 저장되었습니다."})
    else:
        return JsonResponse({"status": "error", "message": "POST 요청만 허용됩니다."}, status=405)


@csrf_exempt
def update_destination_view(request):
    """
    AJAX GET 요청으로 전달된 destination을 기반으로,
    Google Places API (Text Search, Nearby Search)와 한국관광공사 API를 사용해
    추천 장소 데이터를 수집하고, 해당 지역의 지도 중심 좌표와 함께 JSON으로 반환합니다.
    """
    # GET 요청 처리: 기존 코드 그대로 추천 장소 수집 등
    destination = request.GET.get("destination", "")
    recommended_places = []
    search_lat, search_lng = None, None

    if destination:
        # 1. Google Places API - Text Search
        google_url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={destination}&language=ko&key={GOOGLE_MAPS_API_KEY}"
        google_response = requests.get(google_url)
        google_places = google_response.json()
        if "results" in google_places and google_places["results"]:
            first_place = google_places["results"][0]
            search_lat = first_place["geometry"]["location"]["lat"]
            search_lng = first_place["geometry"]["location"]["lng"]
            for place in google_places["results"]:
                recommended_places.append({
                    "name": place["name"],
                    "address": place.get("formatted_address", ""),
                    "description": place.get("types", []),
                    "lat": place["geometry"]["location"]["lat"],
                    "lng": place["geometry"]["location"]["lng"],
                })
        # 2. Google Places API - Nearby Search
        if search_lat and search_lng:
            nearby_url = f"https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={search_lat},{search_lng}&radius=2000&language=ko&key={GOOGLE_MAPS_API_KEY}"
            nearby_response = requests.get(nearby_url)
            nearby_places = nearby_response.json()
            for place in nearby_places.get("results", []):
                recommended_places.append({
                    "name": place["name"],
                    "address": place.get("vicinity", ""),
                    "description": place.get("types", []),
                    "lat": place["geometry"]["location"]["lat"],
                    "lng": place["geometry"]["location"]["lng"],
                })
        # 3. 한국관광공사 API
        api_url = "http://apis.data.go.kr/B551011/KorService1/searchKeyword1"
        params = {
            "serviceKey": KTO_API_KEY,
            "keyword": destination,
            "numOfRows": 100,
            "pageNo": 1,
            "MobileOS": "ETC",
            "MobileApp": "AppTest",
            "_type": "json"
        }
        try:
            ktour_response = requests.get(api_url, params=params)
            ktour_response.raise_for_status()  # HTTP 오류 시 예외 발생
            ktour_places = ktour_response.json()
            # 디버깅: 서버 콘솔에 API 응답 출력
            print("KTO API 응답:", json.dumps(ktour_places, indent=2, ensure_ascii=False))
            items = ktour_places.get("response", {}).get("body", {}).get("items", {}).get("item", [])

            # items가 딕셔너리인 경우 리스트로 변환
            if isinstance(items, dict):
                items = [items]

            for place in items:
                recommended_places.append({
                    "name": place.get("title", ""),
                    "address": place.get("addr1", ""),
                    "description": place.get("contenttypeid", "설명 없음"),
                    "firstimage2": place.get("firstimage2", "https://via.placeholder.com/200?text=No+Image"),
                    "lat": place.get("mapx", ""),
                    "lng": place.get("mapy", ""),
                    "source": "kto"
                })
        except requests.exceptions.RequestException as e:
            print(f"한국관광공사 API 요청 중 오류 발생: {e}")

    if search_lat is None or search_lng is None:
        map_center = {"lat": 36.5, "lng": 127.5}
    else:
        map_center = {"lat": search_lat, "lng": search_lng}
    context = {
        "destination": destination,
        "recommended_places": recommended_places,
        "recommended_json": json.dumps(recommended_places),
        "google_map_api_key": GOOGLE_MAPS_API_KEY,
        "map_center": map_center,
    }
    return JsonResponse({
        "destination": destination,
        "map_center": map_center,
        "recommended_places": recommended_places
    })

def board_list(request):
    """
    게시판 목록 페이지:
    - 모든 게시글을 최신순으로 보여주고, 페이지네이션 처리합니다.
    - 검색어가 있으면 제목 또는 내용을 기준으로 필터링합니다.
    """
    query = request.GET.get("q", "")
    boards = Board.objects.all().order_by("-created_at")
    if query:
        boards = boards.filter(title__icontains=query) | boards.filter(content__icontains=query)
    paginator = Paginator(boards, 3)  # 페이지당 3개 게시글
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "planner/board_list.html", {"page_obj": page_obj, "query": query})


def board_detail(request, board_id):
    """
    게시글 상세보기 페이지
    """
    board = Board.objects.get(id=board_id)
    return render(request, "planner/board_detail.html", {"board": board})


@csrf_exempt
def board_create(request):
    """
    게시글 작성 기능 (로그인 필요)
    AJAX POST 요청을 받아 새 게시글을 생성합니다.
    """
    user_email = request.session.get("user_email")
    if not user_email:
        return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)
    try:
        author = Signup.objects.get(email=user_email)
    except Signup.DoesNotExist:
        return JsonResponse({"status": "error", "message": "회원 정보를 찾을 수 없습니다."}, status=400)

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if not title or not content:
            return JsonResponse({"status": "error", "message": "제목과 내용을 모두 입력해 주세요."}, status=400)
        board = Board.objects.create(
            title=title,
            content=content,
            author=author,
        )
        return JsonResponse({"status": "success", "message": "게시글이 작성되었습니다.", "board_id": board.id})
    else:
        # GET 요청: 게시글 작성 폼 렌더링
        return render(request, "planner/board_create.html")


@csrf_exempt
def board_update(request, board_id):
    """
    게시글 수정 기능
    """
    user_email = request.session.get("user_email")
    if not user_email:
        return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)

    board = Board.objects.get(id=board_id)
    if board.author.email != user_email:
        return JsonResponse({"status": "error", "message": "수정 권한이 없습니다."}, status=403)

    if request.method == "POST":
        title = request.POST.get("title")
        content = request.POST.get("content")
        if not title or not content:
            return JsonResponse({"status": "error", "message": "제목과 내용을 모두 입력해 주세요."}, status=400)
        board.title = title
        board.content = content
        board.save()
        return JsonResponse({"status": "success", "message": "게시글이 수정되었습니다."})
    else:
        return render(request, "planner/board_update.html", {"board": board})


@csrf_exempt
def board_delete(request, board_id):
    """
    게시글 삭제 기능
    """
    user_email = request.session.get("user_email")
    if not user_email:
        return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)

    board = Board.objects.get(id=board_id)
    if board.author.email != user_email:
        return JsonResponse({"status": "error", "message": "삭제 권한이 없습니다."}, status=403)

    if request.method == "POST":
        board.delete()
        return JsonResponse({"status": "success", "message": "게시글이 삭제되었습니다."})
    else:
        return render(request, "planner/board_delete.html", {"board": board})


@csrf_exempt
def comment_create(request, board_id):
    """
    댓글 작성 뷰:
    - 로그인한 사용자가 게시글(board_id)에 댓글을 작성합니다.
    - AJAX POST 요청으로 댓글 내용을 받아 저장합니다.
    """
    user_email = request.session.get("user_email")
    if not user_email:
        return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)

    try:
        author = Signup.objects.get(email=user_email)
    except Signup.DoesNotExist:
        return JsonResponse({"status": "error", "message": "회원 정보를 찾을 수 없습니다."}, status=400)

    try:
        board = Board.objects.get(id=board_id)
    except Board.DoesNotExist:
        return JsonResponse({"status": "error", "message": "게시글을 찾을 수 없습니다."}, status=404)

    if request.method == "POST":
        content = request.POST.get("content")
        if not content:
            return JsonResponse({"status": "error", "message": "댓글 내용을 입력해 주세요."}, status=400)

        comment = Comment.objects.create(
            board=board,
            author=author,
            content=content
        )

        return JsonResponse({
            "status": "success",
            "message": "댓글이 작성되었습니다.",
            "comment": {
                "id": comment.id,
                "author": comment.author.name,
                "content": comment.content,
                "created_at": comment.created_at.strftime("%Y-%m-%d %H:%M")
            }
        })
    else:
        return JsonResponse({"status": "error", "message": "POST 요청만 허용됩니다."}, status=405)

@csrf_exempt
def comment_update(request, comment_id):
    """
    댓글 수정 기능
    - 로그인된 사용자가 자신의 댓글을 수정할 수 있음.
    """
    if request.method == "POST":
        comment = get_object_or_404(Comment, id=comment_id)

        # 로그인된 사용자 확인 (예제에서는 세션 사용)
        user_email = request.session.get("user_email")
        if not user_email:
            return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)

        # 댓글 작성자가 본인인지 확인
        if comment.author.email != user_email:
            return JsonResponse({"status": "error", "message": "수정 권한이 없습니다."}, status=403)

        new_content = request.POST.get("content")
        if not new_content:
            return JsonResponse({"status": "error", "message": "댓글 내용을 입력하세요."}, status=400)

        # 댓글 내용 업데이트
        comment.content = new_content
        comment.save()

        return JsonResponse({"status": "success", "message": "댓글이 수정되었습니다.", "updated_content": new_content})

    return JsonResponse({"status": "error", "message": "잘못된 요청 방식입니다."}, status=400)


@csrf_exempt
def comment_delete(request, comment_id):
    """
    댓글 삭제 뷰:
    - 로그인한 사용자가 자신의 댓글(comment_id)을 삭제합니다.
    """
    user_email = request.session.get("user_email")
    if not user_email:
        return JsonResponse({"status": "error", "message": "로그인이 필요합니다."}, status=401)

    try:
        comment = Comment.objects.get(id=comment_id)
    except Comment.DoesNotExist:
        return JsonResponse({"status": "error", "message": "댓글을 찾을 수 없습니다."}, status=404)

    # 댓글 작성자 본인인지 확인
    if comment.author.email != user_email:
        return JsonResponse({"status": "error", "message": "삭제 권한이 없습니다."}, status=403)

    if request.method == "POST":
        comment.delete()
        return JsonResponse({"status": "success", "message": "댓글이 삭제되었습니다."})
    else:
        return JsonResponse({"status": "error", "message": "POST 요청만 허용됩니다."}, status=405)
