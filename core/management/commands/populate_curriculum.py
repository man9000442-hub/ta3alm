from django.core.management.base import BaseCommand
from core.models import Subject, CurriculumUnit, CurriculumLesson

class Command(BaseCommand):
    help = 'Populates the database with sample curriculum data for AI exam generation'

    def handle(self, *args, **kwargs):
        self.stdout.write("Starting to populate curriculum...")

        # 1. Ensure a basic subject exists
        subject, created = Subject.objects.get_or_create(name="اللغة العربية")
        subject_science, _ = Subject.objects.get_or_create(name="العلوم")
        subject_math, _ = Subject.objects.get_or_create(name="الرياضيات")

        # 2. Add sample units and lessons for Arabic 1st Prep (Term 1)
        grade = '1_prep'
        term = '1'

        # Unit 1: Arabic
        u1, _ = CurriculumUnit.objects.get_or_create(
            subject=subject, grade=grade, term=term, order=1,
            defaults={'title': "الوحدة الأولى: رحلة عبر الفضاء"}
        )
        CurriculumLesson.objects.get_or_create(unit=u1, order=1, defaults={'title': "ظواهر كونية"})
        CurriculumLesson.objects.get_or_create(unit=u1, order=2, defaults={'title': "مجموعتنا الشمسية"})

        # Unit 2: Arabic
        u2, _ = CurriculumUnit.objects.get_or_create(
            subject=subject, grade=grade, term=term, order=2,
            defaults={'title': "الوحدة الثانية: رحلة على كوكب الأرض"}
        )
        CurriculumLesson.objects.get_or_create(unit=u2, order=1, defaults={'title': "شكل الأرض وأبعادها"})
        CurriculumLesson.objects.get_or_create(unit=u2, order=2, defaults={'title': "الليل والنهار"})
        CurriculumLesson.objects.get_or_create(unit=u2, order=3, defaults={'title': "فصول السنة"})

        # Unit 1: Science (1st Prep Term 1)
        u3, _ = CurriculumUnit.objects.get_or_create(
            subject=subject_science, grade=grade, term=term, order=1,
            defaults={'title': "الوحدة الأولى: المادة وتركيبها"}
        )
        CurriculumLesson.objects.get_or_create(unit=u3, order=1, defaults={'title': "المادة وخواصها"})
        CurriculumLesson.objects.get_or_create(unit=u3, order=2, defaults={'title': "تركيب المادة"})
        CurriculumLesson.objects.get_or_create(unit=u3, order=3, defaults={'title': "التركيب الذري للمادة"})

        # Note to user: This is a sample. The full curriculum is massive.
        
        self.stdout.write(self.style.SUCCESS("Successfully populated sample curriculum!"))
