from rest_framework import serializers
from .models import Room, Review, Booking, Payment


class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = '__all__'


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = '__all__'


class BookingSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'


class AllSerializer(serializers.ModelSerializer):

    def to_representation(self, instance):
        data = super().to_representation(instance)
        class_room = RoomSerializer(instance)
        class_booking = BookingSerializer(instance)
        class_review = ReviewSerializer(instance)
        class_payment = PaymentSerializer(instance)

        data.update(class_room)
        data.update(class_booking)
        data.update(class_review)
        data.update(class_payment)
        return data

    # def get_class_room(self, obj):
    #     serializer = RoomSerializer(obj)
    #     return serializer.data
    #
    # def get_class_booking(self, obj):
    #     serializer = BookingSerializer(obj)
    #     return serializer.data
    # def get_class_review(self, obj):
    #     serializer = ReviewSerializer(obj)
    #     return serializer.data
    # def get_class_payment(self, obj):
    #     serializer = PaymentSerializer(obj)
    #     return serializer.data