from django.utils import timezone
from rest_framework import serializers


class AnalyticsBreakdownSerializer(serializers.Serializer):
    """
    Serializer for analytics breakdown data.
    """

    country = serializers.CharField(
        required=False,
        allow_null=True,
    )
    browser = serializers.CharField(
        required=False,
        allow_null=True,
    )
    device = serializers.CharField(
        required=False,
        allow_null=True,
    )
    referrer = serializers.CharField(
        required=False,
        allow_null=True,
    )
    clicks = serializers.IntegerField()


class URLAnalyticsResponseSerializer(serializers.Serializer):
    """
    Serializer for URL analytics response.
    """

    total_clicks = serializers.IntegerField()
    unique_visitors = serializers.IntegerField()
    top_countries = AnalyticsBreakdownSerializer(many=True)
    top_browsers = AnalyticsBreakdownSerializer(many=True)
    top_devices = AnalyticsBreakdownSerializer(many=True)
    top_referrers = AnalyticsBreakdownSerializer(many=True)


class AnalyticsFilterSerializer(serializers.Serializer):
    """
    Validate date filters for analytics.
    """

    start_date = serializers.DateField(
        required=False,
    )
    end_date = serializers.DateField(
        required=False,
    )

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"date_range": ("start_date must be before or equal to end_date.")}
            )

        today = timezone.localdate()
        for field, value in (("start_date", start_date), ("end_date", end_date)):
            if value and value > today:
                raise serializers.ValidationError(
                    {field: f"{field} cannot be in the future."}
                )

        return attrs


class ClickEventSerializer(serializers.Serializer):
    """
    Serializer for individual click events.
    """

    id = serializers.UUIDField()
    ip_address = serializers.IPAddressField(
        allow_null=True,
    )
    country = serializers.CharField(
        allow_null=True,
    )
    browser = serializers.CharField(
        allow_null=True,
    )
    device = serializers.CharField(
        allow_null=True,
    )
    referrer = serializers.CharField(
        allow_null=True,
    )
    clicked_at = serializers.DateTimeField()


class ClickEventFilterSerializer(serializers.Serializer):
    """
    Validate filters for click event listing.
    """

    start_date = serializers.DateField(
        required=False,
    )
    end_date = serializers.DateField(
        required=False,
    )
    browser = serializers.CharField(
        required=False,
    )
    device = serializers.CharField(
        required=False,
    )
    country = serializers.CharField(
        required=False,
    )

    def validate(self, attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise serializers.ValidationError(
                {"date_range": ("start_date must be before or equal to end_date.")}
            )

        today = timezone.localdate()
        for field, value in (("start_date", start_date), ("end_date", end_date)):
            if value and value > today:
                raise serializers.ValidationError(
                    {field: f"{field} cannot be in the future."}
                )

        return attrs
