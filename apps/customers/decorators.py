from functools import wraps
from django.http import Http404
from apps.customers.views import _get_allowed_third_party

def tenant_isolated(view_func):
    """
    Decorator for views that take 'third_party_id'. Checks that the logged-in 
    user is authorized to access the specified third-party ID.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        third_party_id = kwargs.get("third_party_id")
        if not third_party_id:
            raise Http404("Missing tenant context")
            
        # Securely fetch and validate third party
        customer = _get_allowed_third_party(request.user, third_party_id)
        
        # Inject the validated customer object into kwargs
        kwargs["customer_obj"] = customer
        return view_func(request, *args, **kwargs)
    return _wrapped_view
