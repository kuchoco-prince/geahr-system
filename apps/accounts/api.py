from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# Re-export for router-less urls
token_obtain_pair = TokenObtainPairView.as_view()
token_refresh = TokenRefreshView.as_view()
