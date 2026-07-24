from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from .serializers import RegistrationSerializer,LoginSerializer,UserProfileSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User
from drf_spectacular.utils import extend_schema


class RegisterView(APIView):
    permission_classes = [AllowAny]
    
    @extend_schema(
            summary="Register",
            description="Register Student and Teacher",
            request=RegistrationSerializer,
            responses={201: RegistrationSerializer},
        )

    def post(self, request, *args, **kwargs):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({
            "message": "User registered successfully.",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
            }
        }, status=status.HTTP_201_CREATED)
        
        
class LoginView(APIView):
    @extend_schema(
            summary="Login",
            description="Login Student and Teacher",
            request=LoginSerializer,
            responses={201: LoginSerializer},
        )
        
    def post(self,request):
        email=request.data.get('email')
        password= request.data.get('password')
        
        try:
            user= User.objects.get(email= email)
        except User.DoesNotExist:
            return Response({"error":"User not found"}, status = status.HTTP_404_NOT_FOUND)
        if user.check_password(password):
                refresh= RefreshToken.for_user(user)
                return Response({
                    'message': 'Login Successful',
                    "email": user.email,
                    "full_name": user.full_name,
                    "role": user.role,
                    'user_id':user.id,
                    'refresh':str(refresh),
                    'access':str(refresh.access_token),
                },status= status.HTTP_200_OK)
        else:
                return Response({'message':'Credentials Invalid'}, status= status.HTTP_401_UNAUTHORIZED)
        
@extend_schema(
    summary="Get or Update My Profile",
    description="Retrieve the logged-in user's profile details, or update editable fields like phone number and profile image.",
    responses={200: UserProfileSerializer},
)
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """View Profile"""
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        """Update Profile (Partial Update)"""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response(serializer.data, status=status.HTTP_200_OK)            
        