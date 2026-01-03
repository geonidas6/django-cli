import os
import sys
import subprocess
import textwrap

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_success(msg):
    print(f"{Colors.OKGREEN}✓ {msg}{Colors.ENDC}")

def print_info(msg):
    print(f"{Colors.OKCYAN}ℹ {msg}{Colors.ENDC}")

def print_warning(msg):
    print(f"{Colors.WARNING}⚠ {msg}{Colors.ENDC}")

def print_error(msg):
    print(f"{Colors.FAIL}✖ {msg}{Colors.ENDC}")

def run_command(command, capture_output=False):
    try:
        if capture_output:
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return True, result.stdout
        subprocess.check_call(command, shell=True)
        return True, ""
    except subprocess.CalledProcessError as e:
        # print_error(f"Command failed: {command}")
        return False, getattr(e, 'stderr', str(e))


def get_project_name():
    # Try to find settings in likely locations
    if 'DJANGO_SETTINGS_MODULE' in os.environ:
        return os.environ['DJANGO_SETTINGS_MODULE'].split('.')[0]
    
    # Check current directory for manage.py and settings
    if os.path.exists('manage.py'):
        # basic heuristic: look for a folder that has settings.py/wsgi.py
        for item in os.listdir('.'):
            if os.path.isdir(item) and os.path.exists(os.path.join(item, 'settings.py')):
                return item
    return 'gest_ecole' # Fallback default

def setup_accounts_app(app_name='accounts'):
    print(f"{Colors.BOLD}Setting up '{app_name}' app...{Colors.ENDC}")
    if not os.path.exists(app_name):
        run_command(f"{sys.executable} manage.py startapp {app_name}")
        print_success(f"App '{app_name}' created.")
    
    # Register in settings.py
    project_name = get_project_name()
    settings_path = os.path.join(project_name, 'settings.py')

    with open(settings_path, 'r') as f:
        content = f.read()
    
    modified = False
    if f"'{app_name}'" not in content and f'"{app_name}"' not in content:
        content = content.replace("INSTALLED_APPS = [", f"INSTALLED_APPS = [\n    '{app_name}',")
        modified = True
        print_success(f"Registered '{app_name}' in INSTALLED_APPS.")

    if "AUTH_USER_MODEL" not in content:
        content += f"\nAUTH_USER_MODEL = '{app_name}.CustomUser'\n"
        modified = True
        print_success(f"Configured AUTH_USER_MODEL to '{app_name}.CustomUser'.")

    # Auth Redirects & Email Settings
    auth_settings = [
        f"LOGIN_REDIRECT_URL = '{app_name}:dashboard'",
        f"LOGOUT_REDIRECT_URL = '{app_name}:login'",
        f"LOGIN_URL = '{app_name}:login'",
        f"EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'",
        f"DEFAULT_FROM_EMAIL = 'noreply@gestecole.com'"
    ]
    for setting in auth_settings:
        if setting.split(' = ')[0] not in content:
            content += f"{setting}\n"
            modified = True
            print_success(f"Added {setting.split(' = ')[0]} to settings.py")

    # Commented SMTP block
    smtp_block = textwrap.dedent("""
        # SMTP Settings (Uncomment and configure for Production)
        # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
        # EMAIL_HOST = 'smtp.gmail.com'
        # EMAIL_PORT = 587
        # EMAIL_USE_TLS = True
        # EMAIL_HOST_USER = 'votre-email@gmail.com'
        # EMAIL_HOST_PASSWORD = 'votre-mot-de-passe-d-application'
        # DEFAULT_FROM_EMAIL = 'GestEcole <votre-email@gmail.com>'
    """)
    if "# SMTP Settings" not in content:
        content += smtp_block
        modified = True
        print_success("Added commented SMTP settings placeholder to settings.py")
    
    if modified:
        with open(settings_path, 'w') as f:
            f.write(content)
            
    return True

def generate_models(app_name):
    path = os.path.join(app_name, 'models.py')
    content = textwrap.dedent("""\
        from django.contrib.auth.models import AbstractUser
        from django.db import models

        class CustomUser(AbstractUser):
            photo_profil = models.ImageField(upload_to='profiles/', null=True, blank=True)
            otp_code = models.CharField(max_length=6, blank=True, null=True)
            otp_created_at = models.DateTimeField(blank=True, null=True)
            
            def __str__(self):
                return self.username
    """)
    with open(path, 'w') as f:
        f.write(content)
    print_success("Generated CustomUser model in models.py")

def generate_signals(app_name, default_group, use_welcome_email=True):
    path = os.path.join(app_name, 'signals.py')
    
    email_logic = ""
    if use_welcome_email:
        email_logic = textwrap.dedent(f"""
            # Logic for Welcome Email
            from django.core.mail import send_mail
            from django.conf import settings
            
            subject = 'Bienvenue sur GestEcole'
            message = f'Bonjour {{instance.username}}, merci de vous être inscrit !'
            try:
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [instance.email])
            except Exception as e:
                print(f"Error sending email: {{e}}")
        """)

    content = textwrap.dedent(f"""\
        from django.db.models.signals import post_save
        from django.dispatch import receiver
        from django.contrib.auth.models import Group
        from .models import CustomUser

        @receiver(post_save, sender=CustomUser)
        def assign_default_group(sender, instance, created, **kwargs):
            if created:
                group, _ = Group.objects.get_or_create(name='{default_group}')
                instance.groups.add(group)
        """)
    
    if email_logic:
        # Append logic inside the receiver properly indented
        content = content.strip() + "\n" + textwrap.indent(email_logic.strip(), "        ") + "\n"

    with open(path, 'w') as f:
        f.write(content.strip() + "\n")
    print_success(f"Generated signals.py (Default group: {default_group})")

    # Update apps.py
    apps_path = os.path.join(app_name, 'apps.py')
    with open(apps_path, 'r') as f:
        apps_content = f.read()
    
    if "def ready(self):" not in apps_content:
        # Better injection: find the class end
        if "    name = 'accounts'" in apps_content:
             apps_content = apps_content.replace(
                 "    name = 'accounts'",
                 "    name = 'accounts'\n\n    def ready(self):\n        import accounts.signals"
             )
        else:
            ready_method = textwrap.dedent("""\
                
                    def ready(self):
                        import accounts.signals
            """)
            apps_content = apps_content.strip() + ready_method
            
        with open(apps_path, 'w') as f:
            f.write(apps_content)
        print_success("Updated apps.py to load signals.")

def init_groups(create_users=False):
    print_info("Bootstrapping groups, permissions, and users...")
    project_name = get_project_name()
    init_script = textwrap.dedent(f"""
        import os
        import django

        os.environ.setdefault('DJANGO_SETTINGS_MODULE', '{project_name}.settings')

        django.setup()

        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType

        User = get_user_model()

        # 1. Groups & Permissions
        groups = {{
            'Admin_Site': {{'all': True}},
            'Manager': {{
                'permissions': [
                    'view_customuser', 'change_customuser', 'add_customuser',
                ],
            }},
            'Membre': {{
                'permissions': ['view_customuser'],
            }}
        }}

        for group_name, config in groups.items():
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                print(f"Created group: {{group_name}}")
            
            if config.get('all'):
                all_perms = Permission.objects.all()
                group.permissions.set(all_perms)
            else:
                for perm_code in config.get('permissions', []):
                    try:
                        perm = Permission.objects.get(codename=perm_code)
                        group.permissions.add(perm)
                    except Permission.DoesNotExist:
                        pass
        
        # 2. Users (if requested)
        if {create_users}:
            # Superuser
            if not User.objects.filter(username='superuser').exists():
                User.objects.create_superuser('superuser', 'superuser@mail.com', 'geonidas')
                print("Created Superuser: superuser / geonidas")
            
            # Admin User
            if not User.objects.filter(username='admin').exists():
                u = User.objects.create_user('admin', 'admin@mail.com', 'geonidas')
                g = Group.objects.get(name='Admin_Site')
                u.groups.add(g)
                print("Created Admin User: admin / geonidas (Role: Admin_Site)")
        
        print("Groups and Users initialization complete.")
    """)
    with open('init_auth.py', 'w') as f:
        f.write(init_script)
    run_command(f"{sys.executable} init_auth.py")
    os.remove('init_auth.py')

def generate_forms(app_name):
    path = os.path.join(app_name, 'forms.py')
    content = textwrap.dedent("""\
        from django import forms
        from django.contrib.auth.forms import UserCreationForm, UserChangeForm
        from .models import CustomUser

        class CustomUserCreationForm(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = CustomUser
                fields = UserCreationForm.Meta.fields + ('email', 'photo_profil',)

        class CustomUserChangeForm(UserChangeForm):
            class Meta:
                model = CustomUser
                fields = ('username', 'email', 'photo_profil',)

        class ProfileUpdateForm(forms.ModelForm):
            class Meta:
                model = CustomUser
                fields = ['username', 'email', 'photo_profil', 'first_name', 'last_name']

        class UserAdminForm(forms.ModelForm):
            class Meta:
                model = CustomUser
                fields = ['username', 'email', 'first_name', 'last_name', 'groups', 'is_active', 'is_staff']
                widgets = {
                    'groups': forms.CheckboxSelectMultiple(),
                }

        from django.contrib.auth.models import Group, Permission
        class GroupForm(forms.ModelForm):
            permissions = forms.ModelMultipleChoiceField(
                queryset=Permission.objects.all(),
                widget=forms.CheckboxSelectMultiple(),
                required=False
            )
            class Meta:
                model = Group
                fields = ['name', 'permissions']
    """)
    with open(path, 'w') as f:
        f.write(content)
    print_success("Generated forms.py")

def generate_views(app_name, use_landing=True, use_2fa=False):
    path = os.path.join(app_name, 'views.py')
    
    parts = []
    parts.append(textwrap.dedent("""\
        from django.shortcuts import render, redirect, get_object_or_404
        from django.contrib.auth.decorators import login_required, user_passes_test
        from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
        from django.views.generic import ListView, UpdateView, TemplateView, CreateView
        from django.urls import reverse_lazy
        from .models import CustomUser
        from .forms import CustomUserCreationForm, ProfileUpdateForm, UserAdminForm, GroupForm
        from django.contrib import messages
        from django.contrib.auth.models import Group, Permission
    """))

    if use_2fa:
        parts.append(textwrap.dedent("""\
            import random
            from django.utils import timezone
            from django.core.mail import send_mail
            from django.contrib.auth import login as auth_login
            from django.contrib.auth.views import LoginView
            from django.contrib import messages

            class CustomLoginView(LoginView):
                template_name = 'accounts/login.html'
                
                def form_valid(self, form):
                    user = form.get_user()
                    otp = str(random.randint(100000, 999999))
                    user.otp_code = otp
                    user.otp_created_at = timezone.now()
                    user.save()
                    
                    try:
                        send_mail(
                            'Code de sécurité GestEcole',
                            f'Votre code est : {otp}',
                            None,
                            [user.email],
                            fail_silently=False,
                        )
                        self.request.session['pre_otp_user_id'] = user.id
                        return redirect('accounts:verify_otp')
                    except Exception as e:
                        messages.error(self.request, f"Erreur Email : {e}")
                        return super().form_invalid(form)

            def verify_otp(request):
                user_id = request.session.get('pre_otp_user_id')
                if not user_id: return redirect('accounts:login')
                if request.method == 'POST':
                    otp = request.POST.get('otp')
                    user = CustomUser.objects.filter(id=user_id).first()
                    if user and user.otp_code == otp:
                        auth_login(request, user)
                        del request.session['pre_otp_user_id']
                        return redirect('accounts:dashboard')
                    messages.error(request, "Code invalide.")
                return render(request, 'accounts/verify_otp.html')
        """))

    parts.append(textwrap.dedent("""\
        class LandingView(TemplateView):
            template_name = 'accounts/landing.html'

        class DashboardView(LoginRequiredMixin, TemplateView):
            template_name = 'accounts/dashboard.html'

            def get_context_data(self, **kwargs):
                context = super().get_context_data(**kwargs)
                user = self.request.user
                context['is_admin'] = user.groups.filter(name='Admin_Site').exists() or user.is_superuser
                context['is_manager'] = user.groups.filter(name='Manager').exists()
                context['is_membre'] = user.groups.filter(name='Membre').exists()
                return context

        class UserManagementListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
            model = CustomUser
            template_name = 'accounts/user_list.html'
            context_object_name = 'users'

            def test_func(self):
                return self.request.user.groups.filter(name__in=['Admin_Site', 'Manager']).exists() or self.request.user.is_superuser

        class ProfileUpdateView(LoginRequiredMixin, UpdateView):
            model = CustomUser
            form_class = ProfileUpdateForm
            template_name = 'accounts/profile.html'
            success_url = reverse_lazy('accounts:dashboard')

            def get_object(self):
                return self.request.user

        # --- USER CRUD (ADMIN/MANAGER) ---
        class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
            model = CustomUser
            form_class = UserAdminForm
            template_name = 'accounts/user_form.html'
            success_url = reverse_lazy('accounts:user_list')

            def test_func(self):
                return self.request.user.groups.filter(name__in=['Admin_Site', 'Manager']).exists() or self.request.user.is_superuser

        class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
            template_name = 'accounts/user_confirm_delete.html'

            def test_func(self):
                return self.request.user.groups.filter(name='Admin_Site').exists() or self.request.user.is_superuser

            def post(self, request, pk):
                user = CustomUser.objects.get(pk=pk)
                if user == request.user:
                    messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
                else:
                    user.delete()
                    messages.success(request, "Utilisateur supprimé.")
                return redirect('accounts:user_list')

        # --- GROUP & PERMISSION MANAGEMENT (ADMIN ONLY) ---
        class GroupListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
            model = Group
            template_name = 'accounts/group_list.html'
            context_object_name = 'groups'

            def test_func(self):
                return self.request.user.groups.filter(name='Admin_Site').exists() or self.request.user.is_superuser

        class GroupCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
            model = Group
            form_class = GroupForm
            template_name = 'accounts/group_form.html'
            success_url = reverse_lazy('accounts:group_list')

            def test_func(self):
                return self.request.user.groups.filter(name='Admin_Site').exists() or self.request.user.is_superuser

        class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
            model = Group
            form_class = GroupForm
            template_name = 'accounts/group_form.html'
            success_url = reverse_lazy('accounts:group_list')

            def test_func(self):
                return self.request.user.groups.filter(name='Admin_Site').exists() or self.request.user.is_superuser

        def register(request):
            if request.method == 'POST':
                form = CustomUserCreationForm(request.POST, request.FILES)
                if form.is_valid():
                    form.save()
                    return redirect('accounts:login')
            else:
                form = CustomUserCreationForm()
            return render(request, 'accounts/register.html', {'form': form})
    """))

    with open(path, 'w') as f:
        f.write("\n".join(p.strip() for p in parts) + "\n")
    print_success("Generated views.py")

def generate_urls(app_name, use_landing=True, admin_url='admin', use_2fa=False):
    path = os.path.join(app_name, 'urls.py')
    
    root_path_logic = "path('', views.LandingView.as_view(), name='landing')," if use_landing else "path('', views.DashboardView.as_view(), name='index_dashboard'),"
    
    login_path = "path('login/', views.CustomLoginView.as_view(), name='login')," if use_2fa else "path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),"
    otp_path = f"path('verify-otp/', views.verify_otp, name='verify_otp')," if use_2fa else ""
    
    content = textwrap.dedent(f"""\
        from django.urls import path, reverse_lazy
        from django.contrib.auth import views as auth_views
        from . import views

        app_name = '{app_name}'

        urlpatterns = [
            {root_path_logic}
            path('dashboard/', views.DashboardView.as_view(), name='dashboard'),
            path('profile/', views.ProfileUpdateView.as_view(), name='profile'),
            path('register/', views.register, name='register'),
            {otp_path}

            # User Management
            path('users/', views.UserManagementListView.as_view(), name='user_list'),
            path('users/<int:pk>/edit/', views.UserUpdateView.as_view(), name='user_edit'),
            path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),

            # Group Management
            path('groups/', views.GroupListView.as_view(), name='group_list'),
            path('groups/add/', views.GroupCreateView.as_view(), name='group_add'),
            path('groups/<int:pk>/edit/', views.GroupUpdateView.as_view(), name='group_edit'),
            
            # Auth Overrides
            {login_path}
            path('logout/', auth_views.LogoutView.as_view(next_page='accounts:login'), name='logout'),
            path('password-change/', auth_views.PasswordChangeView.as_view(
                template_name='accounts/password_change.html',
                success_url=reverse_lazy('accounts:dashboard')
            ), name='password_change'),
        ]
    """)
    with open(path, 'w') as f:
        f.write(content)
        
    # Root project URLs
    project_name = get_project_name()
    root_urls_path = os.path.join(project_name, 'urls.py')
    with open(root_urls_path, 'r') as f:

        root_content = f.read()
    
    if "from django.urls import path, include" not in root_content:
        root_content = root_content.replace("from django.urls import path", "from django.urls import path, include")

    # Add app include if not present (only if it's NOT the root path already)
    if not use_landing:
        # If not root, we might want it at /accounts/
        if f"path('{app_name}/'" not in root_content and f"path('', include('{app_name}.urls'))" not in root_content:
            root_content = root_content.replace("urlpatterns = [", f"urlpatterns = [\n    path('{app_name}/', include('{app_name}.urls')),")

    # Root path logic for project URLs
    if f"path('', include('{app_name}.urls'))" not in root_content:
        root_content = root_content.replace("urlpatterns = [", f"urlpatterns = [\n    path('', include('{app_name}.urls')),")

    # Custom Admin URL
    if admin_url != 'admin':
        if "path('admin/', admin.site.urls)" in root_content:
            root_content = root_content.replace("path('admin/', admin.site.urls)", f"path('{admin_url}/', admin.site.urls)")
            print_success(f"Obfuscated Admin URL to: /{admin_url}/")

    if "from django.conf import settings" not in root_content:
        root_content = root_content.replace("from django.urls import path, include", "from django.urls import path, include\nfrom django.conf import settings\nfrom django.conf.urls.static import static")

    # Add media URL pattern if DEBUG is True
    media_pattern = "+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)"
    if media_pattern not in root_content:
        root_content += f"\nif settings.DEBUG:\n    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)"

    with open(root_urls_path, 'w') as f:
        f.write(root_content)
    
    print_success("Generated urls.py and updated root urls.py")

def generate_templates(app_name, use_landing=True):
    templates_dir = os.path.join(app_name, 'templates', 'accounts')
    os.makedirs(templates_dir, exist_ok=True)
    
    def write_t(name, content):
        with open(os.path.join(templates_dir, name), 'w') as f:
            f.write(textwrap.dedent(content))

    if use_landing:
        write_t('landing.html', """
            {% extends 'accounts/base_auth.html' %}
            {% block title %}Bienvenue | GestEcole{% endblock %}
            {% block content %}
            <div class="row align-items-center justify-content-center text-center">
                <div class="col-lg-10 col-xl-8">
                    <div class="card p-5 border-0 rounded-5 bg-white shadow-lg overflow-hidden position-relative">
                        <div class="position-absolute top-0 end-0 p-5 opacity-10 d-none d-md-block">
                            <i class="bi bi-mortarboard-fill" style="font-size: 10rem; transform: rotate(15deg);"></i>
                        </div>
                        <div class="position-relative z-1 py-4">
                            <div class="mb-5">
                                <h1 class="display-3 fw-bold text-dark mb-3">GestEcole <span class="text-primary">Connect</span></h1>
                                <p class="lead text-secondary mx-auto">La gestion scolaire nouvelle génération.</p>
                            </div>
                            <div class="d-grid gap-3 d-sm-flex justify-content-sm-center mb-5">
                                {% if not user.is_authenticated %}
                                    <a href="{% url 'accounts:login' %}" class="btn btn-primary btn-lg px-5 py-3 rounded-pill shadow-lg">Connexion</a>
                                    <a href="{% url 'accounts:register' %}" class="btn btn-outline-primary btn-lg px-5 py-3 rounded-pill">S'inscrire</a>
                                {% else %}
                                    <a href="{% url 'accounts:dashboard' %}" class="btn btn-primary btn-lg px-5 py-3 rounded-pill shadow-lg">Dashboard</a>
                                {% endif %}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endblock %}
        """)

    write_t('base_auth.html', """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{% block title %}Authentification{% endblock %}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
            <style>
                :root {
                    --primary-color: #4e73df;
                    --bg-gradient: linear-gradient(135deg, #f8f9fc 0%, #e2e8f0 100%);
                }
                body { 
                    background: var(--bg-gradient); 
                    font-family: 'Inter', sans-serif;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .card { border: none; border-radius: 1rem; box-shadow: 0 0.5rem 1rem rgba(0,0,0,0.1); }
                .btn-primary { background: var(--primary-color); border: none; padding: 0.75rem 1.5rem; border-radius: 0.5rem; }
                .transition-hover:hover { transform: translateY(-3px); transition: all 0.3s; }
            </style>
        </head>
        <body>
            <div class="container py-5">
                {% block content %}{% endblock %}
            </div>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
    """)

    write_t('base.html', """
        <!DOCTYPE html>
        <html lang="fr">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>{% block title %}GestEcole{% endblock %}</title>
            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.0/font/bootstrap-icons.css">
            <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
            <style>
                :root {
                    --primary: #6366f1;
                    --primary-light: #818cf8;
                    --secondary: #64748b;
                    --success: #10b981;
                    --warning: #f59e0b;
                    --danger: #ef4444;
                    --bg-body: #f1f5f9;
                    --header-height: 75px;
                }
                body {
                    background-color: var(--bg-body);
                    font-family: 'Outfit', sans-serif;
                    color: #1e293b;
                    padding-top: var(--header-height);
                    min-height: 100vh;
                }
                .navbar-custom {
                    height: var(--header-height);
                    background: rgba(255, 255, 255, 0.85);
                    backdrop-filter: blur(12px);
                    border-bottom: 1px solid rgba(255, 255, 255, 0.3);
                    box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.05);
                    z-index: 1030;
                }
                .navbar-brand { font-weight: 700; font-size: 1.5rem; color: var(--primary); letter-spacing: -0.5px; }
                .nav-link { font-weight: 600; color: var(--secondary); padding: 0.5rem 1rem !important; border-radius: 0.5rem; transition: all 0.2s; margin: 0 0.25rem; }
                .nav-link:hover { color: var(--primary); background: rgba(99, 102, 241, 0.08); }
                .nav-link.active { color: var(--primary) !important; background: rgba(99, 102, 241, 0.12); }
                .user-pill {
                    background: white; padding: 0.35rem 1rem 0.35rem 0.5rem; border-radius: 2rem;
                    border: 1px solid #e2e8f0; cursor: pointer; transition: all 0.2s;
                }
                .user-pill:hover { border-color: var(--primary-light); box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1); }
                .avatar-circle {
                    width: 32px; height: 32px; border-radius: 50%; background: var(--primary);
                    color: white; display: flex; align-items: center; justify-content: center; font-weight: 700; font-size: 0.85rem;
                }
                .card { border: none; border-radius: 1.25rem; box-shadow: 0 8px 30px rgba(0, 0, 0, 0.04); transition: transform 0.3s ease, box-shadow 0.3s ease; }
                .card-premium-hover:hover { transform: translateY(-8px); box-shadow: 0 15px 40px rgba(0, 0, 0, 0.08); }
                .btn-primary { background: var(--primary); border: none; padding: 0.65rem 1.75rem; border-radius: 0.85rem; font-weight: 600; box-shadow: 0 4px 15px rgba(99, 102, 241, 0.3); transition: all 0.2s; }
                .btn-primary:hover { background: #4f46e5; transform: translateY(-2px); box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4); }
                @media (max-width: 991.98px) {
                    .navbar-collapse { background: white; margin-top: 1rem; padding: 1.5rem; border-radius: 1.5rem; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.1); border: 1px solid #e2e8f0; }
                    /* Center Dropdown on Mobile */
                    .dropdown-menu {
                        position: absolute;
                        left: 50% !important;
                        transform: translateX(-50%) !important;
                        width: 85%;
                        text-align: center;
                        margin-top: 0.5rem;
                    }
                }
            </style>
        </head>
        <body>
            <nav class="navbar navbar-expand-lg navbar-custom fixed-top">
                <div class="container">
                    <a class="navbar-brand d-flex align-items-center" href="/">
                        <i class="bi bi-mortarboard-fill me-2 fs-3"></i>
                        Gest<span class="text-dark">Ecole</span>
                    </a>
                    
                    <button class="navbar-toggler border-0 shadow-none" type="button" data-bs-toggle="collapse" data-bs-target="#navbarContent">
                        <i class="bi bi-list fs-2 text-primary"></i>
                    </button>
                    
                    <div class="collapse navbar-collapse" id="navbarContent">
                        <ul class="navbar-nav mx-auto mb-2 mb-lg-0">
                            <li class="nav-item">
                                <a class="nav-link {% if request.resolver_match.url_name == 'dashboard' %}active{% endif %}" href="{% url 'accounts:dashboard' %}">
                                    <i class="bi bi-grid-1x2 me-1"></i> Dashboard
                                </a>
                            </li>
                            <li class="nav-item">
                                <a class="nav-link {% if 'user' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'accounts:user_list' %}">
                                    <i class="bi bi-people me-1"></i> Communauté
                                </a>
                            </li>
                            {% if user.is_superuser or user.groups.all %}
                            <li class="nav-item">
                                <a class="nav-link {% if 'group' in request.resolver_match.url_name %}active{% endif %}" href="{% url 'accounts:group_list' %}">
                                    <i class="bi bi-shield-lock me-1"></i> Accès & Rôles
                                </a>
                            </li>
                            {% endif %}
                        </ul>
                        
                        <div class="d-flex align-items-center gap-3">
                            <div class="dropdown">
                                <div class="user-pill d-flex align-items-center dropdown-toggle shadow-none border-0" data-bs-toggle="dropdown">
                                    {% if user.photo_profil %}
                                        <img src="{{ user.photo_profil.url }}" class="rounded-circle me-2" width="32" height="32" style="object-fit: cover;">
                                    {% else %}
                                        <div class="avatar-circle me-2">{{ user.username|make_list|first|upper }}</div>
                                    {% endif %}
                                    <div class="d-none d-sm-block">
                                        <span class="fw-bold small d-block">{{ user.username }}</span>
                                    </div>
                                </div>
                                <ul class="dropdown-menu dropdown-menu-end border-0 shadow-lg rounded-4 p-2 mt-2">
                                    <li><a class="dropdown-item rounded-3 py-2" href="{% url 'accounts:profile' %}"><i class="bi bi-person me-2"></i>Mon Profil</a></li>
                                    <li><a class="dropdown-item rounded-3 py-2" href="{% url 'accounts:password_change' %}"><i class="bi bi-key me-2"></i>Sécurité</a></li>
                                    <li><hr class="dropdown-divider opacity-50"></li>
                                    <li>
                                        <form action="{% url 'accounts:logout' %}" method="post">
                                            {% csrf_token %}
                                            <button type="submit" class="dropdown-item rounded-3 py-2 text-danger">
                                                <i class="bi bi-box-arrow-right me-2"></i>Déconnexion
                                            </button>
                                        </form>
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </div>
                </div>
            </nav>

            <main class="container py-5 animate-fade-in">
                {% if messages %}
                    <div class="messages">
                        {% for message in messages %}
                            <div class="alert alert-{{ message.tags }} alert-dismissible fade show border-0 shadow-sm rounded-4 mb-4 p-3 ps-4 overflow-hidden">
                                <div class="position-absolute start-0 top-0 bottom-0 bg-{{ message.tags }}" style="width: 5px;"></div>
                                <div class="d-flex align-items-center">
                                    <i class="bi {% if message.tags == 'success' %}bi-check-circle-fill text-success{% else %}bi-exclamation-triangle-fill text-warning{% endif %} fs-4 me-3"></i>
                                    <div class="fw-semibold">{{ message }}</div>
                                </div>
                                <button type="button" class="btn-close shadow-none" data-bs-dismiss="alert"></button>
                            </div>
                        {% endfor %}
                    </div>
                {% endif %}
                {% block content %}{% endblock %}
            </main>
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        </body>
        </html>
    """)

    write_t('dashboard.html', """
        {% extends 'accounts/base.html' %}
        {% block title %}Dashboard | GestEcole{% endblock %}
        {% block content %}
        <div class="row mb-5">
            <div class="col-12">
                <div class="card bg-primary text-white p-5 rounded-4 shadow-sm border-0 position-relative overflow-hidden">
                    <div class="position-absolute top-0 end-0 p-4 opacity-25">
                        <i class="bi bi-mortarboard-fill" style="font-size: 8rem;"></i>
                    </div>
                    <div class="position-relative z-1">
                        <h1 class="display-5 fw-bold mb-2">Bienvenue, {{ user.username }} !</h1>
                        <p class="lead mb-0 opacity-75">
                            Rôle : 
                            {% if is_admin %}<span class="badge bg-white text-primary">Administrateur</span>
                            {% elif is_manager %}<span class="badge bg-white text-primary">Manager</span>
                            {% else %}<span class="badge bg-white text-primary">Membre</span>{% endif %}
                        </p>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row g-4">
            <div class="col-md-6 col-lg-3">
                <div class="card p-4 border-0 shadow-sm card-premium-hover h-100">
                    <div class="d-flex align-items-center mb-3">
                        <div class="bg-primary bg-opacity-10 p-3 rounded-circle text-primary me-3">
                            <i class="bi bi-person-circle fs-4"></i>
                        </div>
                        <h5 class="fw-bold mb-0">Mon Profil</h5>
                    </div>
                    <p class="text-muted small">Mettez à jour vos informations personnelles.</p>
                    <a href="{% url 'accounts:profile' %}" class="btn btn-outline-primary btn-sm rounded-pill mt-auto">Gérer</a>
                </div>
            </div>
            
            {% if is_admin or is_manager %}
            <div class="col-md-6 col-lg-3">
                <div class="card p-4 border-0 shadow-sm card-premium-hover h-100">
                    <div class="d-flex align-items-center mb-3">
                        <div class="bg-success bg-opacity-10 p-3 rounded-circle text-success me-3">
                            <i class="bi bi-people fs-4"></i>
                        </div>
                        <h5 class="fw-bold mb-0">Utilisateurs</h5>
                    </div>
                    <p class="text-muted small">Gérez les comptes membres et leurs accès.</p>
                    <a href="{% url 'accounts:user_list' %}" class="btn btn-outline-success btn-sm rounded-pill mt-auto">Administrer</a>
                </div>
            </div>
            {% endif %}

            {% if is_admin %}
            <div class="col-md-6 col-lg-3">
                <div class="card p-4 border-0 shadow-sm card-premium-hover h-100">
                    <div class="d-flex align-items-center mb-3">
                        <div class="bg-warning bg-opacity-10 p-3 rounded-circle text-warning me-3">
                            <i class="bi bi-shield-lock fs-4"></i>
                        </div>
                        <h5 class="fw-bold mb-0">Groupes & Rôles</h5>
                    </div>
                    <p class="text-muted small">Configurez les permissions globales.</p>
                    <a href="{% url 'accounts:group_list' %}" class="btn btn-outline-warning btn-sm rounded-pill mt-auto">Configurer</a>
                </div>
            </div>
            {% endif %}
        </div>
        <style> .bg-primary { background: linear-gradient(135deg, #4e73df 0%, #224abe 100%) !important; } </style>
        {% endblock %}
    """)

    write_t('login.html', """
        {% extends 'accounts/base_auth.html' %}
        {% block content %}
        <div class="row justify-content-center min-vh-75 align-items-center">
            <div class="col-12 col-md-6 col-lg-5">
                <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
                    <div class="p-5">
                        <div class="text-center mb-4">
                            <div class="bg-primary bg-opacity-10 d-inline-block p-3 rounded-circle mb-3">
                                <i class="bi bi-person-lock text-primary fs-1"></i>
                            </div>
                            <h2 class="fw-bold">Bon retour !</h2>
                            <p class="text-muted">Veuillez vous connecter à votre compte</p>
                        </div>
                        
                        {% if form.errors %}
                        <div class="alert alert-danger border-0 rounded-3">
                            Identifiants invalides.
                        </div>
                        {% endif %}

                        <form method="post">
                            {% csrf_token %}
                            <div class="mb-4">
                                <label class="form-label fw-semibold">Nom d'utilisateur</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0"><i class="bi bi-person"></i></span>
                                    <input type="text" name="username" class="form-control border-start-0 bg-light" placeholder="Utilisateur" required>
                                </div>
                            </div>
                            <div class="mb-4">
                                <label class="form-label fw-semibold">Mot de passe</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0"><i class="bi bi-key"></i></span>
                                    <input type="password" name="password" class="form-control border-start-0 bg-light" placeholder="••••••••" required>
                                </div>
                            </div>
                            <button type="submit" class="btn btn-primary w-100 py-3 rounded-3 shadow-sm transition-hover">
                                Se connecter
                            </button>
                        </form>
                        
                        <div class="text-center mt-5">
                            <p class="text-muted mb-0">Pas de compte ?</p>
                            <a href="{% url 'accounts:register' %}" class="text-primary fw-bold text-decoration-none">S'inscrire</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        {% endblock %}
    """)

    write_t('register.html', """
        {% extends 'accounts/base_auth.html' %}
        {% block content %}
        <div class="row justify-content-center py-5">
            <div class="col-12 col-md-8 col-lg-6">
                <div class="card border-0 shadow-lg rounded-4 overflow-hidden">
                    <div class="p-5">
                        <div class="text-center mb-5">
                            <div class="bg-success bg-opacity-10 d-inline-block p-3 rounded-circle mb-3">
                                <i class="bi bi-person-plus text-success fs-1"></i>
                            </div>
                            <h2 class="fw-bold">Inscription</h2>
                            <p class="text-muted">Créez votre compte maintenant</p>
                        </div>

                        <form method="post" enctype="multipart/form-data">
                            {% csrf_token %}
                            {% for field in form %}
                            <div class="mb-4">
                                <label class="form-label fw-semibold">{{ field.label }}</label>
                                <div class="input-group">
                                    <span class="input-group-text bg-light border-end-0">
                                        {% if 'username' in field.name %}<i class="bi bi-person"></i>
                                        {% elif 'email' in field.name %}<i class="bi bi-envelope"></i>
                                        {% elif 'password' in field.name %}<i class="bi bi-lock"></i>
                                        {% else %}<i class="bi bi-pencil"></i>
                                        {% endif %}
                                    </span>
                                    <div class="form-control bg-light border-start-0 p-0 overflow-hidden">
                                        {{ field }}
                                    </div>
                                </div>
                                {% if field.errors %}
                                    {% for error in field.errors %}<div class="text-danger small mt-1">{{ error }}</div>{% endfor %}
                                {% endif %}
                            </div>
                            {% endfor %}

                            <button type="submit" class="btn btn-primary w-100 py-3 rounded-3 shadow-sm transition-hover mt-4">
                                Créer mon compte
                            </button>
                        </form>

                        <div class="text-center mt-5">
                            <p class="text-muted mb-0">Déjà inscrit ?</p>
                            <a href="{% url 'accounts:login' %}" class="text-primary fw-bold text-decoration-none">Se connecter</a>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        <style>
            input, select, textarea { border: none !important; background: transparent !important; padding: 0.75rem 1rem !important; width: 100% !important; outline: none !important; }
        </style>
        {% endblock %}
    """)

    write_t('profile.html', """
        {% extends 'accounts/base.html' %}
        {% block content %}
        <div class="row">
            <div class="col-lg-8 mx-auto">
                <div class="card p-4 shadow-sm border-0 rounded-4">
                    <div class="text-center mb-4">
                        {% if user.photo_profil %}
                            <img src="{{ user.photo_profil.url }}" class="rounded-circle mb-3 shadow-sm object-fit-cover" width="100" height="100" style="border: 3px solid #e2e8f0;">
                        {% else %}
                            <div class="bg-primary bg-opacity-10 d-inline-block p-3 rounded-circle mb-3">
                                <i class="bi bi-person-circle text-primary fs-1"></i>
                            </div>
                        {% endif %}
                        <h3 class="fw-bold">Mon Profil</h3>
                    </div>
                    <form method="post" enctype="multipart/form-data">
                        {% csrf_token %}
                        <div class="mb-4">
                            {{ form.as_p }}
                        </div>
                        <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                            <a href="{% url 'accounts:password_change' %}" class="btn btn-outline-warning rounded-pill px-4">
                                <i class="bi bi-key me-2"></i>Mot de passe
                            </a>
                            <button type="submit" class="btn btn-primary rounded-pill px-5">
                                <i class="bi bi-check-lg me-2"></i>Enregistrer
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <style>
            input, select, textarea { 
                display: block; width: 100%; padding: 0.75rem 1rem; 
                font-size: 1rem; color: #4a5568; background-color: #f8f9fc;
                border: 1px solid #e2e8f0; border-radius: 0.5rem; margin-bottom: 1rem;
            }
            label { font-weight: 600; margin-bottom: 0.5rem; color: #2d3748; }
        </style>
        {% endblock %}
    """)

    write_t('password_change.html', """
        {% extends 'accounts/base.html' %}
        {% block content %}
        <div class="row">
            <div class="col-lg-6 mx-auto">
                <div class="card p-4 shadow-sm border-0 rounded-4">
                    <div class="text-center mb-4">
                        <div class="bg-warning bg-opacity-10 d-inline-block p-3 rounded-circle mb-3">
                            <i class="bi bi-shield-lock text-warning fs-1"></i>
                        </div>
                        <h3 class="fw-bold">Sécurité</h3>
                        <p class="text-muted">Modifier votre mot de passe</p>
                    </div>
                    <form method="post">
                        {% csrf_token %}
                        <div class="mb-4">
                            {{ form.as_p }}
                        </div>
                        <div class="d-grid">
                            <button type="submit" class="btn btn-warning text-white rounded-pill py-3 fw-bold shadow-sm transition-hover">
                                Mettre à jour le mot de passe
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <style>
            input { 
                display: block; width: 100%; padding: 0.75rem 1rem; 
                font-size: 1rem; color: #4a5568; background-color: #f8f9fc;
                border: 1px solid #e2e8f0; border-radius: 0.5rem; margin-bottom: 1rem;
            }
            label { font-weight: 600; margin-bottom: 0.5rem; color: #2d3748; }
            .helptext { font-size: 0.8rem; color: #718096; display: block; margin-top: -0.5rem; margin-bottom: 1rem; }
        </style>
        {% endblock %}
    """)

    write_t('user_list.html', """
        {% extends 'accounts/base.html' %}
        {% block title %}Gestion des Utilisateurs | GestEcole{% endblock %}
        {% block content %}
        <div class="row mb-4 align-items-center">
            <div class="col">
                <h2 class="fw-bold mb-1">Communauté</h2>
                <p class="text-secondary mb-0">Découvrez et gérez les membres de l'institution GestEcole.</p>
            </div>
            {% if user.is_superuser %}
            <div class="col-auto">
                <a href="{% url 'accounts:register' %}" class="btn btn-primary d-flex align-items-center">
                    <i class="bi bi-person-plus me-2 fs-5"></i> Nouvel Utilisateur
                </a>
            </div>
            {% endif %}
        </div>

        <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
            <div class="p-4 bg-white border-bottom d-flex justify-content-between align-items-center">
                <h5 class="fw-bold m-0"><i class="bi bi-people-fill text-primary me-2"></i>Liste des Membres</h5>
                <div class="badge bg-primary bg-opacity-10 text-primary border border-primary border-opacity-25 px-3 py-2 rounded-pill">
                    {{ users.count }} Utilisateurs
                </div>
            </div>
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="bg-light bg-opacity-50">
                        <tr class="small text-uppercase fw-bold text-secondary">
                            <th class="ps-4 py-3">Membre</th>
                            <th class="py-3">Email</th>
                            <th class="py-3">Rôles</th>
                            <th class="py-3">Statut</th>
                            <th class="py-3 text-end pe-4">Actions</th>
                        </tr>
                    </thead>
                    <tbody class="border-top-0">
                        {% for u in users %}
                        <tr>
                            <td class="ps-4">
                                <div class="d-flex align-items-center">
                                    <div class="avatar-sm bg-primary bg-opacity-10 text-primary rounded-circle d-flex align-items-center justify-content-center fw-bold me-3" style="width: 40px; height: 40px;">
                                        {{ u.username|make_list|first|upper }}
                                    </div>
                                    <div>
                                        <div class="fw-bold text-dark">{{ u.username }}</div>
                                        {% if u.is_superuser %}<span class="badge bg-danger bg-opacity-10 text-danger small px-2 rounded-pill">Superadmin</span>{% endif %}
                                    </div>
                                </div>
                            </td>
                            <td class="text-secondary small">{{ u.email }}</td>
                            <td>
                                <div class="d-flex flex-wrap gap-1">
                                    {% for g in u.groups.all %}
                                        <span class="badge bg-indigo bg-opacity-10 text-indigo border border-indigo border-opacity-25 px-2 py-1 rounded-pill small" style="--indigo: #6366f1; color: var(--indigo);">{{ g.name }}</span>
                                    {% empty %}
                                        <span class="text-muted small italic">Aucun rôle</span>
                                    {% endfor %}
                                </div>
                            </td>
                            <td>
                                {% if u.is_active %}
                                    <span class="badge bg-success bg-opacity-10 text-success px-2 py-1 rounded-pill small">Actif</span>
                                {% else %}
                                    <span class="badge bg-secondary bg-opacity-10 text-secondary px-2 py-1 rounded-pill small">Inactif</span>
                                {% endif %}
                            </td>
                            <td class="text-end pe-4">
                                <div class="d-flex justify-content-end gap-2">
                                    <a href="{% url 'accounts:user_edit' u.pk %}" class="btn btn-sm btn-light rounded-pill px-3 shadow-none border">
                                        <i class="bi bi-pencil-square me-1"></i> Éditer
                                    </a>
                                    {% if u != user and user.is_superuser %}
                                    <a href="{% url 'accounts:user_delete' u.pk %}" class="btn btn-sm btn-outline-danger rounded-pill px-3 shadow-none border">
                                        <i class="bi bi-trash"></i>
                                    </a>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        <style> .table-hover tbody tr:hover { background-color: rgba(99, 102, 241, 0.02); } </style>
        {% endblock %}
    """)

    write_t('user_form.html', """
        {% extends 'accounts/base.html' %}
        {% block title %}Modifier l'utilisateur | GestEcole{% endblock %}
        {% block content %}
        <div class="row">
            <div class="col-lg-6 mx-auto">
                <div class="card border-0 shadow-sm p-4 p-md-5 rounded-4 animate-fade-in text-center">
                    <div class="bg-primary bg-opacity-10 d-inline-block p-4 rounded-circle mb-4 mx-auto">
                        <i class="bi bi-person-gear text-primary fs-1"></i>
                    </div>
                    <h2 class="fw-bold mb-1">Paramètres du Compte</h2>
                    <p class="text-secondary mb-5">Modifier les accès et informations de <strong>{{ object.username }}</strong>.</p>
                    <form method="post" class="text-start">
                        {% csrf_token %}
                        <div class="row g-4">
                            {% for field in form %}
                            <div class="col-12">
                                <label class="form-label fw-bold text-dark small">{{ field.label }}</label>
                                {% if field.name == 'groups' %}
                                    <div class="p-3 bg-light rounded-4 border">{{ field }}</div>
                                {% else %}
                                    <div class="bg-light rounded-4 overflow-hidden border">{{ field }}</div>
                                {% endif %}
                                {% if field.help_text %}<div class="form-text small opacity-75 mt-1">{{ field.help_text|safe }}</div>{% endif %}
                                {% for error in field.errors %}<div class="text-danger small mt-1 fw-bold">{{ error }}</div>{% endfor %}
                            </div>
                            {% endfor %}
                        </div>
                        <div class="mt-5 d-grid gap-2">
                            <button type="submit" class="btn btn-primary py-3 fw-bold rounded-4 shadow-sm transition-hover">Enregistrer les modifications</button>
                            <a href="{% url 'accounts:user_list' %}" class="btn btn-link text-secondary text-decoration-none">Annuler</a>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <style>
            input:not([type=checkbox]), select, textarea { display: block; width: 100%; padding: 0.85rem 1.25rem; font-size: 0.95rem; background: transparent; border: none !important; outline: none !important; }
            .bg-light:focus-within { background-color: #fff !important; border-color: var(--primary) !important; box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.1); }
        </style>
        {% endblock %}
    """)

    write_t('user_confirm_delete.html', """
        {% extends 'accounts/base.html' %}
        {% block content %}
        <div class="row justify-content-center">
            <div class="col-md-6">
                <div class="card border-0 shadow p-5 text-center rounded-4">
                    <div class="mb-4 text-danger"><i class="bi bi-exclamation-circle fs-1"></i></div>
                    <h3>Confirmer la suppression</h3>
                    <p class="text-muted">Êtes-vous sûr de vouloir supprimer l'utilisateur <strong>{{ object.username }}</strong> ? Cette action est irréversible.</p>
                    <form method="post">
                        {% csrf_token %}
                        <div class="d-flex justify-content-center gap-3 mt-4">
                            <a href="{% url 'accounts:user_list' %}" class="btn btn-light rounded-pill px-4">Annuler</a>
                            <button type="submit" class="btn btn-danger rounded-pill px-4">Supprimer définitivement</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        {% endblock %}
    """)

    write_t('group_list.html', """
        {% extends 'accounts/base.html' %}
        {% block content %}
        <div class="row mb-4 align-items-center">
            <div class="col"><h2 class="fw-bold">Groupes & Permissions</h2></div>
            <div class="col-auto">
                <a href="{% url 'accounts:group_add' %}" class="btn btn-primary rounded-pill"><i class="bi bi-plus-lg me-2"></i>Nouveau Groupe</a>
            </div>
        </div>
        <div class="card border-0 shadow-sm rounded-4 overflow-hidden">
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="bg-light">
                        <tr><th class="ps-4 py-3">Nom du Groupe</th><th class="py-3">Permissions</th><th class="text-end pe-4">Actions</th></tr>
                    </thead>
                    <tbody>
                        {% for group in groups %}
                        <tr>
                            <td class="ps-4 fw-bold">{{ group.name }}</td>
                            <td><span class="badge bg-secondary rounded-pill">{{ group.permissions.count }} Permissions</span></td>
                            <td class="text-end pe-4">
                                <a href="{% url 'accounts:group_edit' group.pk %}" class="btn btn-sm btn-light border rounded-pill">Éditer</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
        {% endblock %}
    """)

    write_t('group_form.html', """
        {% extends 'accounts/base.html' %}
        {% block content %}
        <div class="row justify-content-center">
            <div class="col-lg-8">
                <div class="card border-0 shadow-sm p-5 rounded-4">
                    <h3 class="fw-bold mb-4">{% if object %}Éditer le Groupe{% else %}Créer un Groupe{% endif %}</h3>
                    <form method="post">
                        {% csrf_token %}
                        <div class="mb-4">
                            <label class="form-label fw-bold">Nom du groupe</label>
                            <input type="text" name="name" class="form-control" value="{{ form.name.value|default:'' }}" required>
                        </div>
                        <div class="mb-4">
                            <label class="form-label fw-bold mb-3">Permissions associées</label>
                            <div class="border rounded-3 p-3 overflow-auto" style="max-height: 400px; background: #f8f9fa;">
                                {{ form.permissions }}
                            </div>
                            <div class="form-text mt-2"><i class="bi bi-info-circle me-1"></i>Maintenez Ctrl (ou Cmd) pour sélectionner plusieurs permissions si nécessaire.</div>
                        </div>
                        <div class="d-flex justify-content-end gap-2">
                            <a href="{% url 'accounts:group_list' %}" class="btn btn-light rounded-pill">Annuler</a>
                            <button type="submit" class="btn btn-primary rounded-pill px-5">Sauvegarder</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
        <style>
             /* Customize checkbox list if rendered as ul/li */
             ul { list-style: none; padding: 0; }
             li { margin-bottom: 5px; }
             label { cursor: pointer; }
        </style>
        {% endblock %}
    """)

    write_t('verify_otp.html', """
        {% extends 'accounts/base_auth.html' %}
        {% block content %}
        <div class="card p-5 text-center" style="max-width: 450px; margin: auto;">
            <div class="bg-warning bg-opacity-10 d-inline-block p-3 rounded-circle mb-4 mx-auto">
                <i class="bi bi-shield-check text-warning fs-1"></i>
            </div>
            <h3 class="fw-bold mb-3">Sécurité</h3>
            <p class="text-muted mb-4">Entrez le code reçu par email</p>
            <form method="post">
                {% csrf_token %}
                <input type="text" name="otp" class="form-control form-control-lg text-center fw-bold mb-4" placeholder="000000" maxlength="6" autofocus required>
                <button type="submit" class="btn btn-primary w-100 py-3">Vérifier</button>
            </form>
            <div class="mt-4"><a href="{% url 'accounts:login' %}" class="text-secondary small">Retour</a></div>
        </div>
        {% endblock %}
    """)
    print_success("Generated templates in accounts/templates/accounts/")


if __name__ == "__main__":
    print(f"{Colors.HEADER}{Colors.BOLD}=== Django Auth CLI Setup ==={Colors.ENDC}")
    
    # Dependency Check
    try:
        from PIL import Image
    except ImportError:
        print_warning("Pillow is not installed. Profile photos will not work. Run: pip install Pillow")

    # Interactive Prompts
    use_2fa = input(f"{Colors.OKBLUE}Add 2FA (Double Authentication)? (yes/no) [no]: {Colors.ENDC}").strip().lower() == 'yes'
    welcome_email = input(f"{Colors.OKBLUE}Send welcome email on registration? (yes/no) [yes]: {Colors.ENDC}").strip().lower() != 'no'
    create_test_users = input(f"{Colors.OKBLUE}Create default test users (superuser & admin)? (yes/no) [yes]: {Colors.ENDC}").strip().lower() != 'no'
    use_landing = input(f"{Colors.OKBLUE}Add a public Landing Page? (yes/no) [yes]: {Colors.ENDC}").strip().lower() != 'no'
    admin_url = input(f"{Colors.OKBLUE}Custom Admin URL path (e.g. 'secret-admin') [admin]: {Colors.ENDC}").strip() or 'admin'

    print("\nAvailable default groups for new users:")
    print("1. Membre (Default)")
    print("2. Manager")
    print("3. Admin_Site")
    group_choice = input(f"{Colors.OKBLUE}Choose default group (1/2/3) [1]: {Colors.ENDC}").strip()
    
    default_groups = { '1': 'Membre', '2': 'Manager', '3': 'Admin_Site' }
    default_group = default_groups.get(group_choice, 'Membre')
    
    print(f"\n{Colors.OKCYAN}Config: 2FA={'ON' if use_2fa else 'OFF'}, WelcomeEmail={'ON' if welcome_email else 'OFF'}, DefaultGroup={default_group}{Colors.ENDC}\n")
    
    confirm = input(f"{Colors.WARNING}Proceed with setup? (yes/no) [yes]: {Colors.ENDC}").strip().lower() != 'no'
    if not confirm:
        print_info("Setup cancelled.")
        sys.exit(0)

    # Execution phases
    app_name = 'accounts'
    if setup_accounts_app(app_name):
        generate_models(app_name)
        generate_signals(app_name, default_group, welcome_email)
        generate_forms(app_name)
        generate_views(app_name, use_landing, use_2fa)
        generate_urls(app_name, use_landing, admin_url, use_2fa)
        generate_templates(app_name, use_landing)
        
        print_info("Initializing groups (Database required)...")
        print_warning("Running makemigrations and migrate first...")
        
        success, err = run_command(f"{sys.executable} manage.py makemigrations {app_name}")
        migration_error = False
        
        if success:
            success, err = run_command(f"{sys.executable} manage.py migrate")
            if not success:
                migration_error = True
        else:
            migration_error = True

        if migration_error:
            print_error("Migration failed. This is often due to introducing a Custom User model in an existing database.")
            print_warning("Strategy: We can attempt a 'Deep Clean' (DELETE db.sqlite3 and all migrations) to start fresh.")
            clean = input(f"{Colors.FAIL}Do you want to PERMANENTLY RESET the database and all migrations? (yes/no) [no]: {Colors.ENDC}").strip().lower() == 'yes'
            
            if clean:
                print_info("Deep cleaning project safely...")
                if os.path.exists('db.sqlite3'):
                    os.remove('db.sqlite3')
                
                # Safer cleaning: skip hidden dirs (like .venv, .git)
                for root, dirs, files in os.walk('.'):
                    # Filter out hidden directories in-place
                    dirs[:] = [d for d in dirs if not d.startswith('.')]
                    
                    if 'migrations' in dirs:
                        m_dir = os.path.join(root, 'migrations')
                        for f in os.listdir(m_dir):
                            if f != '__init__.py' and f.endswith('.py'):
                                try:
                                    os.remove(os.path.join(m_dir, f))
                                except OSError:
                                    pass
                
                print_info("Retrying migrations...")
                run_command(f"{sys.executable} manage.py makemigrations")
                run_command(f"{sys.executable} manage.py makemigrations {app_name}")
                run_command(f"{sys.executable} manage.py migrate")
            else:
                print_error("Setup stopped due to migration errors.")
                sys.exit(1)
        
        init_groups(create_users=create_test_users)
        
        if use_2fa:
            print_info("2FA selected. Please install 'django-two-factor-auth' for full implementation.")
            print_info("Scaffolding for 2FA is conceptually ready in views (LoginRequiredMixin).")

        if welcome_email:
            print_info("Welcome Email enabled. Remember to configure SMTP settings in settings.py.")
            print_info("Logic can be added to the post_save signal in accounts/signals.py.")

        print(f"\n{Colors.OKGREEN}{Colors.BOLD}Setup Completed Successfully!{Colors.ENDC}")
        print_info(f"Login at: /accounts/login/")
        print_info(f"Dashboard at: /accounts/dashboard/")
