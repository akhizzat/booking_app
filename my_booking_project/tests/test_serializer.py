import pytest
from django.contrib.auth import get_user_model
from booking_app.models import Review
from booking_app.serializer import ReviewSerializer

User = get_user_model()


@pytest.mark.django_db
def test_review_serializer_valid():
    # Предполагается, что пользователь и отзыв уже созданы
    user = User.objects.create_user(email='user@example.com', password='testpass')
    review = Review.objects.create(customer=user, title="Great", review="Text", rating=5)

    serializer = ReviewSerializer(review)
    data = serializer.data

    assert data['title'] == "Great"
    assert data['review'] == "Text"
    assert data['rating'] == 5


@pytest.mark.django_db
def test_review_serializer_save():
    user = User.objects.create_user(email='user@example.com', password='testpass')
    review_data = {'customer': user.id, 'title': 'Great', 'review': 'Text', 'rating': 5}

    serializer = ReviewSerializer(data=review_data)

    assert serializer.is_valid()
    review = serializer.save()

    assert review.title == "Great"
    assert Review.objects.count() == 1


