from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Exam, Question
from .forms import QuestionForm
from teachers.views import get_group_permission # <--- استيراد الدالة
from django import forms
from django.db.models import Q
from assistants.models import AssistantJob
from students.models import PackageExamResult
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Exam, Question, ExamResult
from .forms import QuestionForm
from teachers.models import CoursePackage
from students.models import PackageExamResult # هام جداً
from assistants.models import AssistantJob
from teachers.views import get_group_permission # استيراد دالة الصلاحيات

@login_required
def exam_manage(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # متغيرات التحكم
    is_owner = False
    back_url = None
    back_id = None
    teacher = None
    results = []

    # ==========================================
    # 1. تحديد السياق (مجموعة أم حزمة؟)
    # ==========================================
    if exam.group:
        # أ) حالة امتحان مجموعة (Offline)
        group_obj, is_owner = get_group_permission(request, exam.group.id, permission_type='exams')
        if not group_obj:
            messages.error(request, "صلاحية غير كافية.")
            return redirect('home')
        
        teacher = exam.group.teacher
        back_url = 'group_exams'
        back_id = exam.group.id
        
        # نتائج المجموعة
        results = exam.results.all().select_related('student__user').order_by('-score')

    else:
        # ب) حالة امتحان حزمة (Online)
        package = exam.packages.first()
        
        if package:
            teacher = package.teacher
            back_url = 'teacher_package_detail'
            back_id = package.id
            
            # التحقق من الملكية
            if teacher.user == request.user:
                is_owner = True
            elif request.user.role == 'assistant':
                job = AssistantJob.objects.filter(assistant__user=request.user, teacher=teacher, is_active=True).first()
                if job and job.can_manage_packages:
                    is_owner = False
                else:
                    messages.error(request, "ليس لديك صلاحية إدارة الحزم.")
                    return redirect('home')
            else:
                return redirect('home')
            
            # نتائج الحزمة (من الجدول المنفصل)
            results = PackageExamResult.objects.filter(exam=exam).select_related('student__user').order_by('-score')
        else:
            return redirect('home')

    # ==========================================
    # 2. التحقق من الاشتراك (للمساعد)
    # ==========================================
    if not is_owner and teacher and not teacher.has_active_subscription():
        return render(request, 'students/teacher_unavailable.html', {'teacher_name': teacher.user.first_name})

    # ==========================================
    # 3. التحقق من صلاحية الصور (الباقة)
    # ==========================================
    allow_images = False
    if teacher and teacher.current_plan and teacher.current_plan.allow_question_images:
        allow_images = True

    # ==========================================
    # 4. معالجة إضافة سؤال (POST)
    # ==========================================
    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            
            # معالجة الصورة
            if 'image' in request.FILES:
                if allow_images:
                    question.image = request.FILES['image']
                else:
                    # لو الباقة لا تسمح، نتجاهل الصورة وننبه المستخدم
                    messages.warning(request, "تم حفظ السؤال، ولكن تم تجاهل الصورة لأن باقتك الحالية لا تدعم ذلك.")
            
            question.save()
            
            # رسالة نجاح (إذا لم يكن هناك تحذير سابق)
            storage = messages.get_messages(request)
            if not storage: 
                messages.success(request, "تم إضافة السؤال بنجاح.")
                
            return redirect('exam_manage', exam_id=exam.id)
    else:
        form = QuestionForm()

    # ==========================================
    # 5. البحث في النتائج
    # ==========================================
    q = request.GET.get('q')
    if q:
        results = results.filter(
            Q(student__user__first_name__icontains=q) |
            Q(student__user__last_name__icontains=q) |
            Q(student__user__phone__icontains=q)
        )

    context = {
        'exam': exam,
        'questions': exam.questions.all(),
        'results': results,
        'form': form,
        'is_owner': is_owner,
        'back_url': back_url,
        'back_id': back_id,
        'allow_images': allow_images # هام جداً للمودال
    }
    return render(request, 'exams/manage.html', context)

@login_required
def add_question_page(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # تحديد المعلم
    teacher = None
    if exam.group:
        teacher = exam.group.teacher
        group_obj, is_owner = get_group_permission(request, exam.group.id, permission_type='exams')
        if not group_obj: return redirect('home')
    else:
        pkg = exam.packages.first()
        if pkg: teacher = pkg.teacher
        # (يمكنك إضافة نفس التحقق من الصلاحيات هنا للحزم)

    # التحقق من صلاحية الصور
    allow_images = False
    if teacher and teacher.current_plan and teacher.current_plan.allow_question_images:
        allow_images = True

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.exam = exam
            
            # حفظ الصورة فقط لو مسموح
            if 'image' in request.FILES:
                if allow_images:
                    question.image = request.FILES['image']
                else:
                    messages.warning(request, "تم تجاهل الصورة لأن باقتك لا تسمح.")
            
            question.save()
            messages.success(request, "تم إضافة السؤال بنجاح.")
            return redirect('exam_manage', exam_id=exam.id)
    else:
        form = QuestionForm()

    return render(request, 'exams/add_question.html', {
        'form': form, 
        'exam': exam, 
        'allow_images': allow_images
    })


@login_required
def edit_question_page(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    exam = question.exam
    
    # تحديد المعلم
    teacher = None
    if exam.group:
        teacher = exam.group.teacher
        group_obj, is_owner = get_group_permission(request, exam.group.id, permission_type='exams')
        if not group_obj: return redirect('home')
    else:
        pkg = exam.packages.first()
        if pkg: teacher = pkg.teacher

    # التحقق من صلاحية الصور
    allow_images = False
    if teacher and teacher.current_plan and teacher.current_plan.allow_question_images:
        allow_images = True

    if request.method == 'POST':
        form = QuestionForm(request.POST, request.FILES, instance=question)
        if form.is_valid():
            # 1. معالجة حذف الصورة (Checkbox)
            if request.POST.get('image-clear') == 'on':
                question.image = None
            
            # 2. معالجة رفع صورة جديدة
            if 'image' in request.FILES:
                if allow_images:
                    question.image = request.FILES['image']
                else:
                    messages.warning(request, "تم تجاهل الصورة الجديدة.")
            
            # 3. حفظ باقي البيانات
            form.save() # سيحفظ التغييرات (بما فيها الحذف إذا تم تعيينه لـ None)
            
            messages.success(request, "تم تحديث السؤال.")
            return redirect('exam_manage', exam_id=exam.id)
    else:
        form = QuestionForm(instance=question)

    return render(request, 'exams/edit_question.html', {
        'form': form, 
        'question': question, 
        'exam': exam,
        'allow_images': allow_images
    })# 1. تفعيل أو إيقاف الامتحان


@login_required
def toggle_exam_status(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # 1. التحقق من الصلاحيات والاشتراك
    is_allowed = False
    
    # أ) امتحان مجموعة
    if exam.group:
        group_obj, is_owner = get_group_permission(request, exam.group.id, permission_type='exams')
        if group_obj:
            if not is_owner and not group_obj.teacher.has_active_subscription():
                return render(request, 'students/teacher_unavailable.html', {'teacher_name': group_obj.teacher.user.first_name})
            is_allowed = True
            
    # ب) امتحان حزمة
    else:
        package = exam.packages.first()
        if package:
            # التحقق من المالك أو المساعد
            if package.teacher.user == request.user:
                is_allowed = True
            elif request.user.role == 'assistant':
                job = AssistantJob.objects.filter(assistant__user=request.user, teacher=package.teacher, can_manage_packages=True).first()
                if job: is_allowed = True
            
            # التحقق من الاشتراك
            if is_allowed and package.teacher.user != request.user and not package.teacher.has_active_subscription():
                return render(request, 'students/teacher_unavailable.html', {'teacher_name': package.teacher.user.first_name})

    if not is_allowed:
        messages.error(request, "ليس لديك صلاحية لتعديل حالة الامتحان.")
        return redirect('home')

    # 2. تنفيذ التغيير
    exam.is_active = not exam.is_active
    exam.save()
    
    status = "تفعيل" if exam.is_active else "إغلاق"
    messages.success(request, f"تم {status} الامتحان بنجاح.")
    return redirect('exam_manage', exam_id=exam.id)


# 2. حذف الامتحان بالكامل
@login_required
def delete_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    group_id = exam.group.id # نحفظ الرقم للعودة
    
    # التحقق من الصلاحية
    group_obj, is_owner = get_group_permission(request, group_id, permission_type='exams')
    
    # ملاحظة: قد ترغب في منع المساعد من الحذف النهائي، والسماح للمالك فقط
    # لو عايز تمنع المساعد: if not is_owner: return redirect...
    # لكن حالياً سنسمح له طالما يملك صلاحية الامتحانات
    
    if not group_obj:
        messages.error(request, "ليس لديك صلاحية لحذف الامتحان.")
        return redirect('home')

    if not is_owner and not group_obj.teacher.has_active_subscription():
        return render(request, 'students/teacher_unavailable.html', {'teacher_name': group_obj.teacher.user.first_name})

    # تنفيذ الحذف
    exam.delete()
    messages.success(request, "تم حذف الامتحان نهائياً.")
    return redirect('group_exams', group_id=group_id) # العودة لصفحة الامتحانات
# 3. حذف سؤال معين
@login_required
def delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id)
    exam = question.exam
    
    # تحقق من الصلاحية
    group_obj, is_owner = get_group_permission(request, exam.group.id, permission_type='exams')
    if not group_obj:
        return redirect('home')

    question.delete()
    messages.success(request, "تم حذف السؤال.")
    return redirect('exam_manage', exam_id=exam.id)

# 4. تعديل سؤال (يحتاج صفحة خاصة)
@login_required
def edit_question(request, question_id):
    # جلب السؤال
    question = get_object_or_404(Question, id=question_id)
    exam = question.exam
    
    # 1. التحقق من الصلاحية (نطلب صلاحية exams)
    # لاحظ: نرسل exam.group.id
    group_obj, is_owner = get_group_permission(request, exam.group.id, permission_type='exams')
    
    if not group_obj:
        messages.error(request, "ليس لديك صلاحية لتعديل هذا السؤال.")
        return redirect('home')

    # 2. التحقق من الاشتراك (للمساعد)
    if not is_owner and not group_obj.teacher.has_active_subscription():
        return render(request, 'students/teacher_unavailable.html', {
            'teacher_name': group_obj.teacher.user.first_name
        })

    # 3. معالجة التعديل (POST)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=question)
        if form.is_valid():
            form.save()
            messages.success(request, "تم تعديل السؤال بنجاح.")
            return redirect('exam_manage', exam_id=exam.id)
    else:
        form = QuestionForm(instance=question)

        # تحديد المعلم للتحقق من الباقة
    teacher = None
    if exam.group:
        teacher = exam.group.teacher
    else:
        pkg = exam.packages.first()
        if pkg: teacher = pkg.teacher

    allow_images = False
    if teacher and teacher.current_plan and teacher.current_plan.allow_question_images:
        allow_images = True

    # تمرير المتغير للكونتكس
    
        
    return render(request, 'exams/edit_question.html', {'form': form, 'question': question,'allow_images': allow_images})


# في exams/views.py

@login_required
def exam_manage(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)
    
    # 1. تحديد المالك والصلاحيات ومصدر العودة
    is_owner = False
    back_url = None
    back_id = None
    teacher = None
    results = []

    # أ) حالة امتحان مجموعة
    if exam.group:
        group_obj, is_owner = get_group_permission(request, exam.group.id, permission_type='exams')
        if not group_obj:
            messages.error(request, "صلاحية غير كافية.")
            return redirect('home')
        
        teacher = exam.group.teacher
        back_url = 'group_exams'
        back_id = exam.group.id
        results = exam.results.all().select_related('student__user').order_by('-score')

    # ب) حالة امتحان حزمة
    else:
        package = exam.packages.first()
        if package:
            teacher = package.teacher
            back_url = 'teacher_package_detail'
            back_id = package.id
            
            if teacher.user == request.user:
                is_owner = True
            elif request.user.role == 'assistant':
                job = AssistantJob.objects.filter(assistant__user=request.user, teacher=teacher, is_active=True).first()
                if job and job.can_manage_packages:
                    is_owner = False
                else:
                    return redirect('home')
            else:
                return redirect('home')
            
            results = PackageExamResult.objects.filter(exam=exam).select_related('student__user').order_by('-score')
        else:
            return redirect('home')

    # 2. التحقق من الاشتراك
    if not is_owner and teacher and not teacher.has_active_subscription():
        return render(request, 'students/teacher_unavailable.html', {'teacher_name': teacher.user.first_name})

    # 3. تحديد صلاحية الصور
    allow_images = False
    if teacher and teacher.current_plan and teacher.current_plan.allow_question_images:
        allow_images = True

    # 4. معالجة إضافة الأسئلة (من المودال في نفس الصفحة - اختياري)
    form = QuestionForm() # للعرض فقط، الإضافة الفعلية في الصفحة المنفصلة

    # البحث في النتائج
    q = request.GET.get('q')
    if q:
        results = results.filter(
            Q(student__user__first_name__icontains=q) |
            Q(student__user__last_name__icontains=q)
        )

    context = {
        'exam': exam,
        'questions': exam.questions.all(),
        'results': results,
        'form': form,
        'is_owner': is_owner,
        'back_url': back_url,
        'back_id': back_id,
        'allow_images': allow_images # هام للمودال لو استخدمته
    }
    return render(request, 'exams/manage.html', context)


# --- AI Exam Generation Views ---

from core.models import Subject, CurriculumLesson, CurriculumUnit, GRADE_CHOICES, TERM_CHOICES
from .models import BankQuestion
from teachers.models import Group
from services.gemini_service import generate_exam_questions

@login_required
def ai_generate_exam(request):
    # --- فحص: هل الذكاء الاصطناعي مفعّل عالمياً؟ ---
    from core.models import SiteSetting as _SS
    if not _SS.load().is_ai_enabled:
        messages.error(request, "⛔ ميزات الذكاء الاصطناعي معطّلة حالياً من قِبَل الإدارة.")
        return redirect('teacher_dashboard')

    teacher = request.user.teacher_profile
    if not teacher.can_generate_ai_exam():
        messages.error(request, "لقد استنفدت رصيدك لتوليد الامتحانات بالذكاء الاصطناعي هذا الشهر، أو أن باقتك لا تسمح بذلك.")
        return redirect('teacher_dashboard')


    group_id = request.GET.get('group_id')
    group = None
    if group_id:
        group = get_object_or_404(Group, id=group_id, teacher=teacher)

    if request.method == 'POST':
        subject_id = request.POST.get('subject')
        grade = request.POST.get('grade')
        term = request.POST.get('term')
        lesson_ids_raw = request.POST.getlist('lessons')
        difficulty = request.POST.get('difficulty')
        num_questions = int(request.POST.get('num_questions', 5))
        extra_notes = request.POST.get('extra_notes', '')
        exam_title = request.POST.get('exam_title', f"امتحان ذكاء اصطناعي - {grade}")

        subject = get_object_or_404(Subject, id=subject_id)
        
        unit_ids = []
        actual_lesson_ids = []
        for item in lesson_ids_raw:
            if item.startswith('unit_'):
                unit_ids.append(int(item.replace('unit_', '')))
            else:
                actual_lesson_ids.append(int(item))

        lessons = CurriculumLesson.objects.filter(
            Q(id__in=actual_lesson_ids) | Q(unit_id__in=unit_ids)
        )

        if not lessons.exists():
            messages.error(request, "يرجى اختيار درس واحد على الأقل.")
            return redirect(request.path + f"?group_id={group_id}" if group_id else request.path)

        # Call Gemini
        try:
            questions = generate_exam_questions(
                grade_name=dict(GRADE_CHOICES).get(grade, grade),
                subject_name=subject.name,
                term_name=dict(TERM_CHOICES).get(term, term),
                lessons_list=lessons,
                difficulty=difficulty,
                num_questions=num_questions,
                extra_notes=extra_notes
            )
            
            # Save to session for review
            request.session['ai_questions'] = questions
            request.session['ai_exam_data'] = {
                'title': exam_title,
                'group_id': group_id,
                'subject_id': subject_id,
                'grade': grade,
                'term': term,
                'difficulty': difficulty,
                'lesson_ids': list(lessons.values_list('id', flat=True))
            }
            return redirect('ai_review_exam')

        except Exception as e:
            messages.error(request, str(e))
            return redirect(request.path + f"?group_id={group_id}" if group_id else request.path)

    context = {
        'subjects': Subject.objects.all(),
        'grades': GRADE_CHOICES,
        'terms': TERM_CHOICES,
        'group': group,
    }
    return render(request, 'exams/ai_generate.html', context)


@login_required
def ai_review_exam(request):
    teacher = request.user.teacher_profile
    questions = request.session.get('ai_questions')
    exam_data = request.session.get('ai_exam_data')

    if not questions or not exam_data:
        messages.error(request, "لا توجد أسئلة لمراجعتها.")
        return redirect('teacher_dashboard')

    if request.method == 'POST':
        # Teacher approved the questions.
        
        # 1. Create Exam if a group is selected
        exam = None
        group_id = exam_data.get('group_id')
        if group_id:
            group = Group.objects.get(id=group_id)
            exam = Exam.objects.create(
                group=group,
                title=exam_data.get('title'),
                is_active=False
            )
            
        subject = Subject.objects.get(id=exam_data['subject_id'])
        
        # 2. Iterate through edited POST data to create questions
        # Since forms are dynamic, we iterate through num_questions
        for i in range(len(questions)):
            q_text = request.POST.get(f'q_{i}_text')
            q_a = request.POST.get(f'q_{i}_a')
            q_b = request.POST.get(f'q_{i}_b')
            q_c = request.POST.get(f'q_{i}_c')
            q_d = request.POST.get(f'q_{i}_d')
            q_correct = request.POST.get(f'q_{i}_correct')
            q_lesson_name = request.POST.get(f'q_{i}_lesson')
            
            if not q_text: continue # Deleted or empty

            # Try to find the matching lesson from selected lessons to link to bank
            lesson_obj = None
            for l_id in exam_data['lesson_ids']:
                l = CurriculumLesson.objects.get(id=l_id)
                if l.title == q_lesson_name:
                    lesson_obj = l
                    break
            
            if not lesson_obj and exam_data['lesson_ids']:
                lesson_obj = CurriculumLesson.objects.get(id=exam_data['lesson_ids'][0])

            # A. Add to Group Exam
            if exam:
                Question.objects.create(
                    exam=exam,
                    text=q_text,
                    option_a=q_a,
                    option_b=q_b,
                    option_c=q_c,
                    option_d=q_d,
                    correct_answer=q_correct,
                    marks=1
                )

            # B. Add to Global Question Bank
            BankQuestion.objects.create(
                text=q_text,
                option_a=q_a,
                option_b=q_b,
                option_c=q_c,
                option_d=q_d,
                correct_answer=q_correct,
                difficulty=exam_data['difficulty'],
                lesson=lesson_obj,
                unit=lesson_obj.unit if lesson_obj else None,
                subject=subject,
                grade=exam_data['grade'],
                created_by=teacher
            )

        # 3. Increment limit
        teacher.ai_exams_used += 1
        teacher.save()

        # Clear session
        del request.session['ai_questions']
        del request.session['ai_exam_data']

        messages.success(request, "تم اعتماد الأسئلة بنجاح وحفظها في بنك الأسئلة.")
        if exam:
            return redirect('exam_manage', exam_id=exam.id)
        return redirect('teacher_dashboard')

    return render(request, 'exams/ai_review.html', {
        'questions': questions,
        'exam_data': exam_data
    })
