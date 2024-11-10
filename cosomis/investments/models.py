from boto3.session import Session
from botocore.exceptions import NoCredentialsError, ClientError
from django.conf import settings
from django.db import models
from cosomis.models_base import BaseModel
from django.utils.translation import gettext_lazy as _

from administrativelevels.models import AdministrativeLevel, Project, Task, Sector
from usermanager.models import User


class PackageQuerySet(models.QuerySet):
    def get_active_cart(self, user):
        """Get active invoice for user"""
        qs = self.model.objects.filter(user=user, status=Package.PENDING_SUBMISSION)
        package = qs.last()
        if qs.count() > 1:
            qs = qs.exclude(id=package.id)
            for obj in qs:
                obj.status = Package.REJECTED
                obj.save()
        elif qs.count() < 1:
            return self.model.objects.create(
                user=user, status=Package.PENDING_SUBMISSION
            )
        return package


class Investment(BaseModel): # Investment module
    NOT_FUNDED = "N"
    FUNDED = "F"
    IN_PROGRESS = "P"
    COMPLETED = "C"
    PAUSED = "PA"
    PROJECT_STATUS_CHOICES = (
        (NOT_FUNDED, _("Not Funded")),
        (FUNDED, _("Funded")),
        (IN_PROGRESS, _("In Progress")),
        (COMPLETED, _("Completed")),
        (PAUSED, _("Paused")),
    )

    PRIORITY = "p"
    SUBPROJECT = "s"
    INVESTMENT_STATUS_CHOICES = (
        (PRIORITY, _("Priority")),
        (SUBPROJECT, _("SubProject")),
    )
    ranking = models.PositiveIntegerField(null=True, blank=True)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    responsible_structure = models.CharField(max_length=255, null=True, blank=True)
    administrative_level = models.ForeignKey(
        AdministrativeLevel, on_delete=models.CASCADE, related_name="investments"
    )
    sector = models.ForeignKey(
        Sector, on_delete=models.CASCADE, related_name="investments"
    )
    estimated_cost = models.PositiveBigIntegerField()
    start_date = models.DateField(null=True)
    duration = models.PositiveIntegerField(help_text=_("In days"))
    delays_consumed = models.PositiveIntegerField(help_text=_("In days"))
    physical_execution_rate = models.PositiveIntegerField(help_text=_("Percentage"))
    financial_implementation_rate = models.PositiveIntegerField(
        help_text=_("Percentage")
    )
    # project_manager_id // TBD Probably is the moderator
    investment_status = models.CharField(
        max_length=30, choices=INVESTMENT_STATUS_CHOICES, default=PRIORITY
    )
    project_status = models.CharField(
        max_length=30, choices=PROJECT_STATUS_CHOICES, default=NOT_FUNDED
    )
    endorsed_by_youth = models.BooleanField(default=False)
    endorsed_by_women = models.BooleanField(default=False)
    endorsed_by_agriculturist = models.BooleanField(default=False)
    endorsed_by_pastoralist = models.BooleanField(default=False)
    climate_contribution = models.BooleanField(default=False)
    climate_contribution_text = models.TextField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True, verbose_name=_("Latitude"))
    longitude = models.FloatField(null=True, blank=True, verbose_name=_("Longitude"))
    funded_by = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    no_sql_id = models.CharField(max_length=255)
    def __str__(self):
        return f'{self.title}'


class Package(BaseModel):  # investments module (orden de compra(cart de invesments(products)))
    PENDING_SUBMISSION = "PS"
    PENDING_APPROVAL = "P"
    APPROVED = "A"
    REJECTED = "R"
    UNDER_EXECUTION = "E"
    PARTIALLY_APPROVED = "PA"
    STATUS = (
        (PENDING_SUBMISSION, _("Pending Submission")),
        (PENDING_APPROVAL, _("Pending Approval")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
        (UNDER_EXECUTION, _("Under Execution")),
        (PARTIALLY_APPROVED, _("Partially Approved")),
    )

    objects = PackageQuerySet.as_manager()

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="packages",
        null=True,
        blank=True,
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="packages")
    source = models.CharField(
        max_length=255,
        help_text=_("Source of the funding, e.g., a particular organization or grant"),
        blank=True,
        null=True,
    )
    funded_investments = models.ManyToManyField(Investment, through="PackageFundedInvestment", related_name="packages")
    draft_status = models.BooleanField(default=True)
    status = models.CharField(max_length=50, choices=STATUS, default=PENDING_SUBMISSION)

    review_by = models.ForeignKey(User, on_delete=models.SET_NULL,
                                  help_text=_("User who reviews the status of the Package. This user must be a moderator."),
                                  null=True, blank=True)

    rejection_reason = models.TextField(null=True, blank=True)

    def estimated_final_cost(self):
        return self.funded_investments.all().aggregate(
            estimated_final_cost=models.Sum("estimated_cost")
        )["estimated_final_cost"]

class PackageFundedInvestment(BaseModel):
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    investment = models.ForeignKey(Investment, on_delete=models.CASCADE)
    PENDING_APPROVAL = "P"
    APPROVED = "A"
    REJECTED = "R"
    STATUS = (
        (PENDING_APPROVAL, _("Pending Approval")),
        (APPROVED, _("Approved")),
        (REJECTED, _("Rejected")),
    )

    status = models.CharField(max_length=50, choices=STATUS, default=PENDING_APPROVAL)
    rejection_reason = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "investments_package_funded_investments"


class Attachment(BaseModel):
    """
    parent info and tasks info
    """
    AWS_STORAGE_BUCKET_NAME = settings.AWS_STORAGE_BUCKET_NAME
    AWS_ACCESS_KEY_ID = settings.AWS_ACCESS_KEY_ID
    AWS_SECRET_ACCESS_KEY = settings.AWS_SECRET_ACCESS_KEY

    PHOTO = "Photo"
    DOCUMENT = "Document"
    TYPE_CHOICES = ((PHOTO, _("Photo")), (DOCUMENT, _("Document")))

    adm = models.ForeignKey(
        AdministrativeLevel, on_delete=models.CASCADE, related_name="attachments", null=True, blank=True
    )
    investment = models.ForeignKey(
        Investment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="attachments",
    )
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    url = models.URLField(max_length=300)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default=DOCUMENT)

    name = models.CharField(max_length=255, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0)

    @classmethod
    def investment_upload(cls, investment, image, object_name=None):
        s3_client = Session(aws_access_key_id=cls.AWS_ACCESS_KEY_ID, aws_secret_access_key=cls.AWS_SECRET_ACCESS_KEY).client("s3")

        try:
            if object_name is None:
                object_name = image.name

            response = s3_client.upload_fileobj(
                image, cls.AWS_STORAGE_BUCKET_NAME, object_name
            )
            file_url = f"https://{cls.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{object_name}"

            new_attachment = cls.objects.create(
                name=object_name,
                type=cls.PHOTO,
                investment=investment,
                url=file_url
            )

            return True, new_attachment

        except NoCredentialsError:
            return False, "Credentials not available"

        except ClientError as e:
            return False, f"Failed to upload file: {e}"
