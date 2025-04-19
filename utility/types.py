from django.db import models

class FileType(models.TextChoices):
    IMAGE = 'image'
    VIDEO = 'video'
    AUDIO = 'audio'
    DOCUMENT = 'document'
    TEXT = 'txt'



class Language(models.TextChoices):
    ENGLISH = 'en'
    ARABIC = 'ar'



class PermissionLevel(models.TextChoices):
    PUBLIC = 'public'
    PRIVATE = 'private'
    USER = 'user'



class DateFormat(models.TextChoices):
    DMY = 'dd/mm/yyyy'
    MDY = 'mm/dd/yyyy'
    YMD = 'yyyy/mm/dd'



class TimeFormat(models.TextChoices):
    TWELVE_HOUR = '12h'
    TWENTY_FOUR_HOUR = '24h'


class Progress(models.TextChoices):
    ZERO = '0%'
    QUARTER = '25%'
    HALF = '50%'
    THREE_QUARTERS = '75%'
    COMPLETE = '100%'


class Holiday(models.TextChoices):
    FULL_DAY = '8 Hours'
    HALF_DAY = '4 Hours'



class Absence(models.TextChoices):
    SICK_LEAVE = 'Sick Leave'
    NONE = '_'



class State(models.TextChoices):
    DONE = 'Done'
    REVIEW = 'Review'   
    INITIAL = 'Initial'


class Status(models.TextChoices):
    PENDING = 'Pending'
    IN_PROGRESS = 'In Progress'
    COMPLETED = 'Completed'


class Priority(models.TextChoices):
    LOW = 'Low'
    MEDIUM = 'Medium'
    HIGH = 'High'
    CRITICAL = 'Critical'

class Role(models.TextChoices):
    ADMIN = 'admin', 'Admin'
    MODERATOR = 'moderator', 'Moderator'
    NORMAL = 'normal', 'Normal User'

class SocialStatus(models.TextChoices):
    SINGLE = 'Single'
    MARRIED = 'Married'
    DIVORCED = 'Divorced'
    WIDOWED = 'Widowed'
