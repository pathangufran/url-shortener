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