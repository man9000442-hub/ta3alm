from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import User

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    print("--- LOGIN ATTEMPT ---")
    email = request.data.get('email')
    password = request.data.get('password')
    
    print(f"Email received: {email}")
    print(f"Password received: {password}")

    if not email or not password:
        return Response({'error': 'Missing data'}, status=400)

    # 1. البحث المباشر
    user = authenticate(username=email, password=password)
    
    # 2. البحث اليدوي (لو المصادقة فشلت)
    if not user:
        print("Standard authenticate failed, trying manual lookup...")
        try:
            user_obj = User.objects.get(email=email)
            print(f"User found: {user_obj.username}")
            
            if user_obj.check_password(password):
                user = user_obj
                print("Password match!")
            else:
                print("Password MISMATCH!")
        except User.DoesNotExist:
            print("User NOT found with this email.")

    if not user:
        return Response({'error': 'Invalid Credentials'}, status=404)

    print("Login SUCCESS!")
    token, _ = Token.objects.get_or_create(user=user)

    return Response({
        'token': token.key,
        'user_id': user.id,
        'first_name': user.first_name,
        'role': user.role,
        'image': "" 
    })