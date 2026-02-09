from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from rest_framework import mixins, status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .permissions import IsAdminRole
from .serializers import UserSerializer
from .throttles import LoginRateThrottle

User = get_user_model()


class UserViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all().order_by('username')
    serializer_class = UserSerializer

    def get_permissions(self):
        if self.action == 'login':
            return []
        if self.action in {'list', 'create', 'update', 'partial_update'}:
            return [IsAuthenticated(), IsAdminRole()]
        return [IsAuthenticated()]

    def get_throttles(self):
        if self.action == 'login':
            return [LoginRateThrottle()]
        return super().get_throttles()

    @action(detail=False, methods=['post'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(request, username=username, password=password)
        if not user:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        login(request, user)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': token.key, 'role': user.role, 'username': user.username})

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        Token.objects.filter(user=request.user).delete()
        logout(request)
        return Response({'detail': 'Logged out'})
