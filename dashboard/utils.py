from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class JWTRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        jwt_authenticator = JWTAuthentication()
        try:
            user_auth_tuple = jwt_authenticator.authenticate(request)
            if user_auth_tuple is not None:
                request.user = user_auth_tuple[0]
                return super().dispatch(request, *args, **kwargs)
            raise AuthenticationFailed("JWT Authentication failed.")
        except Exception:
            raise AuthenticationFailed("JWT required.")
