from django.contrib.auth.models import User
from ..enums import StudentOnboardingSteps
from ..models import (
    StudentOnboardingStep, StudentPrimaryInfo, UserEducation, 
    UserExperience, UserForeignUniversity, UserFinancialInfo, 
    UserFinancerInfo, Documents
)

class StudentOnboardingStepManager:
    """Manages student onboarding steps - matches priyo_pay_backend pattern"""
    
    def __init__(self, user: User):
        self.user = user
    
    def verify_step_completed(self, step: str) -> bool:
        """Verify if a step is completed"""
        if step == StudentOnboardingSteps.STUDENT_PRIMARY_INFO.value:
            return StudentPrimaryInfo.objects.filter(user=self.user).exists()
        elif step == StudentOnboardingSteps.STUDENT_EDUCATION.value:
            return UserEducation.objects.filter(user=self.user).exists()
        elif step == StudentOnboardingSteps.STUDENT_EXPERIENCE.value:
            return UserExperience.objects.filter(user=self.user).exists()
        elif step == StudentOnboardingSteps.STUDENT_FOREIGN_UNIVERSITY.value:
            return UserForeignUniversity.objects.filter(user=self.user).exists()
        elif step == StudentOnboardingSteps.STUDENT_FINANCIAL_INFO.value:
            return UserFinancialInfo.objects.filter(user=self.user).exists()
        elif step == StudentOnboardingSteps.STUDENT_FINANCER_INFO.value:
            return UserFinancerInfo.objects.filter(user=self.user).exists()
        elif step == StudentOnboardingSteps.STUDENT_DOCUMENTS_UPLOAD.value:
            return Documents.objects.filter(user=self.user).exists()
        return False
    
    def add_step(self, step: str, check_completion=True):
        """Add a step to user's onboarding progress"""
        if check_completion and not self.verify_step_completed(step):
            return None, False
        return StudentOnboardingStep.objects.get_or_create(
            user=self.user, 
            step=step,
            defaults={'is_completed': True}
        )
    
    def get_student_onboarding_flow(self):
        """Get student onboarding flow status"""
        finished_steps = self.user.student_onboarding_steps.filter(
            is_completed=True
        ).values_list('step', flat=True)
        
        expected_steps = StudentOnboardingSteps.get_expected_student_onboarding_flow()
        
        return [
            {
                "step": step,
                "finished": step in finished_steps
            }
            for step in expected_steps
        ]