from datetime import date
from django.utils import timezone
from rest_framework import serializers
from .file_checks import image_check, pdf_check


def validate_text(field_name, min_len=None, max_len=None):
    def validator(value):
        if min_len is not None and len(value) < min_len:
            raise serializers.ValidationError(
                f"{field_name.capitalize()} must be at least {min_len} characters."
            )

        if max_len is not None and len(value) > max_len:
            raise serializers.ValidationError(
                f"{field_name.capitalize()} can be at most {max_len} characters."
            )

    return validator


def validate_links(field_name="links", min_len=None, max_len=None):
    def validator(value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                f"{field_name.capitalize()} must be a list."
            )

        total_len = 0

        for link in value:
            if not isinstance(link, str):
                raise serializers.ValidationError(f"All {field_name} must be strings.")
            link_s = link.strip()
            if len(link_s) == 0:
                continue
            if not link_s.startswith("https:"):
                raise serializers.ValidationError(
                    f"All {field_name} must start with 'https:'."
                )
            total_len += len(link_s)
            if max_len is not None and total_len > max_len:
                raise serializers.ValidationError(
                    f"{field_name.capitalize()} can be at most {max_len} characters."
                )
        if min_len is not None and total_len < min_len:
            raise serializers.ValidationError(
                f"{field_name.capitalize()} must be at least {min_len} characters."
            )

    return validator


def validate_image(min_w, max_w, min_h, max_h, max_file_size):
    def validator(value):
        image_check(
            value,
            min_width=min_w,
            max_width=max_w,
            min_height=min_h,
            max_height=max_h,
            max_file_size=max_file_size,
        )

    return validator


def validate_number(field_name, min_val=None, max_val=None):
    def validator(value):
        try:
            val = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError(
                f"{field_name.capitalize()} must be a number."
            )

        if min_val is not None and val < min_val:
            raise serializers.ValidationError(
                f"{field_name.capitalize()} must be at least {min_val}."
            )

        if max_val is not None and val > max_val:
            raise serializers.ValidationError(
                f"{field_name.capitalize()} can be at most {max_val}."
            )

    return validator


def validate_pk_relation(field_name="tags", min_count=None, max_count=None):
    def validator(value):
        if not isinstance(value, list):
            raise serializers.ValidationError(
                f"{field_name.capitalize()} must be a list."
            )

        # duplicates are discarded by the django

        if min_count is not None and len(value) < min_count:
            raise serializers.ValidationError(
                f"At least {min_count} {field_name} must be selected."
            )

        if max_count is not None and len(value) > max_count:
            raise serializers.ValidationError(
                f"You can select at most {max_count} {field_name}."
            )

    return validator


def validate_pdf(max_file_size, max_pages):
    def validator(value):
        pdf_check(value, max_file_size=max_file_size, max_pages=max_pages)

    return validator


def validate_date(field_name, min_date=None, max_date=None):
    def validator(value):
        # Resolve callable arguments lazily
        actual_min = min_date() if callable(min_date) else min_date
        actual_max = max_date() if callable(max_date) else max_date

        # Convert datetime -> date using Django timezone awareness
        if isinstance(value, timezone.datetime):
            value = (
                timezone.localtime(value).date()
                if timezone.is_aware(value)
                else value.date()
            )

        if not isinstance(value, date):
            raise serializers.ValidationError(
                f"{field_name.capitalize()} must be a valid date."
            )

        if actual_min is not None:
            if isinstance(actual_min, timezone.datetime):
                actual_min = (
                    timezone.localtime(actual_min).date()
                    if timezone.is_aware(actual_min)
                    else actual_min.date()
                )

            if value < actual_min:
                raise serializers.ValidationError(
                    f"{field_name.capitalize()} cannot be before "
                    f"{actual_min.strftime('%Y-%m-%d')}."
                )

        if actual_max is not None:
            if isinstance(actual_max, timezone.datetime):
                actual_max = (
                    timezone.localtime(actual_max).date()
                    if timezone.is_aware(actual_max)
                    else actual_max.date()
                )

            if value > actual_max:
                raise serializers.ValidationError(
                    f"{field_name.capitalize()} cannot be after "
                    f"{actual_max.strftime('%Y-%m-%d')}."
                )

    return validator
