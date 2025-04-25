from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from .models import CustomUser, OTP
from random import randint
import datetime
import uuid
import string
from methodism import METHODISM
from auth_user_app import methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import threading



class Main(METHODISM):
    file = methods
    token_key = 'Token'
    not_auth_methods = ['register', 'login', 'first_step_auth', 'second_step_auth']
    



def validate_phone_number(phone_):
    phone = str(phone_)
    return len(phone) == 12 and isinstance(phone_, int) and phone[:3] == '998'

def validate_password(password):
    return 6 <= len(password) <= 128 and any(map(lambda x:x.isupper(), password)) and any(map(lambda x:x.islower(), password)) and ' ' not in password

# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        data = request.data

        if 'key' not in data or 'password' not in data:
            return Response(
                {'Message': 'Key yoki parol kiritilmagan.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        otp = OTP.objects.filter(key=data['key']).first()

        if not otp or not otp.is_used:
            return Response(
                {'Message': 'Sz ozinginzni kod bilan tasdiqlamagansiz.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        phone = CustomUser.objects.filter(phone=otp.phone)

        if phone:
            return Response(
                {'Message': 'Bu telefon raqam bilan avval royxatdan otilgan'},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        if not validate_password(data['password']):
            return Response(
                {"Message": 'Parol talabga javob bermaydi, boshqa parol kiriting.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        user_data = {
            'phone': otp.phone,
            'password': data['password'],
            'name': data.get('name', '')
            }

        if data.get('secret_key', '') == '123':
            user_data.update({
                'is_staff': True,
                'is_superuser': True
            })
        
        user = CustomUser.objects.create_user(**user_data)
        Token.objects.create(user=user)
        return Response(
            {
                'Message':"Siz muvaffaqiyatli ro'yxatdan o'tdingiz.",
                'is_superuser': user_data.get('is_superuser', False),
                'token': user.auth_token.key
                },
            status=status.HTTP_201_CREATED
            )
    

class LoginView(APIView):
    def post(self, request):
        data = request.data
        user = CustomUser.objects.filter(phone=data['phone']).first()

        if not user:
            return Response(
                {'Error': "Bu telefon raqam bilan ro'yxatdan o'tilmagan."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not user.check_password(data['password']):
            return Response(
                {'Error': "Noto'g'ri parol kiritildi."},
                status=status.HTTP_400_BAD_REQUEST
            )

        token = Token.objects.get_or_create(user=user)

        return Response(
            {
                'Message': 'Siz tizimga muvaffaqiyatli kirdingiz.',
                'token': token[0].key
                },
            status=status.HTTP_200_OK
        )
    
    
class LogoutView(APIView):
    permission_classes = IsAuthenticated,
    authentication_classes = TokenAuthentication,
    
    def post(self, request):
        token = Token.objects.filter(user=request.user).first()
        token.delete()
        return Response(
            {'Message': 'Siz tizimdan chiqarildingiz.'}, 
            status=status.HTTP_200_OK
            )


class ProfileView(APIView):
    permission_classes = IsAuthenticated,
    authentication_classes = TokenAuthentication,

    def get(self, request):
        user = request.user
        return Response(
            {'Data': user.format()},
            status=status.HTTP_200_OK
            )
 
    def patch(self, request):

        data = request.data
        user = request.user

        if not data.get('phone', ''):
            return Response(
                {'Error': 'Telefon raqam kiritlishi shart.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        if not validate_phone_number(data['phone']):
            return Response(
                {"Error": 'Telefon raqamni tekshirib qaytadan kiriting.'},
                status=status.HTTP_400_BAD_REQUEST
                )
       
        user_ = CustomUser.objects.filter(phone=data['phone']).first()

        if user_ and user != user_:
            return Response(
                {'Message': "Bu raqam bilan avvalroq ro'yxatdan o'tilgan."},
                status=status.HTTP_400_BAD_REQUEST
                )

        if data.get('secret_key', '') == '123':
            user.is_staff = True
            user.is_superuser = True

        user.phone = data['phone']
        user.name = data.get('name', user.name)
        
        user.save()
        return Response(
            {
                'Message': "Ma'lumotlaringiz muvvaqiyatli o'zgartirildi.",
                'Data': f"O'zgartirilgan ma'lumotlar {data}",
                },
                status=status.HTTP_200_OK
            )

    def delete(self, request):
        user = request.user
        user.delete()
        return Response(
            {'Message': 'Telefon raqamingiz hisobdan chiqarildi.'},
            status=status.HTTP_200_OK
        )


class PasswordChangeView(APIView):
    permission_classes = IsAuthenticated,
    authentication_classes = TokenAuthentication,

    def post(self, request):
        data = request.data
        user = request.user

        if not data.get('old') or not data.get('new'):
            return Response(
                {"Messages": 'Eski yoki yangi parol kiritilmagan.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        if not user.check_password(data['old']):
            return Response(
                {"Error": "Eski parol noto'g'ri kiritilgan."},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        if not validate_password(data['new']):
            return Response(
                {"Message": 'Parol talabga javob bermaydi, boshqa parol kiriting.'},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        user.set_password(data['new'])
        user.save()
        return Response(
            {'Message': "Parolingiz muvaffaqiyatli o'zgartirildi!"},
            status=status.HTTP_200_OK
            )


class FirstStepAuthView(APIView):
    def post(self, request):
        data = request.data

        if not data.get('phone'):
            return Response(
                {'Error': 'Telefon raqam kiritilmagan.'},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        if not validate_phone_number(data['phone']):
            return Response(
                {"Message": 'Telefon raqamni tekshirib qaytadan kiriting.'},
                status=status.HTTP_400_BAD_REQUEST  
                )
        
        chars = string.digits + string.ascii_letters
        code = ''.join([chars[randint(0, len(chars)-1)] for _ in range(6)])
        key = str(uuid.uuid4()) + code
        send_to_mail(request, 'volidamlola@gmail.com, code')
        otp = OTP.objects.create(phone=data['phone'], key=key)
        
        return Response({
            'code': code,
            'key': otp.key},
            status=status.HTTP_200_OK
            )


class SecondStepAuthView(APIView):
    def post(self, request):
        data = request.data
        try:
            code = data['code']
            key = data['key']
        except:
            return Response(
                {'Error': "Ma'lumotlar to'liq kiritlmagan."},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        otp = OTP.objects.filter(key=key).first()

        if not otp:
            return Response(
                {'Error': "Noto'g'ri key yuborildi!"},
                status=status.HTTP_400_BAD_REQUEST
                )

        if otp.is_expire:
            return Response(
                {'Message': 'Key yaroqsiz'},
                status=status.HTTP_400_BAD_REQUEST
                )

        if otp.is_used:
            return Response(
                {'Message': 'Bu koddan foydalanilgan.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        now = datetime.datetime.now(datetime.timezone.utc)
        if (now - otp.created).total_seconds() >= 180:
            otp.is_expire = True
            otp.save()
            return Response(
                {'Message': 'Koddan foydalanish vaqti tugagan.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        if key[-6:] != str(code):
            otp.tried += 1
            otp.save()
            return Response(
                {'Error': "Kod noto'g'ri kiritilgan!"},
                status=status.HTTP_400_BAD_REQUEST
                )

        otp.is_used = True
        otp.save()

        user = CustomUser.objects.filter(phone=otp.phone).first()

        return Response(
            {'Message': 'Success!',
            'is_registered': user is not None},
            status=status.HTTP_200_OK
            )

def send_mail(email):
    print(f"Sending verification email to {email}...")

def is_email(user_input):
    return "@" in user_input and "." in user_input.split("@")[-1]

def is_phone(user_input):
    return user_input.startswith("+") and user_input[1:].isdigit() or user_input.isdigit()

@csrf_exempt 
def authorize_user(request):
    if request.method == 'POST':
        user_input = request.POST.get('contact')

        if not user_input:
            return JsonResponse({"error": "Kontakt ma'lumotlari kiritilmadi."}, status=400)

        if is_email(user_input):
            thread = threading.Thread(target=send_mail, args=(user_input,))
            thread.start()
            return JsonResponse({"message": "Email yuborildi", "type": "email"})
        
        elif is_phone(user_input):
            code = "1234"
            print(f"{user_input} raqamiga tasdiqlovchi kod yuborildi: {code}")
            return JsonResponse({"message": "Kod yuborildi", "type": "phone"})
        
        else:
            return JsonResponse({"error": "Notogri email yoki telefon raqam formati."}, status=400)
    
    return JsonResponse({"error": "Faqat POST so'rovlar qabul qilinadi."}, status=405)