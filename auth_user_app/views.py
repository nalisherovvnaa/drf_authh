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


class Main(METHODISM):
    file = methods
    token_key = 'Token'
    not_auth_methods = ['register', 'login', 'first_step_auth', 'second_step_auth']
    



def validate_phone_number(phone_):
    """Telefon raqam validatsiyadan o'tsa True qaytaradi"""
    phone = str(phone_)
    return len(phone) == 12 and isinstance(phone_, int) and phone[:3] == '998'

def validate_password(password):
    """Parol validatsiyadan o'tsa True qaytaradi"""
    return 6 <= len(password) <= 128 and any(map(lambda x:x.isupper(), password)) and any(map(lambda x:x.islower(), password)) and ' ' not in password

# Create your views here.

class RegisterView(APIView):
    def post(self, request):
        data = request.data

        # Telefon raqam va password kiritlganligini tekshiruvchi shartli qism
        if 'key' not in data or 'password' not in data:
            return Response(
                {'Message': 'Key yoki parol kiritilmagan.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        otp = OTP.objects.filter(key=data['key']).first()

        if not otp or not otp.is_used:
            return Response(
                {'Message': 'Siz o\'zinginzni kod bilan tasdiqlamagansiz.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        phone = CustomUser.objects.filter(phone=otp.phone)

        # Avval bu telefon raqam orqali ro'yxatdan o'tilmaganligini tekshiruvchi shartli qism
        if phone:
            return Response(
                {'Message': 'Bu telefon raqam bilan avval ro\'yxatdan o\'tilgan'},
                status=status.HTTP_400_BAD_REQUEST
                )
        
        # Parolni validatsiyadan o'tkazadi
        if not validate_password(data['password']):
            return Response(
                {"Message": 'Parol talabga javob bermaydi, boshqa parol kiriting.'},
                status=status.HTTP_400_BAD_REQUEST
                )

        # Yuqoridagi shartlarni qanoatlantirgach foydalanuvchi ma'lumotlarini user_data nomli o'zgaruvchiga tenglashtirib oladi
        user_data = {
            'phone': otp.phone,
            'password': data['password'],
            'name': data.get('name', '')
            }

        # Agar `key'   `123` qiymatiga teng bo'lsa user_data ni yangilaydi
        if data.get('secret_key', '') == '123':
            user_data.update({
                'is_staff': True,
                'is_superuser': True
            })
        
        # `key` yuborilmagan holatda yoki noto'g'ri `key` yuborilgan holatda oddiy foydalanuvchi yaratiladi
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

    # Foydalanuvchining [phone, name, is_active, is_staff, is_superuser] ma'lumotlarini qaytaradi
    def get(self, request):
        user = request.user
        return Response(
            {'Data': user.format()},
            status=status.HTTP_200_OK
            )
 
    def patch(self, request):
        """
        Foydalanuvchining telefon nomeri va ismini o'zgartiradi, 
        agar yuborilayotgan ma'lumotlar ichida `secret_key` mavjud va u to'g'ri bo'lsa superuser ga o'zgartiriladi.
        """
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
       
        # data['phone'] = str(data['phone'])
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
        
        # Telefon raqamni validatsiya qilish qismi
        if not validate_phone_number(data['phone']):
            return Response(
                {"Message": 'Telefon raqamni tekshirib qaytadan kiriting.'},
                status=status.HTTP_400_BAD_REQUEST  
                )
        
        """
        random.randint dan foydalanib tuzilgan 4 xonali mijozga jo'natiladigan kod
        """
        # code_ = ''.join([str(randint(100000, 999999))[-1] for _ in range(4)])


        """
        Mijozga sms orqali yuborish uchun barcha raqamlar,
        kichik va katta harflarni qatnashtirib 6 xonali kodni random tarzda tanlab oladi.
        """
        chars = string.digits + string.ascii_letters
        code = ''.join([chars[randint(0, len(chars)-1)] for _ in range(6)])
        key = str(uuid.uuid4()) + code

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