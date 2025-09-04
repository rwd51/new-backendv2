from error_handling.custom_exception import CustomErrorWithCode, CustomValidationError
from custom_api_exceptions import SessionExpired


class CUSTOM_ERROR_LIST:
    NO_API_KEY_1001 = CustomErrorWithCode(code=1001, message='No API key provided')
    INVALID_API_KEY_1002 = CustomErrorWithCode(code=1002, message='Invalid API key')
    INVALID_HMAC_SIG_1003 = CustomErrorWithCode(code=1003, message='Hmac signature could not be validated')
    PERMISSION_DENIED_API_1004 = CustomErrorWithCode(code=1004, message='You are not permitted to access this API')
    NOT_CONFIGURED_WEBHOOK_1005 = CustomErrorWithCode(code=1005, message='Web hook not configured')
    COULD_NOT_SEND_EMAIL_1006 = CustomErrorWithCode(code=1006, message='Could not send email')
    INACCESSIBLE_ENDPOINT_1007 = CustomErrorWithCode(code=1007, message='You are not permitted to access this API')

    DUPLICATE_MOBILE_2002 = CustomErrorWithCode(code=2002, message='Duplicate Mobile')
    MOBILE_ALREADY_REGISTERED_2003 = CustomErrorWithCode(code=2003, message='Mobile Number already registered')
    USER_MOBILE_ALREADY_VERIFIED_2004 = CustomErrorWithCode(code=2004, message='User already has a verified mobile')
    USER_EMAIL_ALREADY_VERIFIED_2005 = CustomErrorWithCode(code=2005, message='User already has a verified email')
    USER_SOLID_ID_NOT_FOUND_2006 = CustomErrorWithCode(code=2006, message='User does not have any solid user id')
    MOBILE_NOT_REGISTERED_2007 = CustomErrorWithCode(code=2007, message='Mobile Number not registered')
    USER_MOBILE_NOT_VERIFIED_2008 = CustomErrorWithCode(code=2008,
                                                        message='User doesn\'t have a verified mobile number')
    USER_MOBILE_NOT_MATCHED_2009 = CustomErrorWithCode(code=2009, message='Mobile number doesn\'t match with the user')
    USER_EMAIL_DOES_NOT_EXIST_2010 = CustomErrorWithCode(code=2010, message='User doesn\'t have an email address')
    USER_EMAIL_NOT_MATCHED_2011 = CustomErrorWithCode(code=2011, message='Email address doesn\'t match with the user')
    INVALID_MEDIUM_TYPE_FOR_OTP_2012 = CustomErrorWithCode(code=2012, message='invalid medium type for OTP')
    WRONG_OTP_CONTEXT_2013 = CustomErrorWithCode(code=2013, message='wrong OTP context')
    FILE_UPLOAD_FAILED = CustomErrorWithCode(code=2014, message='Failed to upload file')

    @classmethod
    def INVALID_INPUT_FIELD_3001(cls, message):
        return CustomErrorWithCode(3001, message)

    @classmethod
    def SOLID_REMOTE_API_ERROR_4002(cls, message):
        return CustomErrorWithCode(4002, message)

    @classmethod
    def SYNCTERA_REMOTE_API_ERROR_4002(cls, message):
        return CustomErrorWithCode(4002, message)

    @classmethod
    def DB_NOT_FOUND_ERROR_4003(cls, message):
        return CustomErrorWithCode(4003, message)

    @classmethod
    def DB_GENERAL_ERROR_4004(cls, message=''):
        return CustomErrorWithCode(4004, message)

    PUBSUB_TIMEOUT_ERROR_4005 = CustomErrorWithCode(code=4005, message='Pubsub timeout')
    WEBHOOK_EVENT_NOT_FOUND_4006 = CustomErrorWithCode(code=4006, message='Unknown event')

    REDIS_LOCK_ERROR_4007 = CustomErrorWithCode(code=4007, message='The requested entity is now currently locked')

    @classmethod
    def CUSTOM_VALIDATION_ERROR_4008(cls, message):
        return CustomValidationError(code=4008, message=message)

    @classmethod
    def FAILED_TO_CREATE_ERROR_4009(cls, message):
        return CustomErrorWithCode(code=4009, message=message)

    @classmethod
    def PLAID_REMOTE_API_ERROR_4010(cls, message):
        return CustomErrorWithCode(4010, message)

    @classmethod
    def SOLID_DEBIT_CARD_TOKENIZE_ERROR_4011(cls, message):
        return CustomErrorWithCode(4011, message)

    @classmethod
    def VGS_DEBIT_CARD_LINKING_ERROR_4012(cls, message):
        return CustomErrorWithCode(4012, message)

    @classmethod
    def USER_PERMISSION_ERROR_4013(cls, message):
        return CustomErrorWithCode(4013, message)

    NOT_IMPLEMENTED_ERROR_4014 = CustomErrorWithCode(code=4014, message='Method not implemented yet')
    BALANCE_MISMATCH_ERROR_4015 = CustomErrorWithCode(code=4015, message='Balance mismatch error')
    NO_MATCHING_FEE_FOUND_4016 = CustomErrorWithCode(code=4016, message='No matching fee found for this transactions')
    CONNECTION_ERROR_4017 = CustomErrorWithCode(code=4017, message='Connection error')

    OTP_VERIFICATION_MISSING_ERRR_4018 = CustomErrorWithCode(code=4018, message='Please verify with OTP first')
    OTP_GENERATION_MISSING_ERROR_4019 = CustomErrorWithCode(code=4019, message='Please generate a valid OTP first')
    WRONG_OTP_4020 = CustomErrorWithCode(code=4020, message='Wrong OTP')
    OTP_BLOCKED_4021 = \
        CustomErrorWithCode(code=4021, message='The requested resource has been blocked for the next 24 hours')

    @classmethod
    def OTP_TIMEOUT_ERROR_4022(cls, seconds):
        human_readable_time = get_human_readable_time_from_second(seconds)
        return CustomErrorWithCode(4022, f"The requested resource has been blocked. "
                                         f"Please try again after {human_readable_time}")

    MISSING_INFO_FROM_HEADER_4023 = \
        CustomErrorWithCode(code=4023, message="Device fingerprint and/or device type is missing in request header")

    INVALID_PHONE_NUMBER_4024 = CustomErrorWithCode(4024, message="The provided phone number is invalid")

    SESSION_EXPIRED_4025 = SessionExpired(4025)

    OTP_SENDING_FAILED_4026 = CustomErrorWithCode(code=4026, message="Failed to send OTP")

    @classmethod
    def AUTH_INVALID_USER_DATA_4027(cls, message):
        return CustomErrorWithCode(code=4027, message=message)

    @classmethod
    def PERSONA_API_CLIENT_ERROR(cls, message):
        return CustomErrorWithCode(4028, message)

    @classmethod
    def ZENDESK_API_ERROR(cls, message):
        return CustomErrorWithCode(4029, message)

    EMAIL_SEND_ERROR = CustomErrorWithCode(code=4030, message="Failed to send email")

    @classmethod
    def PAYMENT_GATEWAY_API_CLIENT_ERROR(cls, message):
        return CustomErrorWithCode(4030, message)

    PERSONA_VERIFICATION_NOT_COMPLETE = CustomErrorWithCode(code=4031, message="Persona verification not complete")

    @classmethod
    def PORICHOY_API_ERROR(cls, message):
        return CustomErrorWithCode(4032, message)

    @classmethod
    def DUE_PROCESSING_ERROR(cls, message):
        return CustomErrorWithCode(4033, message)

    UNHANDLED_UCB_ERROR = CustomErrorWithCode(code=4034, message="Unhandled UCB Error")
    UCB_AUTHENTICATION_ERROR = CustomErrorWithCode(code=4035, message="Failed to authenticate at UCB")
    UCB_NOT_VALID_ACCOUNT = CustomErrorWithCode(code=4036, message="Not valid account at UCB")
    UCB_QUERY_TXN_FAILED = CustomErrorWithCode(code=4037, message="Failed to query transaction at UCB")

    @classmethod
    def STATEMENT_GENERATION_ERROR(cls, message):
        return CustomErrorWithCode(4038, message)


def get_human_readable_time_from_second(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    time_str = ""
    time_str += f"{hours} hour(s) " if hours > 0 else ""
    time_str += f"{minutes} minute(s) " if minutes > 0 else ""
    time_str += f"{seconds} second(s)" if seconds > 0 else ""
    return time_str.strip()
