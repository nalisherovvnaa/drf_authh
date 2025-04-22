from auth_user_app.models import CustomUser, OTP
from methodism import custom_response, error_messages, MESSAGE
from rest_framework.authtoken.models import Token
from random import randint
import string, uuid, datetime


# Validatsiya uchun yozilgan funksiyalar
def validate_phone_number(phone_):
    """Telefon raqam validatsiyadan o'tsa True qaytaradi"""
    phone = str(phone_)
    return len(phone) == 12 and isinstance(phone_, int) and phone[:3] == '998'

def validate_password(password):
    """Parol validatsiyadan o'tsa True qaytaradi"""
    return 6 <= len(password) <= 128 and any(map(lambda x:x.isupper(), password)) and any(map(lambda x:x.islower(), password)) and ' ' not in password


# Authentication uchun yozilgan barcha funksiyalar

def first_step_auth(request, params):
    if not params.get('phone'):
        return custom_response(False, message=error_messages.error_params_unfilled('phone'))
    
    # Telefon raqamni validatsiya qilish qismi
    if not validate_phone_number(params['phone']):
        return custom_response(False, message={"message": 'Telefon raqamni tekshirib qaytadan kiriting.'})
        
    """
    Mijozga sms orqali yuborish uchun barcha raqamlar,
    kichik va katta harflarni qatnashtirib 6 xonali kodni random tarzda tanlab oladi.
    """
    chars = string.digits + string.ascii_letters
    code = ''.join([chars[randint(0, len(chars)-1)] for _ in range(6)])
    key = str(uuid.uuid4()) + code

    otp = OTP.objects.create(phone=params['phone'], key=key)
    return custom_response(True, data={'code': code, 'key': otp.key})


def second_step_auth(request, params):
    try:
        code = params['code']
        key = params['key']
    except:
        return custom_response(False, message=MESSAGE['DataNotFull'])
    
    otp = OTP.objects.filter(key=key).first()

    if not otp:
        return custom_response(False, message={'message': "Noto'g'ri key yuborildi!"})

    if otp.is_expire:
        return custom_response(False, message={'message': 'Key yaroqsiz'})
    
    if otp.is_used:
        return custom_response(False, message={'message': 'Bu koddan foydalanilgan.'})

    now = datetime.datetime.now(datetime.timezone.utc)
    if (now - otp.created).total_seconds() >= 180:
        otp.is_expire = True
        otp.save()
        return custom_response(False, message={'message': 'Koddan foydalanish vaqti tugagan.'})

    if key[-6:] != str(code):
        otp.tried += 1
        otp.save()
        return custom_response(False, message=MESSAGE['PasswordError'])
    
    otp.is_used = True
    otp.save()

    user = CustomUser.objects.filter(phone=otp.phone).first()
    return custom_response(True, data={'is_registered': user is not None}, message={'Message': 'Success!'})


def register(request, params):
    # Telefon raqam va password kiritlganligini tekshiruvchi shartli qism
        if 'key' not in params:
            return custom_response(False, message=error_messages.error_params_unfilled('key'))
        
        if 'password' not in params:
            return custom_response(False, message=MESSAGE['PasswordMust'])

        otp = OTP.objects.filter(key=params['key']).first() 
        if not otp:
            return custom_response(False, message=MESSAGE['NotAuthenticated'])
        
        if not otp.is_used:
            return custom_response(False, message=MESSAGE['PermissionDenied'])

        phone = CustomUser.objects.filter(phone=otp.phone)

        # Avval bu telefon raqam orqali ro'yxatdan o'tilmaganligini tekshiruvchi shartli qism
        if phone:
            return custom_response(False, message={'message': "Bu telefon raqam bilan avval ro'yxatdan o'tilgan"})
        
        # Parolni validatsiyadan o'tkazadi
        if not validate_password(params['password']):
            return custom_response(False, message={"message": 'Parol talabga javob bermaydi, boshqa parol kiriting.'})

        # Yuqoridagi shartlarni qanoatlantirgach foydalanuvchi ma'lumotlarini user_data nomli o'zgaruvchiga tenglashtirib oladi
        user_data = {
            'phone': otp.phone,
            'password': params['password'],
            'name': params.get('name', '')
            }

        # Agar `key'   `123` qiymatiga teng bo'lsa user_data ni yangilaydi
        if params.get('secret_key', '') == '123':
            user_data.update({
                'is_staff': True,
                'is_superuser': True
            })
        
        # `key` yuborilmagan holatda yoki noto'g'ri `key` yuborilgan holatda oddiy foydalanuvchi yaratiladi
        user = CustomUser.objects.create_user(**user_data)
        Token.objects.create(user=user)
        return custom_response(True, data={'is_superuser': user_data.get('is_superuser', False), 'token': user.auth_token.key}, message={'message':"Siz muvaffaqiyatli ro'yxatdan o'tdingiz."})


def login(request, params):
    if 'phone' not in params:
        return custom_response(False, message=error_messages.error_params_unfilled('phone'))
    
    if 'password' not in params:
        return custom_response(False, message=MESSAGE['PasswordMust'])

    user = CustomUser.objects.filter(phone=params['phone']).first()
    if not user:
        return custom_response(False, message=MESSAGE['Unauthenticated'])
    
    if not user.check_password(params['password']):
        return custom_response(False, message=MESSAGE["PasswordError"])

    token = Token.objects.get_or_create(user=user)

    return custom_response(True, data={'token':token[0].key}, message={"Success": "Siz tizimga kirdingiz!"})


def logout(request, params):
    token = Token.objects.filter(user=request.user).first()
    token.delete()
    return custom_response(True, message=MESSAGE['LogedOut'])


def get_profile(request, params):
    user = request.user
    print(user.phone)
    return custom_response(True, data=user.format())


def update_profile(request, params):
    user = request.user
    if not params.get('phone', ''):
        return custom_response(False, message=error_messages.error_params_unfilled('phone'))

    if not validate_phone_number(params['phone']):
        return custom_response(False, message={"message": 'Telefon raqamni tekshirib qaytadan kiriting.'})
    
    # data['phone'] = str(data['phone'])
    user_ = CustomUser.objects.filter(phone=params['phone']).first()

    if user_ and user != user_:
        return custom_response(False, message={'message': "Bu raqam bilan avvalroq ro'yxatdan o'tilgan."})

    if params.get('secret_key', '') == '123':
        user.is_staff = True
        user.is_superuser = True

    user.phone = params['phone']
    user.name = params.get('name', user.name)
    
    user.save()
    return custom_response(False, message={'message': "Ma'lumotlaringiz muvvaqiyatli o'zgartirildi."})


def delete_user(request, params):
    user = request.user
    user.delete()
    return custom_response(True, message=MESSAGE['UserSuccessDeleted'])


def change_password(request, params):
    user = request.user

    if not params.get('old') or not params.get('new'):
        return custom_response(False, message=MESSAGE['DataNotFull'])

    if not user.check_password(params['old']):
        return custom_response(False, message=MESSAGE['PasswordError'])
    
    if not validate_password(params['new']):
        return custom_response(False, message={"message": 'Parol talabga javob bermaydi, boshqa parol kiriting.'})           
    
    user.set_password(params['new'])
    user.save()
    return custom_response(True, message=MESSAGE['PasswordChanged'])
