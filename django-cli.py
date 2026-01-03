import os
import sys
import django
from django.conf import settings
from django.apps import apps
import textwrap
import subprocess


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
    return 'my_django_project' # Fallback default

def setup_django():
    if not os.path.exists('manage.py'):
        print("Warning: manage.py not found. Ensure you are in the project root.")
        # We don't exit here because 'init:project' might be running
    
    project_name = get_project_name()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', f'{project_name}.settings')
    try:
        django.setup()
    except Exception as e:
        # Only warn if we are not running init command
        if len(sys.argv) > 1 and sys.argv[1] == 'init:project':
             pass
        else:
             print(f"Warning: Django setup failed: {e}")
             print("Continuing, but some features might fail if they rely on the app registry.")


def ensure_app_exists(app_name):
    if not os.path.exists(app_name):
        print(f"App '{app_name}' does not exist. Creating it...")
        try:
            subprocess.check_call([sys.executable, 'manage.py', 'startapp', app_name])
            print(f"App '{app_name}' created.")
            
            project_name = get_project_name()
            settings_path = os.path.join(project_name, 'settings.py')

            with open(settings_path, 'r') as f:
                content = f.read()
            
            if f"'{app_name}'" not in content and f'"{app_name}"' not in content:
                print(f"Registering '{app_name}' in settings.py...")
                if "INSTALLED_APPS = [" in content:
                    new_content = content.replace("INSTALLED_APPS = [", f"INSTALLED_APPS = [\n    '{app_name}',")
                    with open(settings_path, 'w') as f:
                        f.write(new_content)
                    print("settings.py updated.")
            if settings.configured:
                 apps.clear_cache()
        except subprocess.CalledProcessError:
            print("Failed to create app via manage.py.")
            sys.exit(1)
    return True

def ensure_media_config():
    project_name = get_project_name()
    settings_path = os.path.join(project_name, 'settings.py')

    if not os.path.exists(settings_path):
        return

    with open(settings_path, 'r') as f:
        content = f.read()
    
    modified = False
    if 'MEDIA_URL' not in content:
        print("Configuring MEDIA_URL in settings.py...")
        content += "\nMEDIA_URL = '/uploads/'\n"
        modified = True
    
    if 'MEDIA_ROOT' not in content:
        print("Configuring MEDIA_ROOT in settings.py...")
        content += "MEDIA_ROOT = BASE_DIR / 'uploads'\n"
        modified = True
        
    if modified:
        with open(settings_path, 'w') as f:
            f.write(content)
        print("settings.py updated with media configuration.")

    # Also check URLs
    urls_path = os.path.join(project_name, 'urls.py')

    if not os.path.exists(urls_path):
        return

    with open(urls_path, 'r') as f:
        urls_content = f.read()
    
    if 'static(settings.MEDIA_URL' not in urls_content:
        print("Configuring media serving in urls.py...")
        
        # Add imports if missing
        new_imports = []
        if 'from django.conf import settings' not in urls_content:
            new_imports.append('from django.conf import settings')
        if 'from django.conf.urls.static import static' not in urls_content:
            new_imports.append('from django.conf.urls.static import static')
            
        if new_imports:
            urls_content = "\n".join(new_imports) + "\n" + urls_content
        
        if 'urlpatterns += static(settings.MEDIA_URL' not in urls_content:
             urls_content += "\n\nif settings.DEBUG:\n    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\n"
        
        with open(urls_path, 'w') as f:
            f.write(urls_content)
        print("urls.py updated for media serving.")

def get_fields_interactive(existing_model=False):
    fields_code = ""
    print("\n" + "="*40)
    print(f"Add fields. Press <Enter> on 'property name' to stop.")
    print("="*40)
    
    if existing_model:
        confirm = input("Model exists. Do you want to add more fields? (yes/no) [no]: ").strip().lower()
        if confirm not in ['yes', 'y', 'true']:
             return ""

    while True:
        field_name = input("\n> New property name (or press <Enter> to stop): ").strip()
        if not field_name:
            break
            
        print("  Field types: string (default), text, int, float, bool, date, datetime, email, file, image")
        print("  Relations: foreignkey, onetoone, manytomany")
        field_type_input = input("  > Field type [string]: ").strip().lower()
        
        definition = ""
        is_relation = False
        
        # Field mapping
        if not field_type_input or field_type_input == 'string':
            max_len = input("  > Max Length [255]: ").strip()
            if not max_len: max_len = "255"
            definition = f"models.CharField(max_length={max_len})"
        elif field_type_input == 'text':
            definition = "models.TextField()"
        elif field_type_input in ['int', 'integer']:
            definition = "models.IntegerField()"
        elif field_type_input == 'float':
            definition = "models.FloatField()"
        elif field_type_input in ['bool', 'boolean']:
            definition = "models.BooleanField(default=False)"
        elif field_type_input == 'date':
            definition = "models.DateField()"
        elif field_type_input == 'datetime':
            definition = "models.DateTimeField(auto_now_add=True)"
        elif field_type_input == 'email':
            definition = "models.EmailField()"
        elif field_type_input == 'file':
            ensure_media_config()
            upload_to = input("  > Upload to [uploads/]: ").strip()
            if not upload_to: upload_to = "uploads/"
            definition = f"models.FileField(upload_to='{upload_to}')"
        elif field_type_input == 'image':
            ensure_media_config()
            upload_to = input("  > Upload to [uploads/]: ").strip()
            if not upload_to: upload_to = "uploads/"
            definition = f"models.ImageField(upload_to='{upload_to}')"
            print("  (Note: ImageField requires 'Pillow' library installed)")
        elif field_type_input == 'foreignkey':
            is_relation = True
            related_model = input("  > Related Model (e.g., 'auth.User' or 'OtherModel'): ").strip()
            definition = f"models.ForeignKey('{related_model}', on_delete=models.CASCADE)"
        elif field_type_input == 'onetoone':
            is_relation = True
            related_model = input("  > Related Model: ").strip()
            definition = f"models.OneToOneField('{related_model}', on_delete=models.CASCADE)"
        elif field_type_input == 'manytomany':
            is_relation = True
            related_model = input("  > Related Model: ").strip()
            definition = f"models.ManyToManyField('{related_model}')"
        
        else:
            print(f"  Unknown type '{field_type_input}', defaulting to CharField.")
            definition = "models.CharField(max_length=255)"
            
        nullable = input("  > Can this field be null in the database (nullable)? (yes/no) [no]: ").strip().lower()
        if nullable in ['yes', 'y', 'true']:
            if "()" in definition:
                definition = definition.replace("()", "(null=True, blank=True)")
            else:
                definition = definition[:-1] + ", null=True, blank=True)"
        
        fields_code += f"    {field_name} = {definition}\n"
        print(f"  ✓ Added field '{field_name}'")

    return fields_code

def list_routes():
    from django.urls import get_resolver
    from django.urls.resolvers import URLPattern, URLResolver

    def get_methods(callback):
        if hasattr(callback, 'view_class'):
            view_class = callback.view_class
            methods = []
            for method in ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']:
                if hasattr(view_class, method):
                    methods.append(method.upper())
            return ", ".join(methods) if methods else "ANY"
        
        if hasattr(callback, '_allowed_methods'):
            return ", ".join(callback._allowed_methods())
        
        return "ANY"

    def collect_urls(urls, parent_pattern=''):
        collected = []
        for url in urls:
            pattern = parent_pattern + str(url.pattern)
            if isinstance(url, URLResolver):
                collected.extend(collect_urls(url.url_patterns, pattern))
            elif isinstance(url, URLPattern):
                view_name = ""
                methods = get_methods(url.callback)
                
                if hasattr(url.callback, '__name__'):
                    view_name = url.callback.__name__
                elif hasattr(url.callback, '__class__'):
                    view_name = url.callback.__class__.__name__
                
                if hasattr(url.callback, 'view_class'):
                    view_name = url.callback.view_class.__name__

                name = url.name or ""
                collected.append((pattern, view_name, name, methods))
        return collected

    print("\n" + "="*100)
    print(f"{'URL PATTERN':<40} | {'METHODS':<25} | {'VIEW':<20} | {'NAME':<15}")
    print("-" * 100)
    
    resolver = get_resolver()
    routes = collect_urls(resolver.url_patterns)
    
    for pattern, view, name, methods in routes:
        # Simplify pattern string
        clean_pattern = pattern.replace('^', '').replace('$', '')
        print(f"{clean_pattern:<40} | {methods:<25} | {view:<20} | {name:<15}")
    print("="*100 + "\n")

def ensure_model_exists(app_name, model_name):
    models_path = os.path.join(app_name, 'models.py')
    with open(models_path, 'r') as f:
        content = f.read()
    
    if f"class {model_name}" in content:
        print(f"Model '{model_name}' already exists in '{app_name}'.")
        new_fields = get_fields_interactive(existing_model=True)
        if new_fields:
            # Edit existing class
            lines = content.splitlines()
            class_start_idx = -1
            
            # Find class definition
            for i, line in enumerate(lines):
                 if line.strip().startswith(f"class {model_name}"):
                     class_start_idx = i
                     break
            
            if class_start_idx != -1:
                # Find where to insert (before the next method or at end)
                # Simple logic: insert after class docstring or before first def
                insert_idx = -1
                for i in range(class_start_idx + 1, len(lines)):
                    if lines[i].strip().startswith("def "):
                         insert_idx = i
                         break
                    if lines[i].strip().startswith("class "): # Next class
                         insert_idx = i
                         break
                
                if insert_idx == -1:
                    insert_idx = len(lines)
                
                # Insert fields
                lines.insert(insert_idx, new_fields)
                
                with open(models_path, 'w') as f:
                    f.write("\n".join(lines))
                print(f"Model '{model_name}' updated.")
        return

    # NEW MODEL
    print(f"Creating model '{model_name}' in '{app_name}'...")
    fields_code = get_fields_interactive(existing_model=False)

    if not fields_code:
        fields_code = "    description = models.CharField(max_length=200, default='Description')\n    created_at = models.DateTimeField(auto_now_add=True)\n"

    model_code = f"\n\nclass {model_name}(models.Model):\n{fields_code}\n    def __str__(self):\n        # Try to return a sensical string representation\n        fields = dir(self)\n        if 'nom' in fields: return self.nom\n        if 'name' in fields: return self.name\n        if 'title' in fields: return self.title\n        if 'description' in fields: return str(self.description)\n"
    model_code += f"        return f'{model_name} object ({{self.pk}})'\n"

    with open(models_path, 'a') as f:
        f.write(model_code)
    print(f"\nModel '{model_name}' created under '{models_path}'.")

def get_model_class(app_name, model_name):
    try:
        app_config = apps.get_app_config(app_name)
        return app_config.get_model(model_name)
    except LookupError:
        print(f"Warning: Model '{model_name}' is not yet loaded in Django registry. Template generation might use generic fields.")
        return None

def generate_form(app_name, model_name):
    print(f"\nGenerating forms.py for {model_name}...")
    forms_path = os.path.join(app_name, 'forms.py')
    
    import_line = f"from .models import {model_name}\n"
    class_def = textwrap.dedent(f"""
    class {model_name}Form(forms.ModelForm):
        class Meta:
            model = {model_name}
            fields = '__all__'
    """)
    
    if not os.path.exists(forms_path):
        with open(forms_path, 'w') as f:
            f.write("from django import forms\n")
            f.write(import_line)
            f.write(class_def)
    else:
        with open(forms_path, 'r') as f:
            content = f.read()
        if f"class {model_name}Form" in content:
            print(f"Form for {model_name} already exists. Skipping.")
        else:
            with open(forms_path, 'a') as f:
                if "from django import forms" not in content:
                    f.write("\nfrom django import forms\n")
                if import_line.strip() not in content:
                    f.write(import_line)
                f.write(class_def)
    print("forms.py updated.")

def generate_views(app_name, model_name):
    print(f"\nGenerating views.py for {model_name}...")
    views_path = os.path.join(app_name, 'views.py')
    
    imports = textwrap.dedent(f"""
    from django.urls import reverse_lazy
    from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
    from .models import {model_name}
    from .forms import {model_name}Form
    """)
    
    views_code = textwrap.dedent(f"""
    class {model_name}ListView(ListView):
        model = {model_name}
        template_name = '{app_name}/{model_name.lower()}_list.html'
        context_object_name = '{model_name.lower()}s'

    class {model_name}DetailView(DetailView):
        model = {model_name}
        template_name = '{app_name}/{model_name.lower()}_detail.html'

    class {model_name}CreateView(CreateView):
        model = {model_name}
        form_class = {model_name}Form
        template_name = '{app_name}/{model_name.lower()}_form.html'
        success_url = reverse_lazy('{app_name}:{model_name.lower()}_list')

    class {model_name}UpdateView(UpdateView):
        model = {model_name}
        form_class = {model_name}Form
        template_name = '{app_name}/{model_name.lower()}_form.html'
        success_url = reverse_lazy('{app_name}:{model_name.lower()}_list')

    class {model_name}DeleteView(DeleteView):
        model = {model_name}
        template_name = '{app_name}/{model_name.lower()}_confirm_delete.html'
        success_url = reverse_lazy('{app_name}:{model_name.lower()}_list')
    """)

    if not os.path.exists(views_path):
        with open(views_path, 'w') as f:
            f.write("from django.shortcuts import render\n")
            f.write(imports)
            f.write(views_code)
    else:
        with open(views_path, 'r') as f:
            content = f.read()
        if f"class {model_name}ListView" in content:
            print(f"Views for {model_name} already exist. Skipping.")
        else:
            with open(views_path, 'a') as f:
                f.write("\n" + imports)
                f.write(views_code)
    print("views.py updated.")

def generate_urls(app_name, model_name):
    print(f"\nGenerating urls.py for {model_name}...")
    urls_path = os.path.join(app_name, 'urls.py')
    
    url_patterns_lines = [
        f"    path('{model_name.lower()}/', views.{model_name}ListView.as_view(), name='{model_name.lower()}_list'),",
        f"    path('{model_name.lower()}/<int:pk>/', views.{model_name}DetailView.as_view(), name='{model_name.lower()}_detail'),",
        f"    path('{model_name.lower()}/create/', views.{model_name}CreateView.as_view(), name='{model_name.lower()}_create'),",
        f"    path('{model_name.lower()}/<int:pk>/update/', views.{model_name}UpdateView.as_view(), name='{model_name.lower()}_update'),",
        f"    path('{model_name.lower()}/<int:pk>/delete/', views.{model_name}DeleteView.as_view(), name='{model_name.lower()}_delete'),",
    ]
    
    if not os.path.exists(urls_path):
        patterns_str = "\n".join(url_patterns_lines)
        content = f"from django.urls import path\nfrom . import views\n\napp_name = '{app_name}'\n\nurlpatterns = [\n{patterns_str}\n]\n"
        with open(urls_path, 'w') as f:
            f.write(content)
    else:
        with open(urls_path, 'r') as f:
            lines = f.readlines()
        
        if any(f"name='{model_name.lower()}_list'" in line for line in lines):
             print(f"URLs for {model_name} already exist. Skipping.")
        else:
            end_brace_index = -1
            urlpatterns_found = False
            for i, line in enumerate(lines):
                if 'urlpatterns = [' in line:
                    urlpatterns_found = True
                if urlpatterns_found and ']' in line:
                    end_brace_index = i
            
            if end_brace_index != -1:
                 for p in url_patterns_lines:
                    lines.insert(end_brace_index, p + "\n")
                    end_brace_index += 1
                 with open(urls_path, 'w') as f:
                    f.writelines(lines)
            else:
                print("Could not find 'urlpatterns = []' to append to.")

    # Automate root URL inclusion
    project_name = get_project_name()
    project_urls_path = os.path.join(project_name, 'urls.py')

    if os.path.exists(project_urls_path):
        with open(project_urls_path, 'r') as f:
            root_content = f.read()
        
        inclusion_line = f"path('{app_name}/', include('{app_name}.urls'))"
        if inclusion_line not in root_content:
            print(f"Registering '{app_name}' URLs in project root urls.py...")
            if "urlpatterns = [" in root_content:
                root_content = root_content.replace("urlpatterns = [", f"urlpatterns = [\n    {inclusion_line},")
                with open(project_urls_path, 'w') as f:
                    f.write(root_content)
                print("Project root urls.py updated.")

    print("urls.py updated.")

def generate_templates(app_name, model_name, model_class):
    print(f"\nGenerating templates for {model_name}...")
    templates_dir = os.path.join(app_name, 'templates', app_name)
    os.makedirs(templates_dir, exist_ok=True)
    
    if model_class:
        fields = [f.name for f in model_class._meta.fields if f.name != 'id']
        field_headers = "".join([f"                    <th>{f.capitalize()}</th>\n" for f in fields])
        field_cells = "".join([f"                    <td>{{{{ item.{f} }}}}</td>\n" for f in fields])
        detail_fields = "".join([f"            <li><strong>{f.capitalize()}:</strong> {{{{ object.{f} }}}}</li>\n" for f in fields])
    else:
        field_headers = "                    <th>Description</th>\n"
        field_cells = "                    <td>{{ item }}</td>\n"
        detail_fields = "            <li>{{ object }}</li>\n"

    list_html = textwrap.dedent(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{model_name} List</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-4">
        <h1>{model_name} List</h1>
        <a href="{{% url '{app_name}:{model_name.lower()}_create' %}}" class="btn btn-primary mb-3">Create New</a>
        <table class="table table-striped">
            <thead>
                <tr>
                    <th>ID</th>
{field_headers}                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                {{% for item in {model_name.lower()}s %}}
                <tr>
                    <td>{{{{ item.id }}}}</td>
{field_cells}                    <td>
                        <a href="{{% url '{app_name}:{model_name.lower()}_detail' item.pk %}}" class="btn btn-sm btn-info">View</a>
                        <a href="{{% url '{app_name}:{model_name.lower()}_update' item.pk %}}" class="btn btn-sm btn-warning">Edit</a>
                        <a href="{{% url '{app_name}:{model_name.lower()}_delete' item.pk %}}" class="btn btn-sm btn-danger">Delete</a>
                    </td>
                </tr>
                {{% endfor %}}
            </tbody>
        </table>
    </body>
    </html>
    """)
    with open(os.path.join(templates_dir, f'{model_name.lower()}_list.html'), 'w') as f:
        f.write(list_html)

    form_html = textwrap.dedent(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{model_name} Form</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-4">
        <h1>{{% if object %}}Update{{% else %}}Create{{% endif %}} {model_name}</h1>
        <form method="post" enctype="multipart/form-data">
            {{% csrf_token %}}
            {{{{ form.as_p }}}}
            <button type="submit" class="btn btn-success">Save</button>
            <a href="{{% url '{app_name}:{model_name.lower()}_list' %}}" class="btn btn-secondary">Cancel</a>
        </form>
    </body>
    </html>
    """)
    with open(os.path.join(templates_dir, f'{model_name.lower()}_form.html'), 'w') as f:
        f.write(form_html)

    detail_html = textwrap.dedent(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{model_name} Detail</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-4">
        <h1>{model_name} Details</h1>
        <ul>
            <li><strong>ID:</strong> {{{{ object.pk }}}}</li>
{detail_fields}        </ul>
        <a href="{{% url '{app_name}:{model_name.lower()}_list' %}}" class="btn btn-secondary">Back</a>
    </body>
    </html>
    """)
    with open(os.path.join(templates_dir, f'{model_name.lower()}_detail.html'), 'w') as f:
        f.write(detail_html)

    delete_html = textwrap.dedent(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Confirm Delete</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    </head>
    <body class="container mt-4">
        <h1>Delete {model_name}?</h1>
        <p>Are you sure you want to delete "{{{{ object }}}}"?</p>
        <form method="post">
            {{% csrf_token %}}
            <button type="submit" class="btn btn-danger">Confirm Delete</button>
            <a href="{{% url '{app_name}:{model_name.lower()}_list' %}}" class="btn btn-secondary">Cancel</a>
        </form>
    </body>
    </html>
    """)
    with open(os.path.join(templates_dir, f'{model_name.lower()}_confirm_delete.html'), 'w') as f:
        f.write(delete_html)
    print("Templates generated.")

def process_command(command, args):
    if command == 'make:app':
        if len(args) < 1:
            print("Usage: python django-cli.py make:app <app_name>")
            return
        ensure_app_exists(args[0])
    
    elif command == 'make:model':
         if len(args) < 2:
            print("Usage: python django-cli.py make:model <app_name> <model_name>")
            return
         app_name, model_name = args[0], args[1]
         ensure_app_exists(app_name)
         ensure_model_exists(app_name, model_name)
    
    elif command in ['make:crud', 'make:view', 'make:form']:
         if len(args) < 2:
            print(f"Usage: python django-cli.py {command} <app_name> <model_name>")
            return
         app_name, model_name = args[0], args[1]
         
         ensure_app_exists(app_name)
         ensure_model_exists(app_name, model_name)
         
         model_class = get_model_class(app_name, model_name)

         if command == 'make:form' or command == 'make:crud':
             generate_form(app_name, model_name)
         
         if command == 'make:view' or command == 'make:crud':
             generate_views(app_name, model_name)
             generate_urls(app_name, model_name)
             generate_templates(app_name, model_name, model_class)
             
    elif command == 'route:list':
        list_routes()
    
    if command in ['make:model', 'make:crud']:
         print("\\n" + "="*40)
         do_migrate = input("Do you want to apply database migrations now? (yes/no) [yes]: ").strip().lower()
         if do_migrate in ['', 'yes', 'y']:
             try:
                 print("Running makemigrations...")
                 subprocess.check_call([sys.executable, 'manage.py', 'makemigrations'])
                 print("Running migrate...")
                 subprocess.check_call([sys.executable, 'manage.py', 'migrate'])
                 print("Migrations applied successfully.")
             except subprocess.CalledProcessError:
                 print("Error applying migrations.")

    elif command == 'init:project':
        # New init command
        project_name = os.path.basename(os.getcwd())
        # sanitize name slightly if needed (basic check)
        project_name = project_name.replace('-', '_').replace(' ', '_')
        
        print(f"Initializing Django project '{project_name}' in current directory...")
        try:
            # Check if project already exists
            if os.path.exists('manage.py'):
                print("Error: manage.py found. A project likely already exists here.")
                return

            subprocess.check_call(['django-admin', 'startproject', project_name, '.'])
            print(f"Project '{project_name}' initialized successfully.")
        except subprocess.CalledProcessError:
             print("Failed to run startproject. Ensure django-admin is in your PATH.")
        except FileNotFoundError:
             print("Error: django-admin command not found. Is Django installed? (pip install django)")


if __name__ == "__main__":
    setup_django()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        args = sys.argv[2:]
        process_command(command, args)
    else:
        print("Django CLI Tool")
        print("Usage:")
        print("  python django-cli.py make:app <app_name>")
        print("  python django-cli.py make:model <app_name> <model_name>")
        print("  python django-cli.py make:form <app_name> <model_name>")
        print("  python django-cli.py make:view <app_name> <model_name>")
        print("  python django-cli.py make:crud <app_name> <model_name>")
        print("  python django-cli.py route:list")
        print("  python django-cli.py init:project  (Initialize new project in current dir)")

