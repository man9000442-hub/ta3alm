import os
import json
import google.generativeai as genai
from django.conf import settings

# تهيئة Gemini API
# يجب أن نضمن وجود المفتاح في .env وتحميله في settings
# أو قراءته مباشرة من البيئة
API_KEY = os.environ.get('GEMINI_API_KEY')
if API_KEY:
    genai.configure(api_key=API_KEY)

def generate_exam_questions(grade_name, subject_name, term_name, lessons_list, difficulty, num_questions, extra_notes=""):
    """
    يتصل بـ Gemini لتوليد أسئلة متعددة الخيارات بصيغة JSON.
    """
    if not API_KEY:
        raise ValueError("مفتاح GEMINI_API_KEY غير موجود في إعدادات البيئة.")

    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    # تجهيز قائمة الدروس كنص
    lessons_text = "\n".join([f"- {l.title} (الوحدة: {l.unit.title})" for l in lessons_list])

    prompt = f"""
أنت مدرس خبير وخبير في وضع الامتحانات للمناهج المصرية.
قم بوضع امتحان مكون من {num_questions} سؤال اختيار من متعدد (MCQ) بمستوى صعوبة ({difficulty}) 
للصف: {grade_name}
المادة: {subject_name}
الترم: {term_name}

بناءً على الدروس التالية حصراً:
{lessons_text}

ملاحظات إضافية من المدرس: {extra_notes}

التعليمات الهامة جداً:
1. يجب أن تكون مخرجاتك حصراً بصيغة JSON array صالحة للتحليل (Valid JSON array of objects). لا تضف أي نص أو شرح أو markdown قبل أو بعد الـ JSON. 
2. يجب أن يحتوي كل كائن سؤال (Object) في الـ JSON على الحقول الإنجليزية التالية بالضبط:
   - "text": نص السؤال باللغة العربية.
   - "option_a": الخيار الأول (أ)
   - "option_b": الخيار الثاني (ب)
   - "option_c": الخيار الثالث (ج)
   - "option_d": الخيار الرابع (د)
   - "correct_answer": الحرف الإنجليزي للإجابة الصحيحة ويجب أن يكون حصراً ("A" أو "B" أو "C" أو "D")
   - "difficulty": مستوى الصعوبة ("easy" أو "medium" أو "hard")
   - "lesson_name": اسم الدرس الذي ينتمي إليه هذا السؤال (من القائمة المعطاة)

مثال على المخرج المطلوب:
[
  {{
    "text": "ما هو عاصمة مصر؟",
    "option_a": "الإسكندرية",
    "option_b": "القاهرة",
    "option_c": "الأقصر",
    "option_d": "أسوان",
    "correct_answer": "B",
    "difficulty": "easy",
    "lesson_name": "موقع مصر"
  }}
]
"""

    generation_config = genai.types.GenerationConfig(
        temperature=0.7,
        response_mime_type="application/json",
    )

    response = model.generate_content(prompt, generation_config=generation_config)
    
    try:
        # أحياناً يضع المودل ```json ... ``` لذلك ننظفها
        text = response.text.strip()
        if text.startswith('```json'):
            text = text[7:]
        if text.endswith('```'):
            text = text[:-3]
            
        questions = json.loads(text.strip())
        return questions
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from Gemini: {e}")
        print(f"Raw output: {response.text}")
        raise ValueError("فشل في تحليل المخرجات من الذكاء الاصطناعي كـ JSON. حاول مرة أخرى.")
    except Exception as e:
        raise ValueError(f"خطأ أثناء الاتصال بالذكاء الاصطناعي: {str(e)}")
