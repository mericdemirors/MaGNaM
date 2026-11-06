from django.db import models
from django.core.validators import (
    MinLengthValidator,
    MinValueValidator,
    MaxValueValidator,
)
from ProfilePageApp.models import Profile

from .globals import *


class KanbanTaskTag(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    label = models.CharField(max_length=KANBAN_TAG_LABEL_LEN, unique=True)

    def __str__(self):
        nl = "\n"
        return f"KanbanTaskTag {nl.join(map(str, self.__dict__.items()))}"


class KanbanTask(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    creator = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="tasks")
    description = models.TextField(
        max_length=KANBAN_MAX_DESCRIPTION_LEN,
        validators=[MinLengthValidator(KANBAN_MIN_DESCRIPTION_LEN)],
    )
    tags = models.ManyToManyField(KanbanTaskTag, related_name="tasks")
    importance = models.IntegerField(
        validators=[
            MinValueValidator(KANBAN_MIN_IMPORTANCE),
            MaxValueValidator(KANBAN_MAX_IMPORTANCE),
        ],
        default=KANBAN_MIN_IMPORTANCE,
    )

    class Meta:
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"KanbanTask {nl.join(map(str, self.__dict__.items()))}"


class KanbanTaskVote(models.Model):
    id = models.BigAutoField(primary_key=True, editable=False)
    voter = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name="votes")
    task = models.ForeignKey(KanbanTask, on_delete=models.CASCADE, related_name="votes")
    vote = models.BooleanField()  # True = upvote, False = downvote

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["voter", "task"], name="unique_task_vote")
        ]
        ordering = ["-id"]

    def __str__(self):
        nl = "\n"
        return f"KanbanTaskVote {nl.join(map(str, self.__dict__.items()))}"
