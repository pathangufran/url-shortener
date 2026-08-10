from datetime import timedelta
from django.utils import timezone
from rest_framework import serializers

class AnalyticsBreakdownSerializer(serializers.Serializer):
    """
    Serializer for analytics breakdown data.
    """

    country = serializers.CharField(required=False,
        allow_null=True,)
    browser = serializers.CharField(required=False,
        allow_null=True,)
    device = serializers.CharField(required=False,
        allow_null=True,)
    referrer = serializers.CharField(required=False,
        allow_null=True,)
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

    start_date = serializers.DateField(required=False,)
    end_date = serializers.DateField(required=False,)

    def validate(self,attrs):
        start_date = attrs.get("start_date")
        end_date = attrs.get("end_date")

        if start_date and end_date:
            if start_date > end_date:
                raise serializers.ValidationError(
                    {
                        "date_range": (
                            "start_date must be before "
                            "or equal to end_date."
                        )
                    }
                )

            today = timezone.localdate()
            if start_date and start_date > today:
                raise serializers.ValidationError(
                    {
                        "start_date": (
                            "start_date cannot be in the future."
                        )
                    }
                )
            if end_date and end_date > today:
                raise serializers.ValidationError(
                    {
                        "end_date": (
                            "end_date cannot be in the future."
                        )
                    }
                )

        return attrs