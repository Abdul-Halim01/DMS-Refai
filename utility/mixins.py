from django.shortcuts import redirect

    
class HRCriteriaAddMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='HR',criteria_type='add').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class HRCriteriaEditMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='HR',criteria_type='edit').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class HRCriteriaDeleteMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='HR',criteria_type='delete').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)




    
class FormCriteriaAddMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Form',criteria_type='add').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class FormCriteriaEditMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Form',criteria_type='edit').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class FormCriteriaDeleteMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Form',criteria_type='delete').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)




    
class TasksCriteriaAddMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Tasks',criteria_type='add').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class TasksCriteriaEditMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Tasks',criteria_type='edit').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class TasksCriteriaDeleteMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Tasks',criteria_type='delete').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    



class DataCriteriaAddMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Data',criteria_type='add').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class DataCriteriaEditMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Data',criteria_type='edit').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class DataCriteriaDeleteMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Data',criteria_type='delete').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    



class UsersCriteriaAddMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Users',criteria_type='add').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class UsersCriteriaEditMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Users',criteria_type='edit').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class UsersCriteriaDeleteMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Users',criteria_type='delete').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

    



class DocumentsCriteriaAddMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Documents',criteria_type='add').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class DocumentsCriteriaEditMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Documents',criteria_type='edit').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

class DocumentsCriteriaDeleteMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.role.criteria.filter(name='Documents',criteria_type='delete').exists():
            return redirect('login')
        return super().dispatch(request, *args, **kwargs)

