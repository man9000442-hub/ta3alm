<div align="center">

# 🎓 منصة تَعَلَّم (Ta3alm)
### منصة تعليمية متكاملة للمعلمين والطلاب في مصر

[![Django](https://img.shields.io/badge/Django-6.0-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-Private-red?style=for-the-badge)](LICENSE)

**[🌐 الموقع الرسمي](https://ta3alm.online)** | **[📱 تواصل معنا](#)**

</div>

---

## 📖 نبذة عن المنصة

**تَعَلَّم** هي منصة تعليمية متكاملة تصل بين **المعلمين** و**طلابهم** في مصر. توفر المنصة بيئة متكاملة لإدارة المجموعات التعليمية، ونشر المحاضرات والامتحانات، ومتابعة أداء الطلاب، ومعالجة المدفوعات.

### 🌟 المميزات الرئيسية

| الفئة | المميزات |
|-------|---------|
| 👨‍🏫 **للمعلم** | لوحة تحكم متكاملة، إدارة مجموعات متعددة، نشر محاضرات ومحتوى PDF، إنشاء امتحانات إلكترونية، تتبع الأداء، إدارة مساعدين |
| 👩‍🎓 **للطالب** | الاشتراك في المجموعات، مشاهدة المحاضرات بأكواد آمنة، حل الامتحانات، الاشتراك في الحزم التعليمية الأونلاين |
| 💳 **للدفع** | تكامل مع Paymob (كارت + محفظة) لاشتراكات المعلمين والحزم التعليمية |
| 🤖 **للبوت** | API متكامل لبوت واتساب (التحقق، استعادة كلمة المرور، ربط الحسابات) |
| 🔐 **للأمان** | نظام أدوار متكامل (طالب/معلم/مساعد/سنتر/مسؤول)، تسجيل دخول بجوجل |

---

## 🏗️ هيكلية المشروع

```
ta3alm/
├── 📁 ta3alm_project/          # إعدادات Django الرئيسية
│   ├── settings.py             # ✅ الإعدادات تُقرأ من .env
│   ├── urls.py                 # التوجيه الرئيسي مع دعم i18n
│   ├── middleware.py           # TokenAuth, Ban, Maintenance
│   └── wsgi.py / asgi.py
│
├── 📁 core/                    # نواة المنصة
│   ├── models.py               # SiteSetting, Notification, Subject
│   ├── constants.py            # ✅ GRADE_CHOICES, ROLE_CHOICES (مصدر موحّد)
│   ├── views.py                # الصفحة الرئيسية، لوحة المالك
│   ├── context_processors.py   # الإشعارات لكل الصفحات
│   └── sitemaps.py             # SEO Sitemaps
│
├── 📁 accounts/                # نظام المستخدمين
│   ├── models.py               # User (AbstractUser + role), StudentProfile
│   ├── signals.py              # ضبط Role عند التسجيل عبر AllAuth
│   ├── views.py                # إكمال البيانات، توجيه ما بعد الدخول
│   └── api_views.py            # Auth API للموبايل
│
├── 📁 teachers/                # نظام المعلمين (الأضخم)
│   ├── models.py               # TeacherProfile, Group, Lecture, VideoCode,
│   │                           # CoursePackage, SubscriptionPlan, Wallet
│   ├── views.py                # إدارة المجموعات، الامتحانات، المحاضرات، الدفع
│   ├── forms.py                # نماذج المعلم
│   └── api_views.py / urls.py
│
├── 📁 students/                # نظام الطلاب
│   ├── models.py               # Enrollment, PerformanceLog,
│   │                           # PackageEnrollment, VideoViewTracking
│   └── views.py                # لوحة الطالب، الامتحانات، الحزم
│
├── 📁 exams/                   # نظام الامتحانات
│   ├── models.py               # Exam, Question, ExamResult
│   └── views.py
│
├── 📁 assistants/              # نظام المساعدين
│   └── models.py               # AssistantProfile, AssistantJob
│
├── 📁 bot_api/                 # API بوت واتساب
│   ├── views.py                # ResolveUser, VerifyNID, ChangePassword, LinkLid
│   ├── permissions.py          # IsBotService (Header-based Auth)
│   └── models.py               # WhatsAppLink
│
├── 📁 templates/               # قوالب HTML (RTL Arabic)
├── 📁 static/                  # CSS, JS, الصور الثابتة
├── 📁 locale/                  # ملفات الترجمة (ar, en)
├── 📁 media/                   # ملفات المستخدمين (محلياً) → Supabase (إنتاج)
├── .env.example                # ✅ قالب المتغيرات البيئية
├── requirements.txt            # مكتبات Python
├── runtime.txt                 # إصدار Python لـ Railway/Koyeb
└── manage.py
```

---

## ⚙️ متطلبات التشغيل (Requirements)

| الأداة | الإصدار | الملاحظة |
|-------|---------|---------|
| Python | 3.12+ | مطلوب |
| Django | 6.0 | مطلوب |
| PostgreSQL | 14+ | للإنتاج (SQLite للتطوير) |
| Redis | 6+ | للـ Cache في الإنتاج (اختياري) |
| pip | آخر إصدار | مطلوب |

---

## 🚀 دليل التثبيت (Installation Guide)

### 1. استنساخ المشروع

```bash
git clone https://github.com/YOUR_USERNAME/ta3alm.git
cd ta3alm
```

### 2. إنشاء البيئة الافتراضية

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. تثبيت المكتبات

```bash
pip install -r requirements.txt
```

### 4. إعداد ملف `.env`

```bash
# انسخ القالب
cp .env.example .env

# ثم عدّل .env بمحرر النصوص
notepad .env        # Windows
nano .env           # Linux
```

### 5. تطبيق الـ Migrations

```bash
python manage.py migrate
```

### 6. إنشاء حساب المسؤول

```bash
python manage.py createsuperuser
```

### 7. جمع الملفات الثابتة (للإنتاج فقط)

```bash
python manage.py collectstatic
```

### 8. تشغيل السيرفر

```bash
# التطوير
python manage.py runserver

# الإنتاج (مع Gunicorn)
gunicorn ta3alm_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

---

## 🔐 شرح المتغيرات البيئية (Environment Variables)

> ⚠️ **مهم جداً:** لا ترفع ملف `.env` على Git أبداً! أضف `.env` لملف `.gitignore`.

| المتغير | الوصف | مثال |
|---------|------|------|
| `SECRET_KEY` | المفتاح السري لـ Django (50+ حرف عشوائي) | `django-insecure-...` |
| `DEBUG` | وضع التطوير (`True`) أو الإنتاج (`False`) | `False` |
| `ALLOWED_HOSTS` | النطاقات المسموح بها (مفصولة بفاصلة) | `ta3alm.online,www.ta3alm.online` |
| `USE_SQLITE` | استخدام SQLite (`True`) أو PostgreSQL (`False`) | `True` |
| `DB_NAME` | اسم قاعدة البيانات (PostgreSQL) | `postgres` |
| `DB_USER` | مستخدم قاعدة البيانات | `postgres.xxx` |
| `DB_PASSWORD` | كلمة مرور قاعدة البيانات | `your-password` |
| `DB_HOST` | عنوان سيرفر قاعدة البيانات | `aws-1-eu-central-1.pooler.supabase.com` |
| `DB_PORT` | منفذ قاعدة البيانات | `6543` |
| `AWS_ACCESS_KEY_ID` | مفتاح S3/Supabase Storage | `20750f...` |
| `AWS_SECRET_ACCESS_KEY` | السر الخاص لـ S3/Supabase | `df5c74...` |
| `AWS_S3_ENDPOINT_URL` | رابط Endpoint التخزين | `https://...supabase.co/storage/v1/s3` |
| `AWS_STORAGE_BUCKET_NAME` | اسم البوكت | `media` |
| `PAYMOB_API_KEY` | مفتاح Paymob | `ZXlKa...` |
| `PAYMOB_INTEGRATION_ID` | رقم Integration ID للكارت | `5450551` |
| `PAYMOB_IFRAME_ID` | رقم iFrame للكارت | `991968` |
| `PAYMOB_WALLET_INTEGRATION_ID` | Integration ID للمحفظة | `5462707` |
| `BOT_API_KEY` | مفتاح بوت واتساب (32+ حرف) | `random-secret-key` |
| `CORS_ALLOWED_ORIGINS` | النطاقات المسموح بها للـ API | `https://ta3alm.online` |
| `REDIS_URL` | رابط Redis للـ Cache (اختياري) | `redis://localhost:6379/1` |

---

## 🛠️ التكنولوجيا المستخدمة (Tech Stack)

### Backend
| المكتبة | الوظيفة |
|---------|--------|
| **Django 6.0** | إطار العمل الرئيسي |
| **django-allauth** | المصادقة (Email + Google OAuth) |
| **Django REST Framework** | API للموبايل والبوت |
| **django-storages + boto3** | رفع الملفات لـ Supabase S3 |
| **Gunicorn** | WSGI Server للإنتاج |
| **Whitenoise** | خدمة الملفات الثابتة |
| **psycopg2-binary** | اتصال PostgreSQL |
| **python-dotenv** | تحميل المتغيرات البيئية |
| **Pillow** | معالجة الصور |
| **cryptography / PyJWT** | التشفير والتوكن |

### Infrastructure & Services
| الخدمة | الاستخدام |
|--------|---------|
| **Supabase** | قاعدة بيانات PostgreSQL + تخزين الملفات (S3) |
| **Railway / Koyeb** | استضافة التطبيق |
| **Paymob** | بوابة الدفع (كارت + محفظة) |
| **Google OAuth** | تسجيل الدخول بجوجل |

---

## 🗂️ نظام الأدوار (User Roles)

```
👑 admin (مسؤول المنصة)
    └── لوحة تحكم كاملة، إدارة الاشتراكات، وضع الصيانة

👨‍🏫 teacher (معلم)
    ├── إدارة مجموعاته (محاضرات، امتحانات، طلاب، أداء)
    ├── حزم تعليمية أونلاين
    └── محفظة مالية وطلبات سحب

🤝 assistant (مساعد)
    └── صلاحيات محدودة (إدارة طلاب / امتحانات / فيديوهات) يُحددها المعلم

👩‍🎓 student (طالب)
    ├── الاشتراك في مجموعات المعلمين
    ├── مشاهدة المحاضرات بأكواد
    └── الاشتراك في الحزم التعليمية

🏫 center (سنتر) — [قيد التطوير]
```

---

## 📋 قائمة التحسينات والإصلاحات المطلوبة (TODO)

### 🔴 أولوية حرجة
- [ ] تفعيل Redis بدلاً من locmem Cache في الإنتاج
- [ ] إنشاء migration للـ Database Indexes الجديدة (`python manage.py makemigrations`)
- [ ] تفعيل SSL في الإنتاج (`SECURE_SSL_REDIRECT=True` عبر .env)
- [ ] اختبار Bot API بعد تغيير BOT_API_KEY لقيمة حقيقية

### 🟠 أولوية عالية
- [ ] كتابة Unit Tests للـ models الأساسية (Enrollment, TeacherProfile)
- [ ] إضافة `django-debug-toolbar` لبيئة التطوير
- [ ] نقل منطق Paymob لـ `services/paymob_service.py`
- [ ] تحويل `teachers/views.py` لـ Class-Based Views أو Service Layer
- [ ] إضافة Rate Limiting على نماذج الدخول والتسجيل
- [ ] تفعيل `centers` app أو حذفها نهائياً

### 🟡 تحسينات مستقبلية
- [ ] إضافة Celery + Redis لمهام الخلفية (الإشعارات، الإيميلات)
- [ ] إضافة API Documentation (drf-spectacular / Swagger)
- [ ] إضافة WebSockets للإشعارات الفورية
- [ ] تطبيق CDN للـ Static Files
- [ ] إضافة Sentry لمراقبة الأخطاء في الإنتاج

---

## 📁 ملفات مهمة

| الملف | الوصف |
|-------|------|
| [`core/constants.py`](core/constants.py) | **مصدر موحّد** لـ `GRADE_CHOICES` و `ROLE_CHOICES` |
| [`ta3alm_project/middleware.py`](ta3alm_project/middleware.py) | TokenAuth, Ban, Maintenance middleware |
| [`ta3alm_project/settings.py`](ta3alm_project/settings.py) | الإعدادات الرئيسية (كلها من `.env`) |
| [`.env.example`](.env.example) | قالب المتغيرات البيئية — انسخه لـ `.env` |

---

## 🤝 المساهمة في التطوير

1. **Fork** الريبو
2. أنشئ **branch** للميزة: `git checkout -b feature/amazing-feature`
3. **Commit** التغييرات: `git commit -m 'Add amazing feature'`
4. **Push** للـ branch: `git push origin feature/amazing-feature`
5. افتح **Pull Request**

---

## 📄 الترخيص

هذا المشروع ملكية خاصة. جميع الحقوق محفوظة.

---

<div align="center">
  صُنع بـ ❤️ في مصر
</div>
