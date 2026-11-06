from django.urls import reverse
from rest_framework.test import APIRequestFactory
from ..models import *
from .base_test import *
from ..globals import *
from ..serializers import *
from utils.test_utils import send_missing_field, send_invalid_field


# ReturnKanbanTaskTagSerializer
class TestReturnKanbanTaskTagSerializerFields(KanbanTaskTagBaseTestCase):
    def test_tag_returned_fields(self):
        _, _, _, tag = self.create_random_valid_object()

        # serialize the object as it's being returned to the frontend
        serializer = ReturnKanbanTaskTagSerializer(tag)
        data = serializer.data

        # check if serialized return contains all the fields it needs to
        self.assertEqual(set(data.keys()), {"id", "label"})


# ReturnKanbanTaskSerializer
class TestReturnKanbanTaskSerializerFields(KanbanTaskBaseTestCase):
    def test_task_returned_fields(self):
        _, _, _, task = self.create_random_valid_object()

        serializer = ReturnKanbanTaskSerializer(task)
        data = serializer.data

        self.assertEqual(
            set(data.keys()), {"id", "creator_id", "description", "tags", "importance"}
        )


# ReturnKanbanTaskVoteSerializer
class TestReturnKanbanTaskVoteSerializerFields(KanbanTaskVoteBaseTestCase):
    def test_vote_returned_fields(self):
        _, _, _, vote = self.create_random_valid_object()

        serializer = ReturnKanbanTaskVoteSerializer(vote)
        data = serializer.data

        self.assertEqual(set(data.keys()), {"id", "voter_id", "task_id", "vote"})


# ReturnKanbanTaskGallerySerializer
class TestReturnKanbanTaskGallerySerializerFields(KanbanTaskBaseTestCase):
    def test_gallery_returned_fields(self):
        _, _, _, task = self.create_random_valid_object()

        # create a dummy request because we need a user to calculate gallery attributes like is_user_voted
        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user

        # pass the request into the serializer context
        serializer = ReturnKanbanTaskGallerySerializer(
            task, context={"request": request}
        )
        data = serializer.data

        self.assertEqual(
            set(data.keys()),
            {
                "id",
                "creator_id",
                "description",
                "tags",
                "importance",
                # these two are added while view is fetching the database
                # they are not serializer native
                # "num_of_upvotes",
                # "num_of_downvotes",
                "is_user_voted",
            },
        )


# CreateKanbanTaskSerializer
class TestCreateKanbanTaskSerializerFields(KanbanTaskBaseTestCase):
    def test_create_returned_fields(self):
        original_vals, _, _ = self.get_random_valid_data()

        serializer = CreateKanbanTaskSerializer(data=original_vals)

        self.assertTrue(serializer.is_valid(), serializer.errors)

        data = serializer.validated_data

        self.assertEqual(set(data.keys()), {"description", "tags", "importance"})


# CreateKanbanTaskSerializer
class TestCreateKanbanTaskSerializerProcessing(KanbanTaskBaseTestCase):
    def test_field_stripping_functionality(self):
        original_vals, _, _ = self.get_random_valid_data()

        stripped_description = original_vals["description"]
        int_importance = original_vals["importance"]

        original_vals["description"] = f"   {stripped_description}   \n\t"

        # we do this to test this try block in the serializer:
        # """ data["importance"] = int(data["importance"]) """"
        original_vals["importance"] = str(int_importance)

        serializer = CreateKanbanTaskSerializer(data=original_vals)

        self.assertTrue(serializer.is_valid(), serializer.errors)
        data = serializer.validated_data

        # check if description is stripped correctly
        self.assertEqual(data["description"], stripped_description)
        self.assertEqual(data["importance"], int_importance)


# CreateKanbanTaskSerializer
class TestCreateKanbanTaskSerializerInvalidData(KanbanTaskBaseTestCase):
    def setUp(self):
        super().setUp()
        self.profile = self.user.profile
        self.tags = self.get_random_tags_value()
        self.url = reverse(f"{self.namespace}:create-kanban-task")
        self.client.force_authenticate(user=self.user)

    def test_create_task_missing_fields(self):
        # we dont test the invalid 'creator' field because creator is fetched like this in the view:
        # """ serializer.save(creator=request.user.profile) """
        # and there are few reasons why we can ignore this case:
        # case1: no user in the request
        #   this is tested in the view permission cases where guest user cannot create tasks
        # case2: no profile in the request.user
        #   user creation trigger profile creation and they are bonded by """ user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile") """
        #   so user with no profile never exists in the db, and profile with no user cannot exist in the db
        # we also dont test the missing tags data because when view passes request data to serializer it creates it
        # even if request data doesn't contain a tags key, serializer creates one with 'tags':[] mapping
        send_missing_field(
            self,
            self.url,
            ["description"],
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )
        send_missing_field(
            self,
            self.url,
            ["tags"],
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )
        send_missing_field(
            self,
            self.url,
            ["importance"],
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )

    def test_create_task_invalid_fields(self):
        # short description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_description_value(L=KANBAN_MIN_DESCRIPTION_LEN - 1),
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )
        # long description
        send_invalid_field(
            self,
            self.url,
            "description",
            self.get_random_description_value(L=KANBAN_MAX_DESCRIPTION_LEN + 10),
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )
        # no tag
        send_invalid_field(
            self,
            self.url,
            "tags",
            [],
            predefined_vals={"creator": self.profile},
        )
        # less tag
        send_invalid_field(
            self,
            self.url,
            "tags",
            self.get_random_tags_value(count=KANBAN_MIN_TAG_COUNT - 1),
            predefined_vals={"creator": self.profile},
        )
        # more tag
        send_invalid_field(
            self,
            self.url,
            "tags",
            self.get_random_tags_value(count=KANBAN_MAX_TAG_COUNT + 1),
            predefined_vals={"creator": self.profile},
        )        
        # low importance
        send_invalid_field(
            self,
            self.url,
            "importance",
            KANBAN_MIN_IMPORTANCE - 1,
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )
        # high importance
        send_invalid_field(
            self,
            self.url,
            "importance",
            KANBAN_MAX_IMPORTANCE + 1,
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )
        # float importance
        send_invalid_field(
            self,
            self.url,
            "importance",
            1.5,
            predefined_vals={"creator": self.profile, "tags": self.tags},
        )
