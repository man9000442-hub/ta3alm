import os
import sys
import django
from django.test import Client
from django.urls import get_resolver
from django.contrib.auth import get_user_model
import traceback

# Setup Django Environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ta3alm_project.settings')
django.setup()

User = get_user_model()
client = Client(SERVER_NAME='127.0.0.1')

def get_all_urls():
    urls = []
    resolver = get_resolver()
    
    def extract_urls(urlpatterns, prefix=''):
        for pattern in urlpatterns:
            if hasattr(pattern, 'url_patterns'):
                # Include
                extract_urls(pattern.url_patterns, prefix + str(pattern.pattern))
            else:
                url = prefix + str(pattern.pattern)
                # Remove regex anchors and simplify
                url = url.replace('^', '').replace('$', '').replace('\\Z', '')
                
                # Only keep URLs that don't have complex arguments (like <int:id>) for a basic scan,
                # or we can mock them. Let's filter out URLs with '<' or '(?P<' for now, 
                # or replace them with a dummy value like '1' or 'test'.
                if '<' in url or '(?P<' in url:
                    # Replace simple <int:id> with 1
                    import re
                    url = re.sub(r'<int:\w+>', '1', url)
                    url = re.sub(r'<str:\w+>', 'test', url)
                    url = re.sub(r'<uuid:\w+>', '00000000-0000-0000-0000-000000000000', url)
                    
                    # If it still has regex groups, we skip it
                    if '<' in url or '(' in url:
                        continue
                
                if not url.startswith('/'):
                    url = '/' + url
                
                # Add language prefix if it doesn't have it (for i18n_patterns)
                if not url.startswith('/ar/') and not url.startswith('/en/') and not url.startswith('/api/'):
                    url = '/ar' + url
                
                urls.append(url)
                
    extract_urls(resolver.url_patterns)
    # Remove duplicates
    return list(set(urls))


def setup_test_users():
    users = {}
    
    # 1. Superuser
    su, _ = User.objects.get_or_create(username='test_superuser', email='su@test.com', defaults={'is_superuser': True, 'is_staff': True})
    if not su.check_password('password'):
        su.set_password('password')
        su.save()
    users['superuser'] = su
    
    # 2. Admin
    admin, _ = User.objects.get_or_create(username='test_admin', email='admin@test.com', defaults={'role': 'admin'})
    if not admin.check_password('password'):
        admin.set_password('password')
        admin.save()
    users['admin'] = admin
    
    # 3. Teacher
    teacher, _ = User.objects.get_or_create(username='test_teacher', email='teacher@test.com', defaults={'role': 'teacher'})
    if not teacher.check_password('password'):
        teacher.set_password('password')
        teacher.save()
    users['teacher'] = teacher
    
    # 4. Student
    student, _ = User.objects.get_or_create(username='test_student', email='student@test.com', defaults={'role': 'student'})
    if not student.check_password('password'):
        student.set_password('password')
        student.save()
    users['student'] = student
    
    return users


def run_scan():
    print("Starting Comprehensive Project Scan...")
    
    urls = get_all_urls()
    users = setup_test_users()
    
    print(f"Found {len(urls)} testable endpoints.")
    
    roles_to_test = ['anonymous', 'student', 'teacher', 'admin', 'superuser']
    
    errors_found = []
    
    for url in urls:
        # print(f"\\nTesting URL: {url}")
        
        for role in roles_to_test:
            # Create a fresh client for each role to avoid database locking on logout/flush
            client = Client(SERVER_NAME='127.0.0.1')
            
            if role != 'anonymous':
                client.force_login(users[role])
            
            try:
                # We do a GET request
                response = client.get(url, follow=True)
                
                if response.status_code >= 500:
                    error_msg = f"[ERROR 500] at {url} (Role: {role})"
                    print(error_msg)
                    errors_found.append(error_msg)
                elif response.status_code == 404:
                    # 404 is fine (might be a dummy ID we provided)
                    pass
                elif response.status_code == 403:
                    # 403 is fine (permission denied)
                    pass
                else:
                    # print(f"  [OK] {role}: {response.status_code}")
                    pass
                    
            except Exception as e:
                error_msg = f"[EXCEPTION] at {url} (Role: {role}): {type(e).__name__} - {str(e)}"
                print(error_msg)
                errors_found.append(error_msg)
                # traceback.print_exc()
                
    print("\\n" + "="*50)
    if errors_found:
        print(f"Scan completed with {len(errors_found)} potential issues:")
        for err in errors_found:
            print(err)
    else:
        print("Scan completed successfully. No 500 errors found!")


if __name__ == "__main__":
    run_scan()
