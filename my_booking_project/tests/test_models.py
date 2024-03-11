import pytest
from booking_app.models import Room, MealPlan


@pytest.mark.django_db
def test_calculate_total_price():
    # Подготовка данных
    meal_plan = MealPlan.objects.create(type='breakfast', price=100)
    room = Room.objects.create(number='101', category='single', guests=1, price=500)

    # Выполнение тестируемого метода
    total_price = room.calculate_total_price(meal_plan.type)

    # Проверка результата
    assert total_price == 600
