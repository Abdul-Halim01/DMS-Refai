from django.shortcuts import redirect


class ModeratorRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not (request.user.role == 'moderator' or request.user.role == 'admin'):
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)


class AdminRequiredMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not request.user.role == 'admin':
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)