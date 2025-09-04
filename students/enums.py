from enum import Enum


class StudentOnboardingSteps(Enum):
    """Student onboarding steps - matches old backend pattern"""
    STUDENT_PRIMARY_INFO = 'student_primary_info'
    STUDENT_EDUCATION = 'student_education'
    STUDENT_EXPERIENCE = 'student_experience'
    STUDENT_FOREIGN_UNIVERSITY = 'student_foreign_university'
    STUDENT_FINANCIAL_INFO = 'student_financial_info'
    STUDENT_FINANCER_INFO = 'student_financer_info'
    STUDENT_DOCUMENTS_UPLOAD = 'student_documents_upload'

    @classmethod
    def choices(cls):
        return [(step.value, step.value.replace('_', ' ').title()) for step in cls]

    @classmethod
    def values(cls):
        return [step.value for step in cls]


class AbstractEnumChoices(Enum):
    @classmethod
    def choices(cls):
        return [(tag.name, tag.value) for tag in cls]

    @classmethod
    def values(cls):
        return [tag.value for tag in cls]


class ServiceList(AbstractEnumChoices):
    ADMIN = "ADMIN"
    BANK_ADMIN = "BANK_ADMIN"
    PRIYO_PAY = "PRIYO_PAY"
    BD_PAY = "BD_PAY"
    STUDENT = 'STUDENT'
    API_BACKEND = 'API_BACKEND'

    @classmethod
    def get_student_service_list(cls):
        return [
            ServiceList.ADMIN.value,
            ServiceList.BANK_ADMIN.value,
            ServiceList.PRIYO_PAY.value,
            ServiceList.BD_PAY.value,
            ServiceList.STUDENT.value
        ]


class SubServiceList(AbstractEnumChoices):
    WEB_BROWSER = "WEB_BROWSER"
    ANDROID_APP = "ANDROID_APP"
