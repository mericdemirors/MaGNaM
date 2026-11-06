from rest_framework import serializers
from .models import KanbanTask, KanbanTaskTag, KanbanTaskVote

from utils.helper_validators import *
from .globals import *

# === Tag === # === Tag === # === Tag === # === Tag === #


class ReturnKanbanTaskTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = KanbanTaskTag
        fields = ("id", "label")


# === Vote === # === Vote === # === Vote === # === Vote === #


class ReturnKanbanTaskVoteSerializer(serializers.ModelSerializer):
    voter_id = serializers.IntegerField(source="voter.id", read_only=True)
    task_id = serializers.IntegerField(source="task.id", read_only=True)

    class Meta:
        model = KanbanTaskVote
        fields = ("id", "voter_id", "task_id", "vote")


# === Task === # === Task === # === Task === # === Task === #


class ReturnKanbanTaskSerializer(serializers.ModelSerializer):
    tags = ReturnKanbanTaskTagSerializer(many=True, read_only=True)
    creator_id = serializers.IntegerField(source="creator.id", read_only=True)

    class Meta:
        model = KanbanTask
        fields = ("id", "creator_id", "description", "tags", "importance")


class ReturnKanbanTaskGallerySerializer(serializers.ModelSerializer):
    creator_id = serializers.IntegerField(source="creator.id", read_only=True)
    tags = ReturnKanbanTaskTagSerializer(many=True, read_only=True)
    num_of_upvotes = serializers.IntegerField(read_only=True)
    num_of_downvotes = serializers.IntegerField(read_only=True)
    is_user_voted = serializers.SerializerMethodField()

    class Meta:
        model = KanbanTask
        fields = (
            "id",
            "creator_id",
            "description",
            "tags",
            "importance",
            "num_of_upvotes",
            "num_of_downvotes",
            "is_user_voted",
        )

    def get_is_user_voted(self, obj):
        user = self.context["request"].user
        if not user.is_authenticated:
            return 0

        profile = user.profile
        vote = obj.votes.filter(voter=profile).first()
        if not vote:
            return 0

        return 1 if vote.vote else -1


class CreateKanbanTaskSerializer(serializers.ModelSerializer):
    description = serializers.CharField(
        validators=[
            validate_text(
                "description",
                min_len=KANBAN_MIN_DESCRIPTION_LEN,
                max_len=KANBAN_MAX_DESCRIPTION_LEN,
            )
        ],
    )

    tags = serializers.PrimaryKeyRelatedField(
        queryset=KanbanTaskTag.objects.all(),
        many=True,
        allow_empty=False,
        validators=[
            validate_pk_relation(
                "tags", min_count=KANBAN_MIN_TAG_COUNT, max_count=KANBAN_MAX_TAG_COUNT
            )
        ],
    )

    importance = serializers.IntegerField(
        validators=[
            validate_number(
                "importance",
                min_val=KANBAN_MIN_IMPORTANCE,
                max_val=KANBAN_MAX_IMPORTANCE,
            )
        ],
    )

    class Meta:
        model = KanbanTask
        fields = ("description", "tags", "importance")

    def create(self, validated_data):
        tags = validated_data.pop("tags")
        task = KanbanTask.objects.create(**validated_data)
        task.tags.set(tags)
        return task
