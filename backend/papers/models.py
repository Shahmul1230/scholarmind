from django.db import models


class Paper(models.Model):
    STATUS_CHOICES = [
        ("uploaded", "Uploaded"),
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    ]

    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="papers/")
    extracted_text = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="uploaded"
    )
    total_pages = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class PaperChunk(models.Model):
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="chunks"
    )
    chunk_index = models.IntegerField()
    content = models.TextField()

    page_number = models.IntegerField(null=True, blank=True)
    start_line = models.IntegerField(null=True, blank=True)
    end_line = models.IntegerField(null=True, blank=True)
    section_title = models.CharField(max_length=255, blank=True, default="Unknown")

    vector_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.paper.title} - Chunk {self.chunk_index}"


class DocumentAnalysis(models.Model):
    STATUS_CHOICES = [
        ("processing", "Processing"),
        ("ready", "Ready"),
        ("failed", "Failed"),
    ]

    paper = models.OneToOneField(
        Paper,
        on_delete=models.CASCADE,
        related_name="analysis"
    )

    document_type = models.CharField(max_length=100, default="General Academic Document")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="processing")

    profile = models.TextField(blank=True, default="")
    section_summaries = models.JSONField(default=dict, blank=True)
    key_points = models.JSONField(default=dict, blank=True)
    source_coverage = models.JSONField(default=dict, blank=True)

    error_message = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analysis for {self.paper.title}"


class ChatMessage(models.Model):
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
    ]

    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="chat_messages"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    message = models.TextField()

    # Used/relevant sources for this specific assistant answer
    sources = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.paper.title} - {self.role}"
    

class RelatedPaper(models.Model):
    paper = models.ForeignKey(
        Paper,
        on_delete=models.CASCADE,
        related_name="related_papers"
    )

    source = models.CharField(max_length=100, default="OpenAlex")
    openalex_id = models.CharField(max_length=255, blank=True, default="")
    title = models.TextField(blank=True, default="")
    authors = models.JSONField(default=list, blank=True)
    year = models.IntegerField(null=True, blank=True)
    publication_date = models.CharField(max_length=50, blank=True, default="")
    venue = models.TextField(blank=True, default="")
    doi = models.CharField(max_length=255, blank=True, default="")
    url = models.TextField(blank=True, default="")
    pdf_url = models.TextField(blank=True, default="")
    open_access = models.BooleanField(default=False)
    open_access_status = models.CharField(max_length=100, blank=True, default="")
    work_type = models.CharField(max_length=100, blank=True, default="")
    cited_by_count = models.IntegerField(default=0)
    abstract = models.TextField(blank=True, default="")
    concepts = models.JSONField(default=list, blank=True)

    search_query = models.TextField(blank=True, default="")
    why_related = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-cited_by_count", "-year"]

    def __str__(self):
        return self.title[:120] if self.title else "Related Paper"
